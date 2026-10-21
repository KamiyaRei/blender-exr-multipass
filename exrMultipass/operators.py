"""Undoable user actions."""
import bpy
from .core import (get_compositor_tree, setup_nodes, layer_frames, create_exr_multipass,
                   sync_and_link, arrange_frames, render_pass_controls, pass_control_enabled)

class EXR_Operator:
    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.view_layer is not None


class NODE_OT_exr_multipass(EXR_Operator, bpy.types.Operator):
    bl_idname = 'node.exr_multipass'
    bl_label = 'Create Setup'
    bl_description = 'Create a multipass EXR output for the active View Layer'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tree = get_compositor_tree(context.scene, create=False)
        if not context.scene.exr_multipass_settings.allow_multiple and layer_frames(tree, context.scene, context.view_layer.name):
            self.report({'WARNING'}, 'Setup already exists for this View Layer')
            return {'CANCELLED'}
        try:
            create_exr_multipass(context)
        except Exception as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class NODE_OT_exr_multipass_refresh(EXR_Operator, bpy.types.Operator):
    bl_idname = 'node.exr_multipass_refresh'
    bl_label = 'Refresh Setup'
    bl_description = 'Update enabled passes while keeping manual links, output paths and node positions'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tree = get_compositor_tree(context.scene, create=False)
        frames = layer_frames(tree, context.scene, context.view_layer.name)
        if not frames:
            self.report({'WARNING'}, 'No valid setups found; create a setup or repair missing nodes')
            return {'CANCELLED'}
        totals = [0, 0, 0]
        done = 0
        for frame in frames:
            try:
                source, output = setup_nodes(tree, frame)
                stats = sync_and_link(tree, source, output)
                totals = [a + b for a, b in zip(totals, stats)]
                frame.label = source.layer
                source.label = f"Render Layers [{source.layer}]"
                output.label = f"Output [{source.layer}]"
                done += 1
            except (ValueError, RuntimeError, TypeError) as error:
                self.report({'WARNING'}, f"{frame.name}: {error}")
        self.report({'INFO'}, f"Updated {done}/{len(frames)}: added {totals[0]}, removed {totals[1]}, manual links kept {totals[2]}")
        return {'FINISHED'} if done else {'CANCELLED'}


class NODE_OT_exr_multipass_arrange(EXR_Operator, bpy.types.Operator):
    bl_idname = 'node.exr_multipass_arrange'
    bl_label = 'Arrange Current Layer'
    bl_description = 'Arrange managed frames for the active View Layer in creation order'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tree = get_compositor_tree(context.scene, create=False)
        frames = layer_frames(tree, context.scene, context.view_layer.name)
        if not frames:
            return {'CANCELLED'}
        arrange_frames(tree, frames)
        return {'FINISHED'}


class NODE_OT_exr_multipass_toggle_pass(EXR_Operator, bpy.types.Operator):
    bl_idname = 'node.exr_multipass_toggle_pass'
    bl_label = 'Toggle Render Pass'
    bl_description = 'Toggle this pass for the active View Layer and update its EXR setups'
    bl_options = {'UNDO'}

    owner: bpy.props.StringProperty(options={'HIDDEN'})
    prop: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        allowed = {(owner, prop) for _, owner, prop, _ in render_pass_controls(context)}
        if (self.owner, self.prop) not in allowed or not pass_control_enabled(context, self.prop):
            self.report({'WARNING'}, 'This pass is unavailable with the current render settings')
            return {'CANCELLED'}
        target = context.view_layer if self.owner == 'layer' else getattr(context.view_layer, self.owner)
        if target.is_property_readonly(self.prop):
            self.report({'WARNING'}, 'This View Layer is read-only')
            return {'CANCELLED'}
        setattr(target, self.prop, not getattr(target, self.prop))
        context.view_layer.update_render_passes()
        tree = get_compositor_tree(context.scene, create=False)
        for frame in layer_frames(tree, context.scene, context.view_layer.name):
            try:
                source, output = setup_nodes(tree, frame)
                sync_and_link(tree, source, output)
            except (ValueError, RuntimeError, TypeError) as error:
                # The layer change remains undoable even if a manually edited setup fails.
                self.report({'WARNING'}, f'Pass changed, but {frame.name} was not updated: {error}')
        return {'FINISHED'}


