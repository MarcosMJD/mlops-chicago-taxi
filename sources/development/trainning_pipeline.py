import os
import pandas as pd
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.tree import DecisionTreeClassifier
import mlflow
from prefect import flow, task, get_run_logger
from datetime import datetime
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline


class ToDictTransformer(TransformerMixin, BaseEstimator):
    def __init__(self):
        self.columns = None

    def fit(self, df, y=None):
        return self

    def transform(self, df):
        return df.to_dict(orient='records')

    def get_feature_names_out(self, *args, **kwargs):
        return self.columns


def prepareData(df):
    df_new = df.copy()
    df_new.columns = df_new.columns.str.lower().str.replace(' ', '_')

    categorical_columns = list(df_new.dtypes[df_new.dtypes == 'object'].index)

    for c in categorical_columns:
        df_new[c] = df_new[c].str.lower().str.replace(' ', '_')

    max_date = max(df_new['trans_date_trans_time'])

    df_new['hour_of_trans'] = df_new['trans_date_trans_time'].dt.hour
    df_new['day_of_trans'] = df_new['trans_date_trans_time'].dt.weekday
    df_new['age'] = round((max_date - df_new['dob']) / pd.Timedelta('365 days')).astype(
        'int64'
    )

    df_new = df_new[
        [
            'category',
            'amt',
            'gender',
            'city_pop',
            'hour_of_trans',
            'day_of_trans',
            'age',
            'is_fraud',
        ]
    ]
    return df_new


def splitDataset(df: pd.DataFrame, test_size: float, random_state: int) -> pd.DataFrame:

    from sklearn.model_selection import train_test_split

    df_train, df_test = train_test_split(
        df, test_size=test_size, random_state=random_state
    )

    return df_train, df_test


def getTrainingDataset(df_train: pd.DataFrame, df_test: pd.DataFrame):

    df_train = df_train.reset_index(drop=True)
    df_test = df_test.reset_index(drop=True)

    y_train = df_train.is_fraud.values
    y_test = df_test.is_fraud.values

    del df_train["is_fraud"]
    del df_test["is_fraud"]

    return df_train, df_test, y_train, y_test


def model_training(df_train: pd.DataFrame, y, params: dict):

    with mlflow.start_run():
        to_dict = ToDictTransformer()
        dv = DictVectorizer(sparse=False)
        classifier = DecisionTreeClassifier(**params)

        model = Pipeline(
            [
                ('preprocessor1', to_dict),
                ('preprocessor2', dv),
                ('classifier', classifier),
            ]
        )

        model.fit(df_train, y)

    return model


def model_prediction(model, X):

    y_pred = model.predict(X)

    return y_pred


def model_evaluation(y_test, y_pred):

    from sklearn.metrics import roc_auc_score

    score = roc_auc_score(y_test, y_pred)

    return score


params = {
    "max_depth": 15,
    "min_samples_leaf": 15,
    "max_features": 'sqrt',
    "random_state": 42,
}


@task
def train_model(df_train, y_train, params, df_test, y_test):

    model = model_training(df_train, y_train, params=params)
    y_pred = model_prediction(model, df_test)
    score = model_evaluation(y_test, y_pred)
    print(score)
    return model, score


@task
def preprocess(df_raw):

    df = prepareData(df_raw)
    df_train, df_test = splitDataset(df=df, test_size=0.2, random_state=42)
    df_train, df_test, y_train, y_test = getTrainingDataset(df_train, df_test)
    return df_train, df_test, y_train, y_test


@task
def register_models(
    tracking_uri: str, mlflow_experiment_name: str, mlflow_model_name: str, now
):

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)

    experiment_id = client.get_experiment_by_name(mlflow_experiment_name).experiment_id

    client.list_experiments()
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f"attribute.start_time>{int(now)}",
        run_view_type=mlflow.entities.ViewType.ACTIVE_ONLY,
        max_results=1,
    )

    for run in runs:
        run_id = run.info.run_id
        model_uri = f"runs:/{run_id}/model"
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=mlflow_model_name,
        )

    print(f"model: run_id={model_version.run_id} - version={model_version.version}")

    client.transition_model_version_stage(
        name=mlflow_model_name,
        version=model_version.version,
        stage="Staging",
        archive_existing_versions=True,
    )

    latest_versions = client.get_latest_versions(name=mlflow_model_name)
    for version in latest_versions:
        print(f"Version: {version.version}, stage: {version.current_stage}")


@flow
def main_flow():

    PROJECT_ID = os.getenv("PROJECT_ID") or "chicago_taxi"
    MLFLOW_TRACKING_URI = (
        os.getenv("MLFLOW_TRACKING_URI") or "http://52.213.112.212:8080"
    )
    MLFLOW_EXPERIMENT_NAME = "mlflow/" + PROJECT_ID
    MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "chicago-taxi")

    # Setup MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    # Use a subfolder in the S3 bucket
    mlflow.set_experiment(f"{MLFLOW_EXPERIMENT_NAME}")
    mlflow.sklearn.autolog()

    df_raw = pd.read_csv(
        "s3://stg-chicago-taxi-mmjd/data/fraudTrain.csv",
        parse_dates=['trans_date_trans_time', 'dob'],
        index_col=0,
    )

    df_train, df_test, y_train, y_test = preprocess(df_raw)

    now = datetime.now().timestamp() * 1000

    model, score = train_model(df_train, y_train, params, df_test, y_test)

    register_models(
        MLFLOW_TRACKING_URI,
        MLFLOW_EXPERIMENT_NAME,
        MLFLOW_MODEL_NAME,
        now,
    )

    print("Save model successfully")


if __name__ == "__main__":
    main_flow()
