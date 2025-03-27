import os
from datetime import datetime

import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

from utils.callbacks import failure_callback, success_callback
from utils.common import read_sql_file

local_timezone = pendulum.timezone("Asia/Seoul")
conn_id = "feature_store" # connection 만들어놓음 airflow에
airflow_dags_path = Variable.get("AIRFLOW_DAGS_PATH") # airflow에 variables 넣어놈
# path ,로 넣어으면 된다. full path로해도되지만 이렇게하는게 가독성이 좋음
sql_file_path = os.path.join(
    airflow_dags_path,
    "pipelines",
    "continuous_training",
    "data_extract",
    "features.sql",
)
with DAG(
    dag_id="credit_score_classification_ct",
    default_args={
        "owner": "user",
        "depends_on_past": False,
        "email": ["lgcnsuser@gmail.com"],
        "on_failure_callback": failure_callback,
        "on_success_callback": success_callback,
    },
    description="A DAG for continuous training",
    schedule=None,
    start_date=datetime(2025, 1, 1, tzinfo=local_timezone),
    catchup=False,
    tags=["lgcns", "mlops"],
) as dag:
    # TODO: 코드 작성
    # 아래 Task를 적절한 Operator를 사용하여 구현
    data_extract = SQLExecuteQueryOperator(
        task_id="data_extraction",
        conn_id=conn_id,
        sql=read_sql_file(sql_file_path),
        split_statements=True,

    )

    #data_preprocessing = EmptyOperator(task_id="data_preprocessing")
    data_preprocessing = BashOperator(
        task_id="data_preprocessing",
        bash_command=f"cd {airflow_dags_path}/piplines/continuous_traning/docker &&"
        "docker compose up --build && docker compose down",
        env={
            "PYTHON_FILE": "/home/codespace/data_preprocessing/preprocessor.py", 
            "MODEL_NAME": "credit_score_classification",
            "BASE_DT": "{{ ds }}"
        },
        append_env=True,
        retries=1,
    )

    training = EmptyOperator(task_id="model_training")

    data_extract >> data_preprocessing >> training
