"""Run APL scripts as Airflow tasks.

    from apl_tasks import run_apl
    run_apl.override(task_id="report")("integrations/scheduling/job/daily-report.apls", "{{ ds }}")

The script path is relative to the repo, which docker-compose.yaml mounts at
$APL_REPO (/apl), read-only. Arguments can use Airflow templates such as
{{ ds }} (the run's date, YYYY-MM-DD).

The script's exit code decides what Airflow does:
    0          success
    2          bad input: fail now, don't retry (a retry would fail the same way)
    any other  fail, and retry if the task has retries left
"""

import os
import subprocess

from airflow.sdk import task
from airflow.sdk.exceptions import AirflowException, AirflowFailException

REPO = os.environ.get("APL_REPO", "/apl")
BAD_INPUT = 2


@task(retries=2)
def run_apl(script: str, *args: str) -> int:
    path = os.path.join(REPO, script)
    if not os.path.isfile(path):
        raise AirflowFailException(f"no such APL script: {path}")
    # apl-run (in the image) runs dyalogscript and fixes its line endings.
    # Its output goes straight to this task's log.
    code = subprocess.run(["apl-run", path, *args], check=False).returncode
    if code == BAD_INPUT:
        raise AirflowFailException(f"{script}: bad input (exit {code}); not retrying")
    if code != 0:
        raise AirflowException(f"{script} failed with exit {code}")
    return code
