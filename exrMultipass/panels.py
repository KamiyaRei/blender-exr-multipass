"""Compositor sidebar panels."""
import bpy
from .core import (get_compositor_tree, setup_nodes, layer_frames,
                   render_pass_controls, pass_control_enabled)

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
        layout.use_property_decorate = False
        settings = context.scene.exr_multipass_settings
        tree = get_compositor_tree(context.scene, create=False)
        frames = layer_frames(tree, context.scene, context.view_layer.name)

        info = layout.box()
        info.label(text=context.view_layer.name, icon='RENDERLAYERS')
        if frames:
            status = info.row(align=True)
            status.template_node_socket(color=(*frames[0].color, 1.0))
            status.label(text=f"{len(frames)} setup" + ("s" if len(frames) != 1 else ""))
        else:
            info.label(text="No setup for this layer", icon='INFO')

        layout.prop(settings, 'allow_multiple', text="Allow Multiple Copies")
        layout.separator(factor=0.5)
        row = layout.row(align=True)
        # Keep the original add-on's prominent, double-height primary actions.
        row.scale_y = 2.0
        create = row.row(align=True)
        create.enabled = settings.allow_multiple or not frames
        create.operator('node.exr_multipass', text='Create', icon='ADD')
        refresh = row.row(align=True)
        refresh.enabled = bool(frames)
        refresh.operator('node.exr_multipass_refresh', text='Refresh', icon='FILE_REFRESH')
        if frames:
            layout.operator('node.exr_multipass_arrange', text='Arrange Nodes', icon='NODETREE')


class NODE_PT_exr_multipass_passes(bpy.types.Panel):
    bl_label = 'Render Passes'
    bl_idname = 'NODE_PT_exr_multipass_passes'
    bl_parent_id = 'NODE_PT_exr_multipass'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'EXR Multipass'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text=context.view_layer.name, icon='RENDERLAYERS')
        controls = render_pass_controls(context)
        if not controls:
            layout.label(text='Available in Cycles and Eevee', icon='INFO')
            return
        group = None
        for title, owner, prop, label in controls:
            if title != group:
                box = layout.box()
                box.label(text=title)
                column = box.column(align=True)
                group = title
            target = context.view_layer if owner == 'layer' else getattr(context.view_layer, owner)
            row = column.row(align=True)
            row.enabled = pass_control_enabled(context, prop) and not target.is_property_readonly(prop)
            toggle = row.operator('node.exr_multipass_toggle_pass', text=label,
                                  icon='CHECKBOX_HLT' if getattr(target, prop) else 'CHECKBOX_DEHLT',
                                  emboss=False)
            toggle.owner, toggle.prop = owner, prop
        if context.scene.render.use_motion_blur:
            layout.label(text='Vector unavailable with Motion Blur', icon='INFO')


class NODE_PT_exr_multipass_paths(bpy.types.Panel):
    bl_label = 'Output Paths'
    bl_idname = 'NODE_PT_exr_multipass_paths'
    bl_parent_id = 'NODE_PT_exr_multipass'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'EXR Multipass'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.label(text="Folder for new setups", icon='FILE_FOLDER')
        layout.prop(context.scene.exr_multipass_settings, 'directory', text='')
        tree = get_compositor_tree(context.scene, create=False)
        frames = layer_frames(tree, context.scene, context.view_layer.name)
        for index, frame in enumerate(frames, 1):
            _, output = setup_nodes(tree, frame)
            box = layout.box()
            heading = box.row(align=True)
            heading.template_node_socket(color=(*frame.color, 1.0))
            heading.label(text=f"Setup {index}")
            if bpy.app.version >= (5, 0, 0):
                box.prop(output, 'directory', text='Folder')
                box.prop(output, 'file_name', text='File')
            else:
                box.prop(output, 'base_path', text='Path')


