import os

from trainning_pipeline import main_flow
from prefect.deployments import Deployment
from prefect.filesystems import S3

"""
import sys
from pathlib import Path
# Workaround to add /sources path to sys.path so that modules are found
current_path = Path(__file__).parent
package_path = current_path / "../"
print(package_path)
sys.path.append(str(package_path))
"""

if __name__ == "__main__":

    # Use hyphens since it will be used to create AWS S3 buckets
    PROJECT_ID = os.getenv("PROJECT_ID_HYPHENS") or "chicago-taxi"
    S3_BUCKET = os.getenv("BUCKET_NAME") or "stg-chicago-taxi-mmjd"

    block = S3(bucket_path=f"{S3_BUCKET}/prefect")
    block.save(f"{PROJECT_ID}-block", overwrite=True)

    deployment = Deployment.build_from_flow(
        flow=main_flow,
        name=f"{PROJECT_ID}-deployment",
        version=1,
        work_queue_name=f"{PROJECT_ID}",
        storage=block,
    )

    deployment.apply()
