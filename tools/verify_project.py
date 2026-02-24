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
import uuid


SERVER_URL = "http://127.0.0.1:8000"

print(f"Using Python: {sys.executable}")
def start_server():
    print("Starting server...")
    # Use -m uvicorn for better reliability
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server to be ready
    for i in range(10):
        try:
            with urllib.request.urlopen(f"{SERVER_URL}/", timeout=1) as r:
                if r.status == 200:
                    print("Server started successfully.")
                    return proc
        except Exception:
            time.sleep(1)
    
    print("Server failed to start.")
    proc.terminate()
    return None


def stop_server(proc):
    if proc:
        proc.terminate()
        proc.wait()


def check_endpoint(path: str):
    url = f"{SERVER_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def verify_gcode_calculation():
    """Verify that the G-code calculation endpoint works as expected."""
    # 1. Create a machine
    machine_data = {
        "name": f"Verify Printer {uuid.uuid4().hex[:6]}",
        "machine_type": "FDM",
        "purchase_cost": 800.0,
        "lifetime_hours": 800.0,
        "maintenance_factor": 0.15
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/machines/",
        data=json.dumps(machine_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        machine = json.loads(response.read())
    
    machine_id = machine["id"]

    # 2. Prepare dummy G-code
    gcode_content = b";CrealityPrint\n;Filament used: 40.0g\n;Estimated printing time (normal mode): 2h30m\n"
    boundary = uuid.uuid4().hex
    fields = {
        "machine_id": str(machine_id),
        "labor_minutes": "30",
        "hardware_cost": "3.0",
        "material_cost_per_gram": "0.025"
    }

    body = []
    for name, value in fields.items():
        body.append(f'--{boundary}'.encode('ascii'))
        body.append(f'Content-Disposition: form-data; name="{name}"'.encode('ascii'))
        body.append(b'')
        body.append(value.encode('ascii'))
    
    body.append(f'--{boundary}'.encode('ascii'))
    body.append(f'Content-Disposition: form-data; name="file"; filename="verify.gcode"'.encode('ascii'))
    body.append(b'Content-Type: application/octet-stream')
    body.append(b'')
    body.append(gcode_content)
    body.append(f'--{boundary}--'.encode('ascii'))
    
    payload = b'\r\n'.join(body)

    req = urllib.request.Request(
        f"{SERVER_URL}/products/calculate/from-gcode",
        data=payload,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        # Verification based on deterministic formula:
        # machine_hourly_rate = 1.15
        # machine_cost = 2.5 * 1.15 = 2.875
        # material_cost = 40.0 * 0.025 * 1.1 = 1.10
        # labor_cost = 0.5 * 25 = 12.50
        # true_cost = 1.10 + 2.875 + 12.50 + 3.0 = 19.475 -> 19.48
        return result["true_cost"] == 19.48


def verify_asset_calculation():
    """Verify that the engineering asset cost is included in product calculations."""
    # 1. Create an asset
    asset_data = {
        "name": f"Verification Mount {uuid.uuid4().hex[:6]}",
        "design_hours": 10.0,
        "labor_rate": 50.0,
        "target_uses": 100
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/assets/",
        data=json.dumps(asset_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        asset = json.loads(response.read())
    
    # 2. Create a machine
    machine_data = {
        "name": f"Asset Printer {uuid.uuid4().hex[:6]}",
        "machine_type": "FDM",
        "purchase_cost": 1000.0,
        "lifetime_hours": 1000.0,
        "maintenance_factor": 1.0
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/machines/",
        data=json.dumps(machine_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        machine = json.loads(response.read())
    
    # 3. Create a material
    material_data = {
        "name": f"Asset Material {uuid.uuid4().hex[:6]}",
        "cost_per_gram": 0.05
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/materials/",
        data=json.dumps(material_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        material = json.loads(response.read())
    
    # 4. Create a product with the asset
    product_data = {
        "name": "Asset-Linked Product",
        "print_hours": 2.0,
        "labor_minutes": 60,
        "machine_id": machine["id"],
        "materials": [
            {"material_id": material["id"], "grams_used": 100.0}
        ],
        "asset_ids": [asset["id"]]
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/products/",
        data=json.dumps(product_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        product = json.loads(response.read())
    
    # 5. Calculate cost
    req = urllib.request.Request(
        f"{SERVER_URL}/products/{product["id"]}/calculate",
        data=json.dumps({}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        
        # asset_unit_cost = (10 * 50) / 100 = 5.0
        # machine_hourly_rate = (1000 / 1000) * (1 + 1.0) = 2.0
        # machine_cost = 2.0 * 2.0 = 4.0
        # material_cost = 100.0 * 0.05 * 1.1 = 5.5
        # labor_cost = (60 / 60) * 25 = 25.0
        # true_cost = 5.5 + 4.0 + 25.0 + 5.0 = 39.5
        
        return result["true_cost"] == 39.5 and result["asset_cost"] == 5.0


def verify_comparison_calculation():
    """Verify that product comparison accurately calculates deltas."""
    # 1. Create a machine
    machine_data = {
        "name": f"Comp Printer {uuid.uuid4().hex[:6]}",
        "machine_type": "FDM",
        "purchase_cost": 1000.0,
        "lifetime_hours": 1000.0,
        "maintenance_factor": 0.0
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/machines/",
        data=json.dumps(machine_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        machine = json.loads(response.read())

    # 2. Create a material
    material_data = {
        "name": f"Comp Material {uuid.uuid4().hex[:6]}",
        "cost_per_gram": 0.02
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/materials/",
        data=json.dumps(material_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        material = json.loads(response.read())

    # 3. Create two products
    # Variant A: 10 hours, 100g
    # machine_cost = 10 * 1 = 10
    # material_cost = 100 * 0.02 * 1.1 = 2.2
    # labor_cost = 1 * 25 = 25
    # true_cost = 10 + 2.2 + 25 = 37.2
    # suggested_price = 37.2 * 2.7 = 100.44
    # profit = 100.44 - 37.2 = 63.24
    # profit_per_hour = 63.24 / 10 = 6.32
    product_a_data = {
        "name": "Variant A",
        "print_hours": 10.0,
        "labor_minutes": 60,
        "machine_id": machine["id"],
        "materials": [{"material_id": material["id"], "grams_used": 100.0}]
    }
    
    # Variant B: 5 hours, 100g
    # machine_cost = 5 * 1 = 5
    # material_cost = 100 * 0.02 * 1.1 = 2.2
    # labor_cost = 1 * 25 = 25
    # true_cost = 5 + 2.2 + 25 = 32.2
    # suggested_price = 32.2 * 2.7 = 86.94
    # profit = 86.94 - 32.2 = 54.74
    # profit_per_hour = 54.74 / 5 = 10.95 (approx)
    product_b_data = {
        "name": "Variant B",
        "print_hours": 5.0,
        "labor_minutes": 60,
        "machine_id": machine["id"],
        "materials": [{"material_id": material["id"], "grams_used": 100.0}]
    }

    def create_product(data):
        req = urllib.request.Request(
            f"{SERVER_URL}/products/",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())

    prod_a = create_product(product_a_data)
    prod_b = create_product(product_b_data)

    # 4. Compare
    compare_data = {
        "product_a_id": prod_a["id"],
        "product_b_id": prod_b["id"]
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/products/compare",
        data=json.dumps(compare_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        
        # deltas:
        # true_cost_delta = 32.2 - 37.2 = -5.0
        # profit_per_hour_delta = 10.95 - 6.32 = 4.63
        return (
            result["delta"]["true_cost"] == -5.0 and
            result["delta"]["better_variant"] == "product_b"
        )


def verify_automation():
    """Verify batch endpoint and CLI tool."""
    # 1. Setup Data
    machine_data = {
        "name": f"Auto Printer {uuid.uuid4().hex[:6]}",
        "machine_type": "FDM",
        "purchase_cost": 500.0,
        "lifetime_hours": 500.0,
        "maintenance_factor": 0.0
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/machines/",
        data=json.dumps(machine_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        machine = json.loads(response.read())

    def create_prod(name, hours):
        data = {
            "name": name,
            "print_hours": hours,
            "labor_minutes": 0,
            "machine_id": machine["id"],
            "materials": []
        }
        r = urllib.request.Request(
            f"{SERVER_URL}/products/",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read())

    p1 = create_prod("Auto P1", 1.0)
    p2 = create_prod("Auto P2", 2.0)

    # 2. Verify Batch Endpoint
    batch_data = {"product_ids": [p1["id"], p2["id"]]}
    req = urllib.request.Request(
        f"{SERVER_URL}/automation/batch-calculate",
        data=json.dumps(batch_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        batch_res = json.loads(response.read())
        if len(batch_res["results"]) != 2:
            return False

    # 3. Verify CLI (using subprocess)
    try:
        # Test CLI 'list'
        cp = subprocess.run(
            [sys.executable, "tools/maker_ops_cli.py", "list"],
            capture_output=True, text=True, check=True
        )
        if "Auto P1" not in cp.stdout:
            return False

        # Test CLI 'compare'
        cp = subprocess.run(
            [sys.executable, "tools/maker_ops_cli.py", "compare", str(p1["id"]), str(p2["id"])],
            capture_output=True, text=True, check=True
        )
        if "better_variant" not in cp.stdout:
            return False
            
        return True
    except subprocess.CalledProcessError:
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
    
    print("Checking G-code calculation...")
    try:
        if not verify_gcode_calculation():
            failures.append("gcode_calculation_accuracy")
    except Exception as e:
        print(f"G-code calculation failed with error: {e}")
        failures.append("gcode_calculation_error")

    print("Checking Engineering Asset calculation...")
    try:
        if not verify_asset_calculation():
            failures.append("asset_calculation_accuracy")
    except Exception as e:
        print(f"Engineering Asset calculation failed with error: {e}")
        failures.append("asset_calculation_error")

    print("Checking Design Comparison calculation...")
    try:
        if not verify_comparison_calculation():
            failures.append("comparison_calculation_accuracy")
    except Exception as e:
        print(f"Design Comparison calculation failed with error: {e}")
        failures.append("comparison_calculation_error")

    print("Checking Automation (Batch/CLI)...")
    try:
        if not verify_automation():
            failures.append("automation_failure")
    except Exception as e:
        print(f"Automation verification failed with error: {e}")
        failures.append("automation_error")

    return failures


def main():
    proc = start_server()
    if not proc:
        sys.exit(1)

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

