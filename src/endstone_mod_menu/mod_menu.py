"""
Mod Menu Plugin for Endstone
Port of Minecraft Bedrock Script API mod menu to Endstone
"""
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.form import ActionForm, ModalForm, TextInput, Dropdown
from endstone import Player, GameMode
from endstone.event import ActorSpawnEvent, PlayerDropItemEvent, EventPriority, event_handler

from .gamemode_guard import GameModeLeadGuard

# Config constants
FILL_VOLUME_LIMIT = 32768
NV_DURATION_TICKS = 999999  # Legacy name: /effect expects seconds.
NV_SHOW_PARTICLES = False

# Blocked items - these cannot be given by admins
BLOCKED_ITEMS = {
    # Plushies
    "plushies:allay_plushie", "plushies:armadillo_plushie", "plushies:axolotl_plushie", "plushies:bat_plushie",
    "plushies:bee_plushie", "plushies:black_rabbit_plushie", "plushies:blaze_plushie", "plushies:bogged_plushie",
    "plushies:breeze_plushie", "plushies:brown_rabbit_plushie", "plushies:camel_plushie", "plushies:cat_plushie",
    "plushies:cave_spider_plushie", "plushies:chicken_plushie", "plushies:cod_plushie", "plushies:cold_frog_plushie",
    "plushies:cow_plushie", "plushies:creeper_plushie", "plushies:dolphin_plushie", "plushies:donkey_plushie",
    "plushies:drowned_plushie", "plushies:elder_guardian_plushie", "plushies:enderman_plushie", "plushies:endermite_plushie",
    "plushies:evoker_plushie", "plushies:frog_plushie", "plushies:ghast_plushie", "plushies:glow_squid_plushie",
    "plushies:goat_plushie", "plushies:guardian_plushie", "plushies:hoglin_plushie", "plushies:horse_plushie",
    "plushies:husk_plushie", "plushies:illusioner_plushie", "plushies:iron_golem_plushie", "plushies:killer_bunny_plushie",
    "plushies:large_tropical_fish_plushie", "plushies:llama_plushie", "plushies:magma_cube_plushie", "plushies:mooshroom_plushie",
    "plushies:mule_plushie", "plushies:ocelot_plushie", "plushies:panda_plushie", "plushies:parrot_plushie",
    "plushies:phantom_plushie", "plushies:pig_plushie", "plushies:piglin_brute_plushie", "plushies:piglin_plushie",
    "plushies:pillager_plushie", "plushies:polar_bear_plushie", "plushies:pufferfish_plushie", "plushies:ravager_plushie",
    "plushies:red_fox_plushie", "plushies:salmon_plushie", "plushies:salt_rabbit_plushie", "plushies:sheep_plushie",
    "plushies:shulker_plushie", "plushies:silverfish_plushie", "plushies:skeleton_horse_plushie", "plushies:skeleton_plushie",
    "plushies:slime_plushie", "plushies:small_tropical_fish_plushie", "plushies:sniffer_plushie", "plushies:snow_golem_plushie",
    "plushies:spider_plushie", "plushies:squid_plushie", "plushies:stray_plushie", "plushies:strider_plushie",
    "plushies:tadpole_plushie", "plushies:toast_rabbit_plushie", "plushies:turtle_plushie", "plushies:vex_plushie",
    "plushies:villager_plushie", "plushies:vindicator_plushie", "plushies:wandering_trader_plushie", "plushies:warden_plushie",
    "plushies:warm_frog_plushie", "plushies:white_fox_plushie", "plushies:white_rabbit_plushie", "plushies:white_splotched_rabbit_plushie",
    "plushies:witch_plushie", "plushies:wither_plushie", "plushies:wither_skeleton_plushie", "plushies:wolf_plushie",
    "plushies:yellow_rabbit_plushie", "plushies:zoglin_plushie", "plushies:zombie_horse_plushie", "plushies:zombie_plushie",
    "plushies:zombie_villager_plushie", "plushies:zombiefied_piglin_plushie",
    # Coins
    "ninjos:coin_wood", "ninjos:coin_glass", "ninjos:coin_iron", "ninjos:coin_gold",
    "ninjos:coin_emerald", "ninjos:coin_ruby", "ninjos:coin_diamond", "ninjos:coin_netherite",
    # Restricted vanilla items
    "minecraft:flint_and_steel", "flint_and_steel",
    "minecraft:ender_chest", "ender_chest",
    "minecraft:obsidian", "obsidian",
    "minecraft:bedrock", "bedrock",
}

# Preset items for Give Items menu
PRESET_ITEMS = [
    ("Diamond Sword", "diamond_sword"),
    ("Diamond Pickaxe", "diamond_pickaxe"),
    ("Diamond Armor Set", ["diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots"]),
    ("Netherite Sword", "netherite_sword"),
    ("Netherite Pickaxe", "netherite_pickaxe"),
    ("Netherite Armor Set", ["netherite_helmet", "netherite_chestplate", "netherite_leggings", "netherite_boots"]),
    ("Golden Apple", "golden_apple"),
    ("Enchanted Golden Apple", "enchanted_golden_apple"),
    ("Ender Pearls (16)", "ender_pearl 16"),
    ("Elytra", "elytra"),
    ("Firework Rockets (64)", "firework_rocket 64"),
    ("Totem of Undying", "totem_of_undying"),
]


