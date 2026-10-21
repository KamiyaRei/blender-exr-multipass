# Development and releases

## Structure
- `exrMultipass/__init__.py`: version, settings and registration.
- `core.py`: nodes, EXR slots, pass mapping and compatibility helpers.
- `operators.py`: undoable user actions.
- `panels.py`: sidebar UI.
- `tests/`: developer checks, excluded from the add-on ZIP.
- `tools/build_release.py`: standard-library-only package builder.

## Local checks
Use a disposable Blender profile: set `BLENDER_USER_RESOURCES` to an empty test directory.
Set `EXR_TEST_OUTPUT` to a test output directory. Tests reset factory scenes and write test files.

```sh
python tools/build_release.py
blender --background --factory-startup --python-exit-code 1 --python tests/regression.py
blender --background --factory-startup --python-exit-code 1 --python tests/pass_controls.py
blender --background --factory-startup --python-exit-code 1 --python tests/installation.py
```

Use a separate empty profile for the installation test. It exercises the built ZIP,
including reinstalling over an enabled package. It does not install into your normal profile
when `BLENDER_USER_RESOURCES` is set correctly.

Tests cover node creation, pass removal, AOV name collisions, layer renaming,
manual links, rollback, unique file output, save/reload, engine-specific pass
controls and package installation. Visual UI and external compositor checks remain manual.

## Release
1. Update `bl_info['version']` in `exrMultipass/__init__.py` (the single version source).
2. Update CHANGELOG, README's download filename and `docs/releases/vX.Y.Z.md`.
3. Run tests and inspect the built ZIP. Never rename the `exrMultipass` package.
4. Push to main. CI tests both supported Blender API generations.
5. To publish, use Actions > Test and release > Run workflow > publish, or include
   `[release]` in the main-branch commit message. Publication only runs after both test jobs pass.

The release job creates the version tag at the tested commit and uploads the ZIP and
SHA-256 checksum. Existing release tags are not overwritten by ordinary publication. An explicitly
authorized technical rebuild uses `[release] [rebuild]` and replaces the current
version assets and tag only after tests pass. Pull requests only run tests.
Bumping a version is intentional; ordinary commits do not publish releases.
