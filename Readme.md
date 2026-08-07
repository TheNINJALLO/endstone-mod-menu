# Endstone Mod Menu Plugin

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

1. Ensure you have Endstone 0.10.6+ installed
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
│       └── mod_menu.py
├── pyproject.toml
└── README.md
```

## Configuration

Edit the constants in `mod_menu.py`:
- `FILL_VOLUME_LIMIT` - Maximum blocks for fill command (default: 32768)
- `NV_DURATION_TICKS` - Night vision duration in ticks (default: 999999)
- `NV_SHOW_PARTICLES` - Show particles for night vision effect (default: False)

## API Version
This plugin targets Endstone API version 0.10

## Commands

The plugin provides the `/mod` command to access the menu.

## Forms

The plugin uses Endstone's native form system:
- **ActionForm** - Main menu and commands menu
- **ModalForm** - Fill area and teleport player selection

## Events

Handles commands through the standard Endstone command system.

## Requirements

- Python 3.9+
- Endstone 0.10.6+
- Minecraft Bedrock Dedicated Server

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please open an issue on the project repository.

## Credits

Ported from Minecraft Bedrock Script API to Endstone by following the official Endstone documentation and API references.