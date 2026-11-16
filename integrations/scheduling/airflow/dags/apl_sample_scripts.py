"""Run every script in sample-scripts/ as its own task, in parallel.

No schedule: start it from the UI (▶) or with `airflow.sh trigger apl_sample_scripts`.
One task per NN-name.apls file, so adding a script to sample-scripts/ adds a
task here (within a few seconds). Each task's log shows that script's output.
"""

import glob
import os
import re
from datetime import datetime

from airflow.sdk import dag

from apl_tasks import REPO, run_apl


@dag(schedule=None, start_date=datetime(2026, 11, 1), catchup=False, tags=["apl"], doc_md=__doc__)
def apl_sample_scripts():
    for path in sorted(glob.glob(os.path.join(REPO, "sample-scripts", "[0-9][0-9]-*.apls"))):
        name = os.path.basename(path)[:-len(".apls")]
        task_id = re.sub(r"[^A-Za-z0-9_]", "_", name)       # 08-life → 08_life
        run_apl.override(task_id=task_id, retries=0)(os.path.relpath(path, REPO))


apl_sample_scripts()
