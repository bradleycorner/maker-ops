#!/usr/bin/env python3
import argparse
import json
import sys
import requests

SERVER_URL = "http://127.0.0.1:8000"

def list_products(args):
    r = requests.get(f"{SERVER_URL}/products/")
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))

def calculate_product(args):
    payload = {}
    if args.labor_rate: payload["target_hourly_rate"] = args.labor_rate
    
    r = requests.post(f"{SERVER_URL}/products/{args.id}/calculate", json=payload)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))

def compare_products(args):
    payload = {
        "product_a_id": args.id_a,
        "product_b_id": args.id_b
    }
    r = requests.post(f"{SERVER_URL}/products/compare", json=payload)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))

def upload_gcode(args):
    files = {'file': open(args.file, 'rb')}
    data = {
        "machine_id": args.machine_id,
        "labor_minutes": args.labor_minutes,
        "material_cost_per_gram": args.material_cost,
        "hardware_cost": args.hardware_cost
    }
    r = requests.post(f"{SERVER_URL}/products/calculate/from-gcode", files=files, data=data)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))

def main():
    parser = argparse.ArgumentParser(description="Maker-Ops Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    subparsers.add_parser("list", help="List all products")

    # Calculate
    calc = subparsers.add_parser("calculate", help="Calculate cost for a product")
    calc.add_argument("id", type=int, help="Product ID")
    calc.add_argument("--labor-rate", type=float, help="Override target hourly labor rate")

    # Compare
    comp = subparsers.add_parser("compare", help="Compare two products")
    comp.add_argument("id_a", type=int)
    comp.add_argument("id_b", type=int)

    # Upload
    up = subparsers.add_parser("upload", help="Calculate cost from G-code file")
    up.add_argument("file", help="Path to .gcode file")
    up.add_argument("--machine-id", type=int, required=True)
    up.add_argument("--material-cost", type=float, required=True)
    up.add_argument("--labor-minutes", type=int, default=0)
    up.add_argument("--hardware-cost", type=float, default=0.0)

    args = parser.parse_args()

    try:
        if args.command == "list":
            list_products(args)
        elif args.command == "calculate":
            calculate_product(args)
        elif args.command == "compare":
            compare_products(args)
        elif args.command == "upload":
            upload_gcode(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
