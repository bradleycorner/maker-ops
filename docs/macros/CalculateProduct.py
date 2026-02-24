# FreeCAD Macro: Maker-Ops Integration
# This is a sample macro to demonstrate how to trigger calculations from within CAD.

import json
import requests

# Configuration
SERVER_URL = "http://127.0.0.1:8000"
PRODUCT_ID = 1  # Replace with actual product ID linked to this design

def calculate():
    try:
        print(f"Requesting cost calculation for Product #{PRODUCT_ID}...")
        r = requests.post(f"{SERVER_URL}/products/{PRODUCT_ID}/calculate")
        r.raise_for_status()
        
        result = r.json()
        
        # Display results in FreeCAD report view
        msg = (
            "
--- Maker-Ops Cost Breakdown ---
"
            f"True Unit Cost: ${result['true_cost']:.2f}
"
            f"Suggested Retail: ${result['suggested_price']:.2f}
"
            f"Profit Margin: {result['profit_margin']}%
"
            f"Profit/Print Hour: ${result['profit_per_print_hour']:.2f}
"
            "-------------------------------
"
        )
        print(msg)
        
    except Exception as e:
        print(f"Maker-Ops Error: {e}")

if __name__ == "__main__":
    calculate()

# Note: For this to work in FreeCAD, the 'requests' library must be 
# available to FreeCAD's internal Python interpreter.
# Usually: pip install requests (to the system python or FreeCAD's site-packages)
