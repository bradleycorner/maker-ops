
import json
import urllib.request
import urllib.error
import FreeCAD as App

# Default settings
SERVER_URL = "http://127.0.0.1:8000"

def get_geometry_params(obj):
    """Extract volume and dimensions from a FreeCAD object."""
    if not hasattr(obj, "Shape"):
        return None
        
    shape = obj.Shape
    volume = shape.Volume
    bbox = shape.BoundBox
    
    return {
        "name": obj.Label,
        "volume_mm3": float(volume),
        "dimensions_mm": {
            "x": float(bbox.XMax - bbox.XMin),
            "y": float(bbox.YMax - bbox.YMin),
            "z": float(bbox.ZMax - bbox.ZMin)
        }
    }

def estimate_cost(params, machine_id=1, material_id=1):
    """Call Maker-Ops API to estimate cost."""
    url = f"{SERVER_URL}/products/estimate-from-geometry"
    
    data = {
        "name": params["name"],
        "volume_mm3": params["volume_mm3"],
        "machine_id": machine_id,
        "material_id": material_id,
        "dimensions_mm": params["dimensions_mm"],
        "infill_percentage": 20.0,
        "volumetric_flow_rate": 10.0,
        "save": False
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
            
    except Exception as e:
        return {"error": str(e)}

def format_report(res):
    """Format API result for FreeCAD console."""
    if "error" in res:
        return f"\n[Maker-Ops Error] {res['error']}\n"
        
    calc = res.get("calculation", {})
    return (
        "\n"
        "--- Maker-Ops Cost Estimate ---\n"
        f"Part Mass:    {res.get('estimated_mass_g', 0):.2f} g\n"
        f"Print Time:   {res.get('estimated_print_hours', 0):.2f} hrs\n"
        f"True Cost:    ${calc.get('true_cost', 0):.2f}\n"
        f"SRP (2.7x):   ${calc.get('suggested_price', 0):.2f}\n"
        f"Profit/Hr:    ${calc.get('profit_per_print_hour', 0):.2f}\n"
        "-------------------------------\n"
    )

class MakerOpsObserver:
    """Observer for live updates."""
    def slotChangedObject(self, obj, prop):
        if prop in ["Shape", "ExpressionEngine", "Length", "Width", "Height", "Radius"]:
            params = get_geometry_params(obj)
            if params:
                App.Console.PrintMessage(f"\n[Maker-Ops Live Update] {obj.Label}\n")
                res = estimate_cost(params)
                App.Console.PrintMessage(format_report(res))
