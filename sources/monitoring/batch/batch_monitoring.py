import os
import json
from typing import List
from pathlib import Path

import pandas
from pymongo import MongoClient
from evidently import ColumnMapping
from evidently.dashboard import Dashboard
from evidently.test_suite import TestSuite
from evidently.test_preset import DataDrift
from evidently.model_profile import Profile
from evidently.dashboard.tabs import DataDriftTab, RegressionPerformanceTab
from evidently.model_profile.sections import (
    DataDriftProfileSection,
    RegressionPerformanceProfileSection,
)

from development import downloader
from development.preprocessor import Preprocessor
from production.model_service import init_model_mlflow

# from prefect import flow, task

# @task
def add_target_to_actual_data(filename):
    client = MongoClient("mongodb://localhost:27018/")
    collection = client.get_database("prediction_service").get_collection("data")
    with open(filename) as f_target:
        for line in f_target.readlines():
            row = line.split(",")
            collection.update_one(
                {"trip_id": row[0]}, {"$set": {"target": float(row[1])}}
            )
    client.close()


# @task
def download_reference_data(year, month, days, file_path):

    if not os.path.exists(file_path):
        print(f"Downloading test set: {file_path}")
        downloader.download_dataset(year, month, days, file_path)
    else:
        print("Reference set already exists. Skipping download")

    return file_path


# @task
def preprocess_reference_data(
    ref_set_path: str, date_fields: List[str], dtype: dict, categorical_features
):

    preprocessor = Preprocessor(False, False)
    test_set_path_parquet = preprocessor.read_dataframe_csv(
        ref_set_path, date_fields, dtype
    )
    test_set = preprocessor.read_dataframe_parquet(test_set_path_parquet)
    ref_data, target = preprocessor.preprocess_data(test_set, categorical_features, [])
    # preprocess_data returns the features and the target columns separately
    # target is 'duration' by default, so add it as 'target' for evidently
    ref_data["target"] = target
    return ref_data


# @task
def load_model(tracking_uri: str, name: str, stage: str):
    return init_model_mlflow(tracking_uri=tracking_uri, name=name, stage=stage)


# @task
def add_prediction_to_ref_data(ref_data, model):

    dicts = ref_data.to_dict(orient="records")
    print(type(model.model.predict(dicts[0])))
    print(model.model.predict(dicts[0]))
    ref_data["prediction"] = model.predict(dicts)


# @task
def get_actual_data(features, target, prediction):

    client = MongoClient("mongodb://localhost:27018/")
    data = client.get_database("prediction_service").get_collection("data").find()
    df = pandas.DataFrame(list(data))

    df.drop(
        df.columns.difference(features + target + prediction),
        axis=1,
        inplace=True,
    )

    return df


# @task
def run_evidently(ref_data, data):

    profile = Profile(
        sections=[DataDriftProfileSection(), RegressionPerformanceProfileSection()]
    )
    mapping = ColumnMapping(
        prediction="prediction",
        categorical_features=["pickup_community_area", "dropoff_community_area"],
        numerical_features=[],
        datetime_features=[],
    )
    profile.calculate(ref_data, data, mapping)

    dashboard = Dashboard(
        tabs=[DataDriftTab(), RegressionPerformanceTab(verbose_level=0)]
    )
    dashboard.calculate(ref_data, data, mapping)

    test_suite_results = TestSuite(
        tests=[
            DataDrift(),
        ]
    )

    test_suite_results.run(reference_data=ref_data, current_data=data)
    test_suite_data_results = json.loads(test_suite_results.json())
    print(json.dumps(test_suite_data_results, indent=4))

    return json.loads(profile.json()), dashboard, test_suite_data_results


# @task
def save_report(result):
    client = MongoClient("mongodb://localhost:27018/")
    client.get_database("prediction_service").get_collection("report").insert_one(
        result
    )


# @task
def save_html_report(result, report_path):
    result.save(report_path)


# @flow
def batch_analyze(
    ref_year: int,
    ref_month: int,
    ref_days: int,
    ref_set_path: str,
    test_target_set_path: str,
    report_path: str,
    date_fields: List[str],
    dtype: dict,
    model,
    categorical_features,
):
    # The database has a collection with the actual predictions. Add to the collection the
    # target values, from the csv file
    add_target_to_actual_data(test_target_set_path)

    # Load and preprocess the reference data.
    # Download
    reference_data_csv_path = download_reference_data(
        ref_year, ref_month, ref_days, ref_set_path
    )
    # Preprocess (including target)
    ref_data = preprocess_reference_data(
        reference_data_csv_path, date_fields, dtype, categorical_features
    )
    # Predict
    add_prediction_to_ref_data(ref_data, model)

    print(ref_data.columns)

    # Load the actual data from the database
    actual_data = get_actual_data(
        features=CATEGORICAL_FEATURES, target=["target"], prediction=["prediction"]
    )

    print(actual_data.columns)
    # Run batch monitoring
    profile, dashboard, test_suite_data_results = run_evidently(ref_data, actual_data)

    save_report(profile)
    save_html_report(dashboard, report_path)

    test_result = test_suite_data_results["tests"][0]

    if test_result["status"] == "FAIL":
        print(
            "Data drift detected.",
            f'{test_result["name"]} > '
            f'{test_result["parameters"]["condition"]["lt"]}',
        )
        command = "prefect deployment run main-flow/chicago-taxi-deployment"
        os.system(command)
        # print(json.dumps(" inde"t=4))"


if __name__ == "__main__":

    REF_YEAR = 2022
    REF_MONTH = 3
    REF_DAYS = 2
    REF_SET_NAME = f"Taxi_Trips_2022_{REF_MONTH:02d}.csv"
    current_path = Path(__file__).parent
    REF_PATH = current_path / "reference_data"
    REF_SET_PATH = f"{REF_PATH}/{REF_SET_NAME}"
    TEST_TARGET_SET_NAME = "test_target_values.csv"
    TEST_TARGET_SET_PATH = f"{REF_PATH}/{TEST_TARGET_SET_NAME}"
    DATE_FIELDS = ["Trip Start Timestamp", "Trip End Timestamp"]
    DTYPE = {"Pickup Community Area": str, "Dropoff Community Area": str}

    # trip_id actually is not a feature in the model, but it has to be defined here in order to preprocess the dataset correctly
    CATEGORICAL_FEATURES = [
        "pickup_community_area",
        "dropoff_community_area",
        "trip_id",
    ]
    TARGET = "trip_seconds"

    MLFLOW_MODEL_STAGE = os.getenv("MLFLOW_MODEL_STATE", "Staging")
    MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "chicago-taxi")
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:8080")

    if not os.path.exists(REF_PATH):
        os.makedirs(REF_PATH)

    model = init_model_mlflow(
        tracking_uri=MLFLOW_TRACKING_URI,
        name=MLFLOW_MODEL_NAME,
        stage=MLFLOW_MODEL_STAGE,
    )
    report_path = f"{current_path}/monitor_report.html"

    batch_analyze(
        REF_YEAR,
        REF_MONTH,
        REF_DAYS,
        REF_SET_PATH,
        TEST_TARGET_SET_PATH,
        report_path,
        DATE_FIELDS,
        DTYPE,
        model,
        CATEGORICAL_FEATURES,
    )
