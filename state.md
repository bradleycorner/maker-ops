# Maker-Ops Workbench State (FreeCAD 1.1 RC2)

## Status (2026-02-25)

All workbench items complete. FreeCAD Mod is stable.

| Feature                          | Status |
|----------------------------------|--------|
| Workbench visible ("Maker-Ops")  | ✅     |
| Registration                     | ✅     |
| Live Mode (real-time console)    | ✅     |
| Estimate command (pop-up dialog) | ✅     |
| API integration (FastAPI)        | ✅     |
| Dimension extraction in live mode| ✅     |
| Pop-up dialog with results       | ✅     |
| Per-body breakdown in dialog     | ✅     |
| Summary totals in dialog         | ✅     |

## Verified FreeCAD 1.1 RC2 Facts

- `obj.Shape.isNull` (lowercase) — `IsNull` fails
- `Std_ViewScreenShot` (camera icon) — verified working
- Symlinks in `v1-1/Mod/` followed correctly
- Inner class/function scoping: import `json` and `urllib.request` inside any
  function or method that runs as a callback (observer slots, etc.)
- Module-level helper functions work normally

## Architecture Notes

- All business logic helpers (`_extract_shape_data`, `_call_api`, `_show_dialog`)
  live at module level in `InitGui.py`
- Observer class defined inside `Activated()` to preserve FreeCAD scoping behaviour
- Dialog uses PySide2 (PySide6 fallback) — both ship with FreeCAD 1.1
- Live mode outputs to Report View console; Estimate command opens modal dialog
