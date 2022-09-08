from preprocessor import Preprocessor
from model import Model
import downloader
import json
from pathlib import Path

from datetime import datetime

import pandas as pd

from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_squared_error
# from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression, Lasso, Ridge
from sklearn.svm import LinearSVR
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
import xgboost as xgb
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from hyperopt.pyll import scope

import mlflow
import os

from prefect import flow, task, get_run_logger

def train_xgboost_search(X_train, X_val, y_val):

    def objective(params):

        booster = xgb.train(
            params=params,
            dtrain=X_train,
            num_boost_round=1000,
            evals=[(X_val, 'validation')],
            early_stopping_rounds=50
        )
        y_pred = booster.predict(X_val)
        rmse = mean_squared_error(y_val, y_pred, squared=False)

        return {'loss': rmse, 'status': STATUS_OK}

    search_space = {
        'max_depth': scope.int(hp.quniform('max_depth', 4, 100, 1)),
        'learning_rate': hp.loguniform('learning_rate', -3, 0),
        'reg_alpha': hp.loguniform('reg_alpha', -5, -1),
        'reg_lambda': hp.loguniform('reg_lambda', -6, -1),
        'min_child_weight': hp.loguniform('min_child_weight', -1, 3),
        'objective': 'reg:linear',
        'seed': 42
    }

    best_result = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=50,
        trials=Trials()
    )
    return best_result

@task
def preprocess_datasets(
    TRAIN_PATHFILE: str,
    VAL_PATHFILE: str,
    TEST_PATHFILE: str ):


    DATE_FIELDS = ['Trip Start Timestamp','Trip End Timestamp']
    CATEGORICAL_FEATURES = ['pickup_community_area','dropoff_community_area']
    TARGET = 'trip_seconds'

    data_processor = Preprocessor(verbose=False, analyse=False)

    dv = DictVectorizer()
    X_train, y_train, dv, X_train_dicts = data_processor.process(
        TRAIN_PATHFILE,
        DATE_FIELDS,
        TARGET,
        CATEGORICAL_FEATURES,
        dv,
        True)
    X_val, y_val, dv, X_val_dicts = data_processor.process(
        VAL_PATHFILE,
        DATE_FIELDS,
        TARGET,
        CATEGORICAL_FEATURES,
        dv,
        False)
    X_test, y_test, dv, X_test_dicts = data_processor.process(
        TEST_PATHFILE,
        DATE_FIELDS,
        TARGET,
        CATEGORICAL_FEATURES,
        dv,
        False)
    return X_train, X_train_dicts, y_train, X_val, X_val_dicts, y_val, X_test, X_test_dicts, y_test, dv,

@task
def train_models(X_train, X_train_dicts, y_train, X_val, X_val_dicts, y_val, TRAIN_PATHFILE, VAL_PATHFILE):

    ensemble_models = [GradientBoostingRegressor, ExtraTreesRegressor]
    basic_models = [LinearRegression, Lasso, Ridge]
    svm_models = [LinearSVR]
    model_classes = ensemble_models + basic_models + svm_models
    model_params = [None, None, None, {'alpha':0.1}, None, None]

    for i, model_class in enumerate(model_classes):

        with mlflow.start_run():

            mlflow.set_tag("developer", "marcos")
            mlflow.log_param("train-data-path",TRAIN_PATHFILE)
            mlflow.log_param("val-data-path",VAL_PATHFILE)

            model = Model(model_class, model_params[i])
            if model_class in [ensemble_models + svm_models]:
                model.fit(X_train_dicts, y_train.ravel())
            else:
                model.fit(X_train_dicts, y_train)

            y_pred = model.predict(X_val_dicts)
            print(f"Sample number 25: {json.dumps(X_train_dicts[50])} => {y_pred[50]}")
            rmse = mean_squared_error(y_val, y_pred, squared=False)
            mlflow.log_metric("val_rmse", rmse)
            print(f'rmse = {rmse:.3f}')

    """
    xgb_X_train = xgb.DMatrix(X_train, label=y_train)
    xgb_X_val = xgb.DMatrix(X_val, label=y_val)
    train_xgboost_search(xgb_X_train, xgb_X_val, y_val)
    """

    return

