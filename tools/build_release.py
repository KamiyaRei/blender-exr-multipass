"""Build the installable ZIP using only Python's standard library."""
import argparse
import ast
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def version():
    tree = ast.parse((ROOT / 'exrMultipass/__init__.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'bl_info' for t in node.targets):
            return '.'.join(map(str, ast.literal_eval(node.value)['version']))
    raise ValueError('bl_info version not found')

def build(output):
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'EXR_Multipass_v{version()}.zip'
    files = [(p, 'exrMultipass/' + p.name) for p in sorted((ROOT / 'exrMultipass').glob('*.py'))]
    files.append((ROOT / 'LICENSE', 'exrMultipass/LICENSE'))
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
        for path, name in files:
            if path.suffix == '.py':
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zipped.writestr(info, path.read_text(encoding='utf-8').encode('utf-8'))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    return archive

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--version', action='store_true')
    args = parser.parse_args()
    print(version() if args.version else build(args.output))
