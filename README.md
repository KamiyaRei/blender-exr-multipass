<p align="center"><img src="assets/logo.png" alt="EXR Multipass" width="160"/></p>

# EXR Multipass

Set up multilayer EXR outputs and manage render passes directly from Blender's Compositor sidebar.

**[Download the latest release](https://github.com/KamiyaRei/blender-exr-multipass/releases/latest)** · [Changelog](CHANGELOG.md)

## What it does

- Creates a Render Layers / File Output setup for the active View Layer.
- Lets you toggle Cycles and Eevee passes directly in the panel and updates its EXR outputs immediately.
- Preserves manual processing connections when refreshing passes.
- Assigns distinct output filenames to newly created setups.
- Keeps the large Create / Refresh buttons, with collapsible Render Passes and Output Paths sections.

## Installation

1. Download **EXR_Multipass_v1.7.1.zip** from Releases. The GitHub **Source code** archives are for development, not installation.
2. In Blender, open **Edit → Preferences → Add-ons → Install from Disk** (Install in older versions).
3. Select the ZIP and enable **EXR_multipass**.
4. Open **Compositing → sidebar (N) → EXR Multipass**.

When upgrading from a single-file installation or recovering from a failed update, remove the old add-on, restart Blender, then install this ZIP. This does not delete nodes in saved blend files.

## Quick start

1. Save your blend file, or choose an absolute output folder in **Output Paths**.
2. Choose the active View Layer and click **Create**.
3. Expand **Render Passes** and enable the passes you need.
4. Render. New setups write 16-bit, ZIP-compressed multilayer EXR to `//renders/` by default.

`//` means relative to the blend file. New filenames include scene, layer, a unique setup suffix and frame number. You can edit the destination of each setup under Output Paths.

| Control | Behavior |
| --- | --- |
| Create | Adds a setup for the active layer. Enable Allow Multiple Copies for additional setups. |
| Refresh | Adds enabled passes and removes disabled managed slots; retains paths, positions and existing processing links. |
| Render Passes | Changes the actual layer settings and synchronizes all its valid setups. Available controls depend on the engine. |
| Arrange Nodes | Explicitly arranges current-layer frames in creation order. |
| Output Paths | Sets the default folder for new setups and edits existing destinations. |

Changes made in Blender's own View Layer properties require **Refresh**. Disabling a pass removes its managed output slot and that slot's connection. No setup is created merely by toggling a pass.

## Compatibility and important details

- Locally tested on Windows with Blender **4.5.11 LTS, 5.1.2 and 5.2.2 LTS** for this release. Automated tests target 4.5.11 and 5.2.2 on Linux.
- Pass controls support **Cycles and Eevee**. Vector is unavailable while Motion Blur is enabled. AOV editing and Cryptomatte depth remain in Blender's View Layer properties.
- Built-in Image exports as `beauty`; custom AOVs use an `aov_` prefix to prevent collisions. Long names are shortened and disambiguated.
- This release manages setups created by the 1.6+ code. Recreate setups from 1.5.5 or earlier; automatic legacy adoption is intentionally absent.
- Unique filenames are assigned by Create. Manually duplicating nodes or assigning the same path can still cause collisions.
- The add-on does not denoise or perform color grading. It exports connected data. Verify precision and channel naming for your downstream workflow.
- Background tests cover node operations and EXR headers, not every pass, visual layout, or external compositor interoperability.

## Development

The installable package is `exrMultipass/`: `core.py` handles nodes and passes, `operators.py` contains actions, and `panels.py` contains the interface. `__init__.py` holds the version and registration.

**Users do not need to build anything.** Developers can create the same installation ZIP with Python 3.10+ and no third-party dependencies:

```sh
python tools/build_release.py
```

The ZIP and SHA-256 checksum appear in `dist/`. Tests, documentation and repository files are excluded from the installation package.

See [development and release instructions](docs/DEVELOPMENT.md). The `tests/` folder protects pass synchronization, file output and installation against regressions; it is not shipped to users.

## Reporting problems

[Open an issue](https://github.com/KamiyaRei/blender-exr-multipass/issues) with the Blender and add-on versions, render engine, steps to reproduce, and full error text. Include a minimal blend file only if it contains no private assets.

Created by [KamiyaRei](https://github.com/KamiyaRei).

## License

[GPL-3.0](LICENSE).
