
# Maker-Ops FreeCAD Workbench

Manufacturing cost evaluation integrated directly into FreeCAD 1.1.

## Installation

1. Find your FreeCAD `Mod` directory:
   - On macOS: `~/Library/Application Support/FreeCAD/Mod/`
   - You can verify this in the FreeCAD Python console with: `App.getUserAppDataDir() + "Mod"`

2. Create a symlink or copy this directory:
   ```bash
   ln -s "/Users/bradleycorner/CLionProjects/maker-ops/freecad/Mod/MakerOps" "/Users/bradleycorner/Library/Application Support/FreeCAD/Mod/MakerOps"
   ```

3. Restart FreeCAD.

## Features

- **Estimate Selection**: Select an object in the Tree View and click the icon to get a cost estimate in the Report View.
- **Toggle Live Mode**: Enable real-time updates. Every time you change a parametric value or the geometry, the cost estimate will refresh automatically.

## Requirements

- Maker-Ops backend must be running on `http://127.0.0.1:8000`.
- Requires no external Python libraries (uses built-in `urllib`).
