<p align="center">
  <img src="assets/logo.png" alt="EXR_multipass logo" width="200"/>
</p>

<h1 align="center">EXR Multipass</h1>

A simple Blender add-on to easily create and manage EXR multipass outputs for compositing.


**Download last release:**

[![Download](https://img.shields.io/badge/Download-EXR_multipass-f474a7?style=for-the-badge)](https://github.com/KoyomiRei/EXR_multipass/releases/latest)




## Features

- **Blender 4.x & 5.0+ Compatibility:** Automatically handles API changes between versions for File Output slots and items.
- **Grid Organization:** Arranges nodes into columns by View Layer and vertical stacks for duplicates.
- **Color Coding:** Assigns unique colors to layers and applies 10% brightness stepping for copies.
- **Pass Synchronization:** The "Refresh" button adds new passes and removes disabled ones from the File Output node.
- **Strict Layout Logic:** Calculates frame height mathematically to maintain a fixed gap and prevent overlapping.
- **Duplicate Control:** Toggle "Allow Multiple Copies" to manage whether the same layer can have several setups.

## Installation

1. Download the latest release (.zip).
2. In Blender, go to `Edit` → `Preferences` → `Add-ons` → `Install`.
3. Select the downloaded `.zip` file.
4. Enable the add-on in the list.

## Usage

- Open Blender and go to the **Compositing** tab.
- In the sidebar ("N" key), find the "EXR Multipass" panel.
- Click "Create" to generate the Render Layers and File Output node setup.
- Use the "Refresh" button if you add or change render passes.

## License

This project is licensed under the [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.en.html).
