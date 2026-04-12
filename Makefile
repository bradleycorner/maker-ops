FREECAD_MOD_DIR := $(HOME)/Library/Application Support/FreeCAD/Mod
WORKBENCH_SRC   := freecad/Mod/MakerOps
WORKBENCH_DEST  := $(FREECAD_MOD_DIR)/MakerOps

.PHONY: install-workbench uninstall-workbench

## Copy workbench files from repo into FreeCAD Mod directory.
## Restart FreeCAD after running this.
install-workbench:
	@echo "Installing MakerOps workbench..."
	@mkdir -p "$(WORKBENCH_DEST)"
	@rsync -av --delete "$(WORKBENCH_SRC)/" "$(WORKBENCH_DEST)/"
	@echo "Done. Restart FreeCAD to pick up changes."

## Remove the installed workbench from FreeCAD.
uninstall-workbench:
	@echo "Uninstalling MakerOps workbench..."
	@rm -rf "$(WORKBENCH_DEST)"
	@echo "Done."
