
# Maker-Ops FreeCAD Workbench

Manufacturing cost evaluation integrated directly into FreeCAD 1.1.

## Installation

1. Find your FreeCAD `Mod` directory:
   - On macOS: `~/Library/Application Support/FreeCAD/Mod/`
   - You can verify this in the FreeCAD Python console with: `App.getUserAppDataDir() + "Mod"`

2. Create a symlink pointing to the project on the **internal drive**:
   ```bash
   ln -s "$HOME/Projects/maker-ops/freecad/Mod/MakerOps" \
         "$HOME/Library/Application Support/FreeCAD/Mod/MakerOps"
   ```

   > **Important:** The project must live on the internal drive (`~/Projects/maker-ops`),
   > not on a path that resolves through a symlink to an external volume. If the external
   > drive is not mounted the API will fail to start and the workbench will show
   > "Connection refused".

3. Restart FreeCAD.

## Requirements

- Maker-Ops backend must be running on `http://127.0.0.1:8000`.
- The API auto-starts at login via a launchd agent. Install it once with:
  ```bash
  bash ~/Projects/maker-ops/setup/install-launchagent.sh
  ```
- Requires no external Python libraries (uses built-in `urllib`).

## Features

- **Estimate Selection**: Select an object in the Tree View and click the icon to get a cost estimate in the Report View.
- **Toggle Live Mode**: Enable real-time updates. Every time you change a parametric value or the geometry, the cost estimate will refresh automatically.
