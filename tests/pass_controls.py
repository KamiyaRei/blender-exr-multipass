import bpy
import importlib.util
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import exrMultipass as addon
from exrMultipass import core
addon.register()
for engine in ['CYCLES', 'BLENDER_EEVEE_NEXT' if bpy.app.version < (5, 0, 0) else 'BLENDER_EEVEE']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.use_motion_blur = False
    layer = bpy.context.view_layer
    before = core.get_compositor_tree(scene, create=False)
    assert bpy.ops.node.exr_multipass_toggle_pass(owner='layer', prop='use_pass_z') == {'FINISHED'}
    assert layer.use_pass_z
    assert core.get_compositor_tree(scene, create=False) == before
    frame = core.create_exr_multipass(bpy.context)
    frame2 = core.create_exr_multipass(bpy.context)
    tree = core.get_compositor_tree(scene)
    source, output = core.setup_nodes(tree, frame)
    _, output2 = core.setup_nodes(tree, frame2)
    other = scene.view_layers.new('Other')
    other.use_pass_z = False
    reroute = tree.nodes.new('NodeReroute')
    tree.links.new(source.outputs['Image'], reroute.inputs[0])
    tree.links.new(reroute.outputs[0], output.inputs['beauty'])
    for _, owner, prop, label in core.render_pass_controls(bpy.context):
        target = layer if owner == 'layer' else getattr(layer, owner)
        original = getattr(target, prop)
        for expected in [not original, original]:
            assert bpy.ops.node.exr_multipass_toggle_pass(owner=owner, prop=prop) == {'FINISHED'}, prop
            assert getattr(target, prop) == expected
            planned = {name for _, name in core.pass_plan(source)}
            assert planned == {s.name for s in output.inputs if s.name}, prop
            assert planned == {s.name for s in output2.inputs if s.name}, prop
        if prop == 'use_pass_z':
            assert not other.use_pass_z
        assert output.inputs['beauty'].links[0].from_node == reroute
    assert bpy.ops.node.exr_multipass_toggle_pass(owner='layer', prop='use_pass_z') == {'FINISHED'}
    assert not layer.use_pass_z and output.inputs.get('Z') is None
    scene.render.use_motion_blur = True
    assert bpy.ops.node.exr_multipass_toggle_pass(owner='layer', prop='use_pass_vector') == {'CANCELLED'}
    assert bpy.ops.node.exr_multipass_toggle_pass(owner='layer', prop='name') == {'CANCELLED'}
    print('PASS controls', engine, len(core.render_pass_controls(bpy.context)))
addon.unregister()
print('ALL PASS CONTROL TESTS PASSED', bpy.app.version_string)
