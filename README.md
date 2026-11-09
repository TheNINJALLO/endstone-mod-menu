<!-- endstone-professional-header:start -->
<p align="center">
  <img src="docs/assets/banner.svg" width="100%" alt="Endstone Mod Menu &mdash; Mod menu plugin for Endstone with teleportation, fill commands, and gamemode switching">
</p>

<p align="center">
  <a href="https://github.com/TheNINJALLO/endstone-mod-menu/actions/workflows/wheel-release.yml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/TheNINJALLO/endstone-mod-menu/wheel-release.yml?branch=main&amp;style=for-the-badge&amp;logo=githubactions&amp;logoColor=white&amp;label=Build"></a>
  <a href="https://github.com/TheNINJALLO/endstone-mod-menu/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/TheNINJALLO/endstone-mod-menu?display_name=tag&amp;style=for-the-badge&amp;label=Release"></a>
</p>

<p align="center">
  <img alt="Endstone 0.11.15" src="https://img.shields.io/badge/Endstone-0.11.15-52b7a8?style=flat-square">
  <img alt="API 0.11" src="https://img.shields.io/badge/API-0.11-63b8ff?style=flat-square">
  <img alt="BDS 1.26.60.6" src="https://img.shields.io/badge/BDS-1.26.60.6-8b7dff?style=flat-square">
  <img alt="Python >=3.10" src="https://img.shields.io/badge/Python-%3E=3.10-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white">
</p>

<p align="center">
  <strong>Mod menu plugin for Endstone with teleportation, fill commands, and gamemode switching.</strong>
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> &bull;
  <a href="#how-to-use">How to use</a> &bull;
  <a href="#commands-and-permissions">Commands</a> &bull;
  <a href="#install">Install</a> &bull;
  <a href="https://github.com/TheNINJALLO/endstone-mod-menu/releases">Releases</a>
</p>

## Overview

Mod menu plugin for Endstone with teleportation, fill commands, and gamemode switching. This release is aligned with Endstone 0.11.15 and Minecraft Bedrock Dedicated Server 1.26.60.6, and is distributed as a Python wheel for direct installation in an Endstone server.

## What it does

- Provides form-based moderator and administrator menus for teleportation, fills, gamemode changes, and common staff actions.
- Separates access through the `Mod` and `Admin` scoreboard tags.
- Records administrative actions and exposes a browsable operator log.

## How to use

1. Grant menu access with `/tag <player> add Mod` or `/tag <player> add Admin`.
2. The player runs `/mod` or `/admin` and chooses an action from the form.
3. Operators can review recent actions with `/adminlog` and its optional count or administrator filter.
4. Remove the corresponding scoreboard tag immediately when staff access is revoked.

## Commands and permissions

| Command / usage | What it does | Access |
|---|---|---|
| `/mod` | Open the mod menu | Scoreboard tag `Mod` |
| `/admin` | Open the admin menu | Scoreboard tag `Admin` |
| `/adminlog`<br>`/adminlog <count>`<br>`/adminlog <admin_name>` | View admin action logs (operators only) | Operator |

## Compatibility

| Component | Supported version |
|---|---|
| Endstone | `0.11.15` |
| Endstone API | `0.11` |
| Bedrock Dedicated Server | `1.26.60.6` |
| Python package minimum | `>=3.10` (CI uses `3.11`) |
| Plugin release | `v1.5.6` |

## Install

Download the wheel from the matching GitHub release:

```bash
gh release download v1.5.6 --repo TheNINJALLO/endstone-mod-menu --pattern "*.whl"
```

Copy the downloaded wheel into the server's `plugins/` directory, remove any older wheel for the same plugin, and restart Endstone.

> [!IMPORTANT]
> Use Endstone `0.11.15` with BDS `1.26.60.6`. Back up worlds and plugin data before upgrading a production server.

## Configuration and secrets

Runtime databases, logs, local `.env` files, server directories, and root `config.toml` files are excluded from source releases. When an example configuration is provided, copy it locally and keep live tokens, passwords, webhook URLs, and server identifiers out of Git.

## Release automation

A new package version on `main`, or a matching `v*` tag, runs [the release workflow](.github/workflows/wheel-release.yml). It checks the mode/effect/diagnostic regressions on Linux before building and publishing the wheel. Branch builds leave existing releases unchanged.
<!-- endstone-professional-header:end -->

---

## Project guide

### Version 1.5.6: enchanted gear and spectator switching

