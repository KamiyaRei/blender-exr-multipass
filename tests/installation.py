"""Install the built ZIP, enable it, then reinstall over the enabled package."""
from pathlib import Path
import sys
import bpy
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools'))
from build_release import version
archive = root / 'dist' / f'EXR_Multipass_v{version()}.zip'
for attempt in range(2):
    assert bpy.ops.preferences.addon_install(filepath=str(archive)) == {'FINISHED'}
    assert bpy.ops.preferences.addon_enable(module='exrMultipass') == {'FINISHED'}
    import exrMultipass
    assert '.'.join(map(str, exrMultipass.bl_info['version'])) == version()
    assert Path(exrMultipass.__file__).name == '__init__.py'
    assert str(Path(exrMultipass.__file__).resolve()).startswith(str(Path(bpy.utils.user_resource('SCRIPTS')).resolve()))
    if attempt == 0:
        assert bpy.ops.node.exr_multipass() == {'FINISHED'}
assert bpy.ops.preferences.addon_disable(module='exrMultipass') == {'FINISHED'}
print('INSTALL AND REINSTALL PASSED', bpy.app.version_string)
