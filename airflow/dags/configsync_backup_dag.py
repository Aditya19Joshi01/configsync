import json
import os
from datetime import timedelta, datetime

import requests

from airflow import DAG
from airflow.operators.python import PythonOperator


#===============================================================
# Task - 1: Obtain Access Token
#===============================================================
def get_access_token(**context):
    """
    Obtain an access token from the authentication service.
    This function should implement the logic to authenticate and retrieve
    a valid JWT token for accessing protected endpoints.
    """
    auth_endpoint = "http://backend:8000/auth/login"
    credentials = {
        "username": "admin",
        "password": "adminpassword"
    }

    print("Requesting access token...")
    response = requests.post(
        auth_endpoint,
        data=credentials,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        if token:
            print("Login successful, token obtained.")
            context["ti"].xcom_push(key="jwt_token", value=token)
        else:
            raise ValueError("Token not found in response.")
    else:
        raise ValueError(f"Login failed: {response.status_code} {response.text}")

#===============================================================
# Task - 2: Backup Configurations
#===============================================================
def backup_configs(**context):
    """
    Backup service configurations to a secure location.
    This function should implement the logic to fetch all configurations
    and store them in a backup system (e.g., S3, database, etc.).
    """
    backup_endpoint = "http://backend:8000/config/list"
    backup_dir = "/opt/airflow/dags/backups/"
    token = context["ti"].xcom_pull(key="jwt_token", task_ids="get_access_token")
    headers = {"Authorization": f"Bearer {token}"}

    print("Fetching configurations for backup...")

    response = requests.get(backup_endpoint, headers=headers)

    if response.status_code == 200:
        configs = response.json()
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, "config_backup.json")
        with open(backup_file, "w") as f:
            json.dump(configs, f, indent=4)
        print(f"Configurations backed up successfully to {backup_file}.")

    else:
        raise ValueError(f"Failed to fetch configurations: {response.status_code} {response.text}")

#===============================================================
# DAG Definition
#===============================================================
default_args = {
    "owner": "configsync",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

with DAG(
    dag_id="configsync_backup_dag",
    default_args=default_args,
    description="Daily Backup of configurations via login based auth",
    schedule_interval="@daily",
    start_date=datetime(2025, 11, 1),
    catchup=False,
    tags=["configsync", "backup"]
) as dag:

    task_get_access_token = PythonOperator(
        task_id="get_access_token",
        python_callable=get_access_token,
    )

    task_backup_configs = PythonOperator(
        task_id="backup_configs",
        python_callable=backup_configs,
    )

    task_get_access_token >> task_backup_configs