class ModMenuPlugin(Plugin):
    api_version = "0.11"

    commands = {
        "mod": {
            "description": "Open the mod menu",
            "usages": ["/mod"]
        },
        "admin": {
            "description": "Open the admin menu",
            "usages": ["/admin"]
        },
        "adminlog": {
            "description": "View admin action logs (operators only)",
            "usages": ["/adminlog", "/adminlog <count>", "/adminlog <admin_name>"]
        }
    }

    permissions = {
        "modmenu.use": {
            "description": "Allows access to the mod menu",
            "default": "true"
        },
        "modmenu.owner": {
            "description": "Protects from being teleported",
            "default": "false"
        }
    }

    def on_enable(self) -> None:
        """Called when the plugin is enabled"""
        self.logger.info("Mod Menu Plugin enabled!")
        self._gamemode_guard = GameModeLeadGuard(self.logger)
        self.register_events(self)
        
        # Admin state tracking
        self.muted_players: set[str] = set()  # Player names
        self.frozen_players: set[str] = set()  # Player names
        self.vanished_players: set[str] = set()  # Player names
        self.godmode_players: set[str] = set()  # Player names
        self.flying_players: set[str] = set()  # Player names
        
        # Custom TP locations system
        self.admin_tp_limits: dict[str, int] = {}  # admin_name -> limit (-1 = unlimited)
        self.admin_tp_locations: dict[str, dict[str, dict]] = {}  # admin_name -> {loc_name: {x, y, z, dim}}
        
        # Base Check Locations (shared between admin/mod - admins can CRUD, mods can only TP)
        self.base_check_locations: dict[str, dict] = {}  # loc_name -> {x, y, z, dim}
        
        # Mod area assignments (to restrict Mod TP access)
        self.mod_areas: dict[str, str] = {}  # mod_name -> area_name
        
        # Clear items state
        self._item_clear_pending = False
        
        # Set up admin action log directory
        import os
        self.log_dir = os.path.join(self.data_folder, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Load custom TP data and base check locations
        self._load_custom_tp_data()
        self._load_base_check_locations()
        self._load_mod_areas()

    def _load_mod_areas(self) -> None:
        """Load mod area assignments from JSON"""
        import os
        import json
        area_file = os.path.join(self.data_folder, "mod_areas.json")
        if os.path.exists(area_file):
            try:
                with open(area_file, "r") as f:
                    self.mod_areas = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load mod areas: {e}")

    def _save_mod_areas(self) -> None:
        """Save mod area assignments to JSON"""
        import os
        import json
        os.makedirs(self.data_folder, exist_ok=True)
        area_file = os.path.join(self.data_folder, "mod_areas.json")
        try:
            with open(area_file, "w") as f:
                json.dump(self.mod_areas, f, indent=2)
        except Exception as e:
                self.logger.error(f"Failed to save mod areas: {e}")

    def _load_custom_tp_data(self) -> None:
        """Load custom TP limits and locations from JSON"""
        import os
        import json
        tp_file = os.path.join(self.data_folder, "custom_tps.json")
        if os.path.exists(tp_file):
            try:
                with open(tp_file, "r") as f:
                    data = json.load(f)
                    self.admin_tp_limits = data.get("limits", {})
                    self.admin_tp_locations = data.get("locations", {})
            except Exception as e:
                self.logger.error(f"Failed to load custom TP data: {e}")

    def _save_custom_tp_data(self) -> None:
        """Save custom TP limits and locations to JSON"""
        import os
        import json
        os.makedirs(self.data_folder, exist_ok=True)
        tp_file = os.path.join(self.data_folder, "custom_tps.json")
        try:
            with open(tp_file, "w") as f:
                json.dump({
                    "limits": self.admin_tp_limits,
                    "locations": self.admin_tp_locations
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save custom TP data: {e}")

    def _load_base_check_locations(self) -> None:
        """Load base check locations from JSON"""
        import os
        import json
        loc_file = os.path.join(self.data_folder, "base_check_locations.json")
        if os.path.exists(loc_file):
            try:
                with open(loc_file, "r") as f:
                    self.base_check_locations = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load base check locations: {e}")

    def _save_base_check_locations(self) -> None:
        """Save base check locations to JSON"""
        import os
        import json
        os.makedirs(self.data_folder, exist_ok=True)
        loc_file = os.path.join(self.data_folder, "base_check_locations.json")
        try:
            with open(loc_file, "w") as f:
                json.dump(self.base_check_locations, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save base check locations: {e}")

    def on_disable(self) -> None:
        """Called when the plugin is disabled"""
        if hasattr(self, "_gamemode_guard"):
            self._gamemode_guard.clear()
        self.logger.info("Mod Menu Plugin disabled!")

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_mode_switch_item_spawn(self, event: ActorSpawnEvent):
        self._gamemode_guard.observe_spawn(event.actor)

    @event_handler(priority=EventPriority.MONITOR)
    def on_mode_switch_inventory_drop(self, event: PlayerDropItemEvent):
        # Observe even cancelled drops, but never cancel or restore items here.
        self._gamemode_guard.observe_inventory_drop(event.player, event.item)

    def _change_game_mode(self, player: Player, mode: GameMode) -> bool:
        previous = self._gamemode_guard.recent.get(int(player.id))
        try:
            changed = self._gamemode_guard.change(player, mode)
        finally:
            entry = self._gamemode_guard.recent.get(int(player.id))
            if entry is not None and entry is not previous:
                try:
                    self._sample_mode_equipment(player, entry)
                except Exception as error:
                    self.logger.warning(f"Could not start mode-switch diagnostics: {error}")
                    self._gamemode_guard.finish(entry, "schedule_failed")
        if not changed:
            player.send_message("§cGame mode change was blocked. Your current mode was kept.")
            return False
        return True

    def _sample_mode_equipment(self, player: Player, entry) -> None:
        # Timers retain identity strings and copied data, never a native Player.
        name, unique_id = player.name, str(player.unique_id)

        def sample(final):
            if self._gamemode_guard.recent.get(entry.player_id) is not entry:
                return
            try:
                current = self.server.get_player(name)
            except Exception as error:
                self.logger.warning(f"Could not find player for mode-switch diagnostics: {error}")
                self._gamemode_guard.finish(entry, "player_lookup_failed")
                return
            if current is None or int(current.id) != entry.player_id or str(current.unique_id) != unique_id:
                self._gamemode_guard.finish(entry, "player_left")
                return
            self._gamemode_guard.sample(current, entry, final=final)

        try:
            for delay in (5, 10, 20):
                self.server.scheduler.run_task(self, lambda final=delay == 20: sample(final), delay=delay)
        except Exception as error:
            self.logger.warning(f"Could not schedule mode-switch diagnostics for {name}: {error}")
            self._gamemode_guard.finish(entry, "schedule_failed")

    def _get_visible_players(self, requesting_player: Player, exclude_self: bool = True) -> list:
        """Get list of players visible to the requesting player.
        Admins cannot see other admins - they appear as if offline.
        Mods cannot see admins or other mods - only regular players visible.
        """
        online_players = self.server.online_players
        visible = []
        
        requester_is_admin = requesting_player.is_op
        requester_is_mod = "Mod" in requesting_player.scoreboard_tags and not requester_is_admin
        
        for p in online_players:
            # Skip self if requested
            if exclude_self and p.name == requesting_player.name:
                continue
            # Always skip Owner-tagged players
            if "Owner" in p.scoreboard_tags:
                continue
            # If requester is admin, hide other admins
            if requester_is_admin and p.is_op:
                continue
            # If requester is mod, hide admins AND other mods
            if requester_is_mod:
                if p.is_op or "Mod" in p.scoreboard_tags:
                    continue
            visible.append(p)
        
        return visible


    def log_admin_action(self, admin_name: str, action: str, target: str = "", details: str = "") -> None:
        """Log an admin action to JSON file for operator accountability"""
        import json
        import os
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "admin": admin_name,
            "action": action,
            "target": target,
            "details": details
        }
        
        # Log to console for operators
        log_msg = f"[ADMIN LOG] {admin_name} | {action}"
        if target:
            log_msg += f" | Target: {target}"
        if details:
            log_msg += f" | {details}"
        self.logger.info(log_msg)
        
        # Write to daily log file
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"admin_actions_{date_str}.json")
            
            # Read existing logs or create new list
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to write admin log: {e}")

    def view_admin_logs(self, player: Player, count: int = 10, filter_admin: str = None) -> None:
        """View recent admin logs in-game using ActionForm to prevent crashes"""
        import json
        import os
        from datetime import datetime
        
        try:
            logs = []
            
            # Always read ALL log files for complete history
            if os.path.exists(self.log_dir):
                for filename in sorted(os.listdir(self.log_dir)):
                    if filename.startswith("admin_actions_") and filename.endswith(".json"):
                        log_file = os.path.join(self.log_dir, filename)
                        try:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                file_logs = json.load(f)
                                logs.extend(file_logs)
                        except:
                            continue
            
            if not logs:
                player.send_message("§7No admin logs found.")
                return
            
            if filter_admin:
                logs = [log for log in logs if log.get('admin', '').lower() == filter_admin.lower()]
                if not logs:
                    player.send_message(f"§7No logs found for: §e{filter_admin}")
                    return
            
            # Reverse to show most recent first (no count limit - pagination handles display)
            recent_logs = logs[::-1]
            
            # Store logs in instance for pagination to avoid lambda issues
            self._temp_logs = recent_logs
            self._temp_filter = filter_admin
            
            # Show paged form instead of chat messages
            self._show_logs_page(player, 0)
            
        except Exception as e:
            player.send_message("§cError reading admin logs.")
            self.logger.error(f"Error reading admin logs: {e}")

    def _show_logs_page(self, player: Player, page: int) -> None:
        """Show a page of logs using ActionForm"""
        from datetime import datetime
        
        logs = getattr(self, '_temp_logs', [])
        filter_admin = getattr(self, '_temp_filter', None)
        
        if not logs:
            player.send_message("§7No logs to display.")
            return
        
        ENTRIES_PER_PAGE = 25
        total_pages = (len(logs) + ENTRIES_PER_PAGE - 1) // ENTRIES_PER_PAGE
        start_idx = page * ENTRIES_PER_PAGE
        end_idx = min(start_idx + ENTRIES_PER_PAGE, len(logs))
        page_logs = logs[start_idx:end_idx]
        
        # Build content string
        content_lines = []
        if filter_admin:
            content_lines.append(f"§7Filtered by: §e{filter_admin}")
        content_lines.append(f"§7Page {page + 1}/{total_pages} | Showing {len(page_logs)} of {len(logs)} entries\n")
        
        for log in page_logs:
            timestamp = log.get('timestamp', 'Unknown')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
            except:
                time_str = str(timestamp)[:10]
            
            admin = log.get('admin', 'Unknown')
            action = log.get('action', 'Unknown')
            target = log.get('target', '')
            details = log.get('details', '')
            
            # Use red for failed actions, blue for normal
            action_color = "§c" if "FAILED" in action else "§b"
            line = f"§7[{time_str}] §e{admin} §f→ {action_color}{action}"
            if target:
                line += f" §7→ §a{target}"
            if details:
                line += f"\n   §8{details}"
            content_lines.append(line)

        
        content = "\n".join(content_lines)
        
        # Store current page for navigation
        current_page = page
        max_page = total_pages - 1
        
        def on_submit(p: Player, selection: int) -> None:
            try:
                # Capture values at definition time using default args
                player_ref = p
                prev_page = current_page - 1
                next_page = current_page + 1
                
                if selection == 0:  # Previous
                    if current_page > 0:
                        self.server.scheduler.run_task(
                            self, lambda plr=player_ref, pg=prev_page: self._show_logs_page(plr, pg), delay=1
                        )
                elif selection == 1:  # Next
                    if current_page < max_page:
                        self.server.scheduler.run_task(
                            self, lambda plr=player_ref, pg=next_page: self._show_logs_page(plr, pg), delay=1
                        )
                elif selection == 2:  # Back to Menu
                    self.server.scheduler.run_task(
                        self, lambda plr=player_ref: self.show_admin_log_menu(plr), delay=1
                    )
            except Exception as e:
                self.logger.error(f"Error in log page nav: {e}")

        
        form = ActionForm(
            title="§6Admin Logs",
            content=content,
            on_submit=on_submit
        )
        
        # Add navigation buttons
        prev_label = "§7◀ Previous" if page > 0 else "§8◀ Previous"
        next_label = "§7Next ▶" if page < total_pages - 1 else "§8Next ▶"
        form.add_button(prev_label)
        form.add_button(next_label) 
        form.add_button("§cBack to Menu")
        
        player.send_form(form)

    def clear_old_logs(self, player: Player, days: int) -> None:
        """Clear admin log files older than specified days (operators only)"""
        import os
        from datetime import datetime, timedelta
        
        try:
            if not os.path.exists(self.log_dir):
                player.send_message("§7No log directory found.")
                return
            
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for filename in os.listdir(self.log_dir):
                if filename.startswith("admin_actions_") and filename.endswith(".json"):
                    # Extract date from filename
                    try:
                        date_str = filename.replace("admin_actions_", "").replace(".json", "")
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        if file_date < cutoff_date:
                            file_path = os.path.join(self.log_dir, filename)
                            os.remove(file_path)
                            deleted_count += 1
                    except:
                        continue
            
            if deleted_count > 0:
                player.send_message(f"§aDeleted {deleted_count} log file(s) older than {days} days.")
                self.log_admin_action(player.name, "CLEAR_LOGS", "", f"Deleted {deleted_count} files older than {days} days")
            else:
                player.send_message(f"§7No log files older than {days} days found.")
                
        except Exception as e:
            player.send_message("§cError clearing old logs.")
            self.logger.error(f"Error clearing old logs: {e}")

    def show_admin_log_menu(self, player: Player) -> None:
        """Show main admin log menu"""
        import os
        
        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # View by Admin
                self.show_log_admin_select(p)
            elif selection == 1:  # View Recent Logs
                self.show_log_count_menu(p)
            elif selection == 2:  # Browse by Date
                self.show_log_date_select(p)
            elif selection == 3:  # Clear Old Logs
                self.show_log_clear_menu(p)

        # Count available log files
        log_count = 0
        if hasattr(self, 'log_dir') and os.path.exists(self.log_dir):
            log_count = len([f for f in os.listdir(self.log_dir) if f.startswith("admin_actions_")])

        form = ActionForm(
            title="§6Admin Action Logs",
            content=f"§7Monitor admin activity for accountability.\n§7Log files available: §e{log_count}",
            on_submit=on_submit
        )
        form.add_button("§eView by Admin/Mod")
        form.add_button("§bView Recent Logs")
        form.add_button("§aBrowse by Date")
        form.add_button("§cClear Old Logs")
        player.send_form(form)

    def show_log_admin_select(self, player: Player) -> None:
        """Show menu to select which admin/mod's logs to view"""
        import json
        import os
        
        # Get unique admin/mod names from ALL log files
        admins = set()
        try:
            if os.path.exists(self.log_dir):
                for filename in os.listdir(self.log_dir):
                    if filename.startswith("admin_actions_") and filename.endswith(".json"):
                        log_file = os.path.join(self.log_dir, filename)
                        try:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                logs = json.load(f)
                                for log in logs:
                                    admins.add(log.get('admin', 'Unknown'))
                        except:
                            continue
        except:
            pass
        
        if not admins:
            player.send_message("§7No admin/mod actions logged yet.")
            return
        
        admin_list = sorted(list(admins))
        
        def on_submit(p: Player, response: str) -> None:
            try:
                import json
                data = json.loads(response) if isinstance(response, str) else response
                selected_index = int(data[0]) if isinstance(data, list) else 0
                if 0 <= selected_index < len(admin_list):
                    selected_admin = admin_list[selected_index]
                    # Use scheduler with captured values to avoid form callback crash
                    self.server.scheduler.run_task(
                        self, lambda p=p, a=selected_admin: self.view_admin_logs(p, 20, a), delay=1
                    )
            except Exception as e:
                self.logger.error(f"Error in admin log select: {e}")

        form = ModalForm(title="View Logs by Admin/Mod", on_submit=on_submit)
        form.add_control(Dropdown(label="Select admin/mod:", options=admin_list, default_index=0))
        player.send_form(form)

    def show_log_count_menu(self, player: Player) -> None:
        """Show menu to select how many recent logs to view"""
        count_options = ["10", "25", "50"]
        
        def on_submit(p: Player, response: str) -> None:
            try:
                import json
                data = json.loads(response) if isinstance(response, str) else response
                selected_index = int(data[0]) if isinstance(data, list) else 0
                count = int(count_options[selected_index])
                # Use scheduler with captured values
                self.server.scheduler.run_task(
                    self, lambda p=p, c=count: self.view_admin_logs(p, c, None), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error in log count select: {e}")

        form = ModalForm(title="View Recent Logs", on_submit=on_submit)
        form.add_control(Dropdown(label="Number of entries:", options=count_options, default_index=0))
        player.send_form(form)

    def show_log_date_select(self, player: Player) -> None:
        """Show menu to select which date's logs to view"""
        import os
        
        # Get available log dates
        dates = []
        try:
            if os.path.exists(self.log_dir):
                for filename in sorted(os.listdir(self.log_dir), reverse=True):
                    if filename.startswith("admin_actions_") and filename.endswith(".json"):
                        date_str = filename.replace("admin_actions_", "").replace(".json", "")
                        dates.append(date_str)
        except:
            pass
        
        if not dates:
            player.send_message("§7No log files found.")
            return
        
        def on_submit(p: Player, response: str) -> None:
            try:
                import json
                data = json.loads(response) if isinstance(response, str) else response
                selected_index = int(data[0]) if isinstance(data, list) else 0
                if 0 <= selected_index < len(dates):
                    selected_date = dates[selected_index]
                    # Use scheduler with captured values
                    self.server.scheduler.run_task(
                        self, lambda p=p, d=selected_date: self.view_logs_for_date(p, d), delay=1
                    )
            except Exception as e:
                self.logger.error(f"Error in log date select: {e}")

        form = ModalForm(title="Browse by Date", on_submit=on_submit)
        form.add_control(Dropdown(label="Select date:", options=dates, default_index=0))
        player.send_form(form)

    def view_logs_for_date(self, player: Player, date_str: str) -> None:
        """View logs for a specific date using ActionForm"""
        import json
        import os
        
        try:
            log_file = os.path.join(self.log_dir, f"admin_actions_{date_str}.json")
            
            if not os.path.exists(log_file):
                player.send_message(f"§7No logs found for {date_str}.")
                return
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not logs:
                player.send_message(f"§7No logs found for {date_str}.")
                return
            
            # Get all entries for that date (most recent first)
            recent_logs = logs[::-1]
            
            # Use the shared paged display with a date filter label.
            self._temp_logs = recent_logs
            self._temp_filter = f"Date: {date_str}"
            self._show_logs_page(player, 0)
            
        except Exception as e:
            player.send_message("§cError reading logs.")
            self.logger.error(f"Error reading logs for date: {e}")

    def show_log_clear_menu(self, player: Player) -> None:
        """Show menu to clear old logs"""
        day_options = ["7 days", "14 days", "30 days", "60 days", "90 days"]
        day_values = [7, 14, 30, 60, 90]
        
        def on_submit(p: Player, response: str) -> None:
            try:
                import json
                data = json.loads(response) if isinstance(response, str) else response
                selected_index = int(data[0]) if isinstance(data, list) else 0
                days = day_values[selected_index]
                self.clear_old_logs(p, days)
            except:
                pass

        form = ModalForm(title="Clear Old Logs", on_submit=on_submit)
        form.add_control(Dropdown(label="Delete logs older than:", options=day_options, default_index=0))
        player.send_form(form)

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        """Handle the /mod and /admin commands"""
        if command.name == "mod":
            if not isinstance(sender, Player):
                sender.send_error_message("§cThis command can only be used by players.")
                return False

            # Check if player has the "Mod" tag using scoreboard_tags property
            if "Mod" not in sender.scoreboard_tags:
                sender.send_error_message("§cYou don't have permission to use this command.")
                return False

            # Schedule menu to open after a tick delay
            self.server.scheduler.run_task(
                self, lambda: self.show_mod_menu(sender), delay=1
            )
            return True

        elif command.name == "admin":
            if not isinstance(sender, Player):
                sender.send_error_message("§cThis command can only be used by players.")
                return False

            # Check if player has the "Admin" tag
            if "Admin" not in sender.scoreboard_tags:
                sender.send_error_message("§cYou don't have permission to use this command.")
                return False

            # Schedule admin menu to open after a tick delay
            self.server.scheduler.run_task(
                self, lambda: self.show_admin_menu(sender), delay=1
            )
            return True

        elif command.name == "adminlog":
            if not isinstance(sender, Player):
                sender.send_error_message("§cThis command can only be used by players.")
                return False

            # Only operators can view admin logs
            if not sender.is_op:
                sender.send_error_message("§cOnly operators can view admin logs.")
                return False

            # Open admin log menu
            self.server.scheduler.run_task(
                self, lambda: self.show_admin_log_menu(sender), delay=1
            )
            return True

        return False

    # ===========================
    # Night Vision helpers
    # ===========================
    def give_night_vision(self, player: Player) -> None:
        """Give night vision effect to player"""
        try:
            # Execute effect command as server console to avoid permission issues
            console_sender = self.server.command_sender
            command = f'effect "{player.name}" night_vision {NV_DURATION_TICKS} 0 {str(NV_SHOW_PARTICLES).lower()}'
            self.server.dispatch_command(console_sender, command)
        except Exception as e:
            self.logger.warning(f"[NV] addEffect failed for {player.name}: {e}")

    def clear_night_vision(self, player: Player) -> None:
        """Clear night vision effect from player"""
        try:
            # Execute effect command as server console to avoid permission issues
            console_sender = self.server.command_sender
            # Preserve effects supplied by enchanted gear and other plugins.
            command = f'effect "{player.name}" clear night_vision'
            self.server.dispatch_command(console_sender, command)
        except Exception:
            pass

    def switch_to_spectator_with_nv(self, player: Player) -> bool:
        """Switch to spectator mode and apply night vision"""
        try:
            if not self._change_game_mode(player, GameMode.SPECTATOR):
                return False
            self.give_night_vision(player)
            player.send_message("§7Set gamemode to §eSpectator §7(+ Night Vision).")
            self.log_admin_action(player.name, "MOD_SPECTATOR", player.name)
            return True
        except Exception as e:
            self.logger.warning(f"gamemode spectator failed: {e}")
            player.send_message("§cFailed to set Spectator. Check permissions.")
            return False

    def switch_to_survival_clear_nv(self, player: Player) -> None:
        """Switch to survival mode and clear night vision"""
        try:
            if not self._change_game_mode(player, GameMode.SURVIVAL):
                return
            self.clear_night_vision(player)
            player.send_message("§7Set gamemode to §aSurvival §7(Night Vision cleared).")
            self.log_admin_action(player.name, "MOD_SURVIVAL", player.name)
        except Exception as e:
            self.logger.warning(f"gamemode survival failed: {e}")
            player.send_message("§cFailed to set Survival. Check permissions.")

    # ===========================
    # Main Mod Menu
    # ===========================
    def show_mod_menu(self, player: Player) -> None:
        """Show the main mod menu"""

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # Commands
                self.server.scheduler.run_task(
                    self, lambda: self.show_commands_menu(p), delay=1
                )
            elif selection == 1:  # Spectator
                self.switch_to_spectator_with_nv(p)
            elif selection == 2:  # Survival
                self.switch_to_survival_clear_nv(p)

        form = ActionForm(
            title="Mod Menu",
            content="Select an option:",
            on_submit=on_submit
        )
        form.add_button("Commands")
        form.add_button("Spectator")
        form.add_button("Survival")

        player.send_form(form)

    # ===========================
    # Commands Menu
    # ===========================
    def show_commands_menu(self, player: Player) -> None:
        """Show the commands submenu"""

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # Teleport To
                self.server.scheduler.run_task(
                    self, lambda: self.show_teleport_to_menu(p), delay=1
                )
            elif selection == 1:  # Teleport From
                self.server.scheduler.run_task(
                    self, lambda: self.show_teleport_from_menu(p), delay=1
                )
            elif selection == 2:  # Fill Area
                self.server.scheduler.run_task(
                    self, lambda: self.show_fill_menu(p), delay=1
                )
            elif selection == 3:  # Load Structure
                self.load_structure(p)
            elif selection == 4:  # Base Check Locations (TP only)
                self.server.scheduler.run_task(
                    self, lambda: self.show_base_check_tp_menu(p), delay=1
                )

        form = ActionForm(
            title="Commands Menu",
            content="Select a command:",
            on_submit=on_submit
        )
        form.add_button("Teleport To")
        form.add_button("Teleport From")
        form.add_button("Fill Area")
        form.add_button("Load Structure")
        form.add_button("§eBase Check Locations")

        player.send_form(form)

    # ===========================
    # Fill Area
    # ===========================
    def get_dimension_y_limits(self, dimension_name: str) -> tuple[int, int]:
        """Get the Y coordinate limits for a dimension"""
        # Minecraft Bedrock dimension limits
        dimension_limits = {
            "overworld": (-64, 320),
            "nether": (0, 128),
            "the_end": (0, 256),
            "the end": (0, 256),
        }
        # Default to overworld limits if unknown
        dim_lower = dimension_name.lower() if dimension_name else "overworld"
        return dimension_limits.get(dim_lower, (-64, 320))

    def show_fill_menu(self, player: Player) -> None:
        """Show the fill area menu - mods can only fill with deepslate"""

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                # ModalForm returns data as a list, not a dict
                if isinstance(values, list):
                    if len(values) < 6:
                        p.send_message("§cAll coordinates must be filled in.")
                        return
                    x1_raw = values[0]
                    y1_raw = values[1]
                    z1_raw = values[2]
                    x2_raw = values[3]
                    y2_raw = values[4]
                    z2_raw = values[5]
                else:
                    x1_raw = values.get("x1", "")
                    y1_raw = values.get("y1", "")
                    z1_raw = values.get("z1", "")
                    x2_raw = values.get("x2", "")
                    y2_raw = values.get("y2", "")
                    z2_raw = values.get("z2", "")

                # Mods can only use deepslate
                block_type = "deepslate"

                if not all([x1_raw, y1_raw, z1_raw, x2_raw, y2_raw, z2_raw]):
                    p.send_message("§cAll coordinates must be filled in.")
                    return

                # Parse coordinates for volume check
                loc = p.location

                def parse_coord(coord: str, base: float) -> int:
                    coord = str(coord).strip()
                    if coord.startswith("~"):
                        offset = coord[1:].strip()
                        return int(base + (int(offset) if offset else 0))
                    return int(coord)

                try:
                    x1 = parse_coord(x1_raw, loc.x)
                    y1 = parse_coord(y1_raw, loc.y)
                    z1 = parse_coord(z1_raw, loc.z)
                    x2 = parse_coord(x2_raw, loc.x)
                    y2 = parse_coord(y2_raw, loc.y)
                    z2 = parse_coord(z2_raw, loc.z)
                except ValueError:
                    p.send_message("§cInvalid coordinate format. Use numbers or ~ notation.")
                    return

                # Get dimension limits and clamp Y coordinates
                try:
                    dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                except:
                    dim_name = "overworld"
                
                min_y, max_y = self.get_dimension_y_limits(dim_name)
                
                # Clamp Y values to world bounds
                original_y1, original_y2 = y1, y2
                y1 = max(min_y, min(max_y, y1))
                y2 = max(min_y, min(max_y, y2))
                
                # Notify if coordinates were clamped
                if y1 != original_y1 or y2 != original_y2:
                    p.send_message(f"§eY coordinates clamped to world limits ({min_y} to {max_y})")

                # Auto-normalize: ensure min/max are correct (order doesn't matter)
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                z1, z2 = min(z1, z2), max(z1, z2)

                volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)

                if volume > FILL_VOLUME_LIMIT:
                    p.send_message(f"§cArea is too large! ({volume} blocks). Maximum is {FILL_VOLUME_LIMIT}.")
                    self.log_admin_action(p.name, "MOD_FILL_FAILED", "", f"Reason: Volume too large ({volume} blocks), Block: {block_type}")
                    return

                p.send_message(f"§7Filling area of {volume} blocks with {block_type}...")
                try:
                    # Execute fill command as server console to avoid permission issues
                    console_sender = self.server.command_sender
                    # Use the clamped absolute coordinates, not raw values
                    command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block_type}"
                    success = self.server.dispatch_command(console_sender, command)
                    if success:
                        p.send_message("§aFill executed successfully.")
                        self.log_admin_action(p.name, "MOD_FILL", "", f"Block: {block_type}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2}), Volume: {volume}")
                    else:
                        p.send_message("§cFailed to execute fill command. Check coordinates.")
                        self.log_admin_action(p.name, "MOD_FILL_FAILED", "", f"Reason: Command returned false, Block: {block_type}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2})")
                        self.logger.warning(f"Fill command failed for {p.name}: command returned false")
                except Exception as err:
                    p.send_message("§cFailed to execute fill command. Check coordinates and permissions.")
                    self.log_admin_action(p.name, "MOD_FILL_FAILED", "", f"Reason: Exception - {err}, Block: {block_type}")
                    self.logger.warning(f"Fill command failed: {err}")

            except Exception as e:
                self.logger.error(f"Error in fill menu: {e}")

        form = ModalForm(
            title="Fill Area",
            on_submit=on_submit
        )
        form.add_control(TextInput(label="Start X (e.g., ~ or 100)", placeholder="~"))
        form.add_control(TextInput(label="Start Y (e.g., ~ or 64)", placeholder="~"))
        form.add_control(TextInput(label="Start Z (e.g., ~ or 100)", placeholder="~"))
        form.add_control(TextInput(label="End X (e.g., ~5 or 110)", placeholder="~10"))
        form.add_control(TextInput(label="End Y (e.g., ~5 or 74)", placeholder="~10"))
        form.add_control(TextInput(label="End Z (e.g., ~5 or 110)", placeholder="~10"))

        player.send_form(form)

    def show_admin_fill_menu(self, player: Player) -> None:
        """Show admin fill menu with block selection options"""
        # Block options for admin fill
        block_options = [
            "deepslate", "stone", "cobblestone", "dirt", "grass_block",
            "oak_planks", "spruce_planks", "birch_planks", "glass", "sand",
            "gravel", "iron_block", "gold_block", "diamond_block", "obsidian",
            "bedrock", "air", "water", "lava", "netherrack"
        ]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list):
                    if len(values) < 8:
                        p.send_message("§cAll fields must be filled in.")
                        return
                    x1_raw = values[0]
                    y1_raw = values[1]
                    z1_raw = values[2]
                    x2_raw = values[3]
                    y2_raw = values[4]
                    z2_raw = values[5]
                    block_index = int(values[6]) if values[6] is not None else 0
                    custom_block = str(values[7]).strip() if values[7] else ""
                else:
                    x1_raw = values.get("x1", "")
                    y1_raw = values.get("y1", "")
                    z1_raw = values.get("z1", "")
                    x2_raw = values.get("x2", "")
                    y2_raw = values.get("y2", "")
                    z2_raw = values.get("z2", "")
                    block_index = 0
                    custom_block = ""

                # Get selected block - custom overrides dropdown
                if custom_block:
                    block_type = custom_block
                else:
                    block_type = block_options[block_index] if 0 <= block_index < len(block_options) else "deepslate"

                if not all([x1_raw, y1_raw, z1_raw, x2_raw, y2_raw, z2_raw]):
                    p.send_message("§cAll coordinates must be filled in.")
                    return

                # Parse coordinates
                loc = p.location

                def parse_coord(coord: str, base: float) -> int:
                    coord = str(coord).strip()
                    if coord.startswith("~"):
                        offset = coord[1:].strip()
                        return int(base + (int(offset) if offset else 0))
                    return int(coord)

                try:
                    x1 = parse_coord(x1_raw, loc.x)
                    y1 = parse_coord(y1_raw, loc.y)
                    z1 = parse_coord(z1_raw, loc.z)
                    x2 = parse_coord(x2_raw, loc.x)
                    y2 = parse_coord(y2_raw, loc.y)
                    z2 = parse_coord(z2_raw, loc.z)
                except ValueError:
                    p.send_message("§cInvalid coordinate format.")
                    return

                # Get dimension Y limits
                try:
                    dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                except:
                    dim_name = "overworld"
                min_y, max_y = self.get_dimension_y_limits(dim_name)

                # Clamp Y values
                y1 = max(min_y, min(max_y, y1))
                y2 = max(min_y, min(max_y, y2))

                # Volume check
                volume = abs(x2 - x1 + 1) * abs(y2 - y1 + 1) * abs(z2 - z1 + 1)
                if volume > 32768:
                    p.send_message(f"§cFill area too large ({volume:,} blocks). Max is 32,768.")
                    self.log_admin_action(p.name, "ADMIN_FILL_FAILED", "", f"Reason: Volume too large ({volume} blocks), Block: {block_type}")
                    return

                # Execute fill command
                console = self.server.command_sender
                command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block_type}"
                success = self.server.dispatch_command(console, command)
                if success:
                    p.send_message(f"§aFilled area with {block_type} ({volume:,} blocks)")
                    self.log_admin_action(p.name, "ADMIN_FILL", "", f"{x1},{y1},{z1} to {x2},{y2},{z2} with {block_type}")
                else:
                    p.send_message("§cFill command failed.")
                    self.log_admin_action(p.name, "ADMIN_FILL_FAILED", "", f"Reason: Command returned false, Block: {block_type}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2})")
            except Exception as e:
                self.logger.error(f"Error in admin fill: {e}")
                self.log_admin_action(p.name, "ADMIN_FILL_FAILED", "", f"Reason: Exception - {e}")

        form = ModalForm(
            title="§6Admin Fill Area",
            on_submit=on_submit
        )
        form.add_control(TextInput(label="Start X (e.g., ~ or 100)", placeholder="~"))
        form.add_control(TextInput(label="Start Y (e.g., ~ or 64)", placeholder="~"))
        form.add_control(TextInput(label="Start Z (e.g., ~ or 100)", placeholder="~"))
        form.add_control(TextInput(label="End X (e.g., ~5 or 110)", placeholder="~10"))
        form.add_control(TextInput(label="End Y (e.g., ~5 or 74)", placeholder="~10"))
        form.add_control(TextInput(label="End Z (e.g., ~5 or 110)", placeholder="~10"))
        form.add_control(Dropdown(label="Block Type:", options=block_options, default_index=0))
        form.add_control(TextInput(label="Custom Block (overrides dropdown):", placeholder="e.g., copper_block"))

        player.send_form(form)

    # ===========================
    # Structure Loader
    # ===========================
    def load_structure(self, player: Player) -> None:
        """Load a structure in front of the player"""
        structure_name = "mystructure:tkcheck"

        player.send_message(f"§7Attempting to load structure §e{structure_name}§7...")

        # Get player's location for calculating load position
        loc = player.location

        # Try different structure load command formats using server console
        success = False
        error_msg = ""
        console_sender = self.server.command_sender

        # Format 1: Load at player's current position using absolute coordinates
        try:
            load_x = int(loc.x)
            load_y = int(loc.y)
            load_z = int(loc.z)
            command = f'structure load {structure_name} {load_x} {load_y} {load_z}'
            success = self.server.dispatch_command(console_sender, command)
            if success:
                player.send_message(f"§7Loaded at {load_x}, {load_y}, {load_z}.")
        except Exception as e1:
            error_msg = str(e1)
            success = False

        # Format 2: Try with quotes if first attempt failed
        if not success:
            try:
                load_x = int(loc.x)
                load_y = int(loc.y)
                load_z = int(loc.z)
                command = f'structure load "{structure_name}" {load_x} {load_y} {load_z}'
                success = self.server.dispatch_command(console_sender, command)
                if success:
                    player.send_message(f"§7Loaded at {load_x}, {load_y}, {load_z}.")
            except Exception as e2:
                error_msg = f"Both formats failed. Last error: {str(e2)}"
                success = False

        if success:
            player.send_message(f"§aSuccessfully loaded structure: §e{structure_name}")
            self.log_admin_action(player.name, "MOD_LOADSTRUCTURE", "", f"Structure: {structure_name}, Coords: ({load_x},{load_y},{load_z})")
        else:
            player.send_message(f"§cFailed to load structure: {error_msg}")
            player.send_message("§cMake sure the structure exists in the world's behavior pack.")
            player.send_message("§7You can also try: §e/structure save {structure_name} <from> <to>")
            self.logger.warning(f"Structure load failed for {player.name}: {error_msg}")

    # ===========================
    # Teleport To (player selection with search)
    # ===========================
    def show_teleport_to_menu(self, player: Player) -> None:
        """Show menu to teleport to another player with search option"""
        eligible_players = self._get_visible_players(player)

        if not eligible_players:
            player.send_message("§cNo eligible players to teleport to.")
            return

        def on_search_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    search_term = str(values[0]).strip().lower()
                    
                    # Filter players by search term
                    if search_term:
                        filtered = [plr for plr in eligible_players if search_term in plr.name.lower()]
                        if not filtered:
                            p.send_message(f"§cNo players found matching '{search_term}'")
                            return
                    else:
                        filtered = eligible_players
                    
                    # Show results
                    self.server.scheduler.run_task(
                        self, lambda plr=p, players=filtered: self._show_teleport_to_results(plr, players), delay=1
                    )
            except Exception as e:
                self.logger.error(f"Error in TP search: {e}")

        form = ModalForm(title="Teleport To Player", on_submit=on_search_submit)
        form.add_control(TextInput(label="Search player (leave empty for all):", placeholder="e.g., player name..."))
        player.send_form(form)

    def _show_teleport_to_results(self, player: Player, filtered_players: list) -> None:
        """Show filtered player results for teleport"""
        player_names = [p.name for p in filtered_players]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]

                    if 0 <= selected_index < len(filtered_players):
                        target = filtered_players[selected_index]

                        # Switch to spectator + NV first
                        if not self.switch_to_spectator_with_nv(p):
                            return

                        # Teleport after brief delay
                        def do_teleport():
                            try:
                                p.teleport(target.location)
                                p.send_message(f"§7Teleported to §a{target.name}")
                                self.log_admin_action(p.name, "MOD_TELEPORT", target.name)
                            except Exception as e:
                                p.send_message("§cTeleport failed (chunk not loaded or obstructed).")

                        self.server.scheduler.run_task(self, do_teleport, delay=5)
                    else:
                        p.send_message("§cError: Invalid selection.")
            except Exception as e:
                self.logger.error(f"Error in teleport to: {e}")

        form = ModalForm(title=f"Select Player ({len(player_names)} found)", on_submit=on_submit)
        form.add_control(Dropdown(label="Select a player:", options=player_names, default_index=0))
        player.send_form(form)

    # ===========================
    # Teleport From (bring player)
    # ===========================
    def show_teleport_from_menu(self, player: Player) -> None:
        """Show menu to bring another player to you"""
        eligible_players = self._get_visible_players(player)

        if not eligible_players:
            player.send_message("§cNo eligible players to teleport to you.")
            return

        player_names = [p.name for p in eligible_players]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                # ModalForm returns data as a list
                if isinstance(values, list):
                    if len(values) < 1:
                        p.send_message("§cError: Invalid selection.")
                        return
                    selected_index = values[0]
                else:
                    selected_index = values.get("player_select", 0)

                if 0 <= selected_index < len(eligible_players):
                    target = eligible_players[selected_index]

                    try:
                        target.teleport(p.location)
                        p.send_message(f"§7Brought §a{target.name} §7to your location.")
                        self.log_admin_action(p.name, "MOD_TP_FROM", target.name, f"Brought to location ({int(p.location.x)},{int(p.location.y)},{int(p.location.z)})")
                    except Exception as e:
                        p.send_message("§cTeleport failed (chunk not loaded or obstructed).")
                else:
                    p.send_message("§cError: Invalid selection.")

            except Exception as e:
                self.logger.error(f"Error in teleport from: {e}")

        form = ModalForm(
            title="Teleport From",
            on_submit=on_submit
        )
        form.add_control(Dropdown(label="Select a player to bring here:", options=player_names, default_index=0))

        player.send_form(form)

    # ===========================
    # ADMIN MENU SECTION
    # ===========================
    def show_admin_menu(self, player: Player) -> None:
        """Show the main admin menu"""

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # Player Management
                self.server.scheduler.run_task(
                    self, lambda: self.show_player_management_menu(p), delay=1
                )
            elif selection == 1:  # Teleport
                self.server.scheduler.run_task(
                    self, lambda: self.show_admin_teleport_menu(p), delay=1
                )
            elif selection == 2:  # Self Toggles
                self.server.scheduler.run_task(
                    self, lambda: self.show_self_toggles_menu(p), delay=1
                )
            elif selection == 3:  # Utilities
                self.server.scheduler.run_task(
                    self, lambda: self.show_utilities_menu(p), delay=1
                )

        form = ActionForm(
            title="§6Admin Menu",
            content="Select a category:",
            on_submit=on_submit
        )
        form.add_button("§cPlayer Management")
        form.add_button("§dTeleport")
        form.add_button("§bSelf Toggles")
        form.add_button("§aUtilities")

        player.send_form(form)

    def show_admin_teleport_menu(self, player: Player) -> None:
        """Show admin teleport submenu"""

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # TP to Player
                self.server.scheduler.run_task(
                    self, lambda: self.show_teleport_to_menu(p), delay=1
                )
            elif selection == 1:  # TP Player to You
                self.server.scheduler.run_task(
                    self, lambda: self.show_teleport_from_menu(p), delay=1
                )
            elif selection == 2:  # TP to Coords
                self.server.scheduler.run_task(
                    self, lambda: self.show_tp_coords_menu(p), delay=1
                )
            elif selection == 3:  # Custom TP Locations
                self.server.scheduler.run_task(
                    self, lambda: self.show_admin_tp_locations_menu(p), delay=1
                )

        form = ActionForm(
            title="§dTeleport Menu",
            content="Select a teleport option:",
            on_submit=on_submit
        )
        form.add_button("§aTP to Player")
        form.add_button("§eTP Player to You")
        form.add_button("§bTP to Coordinates")
        form.add_button("§dCustom TP Locations")

        player.send_form(form)

    def show_tp_coords_menu(self, player: Player) -> None:
        """Show teleport to coordinates menu"""

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 3:
                    x_raw = str(values[0]).strip()
                    y_raw = str(values[1]).strip()
                    z_raw = str(values[2]).strip()

                    if not all([x_raw, y_raw, z_raw]):
                        p.send_message("§cAll coordinates must be filled in.")
                        return

                    # Parse coordinates (support ~ relative)
                    loc = p.location

                    def parse_coord(coord: str, base: float) -> float:
                        if coord.startswith("~"):
                            offset = coord[1:].strip()
                            return base + (float(offset) if offset else 0)
                        return float(coord)

                    try:
                        x = parse_coord(x_raw, loc.x)
                        y = parse_coord(y_raw, loc.y)
                        z = parse_coord(z_raw, loc.z)
                    except ValueError:
                        p.send_message("§cInvalid coordinate format.")
                        return

                    # Execute teleport
                    console = self.server.command_sender
                    success = self.server.dispatch_command(console, f'tp "{p.name}" {x} {y} {z}')
                    if success:
                        p.send_message(f"§aTeleported to §e{x:.1f}, {y:.1f}, {z:.1f}")
                        self.log_admin_action(p.name, "ADMIN_TP_COORDS", "", f"Coords: {x:.1f}, {y:.1f}, {z:.1f}")
                    else:
                        p.send_message("§cTeleport failed.")
                else:
                    p.send_message("§cPlease fill all coordinate fields.")
            except Exception as e:
                self.logger.error(f"Error in TP coords: {e}")

        form = ModalForm(
            title="TP to Coordinates",
            on_submit=on_submit
        )
        form.add_control(TextInput(label="X Coordinate:", placeholder="~ or 100"))
        form.add_control(TextInput(label="Y Coordinate:", placeholder="~ or 64"))
        form.add_control(TextInput(label="Z Coordinate:", placeholder="~ or 100"))

        player.send_form(form)

    # ===========================
    # Player Management Menu
    # ===========================
    def show_player_management_menu(self, player: Player) -> None:
        """Show player management submenu"""
        is_operator = player.is_op
        
        # Build button list dynamically based on permissions
        buttons = [
            ("Temp Ban (12 Hours)", lambda p: self.show_temp_ban_menu(p)),
            ("Mute/Unmute Player", lambda p: self.show_mute_menu(p)),
            ("Freeze/Unfreeze Player", lambda p: self.show_freeze_menu(p)),
            ("View Player Inventory", lambda p: self.show_view_inventory_menu(p)),
        ]
        
        # Only operators can clear inventory
        if is_operator:
            buttons.append(("§cClear Player Inventory", lambda p: self.show_clear_inventory_menu(p)))
        
        buttons.append(("Check Player Stats", lambda p: self.show_player_stats_menu(p)))

        def on_submit(p: Player, selection: int) -> None:
            if 0 <= selection < len(buttons):
                self.server.scheduler.run_task(
                    self, lambda plr=p, idx=selection: buttons[idx][1](plr), delay=1
                )

        form = ActionForm(
            title="§cPlayer Management",
            content="Select an action:",
            on_submit=on_submit
        )
        for btn_name, _ in buttons:
            form.add_button(btn_name)

        player.send_form(form)

    def show_temp_ban_menu(self, player: Player) -> None:
        """Show temporary ban menu"""
        online_players = self._get_visible_players(player)
        
        if not online_players:
            player.send_message("§cNo players to ban.")
            return

        player_names = [p.name for p in online_players]
        durations = ["5 minutes", "15 minutes", "30 minutes", "1 hour", "6 hours", "12 hours", "24 hours", "7 days"]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 3:
                    selected_index = values[0]
                    duration_index = values[1]
                    reason = values[2] or "No reason provided"
                    
                    if 0 <= selected_index < len(online_players):
                        target = online_players[selected_index]
                        duration = durations[duration_index]
                        # Kick the player with ban message (actual ban requires external plugin)
                        console = self.server.command_sender
                        self.server.dispatch_command(console, f'kick "{target.name}" §cYou have been temporarily banned for {duration}. Reason: {reason}')
                        p.send_message(f"§aTemp banned §e{target.name}§a for {duration}. Reason: {reason}")
                        p.send_message("§7Note: Persistent bans require a ban management plugin.")
                        self.log_admin_action(p.name, "TEMP_BAN", target.name, f"Duration: {duration}, Reason: {reason}")
            except Exception as e:
                self.logger.error(f"Error in temp ban menu: {e}")

        form = ModalForm(title="Temp Ban Player", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        form.add_control(Dropdown(label="Duration:", options=durations, default_index=5))
        form.add_control(TextInput(label="Reason:", placeholder="Enter reason..."))
        player.send_form(form)

    def show_mute_menu(self, player: Player) -> None:
        """Show mute/unmute menu"""
        online_players = self._get_visible_players(player)
        
        if not online_players:
            player.send_message("§cNo players available.")
            return

        player_names = []
        for p in online_players:
            status = "§c[MUTED]" if p.name in self.muted_players else "§a[OK]"
            player_names.append(f"{p.name} {status}")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(online_players):
                        target = online_players[selected_index]
                        if target.name in self.muted_players:
                            self.muted_players.discard(target.name)
                            p.send_message(f"§aUnmuted §e{target.name}")
                            target.send_message("§aYou have been unmuted.")
                            self.log_admin_action(p.name, "UNMUTE", target.name)
                        else:
                            self.muted_players.add(target.name)
                            p.send_message(f"§cMuted §e{target.name}")
                            target.send_message("§cYou have been muted by an admin.")
                            self.log_admin_action(p.name, "MUTE", target.name)
            except Exception as e:
                self.logger.error(f"Error in mute menu: {e}")

        form = ModalForm(title="Mute/Unmute Player", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player (click to toggle):", options=player_names, default_index=0))
        player.send_form(form)

    def show_freeze_menu(self, player: Player) -> None:
        """Show freeze/unfreeze menu"""
        online_players = self._get_visible_players(player)
        
        if not online_players:
            player.send_message("§cNo players available.")
            return

        player_names = []
        for p in online_players:
            status = "§c[FROZEN]" if p.name in self.frozen_players else "§a[OK]"
            player_names.append(f"{p.name} {status}")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(online_players):
                        target = online_players[selected_index]
                        console = self.server.command_sender
                        if target.name in self.frozen_players:
                            self.frozen_players.discard(target.name)
                            # Remove slowness effect
                            self.server.dispatch_command(console, f'effect "{target.name}" clear slowness')
                            self.server.dispatch_command(console, f'effect "{target.name}" clear mining_fatigue')
                            self.server.dispatch_command(console, f'effect "{target.name}" clear jump_boost')
                            p.send_message(f"§aUnfroze §e{target.name}")
                            target.send_message("§aYou have been unfrozen.")
                            self.log_admin_action(p.name, "MOD_UNFREEZE", target.name)
                        else:
                            self.frozen_players.add(target.name)
                            # Apply slowness, mining fatigue, and negative jump boost
                            self.server.dispatch_command(console, f'effect "{target.name}" slowness 999999 255 true')
                            self.server.dispatch_command(console, f'effect "{target.name}" mining_fatigue 999999 255 true')
                            self.server.dispatch_command(console, f'effect "{target.name}" jump_boost 999999 250 true')
                            p.send_message(f"§cFroze §e{target.name}")
                            target.send_message("§cYou have been frozen by an admin. Do not log out.")
                            self.log_admin_action(p.name, "MOD_FREEZE", target.name)
            except Exception as e:
                self.logger.error(f"Error in freeze menu: {e}")

        form = ModalForm(title="Freeze/Unfreeze Player", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player (click to toggle):", options=player_names, default_index=0))
        player.send_form(form)

    def show_view_inventory_menu(self, player: Player) -> None:
        """Show view inventory menu"""
        online_players = self._get_visible_players(player)
        
        if not online_players:
            player.send_message("§cNo other players online.")
            return

        player_names = [p.name for p in online_players]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(online_players):
                        target = online_players[selected_index]
                        try:
                            inv = target.inventory
                            items = []
                            for i in range(inv.size):
                                item = inv.get_item(i)
                                if item and item.type:
                                    items.append(f"§7[{i}] §f{item.type} x{item.amount}")
                            
                            if items:
                                p.send_message(f"§6=== {target.name}'s Inventory ===")
                                for item_str in items[:20]:  # Limit to 20 items
                                    p.send_message(item_str)
                                if len(items) > 20:
                                    p.send_message(f"§7... and {len(items) - 20} more items")
                            else:
                                p.send_message(f"§e{target.name}'s inventory is empty.")
                        except Exception as e:
                            p.send_message(f"§cCouldn't read inventory: {e}")
            except Exception as e:
                self.logger.error(f"Error in view inventory: {e}")

        form = ModalForm(title="View Player Inventory", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        player.send_form(form)

    def show_clear_inventory_menu(self, player: Player) -> None:
        """Show clear inventory menu"""
        online_players = self._get_visible_players(player)
        
        if not online_players:
            player.send_message("§cNo players available.")
            return

        player_names = [p.name for p in online_players]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(online_players):
                        target = online_players[selected_index]
                        console = self.server.command_sender
                        self.server.dispatch_command(console, f"clear {target.name}")
                        p.send_message(f"§aCleared §e{target.name}'s §ainventory.")
                        target.send_message("§cYour inventory has been cleared by an admin.")
                        self.log_admin_action(p.name, "CLEAR_INVENTORY", target.name)
            except Exception as e:
                self.logger.error(f"Error in clear inventory: {e}")

        form = ModalForm(title="Clear Player Inventory", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        player.send_form(form)

    def show_player_stats_menu(self, player: Player) -> None:
        """Show player stats menu"""
        online_players = self._get_visible_players(player, exclude_self=False)
        
        if not online_players:
            player.send_message("§cNo players online.")
            return

        player_names = [p.name for p in online_players]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(online_players):
                        target = online_players[selected_index]
                        loc = target.location
                        
                        p.send_message(f"§6=== {target.name}'s Stats ===")
                        p.send_message(f"§7Position: §f{int(loc.x)}, {int(loc.y)}, {int(loc.z)}")
                        try:
                            dim_name = target.dimension.name if hasattr(target, 'dimension') and target.dimension else "Unknown"
                            p.send_message(f"§7Dimension: §f{dim_name}")
                        except:
                            pass
                        p.send_message(f"§7Game Mode: §f{target.game_mode.name}")
                        try:
                            p.send_message(f"§7Health: §c{target.health:.1f}§7/§c{target.max_health:.1f}")
                        except:
                            pass
                        
                        # Status flags
                        statuses = []
                        if target.name in self.muted_players:
                            statuses.append("§cMuted")
                        if target.name in self.frozen_players:
                            statuses.append("§bFrozen")
                        if target.name in self.vanished_players:
                            statuses.append("§7Vanished")
                        if target.name in self.godmode_players:
                            statuses.append("§eGod Mode")
                        if target.name in self.flying_players:
                            statuses.append("§aFlying")
                        
                        if statuses:
                            p.send_message(f"§7Status: {', '.join(statuses)}")
                        
                        # Tags
                        tags = list(target.scoreboard_tags)[:10]
                        if tags:
                            p.send_message(f"§7Tags: §f{', '.join(tags)}")
            except Exception as e:
                self.logger.error(f"Error in player stats: {e}")

        form = ModalForm(title="Check Player Stats", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        player.send_form(form)

    # ===========================
    # Self Toggles Menu
    # ===========================
    def show_self_toggles_menu(self, player: Player) -> None:
        """Show self toggles menu"""
        
        # Get current states for display
        vanish_status = "§aON" if player.name in self.vanished_players else "§cOFF"
        god_status = "§aON" if player.name in self.godmode_players else "§cOFF"
        fly_status = "§aON" if player.name in self.flying_players else "§cOFF"
        
        # Get current game mode for display
        current_mode = player.game_mode.name if player.game_mode else "Unknown"

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # Vanish
                self.toggle_vanish(p)
            elif selection == 1:  # God Mode
                self.toggle_godmode(p)
            elif selection == 2:  # Fly Mode
                self.toggle_fly(p)
            elif selection == 3:  # Survival Mode
                if not self._change_game_mode(p, GameMode.SURVIVAL):
                    return
                self.clear_night_vision(p)
                p.send_message("§7Game mode set to §aSurvival")
                self.log_admin_action(p.name, "GAMEMODE_SURVIVAL", p.name)
            elif selection == 4:  # Creative Mode
                if not self._change_game_mode(p, GameMode.CREATIVE):
                    return
                self.clear_night_vision(p)
                p.send_message("§7Game mode set to §eCreative")
                self.log_admin_action(p.name, "GAMEMODE_CREATIVE", p.name)
            elif selection == 5:  # Spectator Mode
                if not self.switch_to_spectator_with_nv(p):
                    return
                self.log_admin_action(p.name, "GAMEMODE_SPECTATOR", p.name)

        form = ActionForm(
            title="§bSelf Toggles",
            content=f"Current mode: §e{current_mode}§r\nToggle your admin abilities:",
            on_submit=on_submit
        )
        form.add_button(f"Vanish [{vanish_status}§r]")
        form.add_button(f"God Mode [{god_status}§r]")
        form.add_button(f"Fly Mode [{fly_status}§r]")
        form.add_button("§a⚔ Survival Mode")
        form.add_button("§e✎ Creative Mode")
        form.add_button("§7👁 Spectator Mode")

        player.send_form(form)

    def toggle_vanish(self, player: Player) -> None:
        """Toggle vanish mode"""
        console = self.server.command_sender
        if player.name in self.vanished_players:
            self.vanished_players.discard(player.name)
            self.server.dispatch_command(console, f'effect "{player.name}" clear invisibility')
            player.send_message("§7Vanish: §cOFF §7- You are now visible.")
            self.log_admin_action(player.name, "VANISH_OFF", player.name)
        else:
            # Block if in survival mode
            if player.game_mode == GameMode.SURVIVAL:
                player.send_message("§cYou cannot use Vanish in Survival mode.")
                return
            self.vanished_players.add(player.name)
            self.server.dispatch_command(console, f'effect "{player.name}" invisibility 999999 1 true')
            player.send_message("§7Vanish: §aON §7- You are now invisible.")
            self.log_admin_action(player.name, "VANISH_ON", player.name)

    def toggle_godmode(self, player: Player) -> None:
        """Toggle god mode (resistance effect)"""
        console = self.server.command_sender
        if player.name in self.godmode_players:
            self.godmode_players.discard(player.name)
            self.server.dispatch_command(console, f'effect "{player.name}" clear resistance')
            self.server.dispatch_command(console, f'effect "{player.name}" clear fire_resistance')
            player.send_message("§7God Mode: §cOFF §7- You can take damage.")
            self.log_admin_action(player.name, "GODMODE_OFF", player.name)
        else:
            # Block if in survival mode
            if player.game_mode == GameMode.SURVIVAL:
                player.send_message("§cYou cannot use God Mode in Survival mode.")
                return
            self.godmode_players.add(player.name)
            self.server.dispatch_command(console, f'effect "{player.name}" resistance 999999 255 true')
            self.server.dispatch_command(console, f'effect "{player.name}" fire_resistance 999999 1 true')
            player.send_message("§7God Mode: §aON §7- You are invincible.")
            self.log_admin_action(player.name, "GODMODE_ON", player.name)

    def toggle_fly(self, player: Player) -> None:
        """Toggle fly mode using may_fly permission"""
        console = self.server.command_sender
        if player.name in self.flying_players:
            self.flying_players.discard(player.name)
            # Remove fly ability
            self.server.dispatch_command(console, f'ability "{player.name}" mayfly false')
            player.send_message("§7Fly Mode: §cOFF")
            self.log_admin_action(player.name, "FLY_OFF", player.name)
        else:
            # Block if in survival mode
            if player.game_mode == GameMode.SURVIVAL:
                player.send_message("§cYou cannot use Fly Mode in Survival mode.")
                return
            self.flying_players.add(player.name)
            # Grant fly ability
            self.server.dispatch_command(console, f'ability "{player.name}" mayfly true')
            player.send_message("§7Fly Mode: §aON §7- Double jump to fly!")
            self.log_admin_action(player.name, "FLY_ON", player.name)

    # ===========================
    # Utilities Menu
    # ===========================
    def show_utilities_menu(self, player: Player) -> None:
        """Show utilities menu"""

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # World Spawn TP
                self.teleport_world_spawn(p)
            elif selection == 1:  # Announce
                self.server.scheduler.run_task(
                    self, lambda: self.show_announce_menu(p), delay=1
                )
            elif selection == 2:  # Give Items (Presets)
                self.server.scheduler.run_task(
                    self, lambda: self.show_give_items_menu(p), delay=1
                )
            elif selection == 3:  # Give Custom Item
                self.server.scheduler.run_task(
                    self, lambda: self.show_custom_give_menu(p), delay=1
                )
            elif selection == 4:  # Heal Player
                self.server.scheduler.run_task(
                    self, lambda: self.show_heal_menu(p), delay=1
                )
            elif selection == 5:  # Feed Player
                self.server.scheduler.run_task(
                    self, lambda: self.show_feed_menu(p), delay=1
                )
            elif selection == 6:  # Fill Area
                self.server.scheduler.run_task(
                    self, lambda: self.show_admin_fill_menu(p), delay=1
                )
            elif selection == 7:  # Replace Blocks (Presets)
                self.server.scheduler.run_task(
                    self, lambda: self.show_admin_replace_menu(p), delay=1
                )
            elif selection == 8:  # Replace Custom Blocks
                self.server.scheduler.run_task(
                    self, lambda: self.show_admin_custom_replace_menu(p), delay=1
                )
            elif selection == 9:  # Manage Admin TP Limits (operator only)
                self.server.scheduler.run_task(
                    self, lambda: self.show_manage_tp_limits_menu(p), delay=1
                )
            elif selection == 10:  # Base Check Locations (full CRUD)
                self.server.scheduler.run_task(
                    self, lambda: self.show_base_check_admin_menu(p), delay=1
                )
            elif selection == 11:  # Clear Ground Items
                self.clear_ground_items(p)
            elif selection == 12:  # Fill Radius
                self.server.scheduler.run_task(
                    self, lambda: self.show_fill_radius_menu(p), delay=1
                )
            elif selection == 13:  # Replace Radius
                self.server.scheduler.run_task(
                    self, lambda: self.show_replace_radius_menu(p), delay=1
                )
            elif selection == 14:  # Manage Mod Areas
                self.server.scheduler.run_task(
                    self, lambda: self.show_manage_mod_areas_menu(p), delay=1
                )

        form = ActionForm(
            title="§aUtilities",
            content="Select an action:",
            on_submit=on_submit
        )
        form.add_button("Teleport to World Spawn")
        form.add_button("Broadcast Announcement")
        form.add_button("Give Items (Presets)")
        form.add_button("Give Custom Item")
        form.add_button("Heal Player")
        form.add_button("Feed Player")
        form.add_button("§6Fill Area")
        form.add_button("§6Replace (Presets)")
        form.add_button("§6Replace Custom Blocks")
        form.add_button("§eManage Admin TP Limits")
        form.add_button("§eBase Check Locations")
        form.add_button("§cClear Ground Items")
        form.add_button("§6Fill Radius")
        form.add_button("§6Replace Radius")
        form.add_button("§eManage Mod Areas")

        player.send_form(form)

    def teleport_world_spawn(self, player: Player) -> None:
        """Teleport to world spawn"""
        console = self.server.command_sender
        self.server.dispatch_command(console, f'tp "{player.name}" 438 97 757')  # Default spawn area
        # Alternative: use spreadplayers or spawnpoint
        player.send_message("§aTeleported to world spawn area.")


    def show_announce_menu(self, player: Player) -> None:
        """Show announcement menu"""

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    message = values[0]
                    if message:
                        console = self.server.command_sender
                        # Broadcast to all players
                        self.server.dispatch_command(console, f"say §6[Announcement] §f{message}")
                        p.send_message("§aAnnouncement sent!")
                    else:
                        p.send_message("§cMessage cannot be empty.")
            except Exception as e:
                self.logger.error(f"Error in announce: {e}")

        form = ModalForm(title="Broadcast Announcement", on_submit=on_submit)
        form.add_control(TextInput(label="Message:", placeholder="Enter your announcement..."))
        player.send_form(form)

    def clear_ground_items(self, player: Player) -> None:
        """Clear all dropped items on the ground with countdown warnings"""
        if self._item_clear_pending:
            player.send_message("§cAn item clear is already in progress!")
            return

        self._item_clear_pending = True
        console = self.server.command_sender

        # Broadcast 30-second warning
        self.server.dispatch_command(console, "say §c[Server] §fItems clearing in 30 seconds!")
        player.send_message("§aItem clear initiated. Items will be cleared in 30 seconds.")
        self.log_admin_action(player.name, "CLEAR_ITEMS", "", "Initiated ground item clear (30s countdown)")

        # 25 seconds later (500 ticks) – broadcast 5-second warning
        def warn_5s():
            self.server.dispatch_command(console, "say §c[Server] §fItems clearing in 5 seconds!")

        self.server.scheduler.run_task(self, warn_5s, delay=500)

        # 30 seconds later (600 ticks) – kill items and reset flag
        def do_clear():
            self.server.dispatch_command(console, "kill @e[type=item]")
            self.server.dispatch_command(console, "say §a[Server] §fGround items have been cleared!")
            self._item_clear_pending = False

        self.server.scheduler.run_task(self, do_clear, delay=600)

    def show_fill_radius_menu(self, player: Player) -> None:
        """Show fill radius menu - fills a cube around the player's position"""
        # Max radius where (2r+1)^3 <= 32768 is r=15 (volume=29791)
        radius_options = [str(r) for r in range(2, 16)]  # "2" through "15"

        block_options = [
            "deepslate", "stone", "cobblestone", "dirt", "grass_block",
            "oak_planks", "spruce_planks", "birch_planks", "glass", "sand",
            "gravel", "iron_block", "gold_block", "diamond_block", "obsidian",
            "bedrock", "air", "water", "lava", "netherrack"
        ]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if not isinstance(values, list) or len(values) < 3:
                    p.send_message("§cAll fields must be filled in.")
                    return

                radius_index = int(values[0]) if values[0] is not None else 0
                block_index = int(values[1]) if values[1] is not None else 0
                custom_block = str(values[2]).strip() if values[2] else ""

                radius = int(radius_options[radius_index]) if 0 <= radius_index < len(radius_options) else 2

                # Custom block overrides dropdown
                if custom_block:
                    block_type = custom_block
                else:
                    block_type = block_options[block_index] if 0 <= block_index < len(block_options) else "deepslate"

                loc = p.location
                cx, cy, cz = int(loc.x), int(loc.y), int(loc.z)

                x1, x2 = cx - radius, cx + radius
                y1, y2 = cy - radius, cy + radius
                z1, z2 = cz - radius, cz + radius

                # Get dimension Y limits and clamp
                try:
                    dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                except:
                    dim_name = "overworld"
                min_y, max_y = self.get_dimension_y_limits(dim_name)
                y1 = max(min_y, y1)
                y2 = min(max_y, y2)

                volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)

                console = self.server.command_sender
                command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block_type}"
                success = self.server.dispatch_command(console, command)
                if success:
                    p.send_message(f"§aFilled radius {radius} with {block_type} ({volume:,} blocks)")
                    self.log_admin_action(p.name, "FILL_RADIUS", "", f"Radius: {radius}, Block: {block_type}, Center: ({cx},{cy},{cz}), Volume: {volume}")
                else:
                    p.send_message("§cFill command failed. Check block ID.")
                    self.log_admin_action(p.name, "FILL_RADIUS_FAILED", "", f"Radius: {radius}, Block: {block_type}, Center: ({cx},{cy},{cz})")
            except Exception as e:
                self.logger.error(f"Error in fill radius: {e}")
                self.log_admin_action(p.name, "FILL_RADIUS_FAILED", "", f"Exception: {e}")

        form = ModalForm(title="§6Fill Radius", on_submit=on_submit)
        form.add_control(Dropdown(label="Radius (blocks from center):", options=radius_options, default_index=0))
        form.add_control(Dropdown(label="Block (preset):", options=block_options, default_index=0))
        form.add_control(TextInput(label="Custom Block ID (overrides preset):", placeholder="e.g. stone_bricks"))
        player.send_form(form)

    def show_replace_radius_menu(self, player: Player) -> None:
        """Show replace radius menu - replaces blocks in a cube around the player's position"""
        radius_options = [str(r) for r in range(2, 16)]  # "2" through "15"

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if not isinstance(values, list) or len(values) < 3:
                    p.send_message("§cAll fields must be filled in.")
                    return

                radius_index = int(values[0]) if values[0] is not None else 0
                from_block = str(values[1]).strip() if values[1] else ""
                to_block = str(values[2]).strip() if values[2] else ""

                if not from_block:
                    p.send_message("§cSource block cannot be empty.")
                    return
                if not to_block:
                    p.send_message("§cReplacement block cannot be empty.")
                    return

                radius = int(radius_options[radius_index]) if 0 <= radius_index < len(radius_options) else 2

                loc = p.location
                cx, cy, cz = int(loc.x), int(loc.y), int(loc.z)

                x1, x2 = cx - radius, cx + radius
                y1, y2 = cy - radius, cy + radius
                z1, z2 = cz - radius, cz + radius

                # Get dimension Y limits and clamp
                try:
                    dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                except:
                    dim_name = "overworld"
                min_y, max_y = self.get_dimension_y_limits(dim_name)
                y1 = max(min_y, y1)
                y2 = min(max_y, y2)

                volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)

                p.send_message(f"§7Replacing §e{from_block}§7 with §a{to_block}§7 in radius {radius}...")
                console = self.server.command_sender
                command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {to_block} replace {from_block}"
                success = self.server.dispatch_command(console, command)
                if success:
                    p.send_message(f"§aReplaced {from_block} with {to_block} in radius {radius} ({volume:,} blocks)")
                    self.log_admin_action(p.name, "REPLACE_RADIUS", "", f"Radius: {radius}, From: {from_block}, To: {to_block}, Center: ({cx},{cy},{cz}), Volume: {volume}")
                else:
                    p.send_message("§cReplace command failed. Check block IDs.")
                    self.log_admin_action(p.name, "REPLACE_RADIUS_FAILED", "", f"Radius: {radius}, From: {from_block}, To: {to_block}, Center: ({cx},{cy},{cz})")
            except Exception as e:
                self.logger.error(f"Error in replace radius: {e}")
                self.log_admin_action(p.name, "REPLACE_RADIUS_FAILED", "", f"Exception: {e}")

        form = ModalForm(title="§6Replace Radius", on_submit=on_submit)
        form.add_control(Dropdown(label="Radius (blocks from center):", options=radius_options, default_index=0))
        form.add_control(TextInput(label="Block to replace:", placeholder="e.g. stone"))
        form.add_control(TextInput(label="Replace with:", placeholder="e.g. glass"))
        player.send_form(form)

    def show_give_items_menu(self, player: Player) -> None:
        """Show give items menu"""
        online_players = list(self.server.online_players)
        player_names = [p.name for p in online_players]
        item_names = [item[0] for item in PRESET_ITEMS]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 2:
                    player_index = values[0]
                    item_index = values[1]
                    
                    if 0 <= player_index < len(online_players) and 0 <= item_index < len(PRESET_ITEMS):
                        target = online_players[player_index]
                        item_name, item_id = PRESET_ITEMS[item_index]
                        console = self.server.command_sender
                        
                        if isinstance(item_id, list):
                            # Multiple items (armor set)
                            for single_item in item_id:
                                self.server.dispatch_command(console, f'give "{target.name}" {single_item}')
                        else:
                            self.server.dispatch_command(console, f'give "{target.name}" {item_id}')
                        
                        p.send_message(f"§aGave §e{item_name} §ato §e{target.name}")
                        target.send_message(f"§aYou received §e{item_name} §afrom an admin.")
                        self.log_admin_action(p.name, "GIVE_PRESET", target.name, f"Item: {item_name}")
            except Exception as e:
                self.logger.error(f"Error in give items: {e}")

        form = ModalForm(title="Give Items", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        form.add_control(Dropdown(label="Select item:", options=item_names, default_index=0))
        player.send_form(form)

    def show_heal_menu(self, player: Player) -> None:
        """Show heal player menu"""
        online_players = list(self.server.online_players)
        player_names = ["§aSelf"] + [p.name for p in online_players if p.name != player.name]
        all_targets = [player] + [p for p in online_players if p.name != player.name]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(all_targets):
                        target = all_targets[selected_index]
                        console = self.server.command_sender
                        # Use instant health effect
                        self.server.dispatch_command(console, f'effect "{target.name}" instant_health 1 255')
                        self.server.dispatch_command(console, f'effect "{target.name}" regeneration 10 5')
                        
                        if target.name == p.name:
                            p.send_message("§aYou have been healed!")
                            self.log_admin_action(p.name, "HEAL", p.name, "Self-heal")
                        else:
                            p.send_message(f"§aHealed §e{target.name}")
                            target.send_message("§aYou have been healed by an admin.")
                            self.log_admin_action(p.name, "HEAL", target.name)
            except Exception as e:
                self.logger.error(f"Error in heal: {e}")

        form = ModalForm(title="Heal Player", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        player.send_form(form)

    def show_feed_menu(self, player: Player) -> None:
        """Show feed player menu"""
        online_players = list(self.server.online_players)
        player_names = ["§aSelf"] + [p.name for p in online_players if p.name != player.name]
        all_targets = [player] + [p for p in online_players if p.name != player.name]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(all_targets):
                        target = all_targets[selected_index]
                        console = self.server.command_sender
                        # Use saturation effect to restore hunger
                        self.server.dispatch_command(console, f'effect "{target.name}" saturation 1 255')
                        
                        if target.name == p.name:
                            p.send_message("§aYou have been fed!")
                            self.log_admin_action(p.name, "FEED", p.name, "Self-feed")
                        else:
                            p.send_message(f"§aFed §e{target.name}")
                            target.send_message("§aYour hunger has been restored by an admin.")
                            self.log_admin_action(p.name, "FEED", target.name)
            except Exception as e:
                self.logger.error(f"Error in feed: {e}")

        form = ModalForm(title="Feed Player", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        player.send_form(form)

    def show_custom_give_menu(self, player: Player) -> None:
        """Show custom give item menu for any item ID"""
        online_players = list(self.server.online_players)
        player_names = [p.name for p in online_players]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 3:
                    player_index = values[0]
                    item_id = str(values[1]).strip()
                    amount = str(values[2]).strip() or "1"
                    
                    if not item_id:
                        p.send_message("§cItem ID cannot be empty.")
                        return
                    
                    # Validate amount
                    try:
                        amt = int(amount)
                        if amt < 1 or amt > 64:
                            p.send_message("§cAmount must be between 1 and 64.")
                            return
                    except ValueError:
                        p.send_message("§cAmount must be a valid number.")
                        return
                    
                    if 0 <= player_index < len(online_players):
                        target = online_players[player_index]
                        
                        # Check if item is blocked
                        if item_id.lower() in BLOCKED_ITEMS:
                            p.send_message(f"§c'{item_id}' is a restricted item and cannot be given.")
                            self.log_admin_action(p.name, "BLOCKED_GIVE_ATTEMPT", target.name, f"Tried to give blocked item: {item_id}")
                            return
                        
                        console = self.server.command_sender
                        
                        # Support both namespaced (minecraft:diamond) and simple IDs (diamond)
                        success = self.server.dispatch_command(console, f'give "{target.name}" {item_id} {amount}')
                        
                        if success:
                            p.send_message(f"§aGave §e{amount}x {item_id} §ato §e{target.name}")
                            target.send_message(f"§aYou received §e{amount}x {item_id} §afrom an admin.")
                            self.log_admin_action(p.name, "GIVE_CUSTOM", target.name, f"Item: {item_id}, Amount: {amount}")
                        else:
                            p.send_message(f"§cFailed to give item. Check if '{item_id}' is a valid item ID.")
            except Exception as e:
                self.logger.error(f"Error in custom give: {e}")

        form = ModalForm(title="Give Custom Item", on_submit=on_submit)
        form.add_control(Dropdown(label="Select player:", options=player_names, default_index=0))
        form.add_control(TextInput(label="Item ID:", placeholder="e.g., diamond, netherite_sword, my_addon:custom_item"))
        form.add_control(TextInput(label="Amount (1-64):", placeholder="1", default_value="1"))
        player.send_form(form)

    def show_admin_fill_menu(self, player: Player) -> None:
        """Show the fill area menu for admins"""
        
        # Common blocks for quick selection
        fill_blocks = [
            "air", "stone", "deepslate", "cobblestone", "dirt", "grass_block",
            "oak_planks", "spruce_planks", "glass", "sand", "gravel",
            "iron_block", "gold_block", "diamond_block", "netherite_block",
            "obsidian", "crying_obsidian", "glowstone", "sea_lantern",
            "water", "lava", "barrier", "light_block"
        ]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 8:
                    x1_raw = values[0]
                    y1_raw = values[1]
                    z1_raw = values[2]
                    x2_raw = values[3]
                    y2_raw = values[4]
                    z2_raw = values[5]
                    block_index = values[6]
                    custom_block = str(values[7]).strip()
                    
                    # Determine which block to use
                    if custom_block:
                        block_type = custom_block
                    elif 0 <= block_index < len(fill_blocks):
                        block_type = fill_blocks[block_index]
                    else:
                        p.send_message("§cNo block selected.")
                        return
                    
                    if not all([x1_raw, y1_raw, z1_raw, x2_raw, y2_raw, z2_raw]):
                        p.send_message("§cAll coordinates must be filled in.")
                        return

                    # Parse coordinates
                    loc = p.location

                    def parse_coord(coord: str, base: float) -> int:
                        coord = str(coord).strip()
                        if coord.startswith("~"):
                            offset = coord[1:].strip()
                            return int(base + (int(offset) if offset else 0))
                        return int(coord)

                    try:
                        x1 = parse_coord(x1_raw, loc.x)
                        y1 = parse_coord(y1_raw, loc.y)
                        z1 = parse_coord(z1_raw, loc.z)
                        x2 = parse_coord(x2_raw, loc.x)
                        y2 = parse_coord(y2_raw, loc.y)
                        z2 = parse_coord(z2_raw, loc.z)
                    except ValueError:
                        p.send_message("§cInvalid coordinate format. Use numbers or ~ notation.")
                        return

                    # Get dimension limits and clamp Y coordinates
                    try:
                        dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                    except:
                        dim_name = "overworld"
                    
                    min_y, max_y = self.get_dimension_y_limits(dim_name)
                    
                    # Clamp Y values to world bounds
                    original_y1, original_y2 = y1, y2
                    y1 = max(min_y, min(max_y, y1))
                    y2 = max(min_y, min(max_y, y2))
                    
                    if y1 != original_y1 or y2 != original_y2:
                        p.send_message(f"§eY coordinates clamped to world limits ({min_y} to {max_y})")

                    # Auto-normalize: ensure min/max are correct (order doesn't matter)
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    z1, z2 = min(z1, z2), max(z1, z2)

                    volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)

                    if volume > FILL_VOLUME_LIMIT:
                        p.send_message(f"§cArea is too large! ({volume} blocks). Maximum is {FILL_VOLUME_LIMIT}.")
                        return

                    p.send_message(f"§7Filling area of {volume} blocks with {block_type}...")
                    try:
                        console = self.server.command_sender
                        command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block_type}"
                        success = self.server.dispatch_command(console, command)
                        if success:
                            p.send_message("§aFill executed successfully.")
                            self.log_admin_action(p.name, "ADMIN_FILL", "", f"Block: {block_type}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2}), Volume: {volume}")
                        else:
                            p.send_message("§cFailed to execute fill command. Check coordinates and block type.")
                    except Exception as err:
                        p.send_message("§cFailed to execute fill command.")
                        self.logger.warning(f"Fill command failed: {err}")

            except Exception as e:
                self.logger.error(f"Error in admin fill menu: {e}")

        form = ModalForm(title="§6Fill Area", on_submit=on_submit)
        form.add_control(TextInput(label="Start X (e.g., ~ or 100):", placeholder="~"))
        form.add_control(TextInput(label="Start Y (e.g., ~ or 64):", placeholder="~"))
        form.add_control(TextInput(label="Start Z (e.g., ~ or 100):", placeholder="~"))
        form.add_control(TextInput(label="End X (e.g., ~10 or 110):", placeholder="~10"))
        form.add_control(TextInput(label="End Y (e.g., ~10 or 74):", placeholder="~10"))
        form.add_control(TextInput(label="End Z (e.g., ~10 or 110):", placeholder="~10"))
        form.add_control(Dropdown(label="Block (preset):", options=fill_blocks, default_index=0))
        form.add_control(TextInput(label="Custom block (overrides preset):", placeholder="e.g., my_addon:custom_block"))
        player.send_form(form)

    def show_admin_replace_menu(self, player: Player) -> None:
        """Show the replace blocks menu for admins"""
        
        # Common blocks for quick selection
        common_blocks = [
            "air", "stone", "deepslate", "cobblestone", "dirt", "grass_block",
            "oak_planks", "spruce_planks", "glass", "sand", "gravel",
            "iron_block", "gold_block", "diamond_block", "netherite_block",
            "obsidian", "glowstone", "sea_lantern", "water", "lava"
        ]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 10:
                    x1_raw = values[0]
                    y1_raw = values[1]
                    z1_raw = values[2]
                    x2_raw = values[3]
                    y2_raw = values[4]
                    z2_raw = values[5]
                    from_block_index = values[6]
                    from_custom = str(values[7]).strip()
                    to_block_index = values[8]
                    to_custom = str(values[9]).strip()
                    
                    # Determine source block
                    if from_custom:
                        from_block = from_custom
                    elif 0 <= from_block_index < len(common_blocks):
                        from_block = common_blocks[from_block_index]
                    else:
                        p.send_message("§cNo source block selected.")
                        return
                    
                    # Determine target block
                    if to_custom:
                        to_block = to_custom
                    elif 0 <= to_block_index < len(common_blocks):
                        to_block = common_blocks[to_block_index]
                    else:
                        p.send_message("§cNo target block selected.")
                        return
                    
                    if not all([x1_raw, y1_raw, z1_raw, x2_raw, y2_raw, z2_raw]):
                        p.send_message("§cAll coordinates must be filled in.")
                        return

                    # Parse coordinates
                    loc = p.location

                    def parse_coord(coord: str, base: float) -> int:
                        coord = str(coord).strip()
                        if coord.startswith("~"):
                            offset = coord[1:].strip()
                            return int(base + (int(offset) if offset else 0))
                        return int(coord)

                    try:
                        x1 = parse_coord(x1_raw, loc.x)
                        y1 = parse_coord(y1_raw, loc.y)
                        z1 = parse_coord(z1_raw, loc.z)
                        x2 = parse_coord(x2_raw, loc.x)
                        y2 = parse_coord(y2_raw, loc.y)
                        z2 = parse_coord(z2_raw, loc.z)
                    except ValueError:
                        p.send_message("§cInvalid coordinate format. Use numbers or ~ notation.")
                        return

                    # Get dimension limits and clamp Y coordinates
                    try:
                        dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                    except:
                        dim_name = "overworld"
                    
                    min_y, max_y = self.get_dimension_y_limits(dim_name)
                    
                    # Clamp Y values to world bounds
                    y1 = max(min_y, min(max_y, y1))
                    y2 = max(min_y, min(max_y, y2))

                    # Auto-normalize: ensure min/max are correct (order doesn't matter)
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    z1, z2 = min(z1, z2), max(z1, z2)

                    volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)

                    if volume > FILL_VOLUME_LIMIT:
                        p.send_message(f"§cArea is too large! ({volume} blocks). Maximum is {FILL_VOLUME_LIMIT}.")
                        self.log_admin_action(p.name, "ADMIN_REPLACE_FAILED", "", f"Reason: Volume too large ({volume} blocks), From: {from_block}, To: {to_block}")
                        return

                    p.send_message(f"§7Replacing {from_block} with {to_block} in {volume} blocks...")
                    try:
                        console = self.server.command_sender
                        command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {to_block} replace {from_block}"
                        success = self.server.dispatch_command(console, command)
                        if success:
                            p.send_message("§aReplace executed successfully.")
                            self.log_admin_action(p.name, "ADMIN_REPLACE", "", f"From: {from_block}, To: {to_block}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2}), Volume: {volume}")
                        else:
                            p.send_message("§cFailed to execute replace command. Check coordinates and block types.")
                            self.log_admin_action(p.name, "ADMIN_REPLACE_FAILED", "", f"Reason: Command returned false, From: {from_block}, To: {to_block}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2})")
                    except Exception as err:
                        p.send_message("§cFailed to execute replace command.")
                        self.log_admin_action(p.name, "ADMIN_REPLACE_FAILED", "", f"Reason: Exception - {err}, From: {from_block}, To: {to_block}")
                        self.logger.warning(f"Replace command failed: {err}")

            except Exception as e:
                self.logger.error(f"Error in admin replace menu: {e}")

        form = ModalForm(title="§6Replace (Presets)", on_submit=on_submit)
        form.add_control(TextInput(label="Start X:", placeholder="~"))
        form.add_control(TextInput(label="Start Y:", placeholder="~"))
        form.add_control(TextInput(label="Start Z:", placeholder="~"))
        form.add_control(TextInput(label="End X:", placeholder="~10"))
        form.add_control(TextInput(label="End Y:", placeholder="~10"))
        form.add_control(TextInput(label="End Z:", placeholder="~10"))
        form.add_control(Dropdown(label="Replace FROM (preset):", options=common_blocks, default_index=0))
        form.add_control(TextInput(label="Replace FROM (custom, overrides preset):", placeholder="e.g., stone"))
        form.add_control(Dropdown(label="Replace TO (preset):", options=common_blocks, default_index=1))
        form.add_control(TextInput(label="Replace TO (custom, overrides preset):", placeholder="e.g., diamond_block"))
        player.send_form(form)

    def show_admin_custom_replace_menu(self, player: Player) -> None:
        """Show the custom replace blocks menu - simpler text-only version"""

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 8:
                    x1_raw = values[0]
                    y1_raw = values[1]
                    z1_raw = values[2]
                    x2_raw = values[3]
                    y2_raw = values[4]
                    z2_raw = values[5]
                    from_block = str(values[6]).strip()
                    to_block = str(values[7]).strip()
                    
                    if not from_block:
                        p.send_message("§cSource block cannot be empty.")
                        return
                    if not to_block:
                        p.send_message("§cTarget block cannot be empty.")
                        return
                    
                    if not all([x1_raw, y1_raw, z1_raw, x2_raw, y2_raw, z2_raw]):
                        p.send_message("§cAll coordinates must be filled in.")
                        return

                    # Parse coordinates
                    loc = p.location

                    def parse_coord(coord: str, base: float) -> int:
                        coord = str(coord).strip()
                        if coord.startswith("~"):
                            offset = coord[1:].strip()
                            return int(base + (int(offset) if offset else 0))
                        return int(coord)

                    try:
                        x1 = parse_coord(x1_raw, loc.x)
                        y1 = parse_coord(y1_raw, loc.y)
                        z1 = parse_coord(z1_raw, loc.z)
                        x2 = parse_coord(x2_raw, loc.x)
                        y2 = parse_coord(y2_raw, loc.y)
                        z2 = parse_coord(z2_raw, loc.z)
                    except ValueError:
                        p.send_message("§cInvalid coordinate format. Use numbers or ~ notation.")
                        return

                    # Auto-normalize: ensure min/max are correct (order doesn't matter)
                    x1, x2 = min(x1, x2), max(x1, x2)
                    z1, z2 = min(z1, z2), max(z1, z2)

                    # Get dimension limits and clamp Y coordinates
                    try:
                        dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                    except:
                        dim_name = "overworld"
                    
                    min_y, max_y = self.get_dimension_y_limits(dim_name)
                    
                    # Clamp and normalize Y values
                    y1 = max(min_y, min(max_y, y1))
                    y2 = max(min_y, min(max_y, y2))
                    y1, y2 = min(y1, y2), max(y1, y2)

                    volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)

                    if volume > FILL_VOLUME_LIMIT:
                        p.send_message(f"§cArea is too large! ({volume} blocks). Maximum is {FILL_VOLUME_LIMIT}.")
                        self.log_admin_action(p.name, "CUSTOM_REPLACE_FAILED", "", f"Reason: Volume too large ({volume} blocks), From: {from_block}, To: {to_block}")
                        return

                    p.send_message(f"§7Replacing §e{from_block}§7 with §a{to_block}§7 in {volume} blocks...")
                    try:
                        console = self.server.command_sender
                        command = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {to_block} replace {from_block}"
                        success = self.server.dispatch_command(console, command)
                        if success:
                            p.send_message("§aReplace executed successfully.")
                            self.log_admin_action(p.name, "CUSTOM_REPLACE", "", f"From: {from_block}, To: {to_block}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2}), Volume: {volume}")
                        else:
                            p.send_message("§cFailed to execute replace. Check block IDs are valid.")
                            self.log_admin_action(p.name, "CUSTOM_REPLACE_FAILED", "", f"Reason: Command returned false, From: {from_block}, To: {to_block}, Coords: ({x1},{y1},{z1}) to ({x2},{y2},{z2})")
                    except Exception as err:
                        p.send_message("§cFailed to execute replace command.")
                        self.log_admin_action(p.name, "CUSTOM_REPLACE_FAILED", "", f"Reason: Exception - {err}, From: {from_block}, To: {to_block}")
                        self.logger.warning(f"Custom replace command failed: {err}")

            except Exception as e:
                self.logger.error(f"Error in admin custom replace menu: {e}")

        form = ModalForm(title="§6Replace Custom Blocks", on_submit=on_submit)
        form.add_control(TextInput(label="Corner 1 - X:", placeholder="~"))
        form.add_control(TextInput(label="Corner 1 - Y:", placeholder="~"))
        form.add_control(TextInput(label="Corner 1 - Z:", placeholder="~"))
        form.add_control(TextInput(label="Corner 2 - X:", placeholder="~10"))
        form.add_control(TextInput(label="Corner 2 - Y:", placeholder="~10"))
        form.add_control(TextInput(label="Corner 2 - Z:", placeholder="~10"))
        form.add_control(TextInput(label="Block to REPLACE:", placeholder="e.g., stone, my_addon:custom_block"))
        form.add_control(TextInput(label="Replace WITH:", placeholder="e.g., diamond_block, my_addon:new_block"))
        player.send_form(form)

    # ===========================
    # Custom TP Locations System
    # ===========================
    def show_admin_tp_locations_menu(self, player: Player) -> None:
        """Show custom TP locations menu for admins"""
        admin_name = player.name
        
        # Get limit and current count
        limit = self.admin_tp_limits.get(admin_name, 0)  # Default 0 if not set
        locations = self.admin_tp_locations.get(admin_name, {})
        current_count = len(locations)
        
        # Build content string
        if limit == -1:
            limit_str = "§aUnlimited"
        else:
            limit_str = f"§e{current_count}§7/§e{limit}"
        
        content = f"Your TP Locations: {limit_str}\n\nManage your saved teleport locations:"

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # Add Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_add_tp_location(p), delay=1
                )
            elif selection == 1:  # Use Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_use_tp_location(p), delay=1
                )
            elif selection == 2:  # Edit Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_edit_tp_location(p), delay=1
                )
            elif selection == 3:  # Delete Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_delete_tp_location(p), delay=1
                )

        form = ActionForm(
            title="§dCustom TP Locations",
            content=content,
            on_submit=on_submit
        )
        form.add_button("§aAdd Location")
        form.add_button("§bUse Location")
        form.add_button("§eEdit Location")
        form.add_button("§cDelete Location")

        player.send_form(form)

    def show_add_tp_location(self, player: Player) -> None:
        """Show form to add a new TP location"""
        admin_name = player.name
        limit = self.admin_tp_limits.get(admin_name, 0)
        locations = self.admin_tp_locations.get(admin_name, {})
        current_count = len(locations)
        
        # Check limit (unless unlimited)
        if limit != -1 and current_count >= limit:
            player.send_message(f"§cYou have reached your TP location limit ({limit}). Delete a location first.")
            return

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    loc_name = str(values[0]).strip()
                    
                    if not loc_name:
                        p.send_message("§cLocation name cannot be empty.")
                        return
                    
                    if loc_name in self.admin_tp_locations.get(p.name, {}):
                        p.send_message(f"§cA location named '{loc_name}' already exists.")
                        return
                    
                    # Get current coordinates
                    loc = p.location
                    try:
                        dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                    except:
                        dim_name = "overworld"
                    
                    # Initialize admin's locations dict if needed
                    if p.name not in self.admin_tp_locations:
                        self.admin_tp_locations[p.name] = {}
                    
                    # Save the location
                    self.admin_tp_locations[p.name][loc_name] = {
                        "x": loc.x,
                        "y": loc.y,
                        "z": loc.z,
                        "dim": dim_name
                    }
                    self._save_custom_tp_data()
                    
                    p.send_message(f"§aSaved location '§e{loc_name}§a' at §b{loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}")
                    self.log_admin_action(p.name, "ADD_TP_LOCATION", "", f"Name: {loc_name}, Coords: {loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}, Dim: {dim_name}")
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_admin_tp_locations_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error adding TP location: {e}")

        form = ModalForm(title="§aAdd TP Location", on_submit=on_submit)
        form.add_control(TextInput(label="Location Name:", placeholder="e.g., My Base, Farm, etc."))
        player.send_form(form)

    def show_use_tp_location(self, player: Player) -> None:
        """Show form to teleport to a saved location"""
        admin_name = player.name
        locations = self.admin_tp_locations.get(admin_name, {})
        
        if not locations:
            player.send_message("§cYou have no saved TP locations.")
            return
        
        loc_names = list(locations.keys())
        loc_options = []
        for name in loc_names:
            loc = locations[name]
            loc_options.append(f"{name} §7({loc['x']:.0f}, {loc['y']:.0f}, {loc['z']:.0f})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(loc_names):
                        loc_name = loc_names[selected_index]
                        loc = self.admin_tp_locations.get(p.name, {}).get(loc_name)
                        
                        if loc:
                            console = self.server.command_sender
                            success = self.server.dispatch_command(console, f'tp "{p.name}" {loc["x"]} {loc["y"]} {loc["z"]}')
                            if success:
                                p.send_message(f"§aTeleported to '§e{loc_name}§a'")
                                self.log_admin_action(p.name, "USE_TP_LOCATION", "", f"Name: {loc_name}, Coords: {loc['x']:.1f}, {loc['y']:.1f}, {loc['z']:.1f}")
                            else:
                                p.send_message("§cTeleport failed.")
            except Exception as e:
                self.logger.error(f"Error using TP location: {e}")

        form = ModalForm(title="§bUse TP Location", on_submit=on_submit)
        form.add_control(Dropdown(label="Select location:", options=loc_options, default_index=0))
        player.send_form(form)

    def show_edit_tp_location(self, player: Player) -> None:
        """Show form to edit a saved location"""
        admin_name = player.name
        locations = self.admin_tp_locations.get(admin_name, {})
        
        if not locations:
            player.send_message("§cYou have no saved TP locations to edit.")
            return
        
        loc_names = list(locations.keys())
        loc_options = []
        for name in loc_names:
            loc = locations[name]
            loc_options.append(f"{name} §7({loc['x']:.0f}, {loc['y']:.0f}, {loc['z']:.0f})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 3:
                    selected_index = values[0]
                    new_name = str(values[1]).strip()
                    update_coords = values[2]  # Toggle
                    
                    if 0 <= selected_index < len(loc_names):
                        old_name = loc_names[selected_index]
                        old_loc = self.admin_tp_locations.get(p.name, {}).get(old_name)
                        
                        if old_loc:
                            # Determine new name
                            final_name = new_name if new_name else old_name
                            
                            # Check if new name already exists (and it's different from old)
                            if final_name != old_name and final_name in self.admin_tp_locations.get(p.name, {}):
                                p.send_message(f"§cA location named '{final_name}' already exists.")
                                return
                            
                            # Get new coordinates if updating
                            if update_coords:
                                loc = p.location
                                try:
                                    dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                                except:
                                    dim_name = "overworld"
                                new_loc = {"x": loc.x, "y": loc.y, "z": loc.z, "dim": dim_name}
                            else:
                                new_loc = old_loc
                            
                            # Remove old entry if renamed
                            if final_name != old_name:
                                del self.admin_tp_locations[p.name][old_name]
                            
                            # Save updated location
                            self.admin_tp_locations[p.name][final_name] = new_loc
                            self._save_custom_tp_data()
                            
                            changes = []
                            if final_name != old_name:
                                changes.append(f"renamed '{old_name}' to '{final_name}'")
                            if update_coords:
                                changes.append(f"updated coords to {new_loc['x']:.1f}, {new_loc['y']:.1f}, {new_loc['z']:.1f}")
                            
                            p.send_message(f"§aLocation updated: {', '.join(changes)}")
                            self.log_admin_action(p.name, "EDIT_TP_LOCATION", "", f"Old: {old_name}, New: {final_name}, Coords: {new_loc['x']:.1f}, {new_loc['y']:.1f}, {new_loc['z']:.1f}")
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_admin_tp_locations_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error editing TP location: {e}")

        form = ModalForm(title="§eEdit TP Location", on_submit=on_submit)
        form.add_control(Dropdown(label="Select location:", options=loc_options, default_index=0))
        form.add_control(TextInput(label="New name (leave blank to keep current):", placeholder=""))
        form.add_control(Dropdown(label="Update to current coordinates?", options=["No", "Yes"], default_index=0))
        player.send_form(form)

    def show_delete_tp_location(self, player: Player) -> None:
        """Show form to delete a saved location"""
        admin_name = player.name
        locations = self.admin_tp_locations.get(admin_name, {})
        
        if not locations:
            player.send_message("§cYou have no saved TP locations to delete.")
            return
        
        loc_names = list(locations.keys())
        loc_options = []
        for name in loc_names:
            loc = locations[name]
            loc_options.append(f"{name} §7({loc['x']:.0f}, {loc['y']:.0f}, {loc['z']:.0f})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(loc_names):
                        loc_name = loc_names[selected_index]
                        loc = self.admin_tp_locations.get(p.name, {}).get(loc_name)
                        
                        if loc:
                            del self.admin_tp_locations[p.name][loc_name]
                            self._save_custom_tp_data()
                            
                            p.send_message(f"§cDeleted location '§e{loc_name}§c'")
                            self.log_admin_action(p.name, "DELETE_TP_LOCATION", "", f"Name: {loc_name}")
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_admin_tp_locations_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error deleting TP location: {e}")

        form = ModalForm(title="§cDelete TP Location", on_submit=on_submit)
        form.add_control(Dropdown(label="Select location to delete:", options=loc_options, default_index=0))
        player.send_form(form)

    def show_manage_tp_limits_menu(self, player: Player) -> None:
        """Show operator menu to manage admin TP limits"""
        if not player.is_op:
            player.send_message("§cOnly operators can manage TP limits.")
            return
        
        # Get list of online players with Admin tag
        admin_tagged = [p for p in self.server.online_players if "Admin" in p.scoreboard_tags and p.name != player.name]
        
        if not admin_tagged:
            player.send_message("§cNo admins with 'Admin' tag are online to configure.")
            return
        
        admin_names = [p.name for p in admin_tagged]
        admin_options = []
        for name in admin_names:
            current_limit = self.admin_tp_limits.get(name, 0)
            if current_limit == -1:
                limit_str = "Unlimited"
            else:
                limit_str = str(current_limit)
            admin_options.append(f"{name} §7(Limit: {limit_str})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 3:
                    selected_index = values[0]
                    limit_str = str(values[1]).strip()
                    unlimited = values[2]  # Toggle index (0=No, 1=Yes)
                    
                    if 0 <= selected_index < len(admin_names):
                        target_admin = admin_names[selected_index]
                        
                        if unlimited == 1:  # Yes = unlimited
                            self.admin_tp_limits[target_admin] = -1
                            p.send_message(f"§aSet §e{target_admin}§a's TP limit to §bUnlimited")
                            self.log_admin_action(p.name, "SET_TP_LIMIT", target_admin, "Limit: Unlimited")
                        else:
                            try:
                                limit = int(limit_str) if limit_str else 0
                                if limit < 0:
                                    limit = 0
                                self.admin_tp_limits[target_admin] = limit
                                p.send_message(f"§aSet §e{target_admin}§a's TP limit to §b{limit}")
                                self.log_admin_action(p.name, "SET_TP_LIMIT", target_admin, f"Limit: {limit}")
                            except ValueError:
                                p.send_message("§cInvalid number. Please enter a valid integer.")
                                return
                        
                        self._save_custom_tp_data()
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_utilities_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error setting TP limit: {e}")

        form = ModalForm(title="§eManage Admin TP Limits", on_submit=on_submit)
        form.add_control(Dropdown(label="Select Admin:", options=admin_options, default_index=0))
        form.add_control(TextInput(label="Number of allowed TPs:", placeholder="e.g., 5"))
        form.add_control(Dropdown(label="Unlimited?", options=["No", "Yes"], default_index=0))
        player.send_form(form)

    def show_manage_mod_areas_menu(self, player: Player) -> None:
        """Show operator menu to assign areas to mods"""
        if not player.is_op:
            player.send_message("§cOnly operators can manage Mod areas.")
            return

        # Get list of online players with Mod tag (exclude Admins)
        mod_tagged = [p for p in self.server.online_players if "Mod" in p.scoreboard_tags and "Admin" not in p.scoreboard_tags]
        mod_names = [p.name for p in mod_tagged]
        
        # Always include a "Custom/Offline Player" option
        mod_options = ["(Type offline mod name below)"] + [f"{name} [§e{self.mod_areas.get(name, 'None')}§r]" for name in mod_names]

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 3:
                    selected_index = values[0]
                    custom_name = str(values[1]).strip()
                    area_name = str(values[2]).strip()
                    
                    # Determine target mod
                    if selected_index == 0:
                        if not custom_name:
                            p.send_message("§cYou must type a mod's name if selecting the custom option.")
                            return
                        target_mod = custom_name
                    else:
                        target_mod = mod_names[selected_index - 1]
                    
                    if not area_name:
                        # Clear assignment if empty
                        if target_mod in self.mod_areas:
                            del self.mod_areas[target_mod]
                            p.send_message(f"§aRemoved area assignment for §e{target_mod}")
                            self.log_admin_action(p.name, "CLEAR_MOD_AREA", target_mod, "")
                    else:
                        self.mod_areas[target_mod] = area_name
                        p.send_message(f"§aAssigned §e{target_mod}§a to area: §b{area_name}")
                        self.log_admin_action(p.name, "SET_MOD_AREA", target_mod, f"Area: {area_name}")
                    
                    self._save_mod_areas()
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_utilities_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error setting Mod area: {e}")

        form = ModalForm(title="§eManage Mod Areas", on_submit=on_submit)
        form.add_control(Dropdown(label="Select Online Mod:", options=mod_options, default_index=0))
        form.add_control(TextInput(label="Or type Offline Mod Name:", placeholder="e.g., Player123"))
        form.add_control(TextInput(label="Assigned Area (leave blank to clear):", placeholder="e.g., Midgard"))
        player.send_form(form)

    # ===========================
    # BASE CHECK LOCATIONS SYSTEM
    # ===========================
    def show_base_check_admin_menu(self, player: Player) -> None:
        """Show base check locations admin menu (full CRUD for admins/operators)"""
        loc_count = len(self.base_check_locations)
        content = f"§7Total Locations: §e{loc_count}\n\nManage base check locations:"

        def on_submit(p: Player, selection: int) -> None:
            if selection == 0:  # Add Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_add_base_check_location(p), delay=1
                )
            elif selection == 1:  # Edit Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_edit_base_check_location(p), delay=1
                )
            elif selection == 2:  # Delete Location
                self.server.scheduler.run_task(
                    self, lambda: self.show_delete_base_check_location(p), delay=1
                )
            elif selection == 3:  # Use Location (TP)
                self.server.scheduler.run_task(
                    self, lambda: self.show_base_check_tp_menu(p), delay=1
                )

        form = ActionForm(
            title="§eBase Check Locations",
            content=content,
            on_submit=on_submit
        )
        form.add_button("§aAdd Location")
        form.add_button("§6Edit Location")
        form.add_button("§cDelete Location")
        form.add_button("§bUse Location (TP)")
        player.send_form(form)

    def show_add_base_check_location(self, player: Player) -> None:
        """Add a new base check location at current position"""
        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 2:
                    loc_name = str(values[0]).strip()
                    area_name = str(values[1]).strip()
                    
                    if not loc_name:
                        p.send_message("§cLocation name cannot be empty.")
                        return
                    
                    if loc_name in self.base_check_locations:
                        p.send_message(f"§cA location named '{loc_name}' already exists.")
                        return
                    
                    # Get current coordinates
                    loc = p.location
                    try:
                        dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                    except:
                        dim_name = "overworld"
                    
                    # Save the location
                    self.base_check_locations[loc_name] = {
                        "x": loc.x,
                        "y": loc.y,
                        "z": loc.z,
                        "dim": dim_name,
                        "area": area_name
                    }
                    self._save_base_check_locations()
                    
                    p.send_message(f"§aSaved base check location '{loc_name}' at {loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}")
                    self.log_admin_action(p.name, "ADD_BASE_CHECK_LOCATION", "", f"Name: {loc_name}, Coords: {loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}, Dim: {dim_name}")
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_base_check_admin_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error adding base check location: {e}")

        form = ModalForm(title="§aAdd Base Check Location", on_submit=on_submit)
        form.add_control(TextInput(label="Location Name:", placeholder="e.g., Player123 Base"))
        form.add_control(TextInput(label="Area Category (Optional):", placeholder="e.g., Midgard"))
        player.send_form(form)

    def show_edit_base_check_location(self, player: Player) -> None:
        """Edit an existing base check location"""
        if not self.base_check_locations:
            player.send_message("§cNo base check locations to edit.")
            return
        
        loc_names = list(self.base_check_locations.keys())
        loc_options = []
        for name in loc_names:
            loc = self.base_check_locations[name]
            area = loc.get("area", "")
            area_str = f" [§e{area}§7]" if area else ""
            loc_options.append(f"{name}{area_str} §7({loc['x']:.0f}, {loc['y']:.0f}, {loc['z']:.0f})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 4:
                    selected_index = values[0]
                    new_name = str(values[1]).strip()
                    new_area = str(values[2]).strip()
                    update_coords = values[3]  # Toggle (0=No, 1=Yes)
                    
                    if 0 <= selected_index < len(loc_names):
                        old_name = loc_names[selected_index]
                        old_loc = self.base_check_locations.get(old_name)
                        
                        if old_loc:
                            final_name = new_name if new_name else old_name
                            
                            # Check if new name already exists (and it's different from old)
                            if final_name != old_name and final_name in self.base_check_locations:
                                p.send_message(f"§cA location named '{final_name}' already exists.")
                                return
                            
                            # Get new coordinates if updating
                            if update_coords == 1:  # Yes
                                loc = p.location
                                try:
                                    dim_name = p.dimension.name if hasattr(p, 'dimension') and p.dimension else "overworld"
                                except:
                                    dim_name = "overworld"
                                new_loc_data = {"x": loc.x, "y": loc.y, "z": loc.z, "dim": dim_name}
                            else:
                                new_loc_data = dict(old_loc)
                            
                            # Always update area
                            new_loc_data["area"] = new_area

                            
                            # Remove old and add new
                            del self.base_check_locations[old_name]
                            self.base_check_locations[final_name] = new_loc_data
                            self._save_base_check_locations()
                            
                            changes = []
                            if final_name != old_name:
                                changes.append(f"Renamed to '{final_name}'")
                            if update_coords == 1:
                                changes.append(f"New coords: {new_loc_data['x']:.1f}, {new_loc_data['y']:.1f}, {new_loc_data['z']:.1f}")
                            
                            p.send_message(f"§aUpdated location: {', '.join(changes) if changes else 'No changes'}")
                            self.log_admin_action(p.name, "EDIT_BASE_CHECK_LOCATION", old_name, f"Changes: {', '.join(changes) if changes else 'None'}")
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_base_check_admin_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error editing base check location: {e}")

        form = ModalForm(title="§6Edit Base Check Location", on_submit=on_submit)
        form.add_control(Dropdown(label="Select Location:", options=loc_options, default_index=0))
        form.add_control(TextInput(label="New Name (leave empty to keep):", placeholder="New name..."))
        form.add_control(TextInput(label="Area Category (Optional):", placeholder="e.g., Midgard"))
        form.add_control(Dropdown(label="Update to current coords?", options=["No", "Yes"], default_index=0))
        player.send_form(form)

    def show_delete_base_check_location(self, player: Player) -> None:
        """Delete a base check location"""
        if not self.base_check_locations:
            player.send_message("§cNo base check locations to delete.")
            return
        
        loc_names = list(self.base_check_locations.keys())
        loc_options = []
        for name in loc_names:
            loc = self.base_check_locations[name]
            loc_options.append(f"{name} §7({loc['x']:.0f}, {loc['y']:.0f}, {loc['z']:.0f})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(loc_names):
                        loc_name = loc_names[selected_index]
                        loc = self.base_check_locations.get(loc_name)
                        
                        if loc:
                            del self.base_check_locations[loc_name]
                            self._save_base_check_locations()
                            p.send_message(f"§aDeleted location '{loc_name}'")
                            self.log_admin_action(p.name, "DELETE_BASE_CHECK_LOCATION", "", f"Deleted: {loc_name}")
                
                self.server.scheduler.run_task(
                    self, lambda plr=p: self.show_base_check_admin_menu(plr), delay=1
                )
            except Exception as e:
                self.logger.error(f"Error deleting base check location: {e}")

        form = ModalForm(title="§cDelete Base Check Location", on_submit=on_submit)
        form.add_control(Dropdown(label="Select Location to Delete:", options=loc_options, default_index=0))
        player.send_form(form)

    def show_base_check_tp_menu(self, player: Player) -> None:
        """Show base check locations TP menu with search (available to mods and admins)"""
        if not self.base_check_locations:
            player.send_message("§cNo base check locations available.")
            return
        
        def on_search_submit(p: Player, data: str) -> None:
            import json
            try:
                # Check permissions
                is_admin = p.is_op or "Admin" in p.scoreboard_tags
                is_mod = "Mod" in p.scoreboard_tags and not is_admin
                mod_area = self.mod_areas.get(p.name, "")

                # Pre-filter locations based on role
                available_locs = {}
                for name, loc in self.base_check_locations.items():
                    loc_area = loc.get("area", "")
                    if is_admin:
                        # Admins see everything
                        available_locs[name] = loc
                    elif is_mod:
                        # Mods see locations matching their area, or uncategorized locations
                        if loc_area.lower() == mod_area.lower() or not loc_area:
                            available_locs[name] = loc
                            
                if not available_locs:
                    p.send_message("§cNo base check locations found for your authorized areas.")
                    return

                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    search_term = str(values[0]).strip().lower()
                    
                    # Filter locations by search term (partial match)
                    if search_term:
                        filtered_locs = {}
                        for name, loc in available_locs.items():
                            if search_term in name.lower():
                                filtered_locs[name] = loc
                        
                        if not filtered_locs:
                            p.send_message(f"§cNo locations found matching '{search_term}'")
                            return
                    else:
                        # No search term = show all available
                        filtered_locs = available_locs
                    
                    # Show results in second form
                    self.server.scheduler.run_task(
                        self, lambda plr=p, locs=filtered_locs: self._show_base_check_results(plr, locs), delay=1
                    )
            except Exception as e:
                self.logger.error(f"Error in base check search: {e}")

        form = ModalForm(title="§bBase Check Locations", on_submit=on_search_submit)
        form.add_control(TextInput(label="Search by name (leave empty for all):", placeholder="e.g., player name..."))
        player.send_form(form)

    def _show_base_check_results(self, player: Player, filtered_locs: dict) -> None:
        """Show filtered base check location results"""
        loc_names = list(filtered_locs.keys())
        loc_options = []
        for name in loc_names:
            loc = filtered_locs[name]
            area = loc.get("area", "")
            area_str = f" [§e{area}§7]" if area else ""
            loc_options.append(f"{name}{area_str} §7({loc['x']:.0f}, {loc['y']:.0f}, {loc['z']:.0f})")

        def on_submit(p: Player, data: str) -> None:
            import json
            try:
                values = json.loads(data)
                if isinstance(values, list) and len(values) >= 1:
                    selected_index = values[0]
                    
                    if 0 <= selected_index < len(loc_names):
                        loc_name = loc_names[selected_index]
                        loc = self.base_check_locations.get(loc_name)
                        
                        if loc:
                            console = self.server.command_sender
                            success = self.server.dispatch_command(console, f'tp "{p.name}" {loc["x"]} {loc["y"]} {loc["z"]}')
                            if success:
                                p.send_message(f"§aTeleported to base check location '{loc_name}'")
                                self.log_admin_action(p.name, "USE_BASE_CHECK_LOCATION", "", f"Name: {loc_name}, Coords: {loc['x']:.1f}, {loc['y']:.1f}, {loc['z']:.1f}")
                            else:
                                p.send_message("§cTeleport failed.")
            except Exception as e:
                self.logger.error(f"Error using base check location: {e}")

        form = ModalForm(title=f"§bResults ({len(loc_names)} found)", on_submit=on_submit)
        form.add_control(Dropdown(label="Select Location to Teleport:", options=loc_options, default_index=0))
        player.send_form(form)
