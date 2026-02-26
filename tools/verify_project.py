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


def verify_geometry_estimation():
    """Verify that geometry-based estimation calculates accurate costs."""
    # 1. Setup machine and material
    machine_data = {
        "name": f"Geo Printer {uuid.uuid4().hex[:6]}",
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

    material_data = {
        "name": f"Geo Material {uuid.uuid4().hex[:6]}",
        "cost_per_gram": 0.02
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/materials/",
        data=json.dumps(material_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        material = json.loads(response.read())

    # 2. Estimate from Geometry
    # Part: 100,000 mm3, 10% infill = 10,000 mm3 actual
    # density 1.25 -> 12.5g
    # flow rate 10.0 mm3/s -> 1000s -> 0.2778 hours
    
    # machine_cost = 0.2778 * 1 = 0.2778
    # material_cost = 12.5 * 0.02 * 1.1 = 0.275
    # true_cost = 0.2778 + 0.275 = 0.5528 -> 0.55
    
    geo_data = {
        "name": "Geo Part",
        "volume_mm3": 100000.0,
        "material_id": material["id"],
        "machine_id": machine["id"],
        "infill_percentage": 10.0,
        "volumetric_flow_rate": 10.0
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/products/estimate-from-geometry",
        data=json.dumps(geo_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        # Check nested calculation result
        return result["calculation"]["true_cost"] == 0.55


def verify_print_normalization():
    """Verify the Print Process Normalization (M7) end-to-end."""
    # 1. Create machine
    machine_data = {
        "name": f"Norm Printer {uuid.uuid4().hex[:6]}",
        "machine_type": "FDM",
        "purchase_cost": 1000.0,
        "lifetime_hours": 1000.0,
        "maintenance_factor": 0.0,
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/machines/",
        data=json.dumps(machine_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        machine = json.loads(response.read())

    # 2. Create material
    material_data = {
        "name": f"Norm PLA {uuid.uuid4().hex[:6]}",
        "cost_per_gram": 0.02,
        "density_g_cm3": 1.24,
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/materials/",
        data=json.dumps(material_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        material = json.loads(response.read())

    # 3. Create print profile
    profile_data = {
        "name": "0.4mm Standard",
        "nozzle_diameter_mm": 0.4,
        "layer_height_mm": 0.2,
        "wall_count": 3,
        "infill_percentage": 20.0,
        "top_layers": 4,
        "bottom_layers": 4,
        "extrusion_width_factor": 1.2,
        "volumetric_flow_rate_mm3s": 10.0,
        "purge_mass_per_change_g": 3.0,
    }
    req = urllib.request.Request(
        f"{SERVER_URL}/print-profiles/",
        data=json.dumps(profile_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        profile = json.loads(response.read())

    assert profile["id"] > 0, "Profile ID must be a positive integer"

    # 4. POST estimate-from-geometry with profile + dimensions
    geo_data = {
        "name": "Norm Test Part",
        "volume_mm3": 50000.0,
        "material_id": material["id"],
        "machine_id": machine["id"],
        "print_profile_id": profile["id"],
        "dimensions_mm": {"x": 40.0, "y": 30.0, "z": 20.0},
        "color_changes": 0,
    }

    def post_estimate():
        req = urllib.request.Request(
            f"{SERVER_URL}/products/estimate-from-geometry",
            data=json.dumps(geo_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())

    result = post_estimate()

    # 5. Assert normalization object present with all fields
    norm = result.get("normalization")
    if norm is None:
        return False
    for field in ("perimeter_g", "infill_g", "top_bottom_g", "purge_g", "confidence_level"):
        if field not in norm:
            return False

    # 6. Assert confidence_level == "medium" (dimensions were provided)
    if norm["confidence_level"] != "medium":
        return False

    # 7. Assert mass > 0 and print_hours > 0
    if result["estimated_mass_g"] <= 0:
        return False
    if result["estimated_print_hours"] <= 0:
        return False

    # 8. Assert print_profile_id echoed back correctly
    if result.get("print_profile_id") != profile["id"]:
        return False

    # 9. Determinism: same request → identical values
    result2 = post_estimate()
    if result["estimated_mass_g"] != result2["estimated_mass_g"]:
        return False
    if result["estimated_print_hours"] != result2["estimated_print_hours"]:
        return False

    return True


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

    print("Checking Geometry Estimation...")
    try:
        if not verify_geometry_estimation():
            failures.append("geometry_estimation_accuracy")
    except Exception as e:
        print(f"Geometry estimation failed with error: {e}")
        failures.append("geometry_estimation_error")

    print("Checking Print Process Normalization...")
    try:
        if not verify_print_normalization():
            failures.append("print_normalization_accuracy")
    except Exception as e:
        print(f"Print normalization failed with error: {e}")
        failures.append("print_normalization_error")

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

