"""Run: blender -b --factory-startup --python-exit-code 1 --python tests/regression.py.

Set EXR_TEST_OUTPUT to a disposable directory. Uses factory scenes only.
"""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import struct

import bpy

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import exrMultipass as addon
from exrMultipass import core
addon.register()
output_root = Path(os.environ.get("EXR_TEST_OUTPUT", tempfile.mkdtemp())).resolve()
output_root.mkdir(parents=True, exist_ok=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.exr_multipass_settings.directory = str(output_root)
    frame = core.create_exr_multipass(bpy.context)
    tree = core.get_compositor_tree(scene)
    source, output = core.setup_nodes(tree, frame)
    return scene, bpy.context.view_layer, tree, frame, source, output


scene, layer, tree, frame, source, output = fresh()
assert output.inputs["beauty"].links[0].from_socket.name == "Image"
assert bpy.ops.node.exr_multipass() == {'CANCELLED'}
layer.use_pass_z = True
core.sync_and_link(tree, source, output)
assert output.inputs.get("Z") is not None
layer.use_pass_z = False
core.sync_and_link(tree, source, output)
assert output.inputs.get("Z") is None
print("PASS create / duplicate guard / remove disabled pass")

for name in ("beauty", "Z", "aov_beauty"):
    layer.aovs.add().name = name
layer.update_render_passes()
core.sync_and_link(tree, source, output)
assert output.inputs["beauty"].links[0].from_socket.name == "Image"
assert output.inputs["aov_beauty"].links[0].from_socket.name == "beauty"
assert output.inputs["aov_Z"].links[0].from_socket.name == "Z"
assert output.inputs["aov_aov_beauty"].links[0].from_socket.name == "aov_beauty"
count = len(output.inputs)
core.sync_and_link(tree, source, output)
assert len(output.inputs) == count
print("PASS AOV collisions / idempotency")

frame.location.y = 321
layer.name = "Renamed"
assert bpy.ops.node.exr_multipass_refresh() == {'FINISHED'}
assert frame.label == "Renamed"
assert frame.location.y == 321
reroute = tree.nodes.new("NodeReroute")
tree.links.new(source.outputs["Image"], reroute.inputs[0])
tree.links.new(reroute.outputs[0], output.inputs["beauty"])
core.sync_and_link(tree, source, output)
assert output.inputs["beauty"].links[0].from_node == reroute
print("PASS layer rename / preserve positions and manual links")

foreign = tree.nodes.new("NodeFrame")
foreign.label = layer.name
foreign.location.y = 999
bpy.ops.node.exr_multipass_refresh()
assert foreign.location.y == 999
core.new_input(output, source.outputs["Image"], "user_custom")
core.sync_and_link(tree, source, output)
assert output.inputs.get("user_custom") is not None
print("PASS foreign frame / user slot untouched")

scene, layer, tree, frame, source, output = fresh()
core.new_input(output, source.outputs["Image"], "Z")
layer.use_pass_z = True
links = len(tree.links)
try:
    core.sync_and_link(tree, source, output)
    raise AssertionError("Expected unmanaged name conflict")
except ValueError:
    pass
assert len(tree.links) == links
print("PASS conflict preflight")

scene, layer, tree, frame, source, output = fresh()
before = len(tree.nodes)
original_sync = core.sync_and_link


def fail(*args):
    raise ValueError("Injected failure")


core.sync_and_link = fail
try:
    core.create_exr_multipass(bpy.context)
    raise AssertionError("Expected creation failure")
except ValueError:
    pass
finally:
    core.sync_and_link = original_sync
assert len(tree.nodes) == before
print("PASS creation rollback")

scene, layer, tree, frame, source, output = fresh()
frame2 = core.create_exr_multipass(bpy.context)
source2, output2 = core.setup_nodes(tree, frame2)
paths = [(n.directory, n.file_name) if bpy.app.version >= (5, 0, 0) else n.base_path
         for n in (output, output2)]
assert paths[0] != paths[1]
frame.name, frame2.name = "ZZZ", "AAA"
assert core.layer_frames(tree, scene, layer.name) == [frame, frame2]
core.arrange_frames(tree, [frame, frame2])
assert frame2.location.y < frame.location.y
print("PASS distinct paths / stable ordering")

camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
scene.collection.objects.link(camera)
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.render.resolution_x = scene.render.resolution_y = 16
scene.render.resolution_percentage = 100
for number in (1, 2):
    scene.frame_set(number)
    bpy.ops.render.render()
files = [p for p in output_root.glob("*.exr") if any(
    n.get(core.TAG)[:12] in p.name for n in (output, output2))]
assert len(files) == 4, [f.name for f in files]


def read_cstring(stream):
    value = bytearray()
    while True:
        byte = stream.read(1)
        assert byte, "Truncated EXR header"
        if byte == b'\0':
            return bytes(value)
        value.extend(byte)


for path in files:
    with path.open('rb') as stream:
        assert stream.read(4) == b'\x76\x2f\x31\x01'
        stream.read(4)
        attributes = {}
        while True:
            name = read_cstring(stream)
            if not name:
                break
            kind = read_cstring(stream)
            length = struct.unpack('<I', stream.read(4))[0]
            attributes[name] = stream.read(length)
        assert struct.unpack('<4i', attributes[b'dataWindow']) == (0, 0, 15, 15)
        assert b'beauty' in attributes[b'channels'] or b'beauty' in attributes.get(b'name', b'')
        assert path.stat().st_size > stream.tell() + 16
print("PASS render two setups x two frames: four EXRs with verified headers")

blend = output_root / "persistence.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
assert bpy.ops.node.exr_multipass_refresh() == {'FINISHED'}
print("PASS save / reload / refresh")
addon.unregister()
addon.register()
addon.unregister()
print("ALL TESTS PASSED", bpy.app.version_string)
