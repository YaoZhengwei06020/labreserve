"""Run the PostgreSQL spike in a uniquely named temporary test database.

Requires an explicitly configured PostgreSQL 17 instance and a role allowed to
create databases and btree_gist. Does not migrate the configured application DB.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from zoneinfo import ZoneInfo

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise SystemExit("Explicit connection settings required: " + ", ".join(missing))
    run_id = uuid.uuid4().hex[:12]
    evidence = ROOT / "docs" / "evidence" / ("postgres-" + run_id)
    evidence.mkdir(parents=True)
    summary = {"run_id": run_id, "started_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
               "stage": "preflight", "status": "NOT_RUN", "python": sys.version.split()[0],
               "test_database": "test_labreserve_spike_" + run_id}

    def save():
        (evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    save()
    try:
        # Read-only preflight against the maintenance DB, not the application DB.
        with psycopg.connect(host=os.environ["POSTGRES_HOST"], port=os.environ["POSTGRES_PORT"],
            user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"],
            dbname="postgres", connect_timeout=5) as conn:
            summary["server_version"] = conn.info.server_version
            if not 170000 <= conn.info.server_version < 180000:
                raise RuntimeError("The validation target must be PostgreSQL 17")
            with conn.cursor() as cursor:
                cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'btree_gist')")
                if not cursor.fetchone()[0]:
                    raise RuntimeError("btree_gist is not available on this server")
        env = os.environ.copy()
        # Django creates test_<NAME>; randomness prevents existing test DB collisions.
        env["POSTGRES_DB"] = "labreserve_spike_" + run_id
        env["PYTHONIOENCODING"] = "utf-8"
        summary["stage"] = "pytest"
        save()
        args = [sys.executable, "-m", "pytest", "-m", "postgres", "-q", "--tb=short", "--maxfail=1",
                "--junitxml=" + str(evidence / "tests.xml")]
        result = subprocess.run(args, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace",
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        # Failure tracebacks may contain connection parameters. Keep secrets out of evidence.
        output = result.stdout.replace(os.environ["POSTGRES_PASSWORD"], "<redacted>")
        (evidence / "pytest.txt").write_text(output, encoding="utf-8")
        print(output)
        summary.update(status="PASSED" if result.returncode == 0 else "FAILED", exit_code=result.returncode)
    except Exception as exc:
        summary.update(status="BLOCKED" if summary["stage"] == "preflight" else "ERROR", error_type=type(exc).__name__)
        print("PostgreSQL validation stopped:", type(exc).__name__)
        # Do not serialize raw exceptions containing connection credentials.
    finally:
        summary["finished_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
        save()
        print("Evidence:", evidence)
    return 0 if summary["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