Night-vision cleanup now uses `effect <player> clear night_vision`, preserving other active potion effects when returning to survival or creative. The previous cleanup cleared every effect, including buffs supplied by enchanted armor or another plugin. See [the Bedrock effect command reference](https://learn.microsoft.com/en-us/minecraft/creator/commands/commands/effect?view=minecraft-bedrock-stable).

Menu game-mode changes skip an already-selected mode and verify that a switch succeeded before applying its effects, logging success or continuing a spectator-dependent teleport.

Read-only diagnostics record equipped armor and held/offhand items before and after a menu mode change: vanilla enchant names/raw IDs and levels, `endstone_custom_enchants` IDs/levels/revision, bounded lore and NBT key names. They observe nearby lead spawns during the setter and briefly afterwards, with follow-up samples at 5, 10 and 20 ticks. Post-switch observation stops after two seconds of wall-clock time or completion. All item drops and enchantments are preserved; proximity and ownership are diagnostic observations, not proof of the cause.

Install the release wheel `endstone_mod_menu-1.5.6-py3-none-any.whl`, remove the older Mod Menu wheel and restart. Preserve the plugin data folder. The reported live lead-drop cause remains unconfirmed; this release fixes the effect-clearing conflict and supplies diagnostics for further investigation.

If a lead still drops:

1. Stand still and switch to spectator and back with enchanted armor removed and an empty hand/offhand. Keep the gear intact in inventory rather than stripping enchantments.
2. Repeat with one enchanted piece equipped at a time, then the full set. Note which piece/set makes the drop appear.
3. Compare with the ordinary `/gamemode` command; these diagnostics watch menu-triggered changes only.
4. Inspect the server log for `[ModeSwitchDiagnostics]`. Preserve the relevant JSON entry and Endstone/BDS versions. It contains before/after equipment and nearby lead timing/ownership observations.

The 37 automated regressions use the native Endstone 0.11.15 SDK with simulated server/player callbacks. They cover selective night-vision cleanup, item/tag inspection, item preservation, menus, delayed drops, shutdown and reconnects. They do not replace live server/client reproduction. After installing the package and Endstone, run `python -m unittest discover -s tests -v` from the source checkout. See [CHANGELOG.md](CHANGELOG.md) and [release notes](.github/release-notes/v1.5.6.md).

A comprehensive moderator menu plugin for Endstone (Minecraft Bedrock Dedicated Server) that provides essential moderation tools through an intuitive UI.

## Features

### Main Menu
- **Commands Submenu** - Access to advanced commands
- **Spectator Mode** - Quick switch to spectator with night vision
- **Survival Mode** - Return to survival and clear night vision

### Commands Menu
- **Teleport To** - Teleport to any online player
- **Teleport From** - Bring any player to your location
- **Fill Area** - Fill regions with deepslate blocks
- **Load Structure** - Load saved structures in front of you

### Special Features
- Automatic night vision when entering spectator mode
- Night vision cleared when returning to survival
- Volume limits on fill commands for safety (32,768 blocks)
- Support for relative coordinates (~, ~5, etc.)
- Permission-based access control

## Installation

1. Ensure you have Endstone 0.11.9+ installed
2. Clone or download this plugin
3. Install using pip:
   ```bash
   pip install .
   ```
4. Restart your Endstone server

## Usage

### Trigger the Menu
Simply type `/mod` command to open the mod menu (requires permission).

### Permissions
- Players with the `Mod` scoreboard tag can access the mod menu
- Players with the `Owner` scoreboard tag are protected from being teleported

Add tags using:
```
/tag <player> add Mod
/tag <player> add Owner
```

## Project Structure

```
endstone-mod-menu/
├── src/
│   └── endstone_mod_menu/
│       ├── __init__.py
│       ├── gamemode_guard.py
│       └── mod_menu.py
├── pyproject.toml
└── README.md
```

## Configuration

Edit the constants in `mod_menu.py`:
- `FILL_VOLUME_LIMIT` - Maximum blocks for fill command (default: 32768)
- `NV_DURATION_TICKS` - Night vision command duration in seconds (legacy constant name; default: 999999)
- `NV_SHOW_PARTICLES` - Show particles for night vision effect (default: False)

## API Version
This plugin targets Endstone API version 0.11.

## Commands

The plugin provides the `/mod` command to access the menu.

## Forms

The plugin uses Endstone's native form system:
- **ActionForm** - Main menu and commands menu
- **ModalForm** - Fill area and teleport player selection

## Events

Handles commands through the standard Endstone command system.

## Requirements

- Python 3.10+
- Endstone 0.11.9+
- Minecraft Bedrock Dedicated Server

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please open an issue on the project repository.

## Credits

Ported from Minecraft Bedrock Script API to Endstone by following the official Endstone documentation and API references.
