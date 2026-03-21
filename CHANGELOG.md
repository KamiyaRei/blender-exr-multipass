# Changelog



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
