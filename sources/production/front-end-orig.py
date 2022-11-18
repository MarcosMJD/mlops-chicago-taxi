import streamlit as st
import requests
import os
import uuid
import base64


def render(api_gateway_base_url, mlflow_external_ip, prefect_external_ip):

    st.title('MLOps front-end demo')

    api_gateway_base_uri = f"{api_gateway_base_url}/predict"
    AREAS = [
        '-1',
        '1',
        '10',
        '11',
        '12',
        '13',
        '14',
        '15',
        '16',
        '17',
        '18',
        '19',
        '2',
        '20',
        '21',
        '22',
        '23',
        '24',
        '25',
        '26',
        '27',
        '28',
        '29',
        '3',
        '30',
        '31',
        '32',
        '33',
        '34',
        '35',
        '36',
        '37',
        '38',
        '39',
        '4',
        '40',
        '41',
        '42',
        '43',
        '44',
        '45',
        '46',
        '47',
        '48',
        '49',
        '5',
        '50',
        '51',
        '52',
        '53',
        '54',
        '55',
        '56',
        '57',
        '58',
        '59',
        '6',
        '60',
        '61',
        '62',
        '63',
        '64',
        '65',
        '66',
        '67',
        '68',
        '69',
        '7',
        '70',
        '71',
        '72',
        '73',
        '74',
        '75',
        '76',
        '77',
        '8',
        '9',
    ]

    import subprocess
    # def run_and_display_stdout(*cmd_with_args):
    

    def run_bath_monitor():
        """ 
        result = subprocess.Popen(("python", "./monitoring/batch/batch_monitoring.py"), stdout=subprocess.PIPE)
        for line in iter(lambda: result.stdout.readline(), b""):
            st.text(line.decode("utf-8"))
        """
        command = "python ./monitoring/batch/batch_monitoring.py"
        os.system(command)

    def run_flow():
        command = "prefect deployment run main-flow/chicago-taxi-deployment"
        os.system(command)

    st.markdown(
        f"MLFlow Experiment Tracking URI: [Click to open](http://{mlflow_external_ip}:8080)",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Prefect Workflow Orchestration URI: [Click to open](http://{prefect_external_ip}:8080/runs)",
        unsafe_allow_html=True,
    )
    st.button("Execute trainning pipeline", help="Schedule the tranning flow on Prefect server, Prefect agent will actually execute the trainning and model registration", on_click=run_flow)
    st.markdown("After clicking, go to the Prefect server URI and check the running flow.")
    st.markdown("After the flow finishes, go to MLflow uri and check the experiments and registered models.")

    st.button("Execute batch monitor", help="Run batch monitor with reference data and actual predicted data. After finishing, you can click to open the report.", on_click=run_bath_monitor)
    

    api_uri = st.text_input(
        "API Endpoint URI",
        value=api_gateway_base_uri,
        type="default",
        help="The URI of the ML server running on, <url>:<port>/predict. May be localhost or any other external url",
    )

    pickup_community_area = st.selectbox("Pickup Community Area", AREAS, index=3)
    dropoff_community_area = st.selectbox("Dropoff Community Area", AREAS, index=2)
    trip_id = str(uuid.uuid4())

    features = {
        "pickup_community_area": pickup_community_area,
        "dropoff_community_area": dropoff_community_area,
        "trip_id": trip_id,
    }

    response = requests.post(url=api_uri, json=features)
    prediction = response.json()

    if isinstance(prediction, list):
        if len(prediction) == 1:
            prediction = prediction[0]

    st.header(f"Predicted trip time = {prediction:02f} minutes")

    st.image("../assets/chicago-taxi-infrastructure.jpg")
    st.image("../assets/ml-lifecycle-mlops-eternal-knot.png")


if __name__ == "__main__":

    api_gateway_base_url = os.getenv("API_GATEWAY_BASE_URL", "http://localhost:80")
    mlflow_external_ip = os.getenv("MLFLOW_EXTERNAL_IP", "http://localhost")
    prefect_external_ip = os.getenv("PREFECT_EXTERNAL_IP", "http://localhost")

    render(api_gateway_base_url, mlflow_external_ip, prefect_external_ip)
