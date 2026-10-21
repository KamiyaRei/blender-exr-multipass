"""Node management, pass mapping and Blender version compatibility."""
import bpy
import colorsys
import json
import os
import re
import uuid

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

TAG = "exr_multipass_id"
ROLE = "exr_multipass_role"
MAPPING = "exr_multipass_passes"


def get_compositor_tree(scene, create=True):
    if bpy.app.version >= (5, 0, 0):
        tree = scene.compositing_node_group
        if tree is None and create:
            tree = bpy.data.node_groups.new("Compositor", "CompositorNodeTree")
            scene.compositing_node_group = tree
        return tree
    if create:
        scene.use_nodes = True
    return scene.node_tree


def setup_nodes(tree, frame):
    children = [n for n in tree.nodes if n.parent == frame and n.get(TAG) == frame.get(TAG)]
    sources = [n for n in children if n.get(ROLE) == 'source' and n.type == 'R_LAYERS']
    outputs = [n for n in children if n.get(ROLE) == 'output' and n.type == 'OUTPUT_FILE']
    if len(sources) != 1 or len(outputs) != 1:
        raise ValueError("Setup has missing or duplicated nodes; repair it before refreshing")
    return sources[0], outputs[0]


def managed_frames(tree):
    return [n for n in tree.nodes if n.type == 'FRAME' and n.get(TAG)] if tree else []


def layer_frames(tree, scene, layer_name):
    result = []
    for frame in managed_frames(tree):
        try:
            source, _ = setup_nodes(tree, frame)
        except ValueError:
            continue
        if (source.scene is None or source.scene == scene) and source.layer == layer_name:
            result.append(frame)
    return sorted(result, key=lambda n: n.get("exr_multipass_order", 0))


def safe_name(value):
    return re.sub(r'[^A-Za-z0-9_-]+', '_', value).strip('_')[:40] or 'layer'


def configure_path(scene, layer_name, output, setup_id):
    directory = scene.exr_multipass_settings.directory or "//renders/"
    stem = f"{safe_name(scene.name)}_{safe_name(layer_name)}_{setup_id[:12]}_####"
    if bpy.app.version >= (5, 0, 0):
        output.directory = directory
        output.file_name = stem
    else:
        output.base_path = os.path.join(directory, stem)


def pass_plan(source):
    # Allocate built-in names first so AOVs can never replace beauty or utility passes.
    scene = source.scene
    layer = scene.view_layers.get(source.layer) if scene else None
    aov_names = {a.name for a in layer.aovs} if layer else set()
    sockets = [s for s in source.outputs if s.enabled]
    builtins = [s for s in sockets if s.name not in aov_names]
    aovs = [s for s in sockets if s.name in aov_names]
    used = set()
    result = []
    for socket in builtins + aovs:
        base = 'aov_' + socket.name if socket.name in aov_names else PASS_MAP.get(socket.name, socket.name)
        # EXR names are bounded by Blender; leave room for a disambiguating suffix.
        base = base[:48]
        name = base
        index = 2
        while name in used:
            name = f"{base}_{index}"
            index += 1
        used.add(name)
        result.append((socket, name))
    return result


def remove_input(output, index):
    if bpy.app.version >= (5, 0, 0):
        output.file_output_items.remove(output.file_output_items[index])
    else:
        output.layer_slots.remove(output.inputs[index])


def new_input(output, source, name):
    if bpy.app.version >= (5, 0, 0):
        socket_type = 'FLOAT' if source.type == 'VALUE' else source.type
        if socket_type not in {'FLOAT', 'INT', 'BOOLEAN', 'VECTOR', 'RGBA'}:
            socket_type = 'RGBA'
        item = output.file_output_items.new(socket_type, name)
        return output.inputs.get(item.name)
    return output.layer_slots.new(name)


def sync_and_link(tree, src, dst):
    if dst.format.file_format != 'OPEN_EXR_MULTILAYER':
        raise ValueError("File Output must use OpenEXR Multilayer")
    plan = pass_plan(src)
    desired = {name for _, name in plan}
    managed = set(json.loads(dst.get(MAPPING, '[]')))
    # Validate the entire plan before touching existing slots or connections.
    for _, name in plan:
        if dst.inputs.get(name) is not None and name not in managed:
            raise ValueError(f"Unmanaged output '{name}' conflicts with a render pass")
    added = removed = preserved = 0
    # Never delete user-created slots. Only retire slots previously managed by us.
    for index in range(len(dst.inputs) - 1, -1, -1):
        socket = dst.inputs[index]
        if socket.name in managed - desired:
            remove_input(dst, index)
            removed += 1
    tracked = set()
    for source, name in plan:
        target = dst.inputs.get(name)
        if target is None:
            target = new_input(dst, source, name)
            added += 1
        tracked.add(target.name)
        if target.is_linked:
            if all(link.from_node == src for link in target.links):
                if target.links[0].from_socket != source:
                    tree.links.new(source, target)
            else:
                preserved += 1
            # Existing processing chains and manual links belong to the user.
        else:
            tree.links.new(source, target)
    dst[MAPPING] = json.dumps(sorted(tracked))
    return added, removed, preserved


