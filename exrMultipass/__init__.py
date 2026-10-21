bl_info = {
    'name': 'EXR_multipass',
    'author': 'Rei',
    'version': (1, 7, 1),
    'blender': (4, 0, 0),
    'category': 'Compositing',
    'location': 'Compositing Tab > Sidebar > EXR_multipass',
    'description': 'Safe EXR multipass setups and pass synchronization.',
}

import bpy
from .operators import (NODE_OT_exr_multipass, NODE_OT_exr_multipass_refresh, NODE_OT_exr_multipass_arrange, NODE_OT_exr_multipass_toggle_pass)
from .panels import (NODE_PT_exr_multipass_panel, NODE_PT_exr_multipass_passes, NODE_PT_exr_multipass_paths)

class EXR_Settings_Group(bpy.types.PropertyGroup):
    allow_multiple: bpy.props.BoolProperty(name="Allow Multiple Copies", default=False)
    directory: bpy.props.StringProperty(name="Output Directory", subtype='DIR_PATH', default="//renders/")


classes = (EXR_Settings_Group, NODE_OT_exr_multipass, NODE_OT_exr_multipass_refresh,
           NODE_OT_exr_multipass_arrange, NODE_OT_exr_multipass_toggle_pass, NODE_PT_exr_multipass_panel,
           NODE_PT_exr_multipass_passes,
           NODE_PT_exr_multipass_paths)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.exr_multipass_settings = bpy.props.PointerProperty(type=EXR_Settings_Group)


def unregister():
    del bpy.types.Scene.exr_multipass_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
