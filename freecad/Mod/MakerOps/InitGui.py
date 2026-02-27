
import FreeCAD as App
import FreeCADGui as Gui

print("Maker-Ops: Loading workbench...")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class EstimateSelectedCommand:
    _profile_id = None
    _profile_name = ""

    def GetResources(self):
        return {
            "Pixmap": "Std_ViewScreenShot",
            "MenuText": "Estimate Selection",
            "ToolTip": "Show cost estimate for selected body/bodies",
        }

    def Activated(self):
        import json, urllib.request  # FreeCAD scoping safety

        # --- helpers (defined locally — module globals unavailable in callbacks) ---

        def extract_shape_data(obj):
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

        def fetch_profiles():
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:8000/print-profiles/", timeout=2
                ) as r:
                    return json.loads(r.read().decode())
            except Exception:
                return []

        def call_api(name, vol, dims, profile_id=None, color_changes=0):
            url = "http://127.0.0.1:8000/products/estimate-from-geometry"
            payload = {
                "name": name,
                "volume_mm3": vol,
                "machine_id": 1,
                "material_id": 1,
                "dimensions_mm": dims,
                "save": False,
                "color_changes": color_changes,
            }
            if profile_id is not None:
                payload["print_profile_id"] = profile_id
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as r:
                return json.loads(r.read().decode())

        def show_dialog(body_results, profile_name=""):
            try:
                from PySide2 import QtWidgets, QtGui
            except ImportError:
                try:
                    from PySide6 import QtWidgets, QtGui
                except ImportError:
                    App.Console.PrintError("Maker-Ops: PySide2/PySide6 not available.\n")
                    return

            W = 44
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
                norm   = res.get("normalization")

                total_mass  += mass
                total_hours += hours
                total_cost  += cost
                total_srp   += srp
                ok_count    += 1

                if profile_name:
                    lines.append(f"  Profile:      {profile_name}")
                lines.append(f"  Volume:       {vol:>12,.1f} mm³")
                if dims:
                    lines.append(f"  Dimensions:   {dims['x']:.1f} × {dims['y']:.1f} × {dims['z']:.1f} mm")

                if norm:
                    conf = norm.get("confidence_level", "")
                    lines.append(f"  Material Breakdown")
                    lines.append(f"  ─ Perimeter:     {norm['perimeter_g']:>9.2f} g")
                    lines.append(f"  ─ Infill:        {norm['infill_g']:>9.2f} g")
                    lines.append(f"  ─ Top/Bottom:    {norm['top_bottom_g']:>9.2f} g")
                    if norm.get("purge_g", 0.0) > 0:
                        lines.append(f"  ─ Purge:         {norm['purge_g']:>9.2f} g")
                    lines.append(f"  Total Mass:   {mass:>12.2f} g  [{conf}]")
                else:
                    lines.append(f"  Mass:         {mass:>12.2f} g")

                lines.append(f"  Print Time:   {hours:>12.2f} hrs")
                lines.append(f"  True Cost:    {'$'+f'{cost:.2f}':>12}")
                lines.append(f"  SRP (2.7×):   {'$'+f'{srp:.2f}':>12}")
                lines.append(f"  Margin:       {margin:>11.1f}%")
                if pph:
                    lines.append(f"  Profit/Hr:    {'$'+f'{pph:.2f}':>12}")
                lines.append("")

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
            doc_height = browser.document().size().height()
            browser.setMinimumHeight(min(int(doc_height) + 20, 600))
            layout.addWidget(browser)

            btn = QtWidgets.QPushButton("Close")
            btn.clicked.connect(dlg.accept)
            layout.addWidget(btn)

            dlg.setLayout(layout)
            dlg.exec()

        # --- main logic ---

        cls = self.__class__

        selection = Gui.Selection.getSelection()
        if not selection:
            App.Console.PrintWarning("Maker-Ops: Select one or more bodies first.\n")
            return

        # Profile picker — shown once per session if profiles are available
        if cls._profile_id is None:
            profiles = fetch_profiles()
            if profiles:
                try:
                    from PySide2 import QtWidgets
                except ImportError:
                    try:
                        from PySide6 import QtWidgets
                    except ImportError:
                        QtWidgets = None

                if QtWidgets is not None:
                    names = [p["name"] for p in profiles]
                    names.insert(0, "(None — M6 fallback)")
                    chosen, ok = QtWidgets.QInputDialog.getItem(
                        Gui.getMainWindow(),
                        "Maker-Ops — Select Print Profile",
                        "Profile:",
                        names,
                        0,
                        False,
                    )
                    if ok and chosen != names[0]:
                        for p in profiles:
                            if p["name"] == chosen:
                                cls._profile_id = p["id"]
                                cls._profile_name = p["name"]
                                break

        body_results = []
        for obj in selection:
            vol, dims = extract_shape_data(obj)
            if vol is None:
                App.Console.PrintWarning(
                    f"Maker-Ops: Skipping '{obj.Label}' — no valid shape.\n"
                )
                continue
            try:
                res = call_api(obj.Label, vol, dims, profile_id=cls._profile_id)
            except Exception as e:
                App.Console.PrintError(
                    f"Maker-Ops: API error for '{obj.Label}': {e}\n"
                )
                res = {"error": str(e)}
            body_results.append((obj.Label, vol, dims, res))

        if body_results:
            show_dialog(body_results, profile_name=cls._profile_name)

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
        import json, urllib.request  # FreeCAD scoping safety

        def extract_shape_data(obj):
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

        def call_api(name, vol, dims):
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

        class MakerOpsObserver:
            def slotChangedObject(self, obj, prop):
                import json, urllib.request
                if prop != "Shape":
                    return
                vol, dims = extract_shape_data(obj)
                if vol is None:
                    return
                try:
                    res = call_api(obj.Label, vol, dims)
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