def arrange_frames(tree, frames):
    # Use measured bounds where available and a conservative fallback in background mode.
    y = 0
    for frame in frames:
        children = [n for n in tree.nodes if n.parent == frame]
        tops, bottoms = [], []
        for node in children:
            sockets = max(sum(s.enabled and not s.hide for s in node.inputs),
                          sum(s.enabled and not s.hide for s in node.outputs))
            estimate = 320 + sockets * 26
            height = max(node.dimensions.y, estimate) if not node.hide else max(node.dimensions.y, 40)
            tops.append(node.location.y)
            bottoms.append(node.location.y - height)
        height = max(tops, default=0) - min(bottoms, default=-200)
        frame.location.y = y
        y -= height + 100


def create_exr_multipass(context):
    scene, layer = context.scene, context.view_layer
    tree = get_compositor_tree(scene)
    before = set(tree.nodes)
    try:
        existing = managed_frames(tree)
        siblings = layer_frames(tree, scene, layer.name)
        order = max((f.get('exr_multipass_order', 0) for f in existing), default=0) + 1
        setup_id = uuid.uuid4().hex
        frame = tree.nodes.new('NodeFrame')
        frame[TAG], frame[ROLE] = setup_id, 'frame'
        frame['exr_multipass_order'] = order
        frame.label = layer.name
        frame.use_custom_color = True
        column = siblings[0].get('exr_multipass_column', 0) if siblings else max((f.get('exr_multipass_column', -1) for f in existing), default=-1) + 1
        frame['exr_multipass_column'] = column
        rgb = tuple(int(COLOR_PALETTE[column % len(COLOR_PALETTE)][i:i+2], 16) / 255 for i in (0, 2, 4))
        h, s, v = colorsys.rgb_to_hsv(*rgb)
        frame.color = colorsys.hsv_to_rgb(h, s, max(0.15, v - 0.1 * (len(siblings) % 6)))
        frame.location = (column * 900, 0)
        source = tree.nodes.new('CompositorNodeRLayers')
        source.scene, source.layer = scene, layer.name
        source.label = f"Render Layers [{layer.name}]"
        source.parent = frame
        source.location = (0, 0)
        output = tree.nodes.new('CompositorNodeOutputFile')
        output.label = f"Output [{layer.name}]"
        output.parent = frame
        output.location = (450, 0)
        for node, role in ((source, 'source'), (output, 'output')):
            node[TAG], node[ROLE] = setup_id, role
        output.format.file_format = 'OPEN_EXR_MULTILAYER'
        output.format.color_depth = '16'
        output.format.exr_codec = 'ZIP'
        if bpy.app.version >= (5, 0, 0):
            output.file_output_items.clear()
        else:
            output.layer_slots.clear()
        configure_path(scene, layer.name, output, setup_id)
        sync_and_link(tree, source, output)
        # Position only the new frame; creation never rearranges existing work.
        if siblings:
            last = siblings[-1]
            children = [n for n in tree.nodes if n.parent == last]
            lowest = min((n.location.y - max(n.dimensions.y, 320 + 26 * max(len(n.inputs), len(n.outputs))) for n in children), default=-400)
            frame.location.y = last.location.y + lowest - 100
        return frame
    except Exception:
        for node in list(tree.nodes):
            if node not in before:
                tree.nodes.remove(node)
        raise


def render_pass_controls(context):
    """Mirror supported engine settings; read live values, never cache layer state."""
    engine = context.scene.render.engine
    cycles = engine == 'CYCLES'
    eevee = engine in {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}
    if not (cycles or eevee):
        return []
    entries = []

    def add(group, owner, prop, label):
        target = context.view_layer if owner == 'layer' else getattr(context.view_layer, owner, None)
        if target is not None and hasattr(target, prop):
            entries.append((group, owner, prop, label))

    for prop, label in [('z', 'Z / Depth'), ('mist', 'Mist'), ('normal', 'Normal'),
                        ('position', 'Position'), ('vector', 'Vector')]:
        add('Data', 'layer', 'use_pass_' + prop, label)
    if cycles:
        for prop, label in [('uv', 'UV'), ('object_index', 'Object Index'), ('material_index', 'Material Index')]:
            add('Data', 'layer', 'use_pass_' + prop, label)
        add('Data', 'cycles', 'denoising_store_passes', 'Denoising Data')
    for kind, label in [('diffuse', 'Diffuse'), ('glossy', 'Glossy / Specular')]:
        for part in (['direct', 'indirect', 'color'] if cycles else ['direct', 'color']):
            add(label, 'layer', f'use_pass_{kind}_{part}', 'Light' if eevee and part == 'direct' else part.title())
    if cycles:
        for part in ['direct', 'indirect', 'color']:
            add('Transmission', 'layer', 'use_pass_transmission_' + part, part.title())
    for part in (['direct', 'indirect'] if cycles else ['direct']):
        add('Volume', 'cycles' if cycles else 'eevee', 'use_pass_volume_' + part,
            part.title() if cycles else 'Light')
    for prop, label in [('emit', 'Emission'), ('environment', 'Environment'), ('ambient_occlusion', 'Ambient Occlusion')]:
        add('Other', 'layer', 'use_pass_' + prop, label)
    if cycles:
        add('Other', 'cycles', 'use_pass_shadow_catcher', 'Shadow Catcher')
    else:
        add('Other', 'layer', 'use_pass_shadow', 'Shadow')
        add('Other', 'eevee', 'use_pass_transparent', 'Transparent')
    for part in ['object', 'material', 'asset']:
        add('Cryptomatte', 'layer', 'use_pass_cryptomatte_' + part, part.title())
    return entries


def pass_control_enabled(context, prop):
    return prop != 'use_pass_vector' or not context.scene.render.use_motion_blur


