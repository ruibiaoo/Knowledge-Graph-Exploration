import os
import time

import requests


NEPTUNE_ENDPOINT = os.getenv("NEPTUNE_ENDPOINT")
NEPTUNE_PORT = os.getenv("NEPTUNE_PORT", "8182")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

S3_GRAPH_CSV_PATH = "s3://graph-exploration/outputs/graph_csv/"


def run_load_from_s3():

    iam_role_arn = os.getenv("NEPTUNE_LOAD_ROLE_ARN")
    payload = {
        "source": S3_GRAPH_CSV_PATH,
        "format": "csv",
        "iamRoleArn": iam_role_arn,
        "region": AWS_REGION,
        "failOnError": "TRUE",
        "queueRequest": "TRUE"
    }
    
    response = requests.post(f"https://{NEPTUNE_ENDPOINT}:{NEPTUNE_PORT}/loader", json=payload, timeout=30)
    response.raise_for_status()

    return response.json()

if __name__ == "__main__":
    run_load_from_s3()