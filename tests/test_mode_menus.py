import inspect
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from endstone import GameMode
from endstone.actor import Item
from endstone.event import ActorSpawnEvent, Event, EventPriority, PlayerDropItemEvent
from endstone_mod_menu.mod_menu import ModMenuPlugin
from endstone_mod_menu.gamemode_guard import GameModeLeadGuard
from test_gamemode_guard import Player, DroppedItem


class Harness(ModMenuPlugin):
    @property
    def server(self):
        return self.test_server

    @property
    def logger(self):
        return self.test_logger


class Form:
    def __init__(self, **kwargs):
        self.on_submit = kwargs['on_submit']
    def add_button(self, *args, **kwargs):
        pass
    def add_control(self, *args, **kwargs):
        pass


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.plugin = Harness()
        self.plugin.test_logger = Mock()
        self.plugin.test_server = types.SimpleNamespace(command_sender=object(), dispatch_command=Mock(), scheduler=Mock())
        self.plugin._gamemode_guard = GameModeLeadGuard(self.plugin.logger)
        self.plugin.log_admin_action = Mock()
        for state in ('vanished_players', 'godmode_players', 'flying_players'):
            setattr(self.plugin, state, set())
        self.player = Player()
        self.player.unique_id = 'moderator-session'
        self.player.send_message = Mock()
        self.player.send_form = Mock()
        self.player.teleport = Mock()
        self.plugin.test_server.get_player = lambda name: self.player

    def test_spawn_hook_forwards_only_during_owned_setter_scope(self):
        actor = DroppedItem(100)
        def during():
            self.plugin.on_mode_switch_item_spawn(types.SimpleNamespace(actor=actor))
            self.player.dimension.actors.append(actor)
        self.player.during_switch = during
        self.assertTrue(self.plugin.switch_to_spectator_with_nv(self.player))
        actor.remove.assert_not_called()
        self.assertEqual(self.player.game_mode, GameMode.SPECTATOR)
        self.plugin.server.dispatch_command.assert_called_once()

    def test_blocked_spectator_does_not_apply_effects_or_log_success(self):
        self.player.blocked = True
        self.assertFalse(self.plugin.switch_to_spectator_with_nv(self.player))
        self.plugin.server.dispatch_command.assert_not_called()
        self.plugin.log_admin_action.assert_not_called()

    def test_inventory_drop_observer_does_not_cancel_or_remove_real_drop(self):
        actor = DroppedItem(100)
        event = types.SimpleNamespace(player=self.player, item=actor.item_stack, cancel=Mock())
        def during():
            self.plugin.on_mode_switch_inventory_drop(event)
            self.plugin.on_mode_switch_item_spawn(types.SimpleNamespace(actor=actor))
            self.player.dimension.actors.append(actor)
        self.player.during_switch = during
        self.assertTrue(self.plugin.switch_to_spectator_with_nv(self.player))
        event.cancel.assert_not_called()
        actor.remove.assert_not_called()

    def test_survival_menu_uses_same_protection(self):
        self.player._mode = GameMode.SPECTATOR
        actor = DroppedItem(100)
        def during():
            self.plugin.on_mode_switch_item_spawn(types.SimpleNamespace(actor=actor))
            self.player.dimension.actors.append(actor)
        self.player.during_switch = during
        self.plugin.switch_to_survival_clear_nv(self.player)
        actor.remove.assert_not_called()
        self.assertEqual(self.player.game_mode, GameMode.SURVIVAL)

    def test_returning_to_survival_preserves_armor_buffs(self):
        import shlex
        effects = {'night_vision', 'resistance', 'speed', 'health_boost', 'water_breathing'}
        def dispatch(sender, command):
            parts = shlex.split(command)
            self.assertEqual(parts[:3], ['effect', self.player.name, 'clear'])
            if len(parts) == 3:
                effects.clear()
            else:
                effects.discard(parts[3])
            return True
        self.plugin.server.dispatch_command.side_effect = dispatch
        self.player._mode = GameMode.SPECTATOR
        self.plugin.switch_to_survival_clear_nv(self.player)
        self.assertEqual(effects, {'resistance', 'speed', 'health_boost', 'water_breathing'})

    def test_admin_survival_and_creative_clear_only_night_vision(self):
        with patch('endstone_mod_menu.mod_menu.ActionForm', Form):
            for selection in (3, 4):
                self.player._mode = GameMode.SPECTATOR
                self.plugin.server.dispatch_command.reset_mock()
                self.plugin.show_self_toggles_menu(self.player)
                self.player.send_form.call_args.args[0].on_submit(self.player, selection)
                self.plugin.server.dispatch_command.assert_called_once_with(
                    self.plugin.server.command_sender, f'effect "{self.player.name}" clear night_vision')

    def test_admin_self_menu_routes_every_mode_through_guard(self):
        with patch('endstone_mod_menu.mod_menu.ActionForm', Form):
            for selection, mode in ((3, GameMode.SURVIVAL), (4, GameMode.CREATIVE), (5, GameMode.SPECTATOR)):
                self.plugin._change_game_mode = Mock(return_value=True)
                self.plugin.show_self_toggles_menu(self.player)
                form = self.player.send_form.call_args.args[0]
                form.on_submit(self.player, selection)
                self.plugin._change_game_mode.assert_called_once_with(self.player, mode)

    def test_blocked_admin_spectator_is_not_logged_as_success(self):
        self.player.blocked = True
        with patch('endstone_mod_menu.mod_menu.ActionForm', Form):
            self.plugin.show_self_toggles_menu(self.player)
        self.player.send_form.call_args.args[0].on_submit(self.player, 5)
        self.plugin.log_admin_action.assert_not_called()

    def test_teleport_to_player_does_not_run_when_spectator_is_blocked(self):
        self.player.blocked = True
        with patch('endstone_mod_menu.mod_menu.ModalForm', Form):
            self.plugin._show_teleport_to_results(self.player, [types.SimpleNamespace(name='Target')])
        self.player.send_form.call_args.args[0].on_submit(self.player, '[0]')
        for call in self.plugin.server.scheduler.run_task.call_args_list:
            call.args[1]()
        self.player.teleport.assert_not_called()

    def test_disable_clears_capture_scope(self):
        self.plugin._gamemode_guard.active[10] = object()
        self.plugin.on_disable()
        self.assertFalse(self.plugin._gamemode_guard.active)

    def test_followup_samples_capture_enchanted_armor_and_late_lead(self):
        from test_gamemode_guard import armor
        self.player.inventory.chestplate = armor()
        self.plugin.switch_to_spectator_with_nv(self.player)
        actor = DroppedItem(100, thrower=None)
        self.plugin.on_mode_switch_item_spawn(types.SimpleNamespace(actor=actor))
        self.player.dimension.actors.append(actor)
        for call in self.plugin.server.scheduler.run_task.call_args_list:
            call.args[1]()
        self.assertFalse(self.plugin._gamemode_guard.recent)
        reports = [call.args[0] for call in self.plugin.logger.info.call_args_list]
        self.assertTrue(any('ninjos:example_armor' in text and 'after_mode_change' in text for text in reports))
        actor.remove.assert_not_called()

    def test_repeated_same_mode_click_does_not_multiply_pending_samples(self):
        self.plugin.switch_to_spectator_with_nv(self.player)
        pending = self.plugin.server.scheduler.run_task.call_count
        self.plugin.switch_to_spectator_with_nv(self.player)
        self.assertEqual(self.player.writes, 1)
        self.assertEqual(self.plugin.server.scheduler.run_task.call_count, pending)

    def test_followup_cannot_follow_a_reconnected_player_with_same_name(self):
        self.plugin.switch_to_spectator_with_nv(self.player)
        replacement = Player()
        replacement.unique_id = 'different-session'
        self.plugin.test_server.get_player = lambda name: replacement
        for call in self.plugin.server.scheduler.run_task.call_args_list:
            call.args[1]()
        self.assertFalse(self.plugin._gamemode_guard.recent)

    def test_disable_invalidates_pending_followups_before_server_access(self):
        self.plugin.switch_to_spectator_with_nv(self.player)
        self.plugin.on_disable()
        self.plugin.test_server.get_player = Mock(side_effect=RuntimeError('server disabled'))
        for call in self.plugin.server.scheduler.run_task.call_args_list:
            call.args[1]()
        self.plugin.test_server.get_player.assert_not_called()

    def test_failed_diagnostic_scheduling_does_not_fail_mode_change(self):
        self.plugin.server.scheduler.run_task.side_effect = RuntimeError('cannot schedule')
        self.assertTrue(self.plugin.switch_to_spectator_with_nv(self.player))
        self.assertFalse(self.plugin._gamemode_guard.recent)

    def test_real_endstone_hook_signatures_and_required_properties(self):
        for name, event_type in (('on_mode_switch_item_spawn', ActorSpawnEvent), ('on_mode_switch_inventory_drop', PlayerDropItemEvent)):
            method = getattr(ModMenuPlugin, name)
            self.assertTrue(method._is_event_handler)
            self.assertIs(list(inspect.signature(method).parameters.values())[1].annotation, event_type)
            self.assertTrue(issubclass(event_type, Event))
        for name in ('thrower', 'item_stack', 'id', 'is_valid', 'remove'):
            self.assertTrue(hasattr(Item, name), name)


if __name__ == '__main__':
    unittest.main()
