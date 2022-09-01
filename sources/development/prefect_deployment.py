from prefect.filesystems import S3
from trainning_pipeline import main_flow
from prefect.deployments import Deployment
import os

if __name__ == "__main__":

    # Use hypthens since it will be used to create AWS S3 buckets
    PROJECT_NAME = os.getenv("PROJECT_NAME_HYPHENS") or "chigaco-taxi"
    S3_BUCKET = os.getenv("S3_BUCKET") or "chicago-taxi-fc4rdz8d"

    block = S3(bucket_path=f"{S3_BUCKET}/prefect")
    block.save(f"{PROJECT_NAME}-block", overwrite=True)
    
    deployment = Deployment.build_from_flow(
        flow=main_flow,
        name=f"{PROJECT_NAME}-deployment",
        version=1,
        work_queue_name=f"{PROJECT_NAME}",
        storage=block
    )

    deployment.apply()
    