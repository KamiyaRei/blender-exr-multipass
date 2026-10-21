# Changelog

## [1.7.1] - 2026-10-21

Public update from 1.5.5, consolidating the local 1.6.x and 1.7.0 preview builds.

### Added
- Render Passes panel for the active View Layer, with engine-specific Cycles/Eevee controls and immediate EXR synchronization.
- Editable output paths and unique filenames for newly created setups.
- Frame-color status markers, collapsible panels and an explicit Arrange Nodes action.
- Reproducible ZIP build script, checksum, background tests and test-gated GitHub releases.

### Fixed
- Blender 4.x errors when removing disabled passes.
- Custom AOV names colliding with built-in beauty and utility passes.
- Unrelated frames being mistaken for add-on setups.
- Refresh losing setups after View Layer renaming or replacing manual processing connections.
- New setup outputs sharing a filename.
- Package/file layout changes causing installation errors.

### Changed
- Custom AOVs use the `aov_` prefix. Built-in Image remains `beauty`.
- Refresh preserves positions and output paths; arranging is a separate action.
- Create and Refresh retain double-height buttons.
- Code is organized as a stable `exrMultipass` package with core, operators and panels modules.

### Upgrade notes
- Remove a previous single-file installation and restart Blender before installing this ZIP.
- Setups from 1.5.5 and earlier must be recreated; legacy adoption is not included.
- Update downstream AOV channel selections if needed. Existing 1.6+ output paths are preserved.

---

## [v1.5.5]

- Fix: Unified positioning with strict gap between frames.
- Fix: Name-based sorting to keep new copies at the bottom of the stack.
- Fix: Math-based height calculation (ignores unstable UI dimensions).

---

## [v1.5.4]

- Update: Dynamic Y-offset based on node height/socket count.
- Change: Increased horizontal spacing to 750px for wider nodes.
- Fix: Prevented frame overlaps when adding multiple render passes.

---

## [v1.5.3]

- Update: Column-based grid layout (Layers as columns, Copies as stacks).
- Update: Smart column detection for existing View Layers.

---

## [v1.5.2]

- Update: 10% brightness stepping for duplicate layers.
- Fix: Refresh operator for Blender 4.x (fixed `.path` vs `.name` access).
- Fix: Stable layer-to-color assignment based on creation order.

---

## [v1.5.1]

- Update: Added "Allow Multiple Copies" settings toggle.
- Update: Dynamic frame coloring based on scene name hashing.
- Change: Node labeling updated.
- Update: Automatic grouping of nodes into Frames.

---

## [v1.5.0]

- Update: Universal support for Blender 4.x and 5.x.


---

## [v1.4.0]

- Update: Initial compatibility for Blender 5.0+ Node API.


---
## [v1.3.0]

### Duplicate Node Protection
- When pressing "Create EXR Multipass", the add-on now checks if an `EXR_multipass_output` node already exists.
- If it does, no new nodes are created. A warning appears and the viewport focuses on the existing node.

### Refresh Operator
- Added a "Refresh EXR Multipass" button in the UI.
- It updates all slots and connections without recreating the node.

### Pass Naming
- Further improvements to pass names for better clarity and consistency.

---

## [v1.2.0]

### Interface
- Slight UI adjustments for better clarity.

### File Output Node
- Set label to `"EXR_multipass_output"` for easier identification.

### Pass Naming
- Some pass names have been adjusted to a more common and widely used style.

---

## [v1.1.0]

- Initial release
- Created EXR multipass output setup
