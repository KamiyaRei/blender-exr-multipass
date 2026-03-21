bl_info = {
    'name': 'EXR_multipass',
    'author': 'Rei',
    'version': (1, 5, 2),
    'blender': (4, 0, 0),
    'category': 'Compositing',
    'location': 'Compositing Tab > Sidebar > EXR_multipass',
    'description': 'EXR setup with ordered coloring, 10% brightness steps, and tight offset.',
}

import bpy
import colorsys

# User defined HEX Palette
COLOR_PALETTE = ["576FB3", "B3557A", "975CB3", "6F9976", "998057"]

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

class EXR_Settings_Group(bpy.types.PropertyGroup):
    allow_multiple: bpy.props.BoolProperty(
        name="Allow Multiple Copies",
        description="Enable to create additional setups for the same View Layer",
        default=False
    )

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def get_logic_color(tree, layer_name):
    '''Calculates color group by creation order and brightness by copy count'''
    frames = [n for n in tree.nodes if n.type == 'FRAME']
    
    # Get unique layers already existing in the tree to determine group index
    unique_existing_layers = []
    for f in frames:
        if f.label not in unique_existing_layers:
            unique_existing_layers.append(f.label)
    
    if layer_name in unique_existing_layers:
        group_idx = unique_existing_layers.index(layer_name)
    else:
        group_idx = len(unique_existing_layers)
        
    # Count how many copies of THIS specific layer already exist
    copy_idx = len([f for f in frames if f.label == layer_name])
    
    # Pick base color from palette
    base_rgb = hex_to_rgb(COLOR_PALETTE[group_idx % len(COLOR_PALETTE)])
    h, s, v = colorsys.rgb_to_hsv(*base_rgb)
    
    # 10% brightness reduction. Cycles if it gets too dark (< 0.15)
    reduction = (copy_idx * 0.10) % 0.6
    new_v = max(0.15, v - reduction)
    
    return colorsys.hsv_to_rgb(h, s, new_v)

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
        if not out.enabled: continue
        name = out.name
        key = name if name.startswith('Crypto') else PASS_MAP.get(name, name)
        
        target_input = dst.inputs.get(key)
        if not target_input:
            for inp in dst.inputs:
                if inp.identifier == key or inp.name == key:
                    target_input = inp
                    break
                    
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
    
    # Calculate tight Y offset (320px gap)
    min_y = 0
    if nodes:
        min_y = min([n.location.y for n in nodes]) - 320

    # Create Frame
    frame = nodes.new('NodeFrame')
    frame.label = view_layer
    frame.use_custom_color = True
    rgb = get_logic_color(tree, view_layer)
    frame.color = rgb
    frame.location = (0, min_y)

    # Nodes Setup
    rl = nodes.new('CompositorNodeRLayers')
    rl.label = f"Render Layers [{view_layer}]"
    rl.layer = view_layer
    rl.parent = frame
    rl.location = (0, 0)

    fo = nodes.new('CompositorNodeOutputFile')
    fo.label = f"Output [{view_layer}]"
    fo.parent = frame
    fo.location = (450, 0)
    
    if bpy.app.version >= (5, 0, 0):
        fo.directory = ""
        fo.file_output_items.clear()
    else:
        fo.base_path = ""
        fo.file_slots.clear()
    
    fo.format.file_format = 'OPEN_EXR_MULTILAYER'
    fo.format.color_depth = '16'
    fo.format.exr_codec = 'ZIP'

    link_render_layers(tree, rl, fo)
    return frame

class NODE_OT_exr_multipass(bpy.types.Operator):
    bl_idname = 'node.exr_multipass'
    bl_label = 'Create Setup'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.exr_multipass_settings
        tree = get_compositor_tree(context.scene)
        view_layer = context.view_layer.name
        
        if not settings.allow_multiple:
            existing = next((n for n in tree.nodes if n.type == 'FRAME' and n.label == view_layer), None)
            if existing:
                self.report({'WARNING'}, f"Setup for '{view_layer}' already exists.")
                return {'CANCELLED'}

        create_exr_multipass(context)
        self.report({'INFO'}, f"Setup generated for {view_layer}")
        return {'FINISHED'}

class NODE_PT_exr_multipass_panel(bpy.types.Panel):
    bl_label = 'EXR Multipass'
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
        info = col.box()
        row = info.row()
        row.label(text="Target Layer:", icon='RENDERLAYERS')
        row.label(text=context.view_layer.name)
        
        sett = col.box()
        sett.prop(settings, "allow_multiple", text="Allow Multiple Copies") 
        
        col.separator(factor=1.0)
        row = col.row()
        row.scale_y = 2.0
        row.operator('node.exr_multipass', text='Create Setup', icon='ADD')

classes = (
    EXR_Settings_Group,
    NODE_OT_exr_multipass,
    NODE_PT_exr_multipass_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.exr_multipass_settings = bpy.props.PointerProperty(type=EXR_Settings_Group)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.exr_multipass_settings

if __name__ == '__main__':
    register()