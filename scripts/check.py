import os
import subprocess
import time
import urllib.error
import urllib.request
import sys
import json
import atexit
from pathlib import Path

PROJECT = f"hw3-test-{os.getpid()}-{int(time.time())}"
PORT = "12345"
os.environ["HOST_PORT"] = PORT
BASE = f"http://127.0.0.1:{PORT}"
N = 3
BACKUPS_DIR = Path(__file__).resolve().parent.parent / "backups"

STAGE = 'before all stages'

def cleanup():
    subprocess.run(["docker", "compose", "-p", PROJECT, "down", "-v", "--remove-orphans"],
                   capture_output=True)

atexit.register(cleanup)

def make_request(path, method="GET"):
    r = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except (urllib.error.URLError, OSError):
        return 0, ""

def ensure(ok, msg):
    if not ok:
        print(f"Error on state '{STAGE}': {msg}", file=sys.stderr)
        sys.exit(1)

def wait(timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        if make_request("/readyz")[0] == 200:
            return
        time.sleep(1)
    ensure(False, f"timeout {timeout} exceeded")

def wait_status(path, expected, method="GET", timeout=60):
    end = time.time() + timeout
    status = 0
    while time.time() < end:
        status, _ = make_request(path, method)
        if status == expected:
            return
        time.sleep(1)
    subprocess.run(["docker", "compose", "-p", PROJECT, "ps", "-a"])
    subprocess.run(["docker", "compose", "-p", PROJECT, "logs", "--tail", "20", "app"])
    ensure(False, f"{method} {path}: expected {expected}, last status {status}")

def get_json(path, method="GET"):
    status, data = make_request(path, method)
    ensure(status == 200, f"unable to get json from {path}, status: {status}")
    return json.loads(data)

def get_count():
    return get_json("/")["count"]

def increment():
    status, _ = make_request("/increment", "POST")
    ensure(status == 200, f"increment failed with status {status}")

def compose(*args):
    subprocess.run(["docker", "compose", "-p", PROJECT] + list(args), check=True)

STAGE = 'initialization'
print(f"== {STAGE}")
compose("up", "-d", "--build")
wait()

STAGE = 'check counter'
print(f"== {STAGE}")
ensure(get_count() == 0, "initial count must be 0")
for _ in range(N):
    increment()
ensure(get_count() == N, f"count must be {N} after {N} increments")

STAGE = 'check save data in app down'
print(f"== {STAGE}")
hostname_before_rebuild = get_json("/")["hostname"]
compose("up", "-d", "--force-recreate", "--no-deps", "app")
wait()
hostname_after_rebuild = get_json("/")["hostname"]
ensure(hostname_after_rebuild != hostname_before_rebuild, "hostname after rebuild must be different")
ensure(get_count() == N, f"count must be {N} after app rebuild")

STAGE = 'stop redis'
print(f"== {STAGE}")
compose("stop", "redis")
wait_status("/healthz", 200)
wait_status("/readyz", 503)
wait_status("/increment", 503, "POST")

STAGE = 'redis start again'
print(f"== {STAGE}")
compose("start", "redis")
wait()
ensure(get_count() == N, f"count must be {N} after redis restart")
increment()
ensure(get_count() == N + 1, f"count must be {N + 1} after increment post-restart")

STAGE = 'consistent backup'
print(f"== {STAGE}")
compose("stop", "app", "redis")
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
rid_result = subprocess.run(
    ["docker", "compose", "-p", PROJECT, "ps", "-a", "-q", "redis"],
    check=True, capture_output=True, text=True
)
redis_id = rid_result.stdout.strip()
ensure(redis_id != "", "failed to get redis container id")
backup_file = BACKUPS_DIR / "redis-backup.tar.gz"
subprocess.run([
    "docker", "run", "--rm",
    "--volumes-from", redis_id,
    "-v", f"{BACKUPS_DIR.absolute()}:/backup",
    "alpine:3.20",
    "tar", "-czpf", f"/backup/{backup_file.name}", "-C", "/data", "."
], check=True)
ensure(backup_file.exists() and backup_file.stat().st_size > 0, "backup file is missing or empty")

STAGE = 'collect logs'
print(f"== {STAGE}")
log_file = Path(__file__).resolve().parent.parent / "logs.txt"
with open(log_file, "w", encoding="utf-8") as f:
    subprocess.run(
        ["docker", "compose", "-p", PROJECT, "logs", "--no-log-prefix", "app"],
        stdout=f,
        check=True
    )

STAGE = 'cleanup'
print(f"== {STAGE}")
cleanup()

print("Test passed")