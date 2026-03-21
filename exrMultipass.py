bl_info = {
    'name': 'EXR_multipass',
    'author': 'Rei',
    'version': (1, 5, 1),
    'blender': (4, 0, 0),
    'category': 'Compositing',
    'location': 'Compositing Tab > Sidebar > EXR_multipass',
    'description': 'Create named Render Layer + File Output pairs with auto-framing.',
}

import bpy

PASS_MAP = {
    'Image': 'beauty', 'Alpha': 'alpha', 'Depth': 'Z', 'Mist': 'mist',
    'Position': 'position', 'Normal': 'normal', 'Vector': 'vector', 'UV': 'UV',
    'Denoising Normal': 'denoising_normal', 'Denoising Albedo': 'denoising_albedo',
    'Denoising Depth': 'denoising_depth', 'IndexOB': 'object_ID', 'IndexMA': 'material_ID',
    'DiffDir': 'diffuse_direct', 'DiffInd': 'diffuse_indirect', 'DiffCol': 'diffuse_color',
    'GlossDir': 'glossy_direct', 'GlossInd': 'glossy_indirect', 'GlossCol': 'glossy_color',
    'TransDir': 'transmission_direct', 'TransInd': 'transmission_indirect', 
    'TransCol': 'transmission_color', 'VolumeDir': 'volume_direct', 'VolumeInd': 'volume_indirect',
    'Emit': 'emission', 'Env': 'environment', 'AO': 'AO',
    'Shadow Catcher': 'shadow_catcher', 'Noisy Shadow Catcher': 'noisy_shadow_catcher',
    'Noisy Image': 'noisy_image',
}

# Global toggle for multiple instances
class EXR_Multipass_Settings(bpy.types.PropertyGroup):
    allow_multiple: bpy.props.BoolProperty(
        name="Allow Multiple",
        description="Allow creating multiple Render Layer + Output setups",
        default=False
    )

def get_compositor_tree(scene):
    if bpy.app.version >= (5, 0, 0):
        if getattr(scene, 'compositing_node_group', None) is None:
            tree = bpy.data.node_groups.new("Compositor", "CompositorNodeTree")
            scene.compositing_node_group = tree
        return scene.compositing_node_group
    else:
        scene.use_nodes = True
        return scene.node_tree

def link_render_layers(tree, src, dst):
    for out in src.outputs:
        if not out.enabled:
            continue
        name = out.name
        key = name if name.startswith('Crypto') else PASS_MAP.get(name, name)
        
        target_input = dst.inputs.get(key)
        if not target_input:
            if bpy.app.version >= (5, 0, 0):
                sock_type = 'FLOAT' if out.type == 'VALUE' else out.type
                if sock_type not in ('FLOAT', 'INT', 'BOOLEAN', 'VECTOR', 'RGBA'):
                    sock_type = 'RGBA'
                new_item = dst.file_output_items.new(sock_type, key)
                target_input = dst.inputs.get(new_item.name) or dst.inputs[-2]
            else:
                dst.file_slots.new(key)
                target_input = dst.inputs[-1]
                
        if target_input:
            tree.links.new(out, target_input)

def create_exr_multipass(context):
    scene = context.scene
    view_layer = context.view_layer.name
    tree = get_compositor_tree(scene)
    nodes = tree.nodes
    
    # Create Frame
    frame = nodes.new('NodeFrame')
    frame.label = f"EXR_{view_layer}"
    frame.use_custom_color = True
    frame.color = (0.2, 0.3, 0.4)

    # Create Render Layers
    rl = nodes.new('CompositorNodeRLayers')
    rl.label = f"RL_{view_layer}"
    rl.layer = view_layer
    rl.parent = frame
    rl.location = (0, 0)

    # Create File Output
    fo = nodes.new('CompositorNodeOutputFile')
    fo.label = f"OUT_{view_layer}"
    fo.parent = frame
    fo.location = (400, 0)
    
    if bpy.app.version >= (5, 0, 0):
        fo.directory = ""
    else:
        fo.base_path = ""
    
    fo.format.file_format = 'OPEN_EXR_MULTILAYER'
    fo.format.color_depth = '16'
    fo.format.exr_codec = 'ZIP'

    # Clear and Link
    if bpy.app.version >= (5, 0, 0):
        fo.file_output_items.clear()
    else:
        fo.file_slots.clear()
        
    link_render_layers(tree, rl, fo)
    return frame

class NODE_OT_exr_multipass(bpy.types.Operator):
    bl_idname = 'node.exr_multipass'
    bl_label = 'Create EXR Multipass'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.exr_multipass_settings
        tree = get_compositor_tree(context.scene)
        view_layer = context.view_layer.name
        
        if not settings.allow_multiple:
            existing = next((n for n in tree.nodes if n.label == f"OUT_{view_layer}"), None)
            if existing:
                self.report({'WARNING'}, f"Setup for {view_layer} already exists!")
                return {'CANCELLED'}

        create_exr_multipass(context)
        self.report({'INFO'}, f"EXR setup created for {view_layer}")
        return {'FINISHED'}

class NODE_PT_exr_multipass_panel(bpy.types.Panel):
    bl_label = 'EXR Multipass v1.6'
    bl_idname = 'NODE_PT_exr_multipass'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'EXR Multipass'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.exr_multipass_settings
        
        col = layout.column(align=True)
        col.prop(settings, "allow_multiple", toggle=True, icon='DUPLICATE')
        col.separator()
        
        row = col.row()
        row.scale_y = 2.0
        row.operator('node.exr_multipass', text='Create Multipass', icon='ADD')

classes = (
    EXR_Multipass_Settings,
    NODE_OT_exr_multipass,
    NODE_PT_exr_multipass_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.exr_multipass_settings = bpy.props.PointerProperty(type=EXR_Multipass_Settings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.exr_multipass_settings

if __name__ == '__main__':
    register()