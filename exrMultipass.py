bl_info = {
    'name': 'EXR_multipass',
    'author': 'Rei',
    'version': (1, 5, 0),
    'blender': (4, 0, 0),
    'category': 'Compositing',
    'location': 'Compositing Tab > Sidebar > EXR_multipass',
    'description': (
        'Auto-create Render Layers + File Output (OpenEXR Multilayer) with named passes. '
        'Universal version for Blender 4.x and 5.x'
    ),
}

import bpy

PASS_MAP = {
    # data passes
    'Image': 'beauty',
    'Alpha': 'alpha',
    'Depth': 'Z',
    'Mist': 'mist',
    'Position': 'position',
    'Normal': 'normal',
    'Vector': 'vector',
    'UV': 'UV',
    # denoising data
    'Denoising Normal': 'denoising_normal',
    'Denoising Albedo': 'denoising_albedo',
    'Denoising Depth': 'denoising_depth',
    # indexes
    'IndexOB': 'object_ID',
    'IndexMA': 'material_ID',
    # debug
    'Debug Sample Count': 'debug_sample_count',
    # light passes
    'DiffDir': 'diffuse_direct',
    'DiffInd': 'diffuse_indirect',
    'DiffCol': 'diffuse_color',
    'GlossDir': 'glossy_direct',
    'GlossInd': 'glossy_indirect',
    'GlossCol': 'glossy_color',
    'TransDir': 'transmission_direct',
    'TransInd': 'transmission_indirect',
    'TransCol': 'transmission_color',
    'VolumeDir': 'volume_direct',
    'VolumeInd': 'volume_indirect',
    # other passes
    'Emit': 'emission',
    'Env': 'environment',
    'AO': 'AO',
    'Shadow Catcher': 'shadow_catcher',
    'Noisy Shadow Catcher': 'noisy_shadow_catcher',
    'Noisy Image': 'noisy_image',
}


def get_compositor_tree(scene):
    '''Universal node tree getter for all Blender versions'''
    if bpy.app.version >= (5, 0, 0):
        if getattr(scene, 'compositing_node_group', None) is None:
            tree = bpy.data.node_groups.new("Compositor", "CompositorNodeTree")
            scene.compositing_node_group = tree
        return scene.compositing_node_group
    else:
        scene.use_nodes = True
        return scene.node_tree


def link_render_layers(tree, src, dst):
    '''Link enabled outputs from Render Layers to File Output using PASS_MAP.'''
    for out in src.outputs:
        if not out.enabled:
            continue
            
        name = out.name
        key = name if name.startswith('Crypto') else PASS_MAP.get(name, name)
        
        # Check if socket already exists
        target_input = dst.inputs.get(key)
        if not target_input:
            for inp in dst.inputs:
                if inp.identifier == key or inp.name == key:
                    target_input = inp
                    break
                
        # Create new slot if missing
        if not target_input:
            if bpy.app.version >= (5, 0, 0):
                # Logic for Blender 5.0+
                sock_type = out.type
                if sock_type == 'VALUE':
                    sock_type = 'FLOAT'
                elif sock_type not in ('FLOAT', 'INT', 'BOOLEAN', 'VECTOR', 'RGBA'):
                    sock_type = 'RGBA'
                    
                new_item = dst.file_output_items.new(sock_type, key)
                target_input = dst.inputs.get(new_item.name)
                # Fallback to avoid virtual socket in 5.x
                if not target_input:
                    target_input = dst.inputs[-2]
            else:
                # Logic for Blender 4.x
                dst.file_slots.new(key)
                target_input = dst.inputs[-1]
                
        # Establish link
        if target_input:
            tree.links.new(out, target_input)


def clear_slots(node_out):
    '''Remove all file slots from the File Output node.'''
    if bpy.app.version >= (5, 0, 0):
        items = node_out.file_output_items
        try:
            items.clear()
        except AttributeError:
            for i in range(len(items) - 1, -1, -1):
                items.remove(items[i])
    else:
        try:
            node_out.file_slots.clear()
        except AttributeError:
            for i in range(len(node_out.file_slots) - 1, -1, -1):
                node_out.file_slots.remove(node_out.file_slots[i])


