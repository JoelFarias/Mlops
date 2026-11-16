from pathlib import Path
import subprocess
import yaml

def data_md5(dvc_pointer: Path = Path("data/churn.csv.dvc")) -> str:
    try:
        doc = yaml.safe_load(dvc_pointer.read_text())
        return doc["outs"][0]["md5"]
    except FileNotFoundError:
        return "sem_dvc"

def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()
    except Exception:
        return "sem_git"
