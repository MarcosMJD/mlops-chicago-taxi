import os
import json
from pathlib import Path
from datetime import datetime

import mlflow
import xgboost as xgb
from model import LinReg
from prefect import flow, task, get_run_logger
from hyperopt import STATUS_OK, Trials, hp, tpe, fmin
from sklearn.svm import LinearSVR
from hyperopt.pyll import scope
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Lasso, Ridge, LinearRegression
from sklearn.feature_extraction import DictVectorizer

from development import downloader
from development.preprocessor import Preprocessor


def train_xgboost_search(X_train, X_val, y_val):
    def objective(params):

        booster = xgb.train(
            params=params,
            dtrain=X_train,
            num_boost_round=1000,
            evals=[(X_val, "validation")],
            early_stopping_rounds=50,
        )
        y_pred = booster.predict(X_val)
        rmse = mean_squared_error(y_val, y_pred, squared=False)

        return {"loss": rmse, "status": STATUS_OK}

    search_space = {
        "max_depth": scope.int(hp.quniform("max_depth", 4, 100, 1)),
        "learning_rate": hp.loguniform("learning_rate", -3, 0),
        "reg_alpha": hp.loguniform("reg_alpha", -5, -1),
        "reg_lambda": hp.loguniform("reg_lambda", -6, -1),
        "min_child_weight": hp.loguniform("min_child_weight", -1, 3),
        "objective": "reg:linear",
        "seed": 42,
    }

    best_result = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=50,
        trials=Trials(),
    )
    return best_result


@task
def download_dataset(year: int, month: int, days: int, output_filename: str):
    downloader.download_dataset(year, month, days, output_filename)


@task
def preprocess_datasets(TRAIN_PATHFILE: str, VAL_PATHFILE: str, TEST_PATHFILE: str):

    DATE_FIELDS = ["Trip Start Timestamp", "Trip End Timestamp"]
    CATEGORICAL_FEATURES = ["pickup_community_area", "dropoff_community_area"]
    TARGET = "trip_seconds"
    DTYPE = {"Pickup Community Area": str, "Dropoff Community Area": str}

    data_processor = Preprocessor(verbose=False, analyse=False)
    # Fit only the train dataset.
    df_train, y_train = data_processor.process(
        TRAIN_PATHFILE, DATE_FIELDS, TARGET, CATEGORICAL_FEATURES, dtype=DTYPE
    )
    df_val, y_val, = data_processor.process(
        VAL_PATHFILE, DATE_FIELDS, TARGET, CATEGORICAL_FEATURES, dtype=DTYPE
    )
    df_test, y_test = data_processor.process(
        TEST_PATHFILE, DATE_FIELDS, TARGET, CATEGORICAL_FEATURES, dtype=DTYPE
    )
    return (
        df_train,
        y_train,
        df_val,
        y_val,
        df_test,
        y_test,
    )


@task
def train_models(
    df_train,
    y_train,
    df_val,
    y_val,
    TRAIN_PATHFILE,
    VAL_PATHFILE,
):
    # pylint: disable=unused-argument
    # pylint: disable=unused-variable

    categorical = ["pickup_community_area", "dropoff_community_area"]
    numerical = []

    ensemble_models = []  # GradientBoostingRegressor, ExtraTreesRegressor]
    # basic_models = [LinearRegression] #, Lasso, Ridge]
    basic_models = [LinReg]  # , Lasso, Ridge]
    svm_models = []  # LinearSVR]
    model_classes = ensemble_models + basic_models + svm_models
    # model_params = [None, None, None, {"alpha": 0.1}, None, None]
    model_params = [None]

    for i, model_class in enumerate(model_classes):

        with mlflow.start_run():

            mlflow.set_tag("developer", "marcos")
            mlflow.log_param("train-data-path", TRAIN_PATHFILE)
            mlflow.log_param("val-data-path", VAL_PATHFILE)

            model = model_class(categorical=categorical, numerical=numerical)
            print(f"Model class: {model}")
            if model_class in ensemble_models + svm_models:
                model.fit(df_train, y_train.ravel())
            else:
                model.fit(df_train, y_train)

            y_pred = model.predict(df_val)
            print(
                f"Sample number 51: {json.dumps(df_train.iloc[155].tolist())} => {y_pred[155]}"
            )
            rmse = mean_squared_error(y_val, y_pred, squared=False)
            mlflow.log_metric("val_rmse", rmse)
            print(f"total rmse = {rmse:.3f}")
    """
    xgb_X_train = xgb.DMatrix(X_train, label=y_train)
    xgb_X_val = xgb.DMatrix(X_val, label=y_val)
    train_xgboost_search(xgb_X_train, xgb_X_val, y_val)
    """