def create_exr_multipass(context):
    '''Create or update Render Layers + File Output nodes.'''  
    scene = context.scene
    tree = get_compositor_tree(scene)
    nodes = tree.nodes

    rl = nodes.new('CompositorNodeRLayers')
    rl.location = (-300, 0)

    fo = nodes.new('CompositorNodeOutputFile')
    fo.location = (50, 0)
    fo.label = 'EXR_multipass_output'
    
    # Path attribute naming difference
    if bpy.app.version >= (5, 0, 0):
        fo.directory = ''
    else:
        fo.base_path = ''
        
    fo.width = 300

    fmt = fo.format
    fmt.file_format = 'OPEN_EXR_MULTILAYER'
    fmt.color_depth = '16'
    fmt.exr_codec = 'ZIP'

    clear_slots(fo)
    link_render_layers(tree, rl, fo)


def update_exr_multipass(context):
    '''Refresh slots & links for existing EXR multipass node.'''  
    tree = get_compositor_tree(context.scene)
    if not tree:
        return False
        
    fo = next(
        (n for n in tree.nodes
         if n.bl_idname == 'CompositorNodeOutputFile' and n.label == 'EXR_multipass_output'),
        None,
    )
    rl = next(
        (n for n in tree.nodes if n.bl_idname == 'CompositorNodeRLayers'),
        None,
    )
    if not fo or not rl:
        return False
        
    clear_slots(fo)
    link_render_layers(tree, rl, fo)
    return True


class NODE_OT_exr_multipass(bpy.types.Operator):
    bl_idname = 'node.exr_multipass'
    bl_label = 'Create EXR Multipass'
    bl_description = 'Create Render Layers + File Output for OpenEXR Multilayer'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sd = context.space_data
        return sd.type == 'NODE_EDITOR' and sd.tree_type == 'CompositorNodeTree'

    def execute(self, context):
        tree = get_compositor_tree(context.scene)
        
        if tree:
            existing = next(
                (n for n in tree.nodes
                 if n.bl_idname == 'CompositorNodeOutputFile' and n.label == 'EXR_multipass_output'),
                None,
            )
            if existing:
                for n in tree.nodes:
                    n.select = False
                existing.select = True
                tree.nodes.active = existing
                bpy.ops.node.view_selected()
                self.report({'WARNING'}, 'EXR multipass already exists')
                return {'CANCELLED'}
                
        create_exr_multipass(context)
        self.report({'INFO'}, 'EXR multipass nodes created and linked')
        return {'FINISHED'}


class NODE_OT_exr_multipass_refresh(bpy.types.Operator):
    bl_idname = 'node.exr_multipass_refresh'
    bl_label = 'Refresh EXR Multipass'
    bl_description = 'Refresh slots & links on existing EXR multipass nodes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sd = context.space_data
        return sd.type == 'NODE_EDITOR' and sd.tree_type == 'CompositorNodeTree'

    def execute(self, context):
        ok = update_exr_multipass(context)
        if ok:
            self.report({'INFO'}, 'EXR multipass refreshed')
        else:
            self.report({'WARNING'}, 'No existing EXR multipass nodes found')
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
        for op_id, text, icon in (
            ('node.exr_multipass', 'Create EXR Multipass', 'ADD'),
            ('node.exr_multipass_refresh', 'Refresh EXR Multipass', 'FILE_REFRESH'),
        ):
            row = layout.row(align=True)
            row.scale_x = 2.0
            row.scale_y = 1.5
            row.separator(factor=1.0)
            row.operator(op_id, text=text, icon=icon)


classes = (
    NODE_OT_exr_multipass,
    NODE_OT_exr_multipass_refresh,
    NODE_PT_exr_multipass_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()