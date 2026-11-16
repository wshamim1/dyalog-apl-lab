"""Daily sales report, written in APL and run by Airflow.

    run_date, check_input  →  report (APL)  →  summary (Python reads the APL's JSON)

Runs every day at 06:00 (UTC). Each run makes the report for its own date, so
re-running an old day rebuilds exactly that day's report. To make the report
for a particular day by hand, trigger with  {"date": "2026-11-01"}.
"""

import json
import os
from datetime import datetime, timedelta

from airflow.sdk import Param, dag, get_current_context, task
from airflow.sdk.exceptions import AirflowFailException

from apl_tasks import REPO, run_apl

JOB = "integrations/scheduling/job/daily-report.apls"
INPUT = "integrations/scheduling/job/data/sales.csv"
REPORT_DIR = os.environ.get("REPORT_DIR", "/apl-output/reports")


@dag(
    schedule="0 6 * * *",
    start_date=datetime(2026, 11, 1),
    catchup=False,                      # don't run every day since start_date at once
    max_active_runs=1,
    default_args={"retry_delay": timedelta(minutes=2)},
    params={"date": Param("", type="string", description="YYYY-MM-DD; empty = the run's own date")},
    tags=["apl"],
    doc_md=__doc__,
)
def apl_daily_report():
    @task
    def run_date() -> str:
        # The date this run reports on: the "date" param if given, else the
        # scheduled date. Manual runs have no logical date in Airflow 3, so
        # they use the time they were triggered.
        ctx = get_current_context()
        if ctx["params"].get("date"):
            return ctx["params"]["date"]
        when = ctx.get("logical_date") or ctx["dag_run"].run_after
        return when.strftime("%Y-%m-%d")

    @task
    def check_input() -> str:
        path = os.path.join(REPO, INPUT)
        if not os.path.isfile(path):
            raise AirflowFailException(f"input not found: {path}")
        return path

    @task
    def summary(date: str) -> dict:
        # The APL job wrote the report as JSON; hand the numbers to Python
        # (they show up in the task's XCom tab, ready for a next step).
        with open(os.path.join(REPORT_DIR, f"sales-{date}.json")) as f:
            report = json.load(f)
        print(f"{date}: {report['orders']} orders, revenue {report['revenue']:.2f}, "
              f"best seller {report['best_seller']}")
        return {"date": date, "orders": report["orders"], "revenue": report["revenue"]}

    date = run_date()
    report = run_apl.override(task_id="report")(JOB, date, check_input())
    report >> summary(date)


apl_daily_report()
