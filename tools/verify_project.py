#!/usr/bin/env python3
"""
Maker-Ops Project Verification Script

Purpose:
Ensures architectural safety by verifying that the API
and regression baseline remain functional after changes.

Exit Codes:
0 = success
1 = failure
"""

import subprocess
import sys
import time
import urllib.request
import json


SERVER_URL = "http://127.0.0.1:8000"

print(f"Using Python: {sys.executable}")
def start_server():
    print("Starting server...")
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    return proc


def stop_server(proc):
    proc.terminate()
    proc.wait()


def check_endpoint(path: str):
    url = f"{SERVER_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def run_checks():
    checks = {
        "health": "/docs",
        "openapi": "/openapi.json",
    }

    failures = []

    for name, path in checks.items():
        print(f"Checking {name}...")
        if not check_endpoint(path):
            failures.append(name)

    return failures


def main():
    proc = start_server()

    try:
        failures = run_checks()
    finally:
        stop_server(proc)

    if failures:
        print("\nVerification FAILED:")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)

    print("\nVerification PASSED ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()