@task
def register_models(tracking_uri: str, mlflow_experiment_name: str, mlflow_model_name: str):

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)

    experiment_id = client.get_experiment_by_name(mlflow_experiment_name).experiment_id

    client.list_experiments()
    runs = client.search_runs(
        experiment_ids = [experiment_id],
        filter_string = '',
        run_view_type = mlflow.entities.ViewType.ACTIVE_ONLY,
        max_results = 3,
        order_by = ["metrics.val_rmse ASC"])

    model_versions = []
    for run in runs:
        run_id =run.info.run_id
        print(f"Run id: {run_id}, val_rmse: {run.data.metrics['val_rmse']:.3f}")
        model_version = mlflow.register_model(
            model_uri=f"runs:/{run_id}/model",
            name=mlflow_model_name,
            tags={"estimator": f"{run.data.tags['estimator_name']}"}
            )
        model_versions.append(model_version)

    production_version = model_versions[0].version

    client.transition_model_version_stage(
        name = mlflow_model_name,
        version = production_version,
        stage = "Production",
        archive_existing_versions = False)

    latest_versions = client.get_latest_versions(name=mlflow_model_name)
    for version in latest_versions:
        print(f"Version: {version.version}, stage: {version.current_stage}")

    return

@flow
def main_flow(
    data_path: str = "data",
    train_month: int = 2,
    val_month: int = 3,
    test_month: int = 4):

    TRAIN_SET_NAME = f"Taxi_Trips_2022_{train_month:02d}.csv"
    VAL_SET_NAME = f"Taxi_Trips_2022_{val_month:02d}.csv"
    TEST_SET_NAME = f"Taxi_Trips_2022_{test_month:02d}.csv"
    TRAIN_PATHFILE = f"{data_path}/{TRAIN_SET_NAME}"
    VAL_PATHFILE = f"{data_path}/{VAL_SET_NAME}"
    TEST_PATHFILE = f"{data_path}/{TEST_SET_NAME}"

    PROJECT_NAME = os.getenv("PROJECT_NAME") or "chicago_taxi"
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI") or "http://52.213.112.212:8080"
    MLFLOW_EXPERIMENT_NAME = "mlflow/" + PROJECT_NAME
    MLFLOW_MODEL_NAME = PROJECT_NAME +"_regressor"

    # Setup MLflow

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    # Use a subfolder in the S3 bucket
    mlflow.set_experiment(f"{MLFLOW_EXPERIMENT_NAME}")
    mlflow.sklearn.autolog()

    # We create a subfolder to store the data files. Note that with running a prefect agent, we
    # have to ensure that the files are stored locally (to the agent).
    # For instance, in windows, the flow is executed in a temp folder, not in the folder where the
    # agent is started.
    logger = get_run_logger()

    # current_path = Path(__file__).parent
    # logger.info(f"Current path: {current_path}")

    # logger.info(f"Download path: {TRAIN_PATHFILE}")
    if not os.path.exists(data_path):

        logger.info(f"Path {data_path} does not exist, creating...")
        os.makedirs(data_path)


    # Download datasets
    print(f'Downloading train set: {TRAIN_SET_NAME}')
    downloader.download_dataset(datetime(2022,train_month,1),datetime(2022,train_month,2),TRAIN_PATHFILE)
    print(f'Downloading val set: {VAL_SET_NAME}')
    downloader.download_dataset(datetime(2022,val_month,1),datetime(2022,val_month,2), VAL_PATHFILE)
    print(f'Downloading test set: {TEST_SET_NAME}')
    downloader.download_dataset(datetime(2022,test_month,1),datetime(2022,test_month,2), TEST_PATHFILE)

    # Prepare X and y
    X_train, X_train_dicts, y_train, X_val, X_val_dicts, y_val, X_test, X_test_dicts, y_test, dv, = preprocess_datasets(
        TRAIN_PATHFILE,
        VAL_PATHFILE,
        TEST_PATHFILE)

    # Train a set of models
    train_models(X_train, X_train_dicts, y_train, X_val, X_val_dicts, y_val, TRAIN_PATHFILE, VAL_PATHFILE)

    # Get the best 3 models and register them
    register_models(MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME, MLFLOW_MODEL_NAME)

@flow
def _main_flow(
    data_path: str = "data",
    train_month: int = 2,
    val_month: int = 3,
    test_month: int = 4):

    print("hello")

if __name__ == "__main__":

    DATA_PATH = "data"
    TRAIN_MONTH = 2
    VAL_MONTH = 3
    TEST_MONTH = 4

    main_flow(DATA_PATH, TRAIN_MONTH, VAL_MONTH, TEST_MONTH)
