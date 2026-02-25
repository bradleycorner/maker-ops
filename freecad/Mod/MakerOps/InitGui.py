
import json, urllib.request
import FreeCAD as App
import FreeCADGui as Gui

print("Maker-Ops: Loading workbench...")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_shape_data(obj):
    """Return (volume_mm3, dims_dict) from a FreeCAD object, or (None, None)."""
    if not hasattr(obj, "Shape") or obj.Shape is None:
        return None, None
    shape = obj.Shape
    is_null = False
    if hasattr(shape, "isNull"):
        is_null = shape.isNull() if callable(shape.isNull) else shape.isNull
    if is_null:
        return None, None
    if hasattr(shape, "isValid") and not shape.isValid():
        return None, None
    vol = float(shape.Volume)
    bb = shape.BoundBox
    dims = {
        "x": float(bb.XMax - bb.XMin),
        "y": float(bb.YMax - bb.YMin),
        "z": float(bb.ZMax - bb.ZMin),
    }
    return vol, dims


def _call_api(name, vol, dims):
    """POST to /products/estimate-from-geometry. Returns response dict."""
    import json, urllib.request  # import inside for FreeCAD scoping safety
    url = "http://127.0.0.1:8000/products/estimate-from-geometry"
    payload = {
        "name": name,
        "volume_mm3": vol,
        "machine_id": 1,
        "material_id": 1,
        "dimensions_mm": dims,
        "save": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.loads(r.read().decode())


def _show_dialog(body_results):
    """
    Show a Qt dialog with per-body cost breakdown and a totals summary.

    body_results: list of (label, vol, dims, api_response) tuples.
                  On API error the api_response is {"error": "..."}.
    """
    try:
        from PySide2 import QtWidgets, QtGui
    except ImportError:
        try:
            from PySide6 import QtWidgets, QtGui
        except ImportError:
            App.Console.PrintError("Maker-Ops: PySide2/PySide6 not available.\n")
            return

    W = 44  # column width for separator lines

    lines = []
    total_mass = total_hours = total_cost = total_srp = 0.0
    ok_count = 0

    for label, vol, dims, res in body_results:
        lines.append("─" * W)
        lines.append(f"  {label}")
        lines.append("─" * W)

        if "error" in res:
            lines.append(f"  ERROR: {res['error']}")
            lines.append("")
            continue

        calc   = res.get("calculation", {})
        mass   = res.get("estimated_mass_g", 0.0)
        hours  = res.get("estimated_print_hours", 0.0)
        cost   = calc.get("true_cost", 0.0)
        srp    = calc.get("suggested_price", 0.0)
        margin = calc.get("profit_margin", 0.0)
        pph    = calc.get("profit_per_print_hour", 0.0)

        total_mass  += mass
        total_hours += hours
        total_cost  += cost
        total_srp   += srp
        ok_count    += 1

        lines.append(f"  Volume:       {vol:>12,.1f} mm³")
        lines.append(f"  Dimensions:   {dims['x']:.1f} × {dims['y']:.1f} × {dims['z']:.1f} mm")
        lines.append(f"  Mass:         {mass:>12.2f} g")
        lines.append(f"  Print Time:   {hours:>12.2f} hrs")
        lines.append(f"  True Cost:    {'$'+f'{cost:.2f}':>12}")
        lines.append(f"  SRP (2.7×):   {'$'+f'{srp:.2f}':>12}")
        lines.append(f"  Margin:       {margin:>11.1f}%")
        if pph:
            lines.append(f"  Profit/Hr:    {'$'+f'{pph:.2f}':>12}")
        lines.append("")

    # Summary
    count_label = f"{ok_count} bod{'y' if ok_count == 1 else 'ies'}"
    lines.append("═" * W)
    lines.append(f"  SUMMARY — {count_label}")
    lines.append("═" * W)
    lines.append(f"  Total Mass:   {total_mass:>12.2f} g")
    lines.append(f"  Total Time:   {total_hours:>12.2f} hrs")
    lines.append(f"  Total Cost:   {'$'+f'{total_cost:.2f}':>12}")
    lines.append(f"  Total SRP:    {'$'+f'{total_srp:.2f}':>12}")
    lines.append("═" * W)

    text = "\n".join(lines)

    dlg = QtWidgets.QDialog(Gui.getMainWindow())
    dlg.setWindowTitle("Maker-Ops — Cost Estimate")
    dlg.setMinimumWidth(460)

    layout = QtWidgets.QVBoxLayout()

    browser = QtWidgets.QTextEdit()
    browser.setReadOnly(True)
    browser.setFont(QtGui.QFont("Courier New", 10))
    browser.setPlainText(text)
    # Size the text area to content, capped at a reasonable height
    doc_height = browser.document().size().height()
    browser.setMinimumHeight(min(int(doc_height) + 20, 600))
    layout.addWidget(browser)

    btn = QtWidgets.QPushButton("Close")
    btn.clicked.connect(dlg.accept)
    layout.addWidget(btn)

    dlg.setLayout(layout)
    dlg.exec_()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class EstimateSelectedCommand:
    def GetResources(self):
        return {
            "Pixmap": "Std_ViewScreenShot",
            "MenuText": "Estimate Selection",
            "ToolTip": "Show cost estimate for selected body/bodies",
        }

    def Activated(self):
        selection = Gui.Selection.getSelection()
        if not selection:
            App.Console.PrintWarning("Maker-Ops: Select one or more bodies first.\n")
            return

        body_results = []
        for obj in selection:
            vol, dims = _extract_shape_data(obj)
            if vol is None:
                App.Console.PrintWarning(
                    f"Maker-Ops: Skipping '{obj.Label}' — no valid shape.\n"
                )
                continue
            try:
                res = _call_api(obj.Label, vol, dims)
            except Exception as e:
                App.Console.PrintError(
                    f"Maker-Ops: API error for '{obj.Label}': {e}\n"
                )
                res = {"error": str(e)}
            body_results.append((obj.Label, vol, dims, res))

        if body_results:
            _show_dialog(body_results)

    def IsActive(self):
        return App.ActiveDocument is not None


class ToggleLiveModeCommand:
    _observer = None
    _active = False

    def GetResources(self):
        return {
            "Pixmap": "Std_ViewScreenShot",
            "MenuText": "Toggle Live Mode",
            "ToolTip": "Print live cost updates to console when geometry changes",
        }

    def Activated(self):
        class MakerOpsObserver:
            def slotChangedObject(self, obj, prop):
                if prop != "Shape":
                    return
                vol, dims = _extract_shape_data(obj)
                if vol is None:
                    return
                try:
                    res = _call_api(obj.Label, vol, dims)
                    calc  = res.get("calculation", {})
                    mass  = res.get("estimated_mass_g", 0.0)
                    hours = res.get("estimated_print_hours", 0.0)
                    cost  = calc.get("true_cost", 0.0)
                    srp   = calc.get("suggested_price", 0.0)
                    App.Console.PrintMessage(
                        f"⚡ Live | {obj.Label} | "
                        f"{vol:,.0f} mm³  "
                        f"{dims['x']:.1f}×{dims['y']:.1f}×{dims['z']:.1f} mm | "
                        f"{mass:.2f} g  {hours:.2f} h | "
                        f"Cost ${cost:.2f}  SRP ${srp:.2f}\n"
                    )
                except Exception as e:
                    App.Console.PrintError(f"Maker-Ops Live: {e}\n")

        cls = self.__class__
        cls._active = not cls._active
        if cls._active:
            cls._observer = MakerOpsObserver()
            App.addDocumentObserver(cls._observer)
            App.Console.PrintMessage("Maker-Ops: Live Mode ON\n")
        else:
            if cls._observer:
                App.removeDocumentObserver(cls._observer)
                cls._observer = None
            App.Console.PrintMessage("Maker-Ops: Live Mode OFF\n")

    def IsActive(self):
        return App.ActiveDocument is not None


# ---------------------------------------------------------------------------
# Workbench
# ---------------------------------------------------------------------------

class MakerOpsWorkbench(Gui.Workbench):
    MenuText = "Maker-Ops"
    ToolTip = "Manufacturing cost tools"
    Icon = "Std_ViewScreenShot"

    def Initialize(self):
        self.appendToolbar("Maker-Ops", ["EstimateSelected", "ToggleLiveMode"])
        self.appendMenu("Maker-Ops", ["EstimateSelected", "ToggleLiveMode"])

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

Gui.addCommand("EstimateSelected", EstimateSelectedCommand())
Gui.addCommand("ToggleLiveMode", ToggleLiveModeCommand())
Gui.addWorkbench(MakerOpsWorkbench())

print("Maker-Ops: Registration complete.")