@task
def register_models(
    tracking_uri: str,
    mlflow_experiment_name: str,
    mlflow_model_name: str,
    df_test,
    y_test,
    now,
):

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)

    experiment_id = client.get_experiment_by_name(mlflow_experiment_name).experiment_id

    client.list_experiments()
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f"attribute.start_time>{int(now)} and metrics.val_rmse < 20",
        run_view_type=mlflow.entities.ViewType.ACTIVE_ONLY,
        max_results=3,
        order_by=["metrics.val_rmse ASC"],
    )

    best_model = 0
    best_rmse = float("inf")

    for run in runs:
        run_id = run.info.run_id
        print(f"Run id: {run_id}, val_rmse: {run.data.metrics['val_rmse']:.3f}")
        model_uri = f"runs:/{run_id}/model"

        model = mlflow.pyfunc.load_model(model_uri)
        y_pred = model.predict(df_test)
        test_rmse = mean_squared_error(y_test, y_pred, squared=False)
        print(f"Run id: {run_id}, test_rmse: {test_rmse:.3f}")

        # Update the metrics in these experiments
        client.log_metric(run.info.run_id, "test_rmse", test_rmse)
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=mlflow_model_name,
            # tags={'test_rmse': test_rmse}
        )

        if test_rmse < best_rmse:
            best_model = model_version
            best_rmse = test_rmse

    print(f"Best model: run_id={best_model.run_id} - version={best_model.version}")

    client.transition_model_version_stage(
        name=mlflow_model_name,
        version=best_model.version,
        stage="Staging",
        archive_existing_versions=True,
    )

    latest_versions = client.get_latest_versions(name=mlflow_model_name)
    for version in latest_versions:
        print(f"Version: {version.version}, stage: {version.current_stage}")


@flow
def main_flow(
    data_path: str = "data",
    year: int = 2022,
    train_month: int = 2,
    val_month: int = 3,
    test_month: int = 4,
    num_of_days=2,
):
    # pylint: disable=unused-argument
    # pylint: disable=unused-variable
    TRAIN_SET_NAME = f"Taxi_Trips_2022_{train_month:02d}.csv"
    VAL_SET_NAME = f"Taxi_Trips_2022_{val_month:02d}.csv"
    TEST_SET_NAME = f"Taxi_Trips_2022_{test_month:02d}.csv"
    TRAIN_PATHFILE = f"{data_path}/{TRAIN_SET_NAME}"
    VAL_PATHFILE = f"{data_path}/{VAL_SET_NAME}"
    TEST_PATHFILE = f"{data_path}/{TEST_SET_NAME}"
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

    # We create a subfolder to store the data files. Note that with running a prefect agent, we
    # have to ensure that the files are stored locally (to the agent).
    # For instance, in windows, the flow is executed in a temp folder, not in the folder where the
    # agent is started.

    # logger = get_run_logger()
    # logger.info("Running flow...")

    if not os.path.exists(data_path):

        # logger.info(f"Path {data_path} does not exist, creating...")
        os.makedirs(data_path)

    # Download datasets

    for dataset_pathfile in [TRAIN_PATHFILE, VAL_PATHFILE, TEST_PATHFILE]:
        if not os.path.exists(dataset_pathfile):
            print(f"Downloading train set: {dataset_pathfile}")
            download_dataset(year, train_month, num_of_days, dataset_pathfile)
        else:
            print("{dataset_pathfile} set already exists. Skipping download")

    # Prepare X and y.
    (
        df_train,
        y_train,
        df_val,
        y_val,
        df_test,
        y_test,
    ) = preprocess_datasets(TRAIN_PATHFILE, VAL_PATHFILE, TEST_PATHFILE)

    now = datetime.now().timestamp() * 1000
    # Train a set of models
    train_models(
        df_train,
        y_train,
        df_val,
        y_val,
        TRAIN_PATHFILE,
        VAL_PATHFILE,
    )

    # Get the best 3 models and register them in the model registry
    register_models(
        MLFLOW_TRACKING_URI,
        MLFLOW_EXPERIMENT_NAME,
        MLFLOW_MODEL_NAME,
        df_test,
        y_test,
        now,
    )


# @flow
def _main_flow(
    data_path: str = "data",
    year: int = 2022,
    train_month: int = 2,
    val_month: int = 3,
    test_month: int = 4,
    num_of_days: int = 2,
):
    # pylint: disable=unused-argument
    print("hello world")


if __name__ == "__main__":

    current_path = Path(__file__).parent
    DATA_PATH = str(current_path / "data")
    YEAR = 2022
    TRAIN_MONTH = 2
    VAL_MONTH = 3
    TEST_MONTH = 4
    NUM_OF_DAYS = 2
    main_flow(DATA_PATH, YEAR, TRAIN_MONTH, VAL_MONTH, TEST_MONTH, NUM_OF_DAYS)
