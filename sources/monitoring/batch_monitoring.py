import os
import json

import mlflow
import pandas
import pyarrow.parquet as pq
from pymongo import MongoClient
from evidently import ColumnMapping
from evidently.dashboard import Dashboard
from evidently.test_suite import TestSuite
from evidently.test_preset import DataDrift
from evidently.model_profile import Profile
from evidently.dashboard.tabs import DataDriftTab, RegressionPerformanceTab
from evidently.model_profile.sections import DataDriftProfileSection, RegressionPerformanceProfileSection

# from prefect import flow, task

# @task
def upload_target(filename):
    client = MongoClient("mongodb://localhost:27018/")
    collection = client.get_database("prediction_service").get_collection("data")
    with open(filename) as f_target:
        for line in f_target.readlines():
            row = line.split(",")
            collection.update_one({"id": row[0]}, {"$set": {"target": float(row[1])}})
    client.close()


# @task
def load_reference_data(filename, model_location):

    model = mlflow.pyfunc.load_model(model_location)
    reference_data = pq.read_table(filename).to_pandas()

    features = ['id', 'pickup_community_area', 'dropoff_community_area']
    target = ['target']

    # Create features
    reference_data['id'] = reference_data['trip_id']
    # add target column
    reference_data = reference_data[reference_data.trip_seconds.notnull()]
    reference_data = reference_data[(reference_data.trip_seconds > 60) & (reference_data.trip_seconds < 3600)]
    reference_data['target'] = reference_data['trip_seconds'] / 60
    reference_data.drop(
        reference_data.columns.difference(features + target),
        axis=1,
        inplace=True,
    )
    dicts = reference_data[features].to_dict(orient='records')
    reference_data['prediction'] = model.predict(dicts)
    return reference_data


# @task
def fetch_data():
    features = ['id', 'pickup_community_area', 'dropoff_community_area']
    target = ['target']
    prediction = ['prediction']
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

    profile = Profile(sections=[DataDriftProfileSection(), RegressionPerformanceProfileSection()])
    mapping = ColumnMapping(
        prediction="prediction",
        categorical_features=['pickup_community_area', 'dropoff_community_area'],
        datetime_features=[],
    )
    profile.calculate(ref_data, data, mapping)

    dashboard = Dashboard(tabs=[DataDriftTab(), RegressionPerformanceTab(verbose_level=0)])
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
    client.get_database("prediction_service").get_collection("report").insert_one(result)


# @task
def save_html_report(result):
    result.save("evidently_report_example.html")


# @flow
def batch_analyze():
    upload_target("target_values.csv")
    ref_data = load_reference_data("./reference_data/Taxi_Trips_2022_03.parquet", "./model")
    print(ref_data)
    data = fetch_data()
    print(data)
    profile, dashboard, test_suite_data_results = run_evidently(ref_data, data)

    save_report(profile)
    save_html_report(dashboard)

    test_result = test_suite_data_results["tests"][0]

    if test_result["status"] == "FAIL":
        print(
            'Data drift detected.',
            f'{test_result["name"]} > ' f'{test_result["parameters"]["condition"]["lt"]}',
        )
        command = "prefect deployment run main-flow/chicago-taxi-deployment"
        os.system(command)
        # print(json.dumps(" inde"t=4))"


if __name__ == "__main__":
    batch_analyze()
