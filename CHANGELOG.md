# 1.5.6

- Fix night-vision cleanup to remove only night vision when returning to survival or creative; preserve other active potion effects from enchanted gear and plugins.
- Route menu game-mode changes through a shared path, skip redundant/re-entrant writes, and verify success before applying dependent effects, teleports or success logs.
- Add read-only mode-switch diagnostics for armor/held enchantment IDs and levels, equipment changes, nearby lead timing and reported ownership. Preserve all items and enchantments.
- Sample after 5, 10 and 20 ticks, stop post-switch observation after two seconds or completion, and invalidate callbacks on shutdown, superseding switches and different login sessions.
- Run 37 regression tests against the Endstone 0.11.15 SDK before release packaging. Refresh installation and diagnostic instructions.

The reported live lead-drop cause has not been confirmed. Automated checks cover the effect-clearing fix and diagnostic behavior; nearby spawns do not prove an enchantment created the item. Live server/client verification remains required.

Target: Endstone 0.11.15 / API 0.11 / BDS 1.26.60.6. Package minimum: Python 3.10; release checks use Python 3.11. Existing plugin data is retained when upgrading from 1.5.3.
