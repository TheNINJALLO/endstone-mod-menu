"""Regression tests for read-only armor diagnostics and mode changes."""
import copy
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from endstone import GameMode, nbt
from endstone_mod_menu.gamemode_guard import GameModeLeadGuard, equipment_snapshot


def location(x=0, dimension="overworld"):
    return types.SimpleNamespace(x=x, y=64, z=0, dimension=types.SimpleNamespace(name=dimension))


def stack(kind="minecraft:lead", amount=1, nbt=None):
    return types.SimpleNamespace(type=kind, amount=amount, data=0, nbt=nbt)


class DroppedItem:
    type = "minecraft:item"
    is_valid = True
    def __init__(self, identity, thrower=10, item=None, x=0, dimension="overworld"):
        self.id, self.thrower = identity, thrower
        self.item_stack, self.location = item or stack(), location(x, dimension)
        self.remove = Mock()


class Player:
    id, name, unique_id = 10, "Moderator", "moderator-session"
    def __init__(self):
        self._mode = GameMode.SURVIVAL
        self.location = location()
        self.dimension = types.SimpleNamespace(actors=[])
        self.inventory = types.SimpleNamespace(contents=[None] * 36, item_in_off_hand=None)
        self.during_switch = lambda: None
        self.writes, self.blocked = 0, False
    @property
    def game_mode(self):
        return self._mode
    @game_mode.setter
    def game_mode(self, mode):
        self.writes += 1
        self.during_switch()
        if not self.blocked:
            self._mode = mode


def armor():
    root = nbt.CompoundTag({
        'ench': nbt.ListTag([nbt.CompoundTag({'id': nbt.ShortTag(7), 'lvl': nbt.ShortTag(32767)})]),
        'endstone_custom_enchants': nbt.CompoundTag({
            'revision': nbt.LongTag(12),
            'entries': nbt.ListTag([nbt.CompoundTag({'id': nbt.StringTag('ninjos:example_armor'), 'level': nbt.IntTag(4)})])
        })
    })
    item = stack('minecraft:diamond_chestplate', nbt=root)
    item.item_meta = types.SimpleNamespace(enchants={'minecraft:protection': 4}, display_name='Test Chestplate', lore=['Example Armor IV'])
    return item


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.logger, self.player = Mock(), Player()
        self.now = 0
        self.guard = GameModeLeadGuard(self.logger, clock=lambda: self.now)
    def spawn(self, actor):
        self.guard.observe_spawn(actor)
        self.player.dimension.actors.append(actor)
    def begin(self):
        self.guard.change(self.player, GameMode.SPECTATOR)
        return self.guard.recent[self.player.id]
    def report(self, entry):
        self.guard.sample(self.player, entry, final=True)
        return json.loads(self.logger.info.call_args.args[0].split(' ', 1)[1])

    def test_reports_native_and_custom_armor_ids_without_changing_them(self):
        self.player.inventory.chestplate = armor()
        before = str(self.player.inventory.chestplate.nbt)
        report = self.report(self.begin())
        piece = report['equipment_before'][0]
        self.assertEqual(piece['enchants'], [{'id': 'minecraft:protection', 'level': 4}])
        self.assertEqual(piece['raw_ench'], [{'id': 7, 'level': 32767}])
        self.assertEqual(piece['custom_enchants'], [{'id': 'ninjos:example_armor', 'level': 4}])
        self.assertEqual(piece['custom_revision'], 12)
        self.assertEqual(str(self.player.inventory.chestplate.nbt), before)

    def test_unknown_custom_markers_and_lore_are_visible(self):
        item = armor()
        item.nbt = nbt.CompoundTag({'ench': item.nbt['ench']})
        item.nbt['other_addon_marker'] = nbt.StringTag('not logged as a full dump')
        self.player.inventory.helmet = item
        report = self.report(self.begin())
        self.assertIn('other_addon_marker', report['equipment_before'][0]['nbt_keys'])
        self.assertEqual(report['equipment_before'][0]['lore'], ['Example Armor IV'])
        self.assertNotIn('not logged as a full dump', str(report))

    def test_captures_held_and_offhand_gear_as_well_as_armor(self):
        self.player.inventory.item_in_main_hand = armor()
        self.player.inventory.item_in_off_hand = armor()
        self.assertEqual({p['slot'] for p in equipment_snapshot(self.player)}, {'item_in_main_hand', 'item_in_off_hand'})

    def test_does_not_remove_any_lead_even_when_owned_and_inventory_unchanged(self):
        actor = DroppedItem(100)
        self.player.during_switch = lambda: self.spawn(actor)
        report = self.report(self.begin())
        actor.remove.assert_not_called()
        self.assertEqual(report['lead_spawns'][0]['phase'], 'native_setter')
        self.assertTrue(report['lead_inventory_unchanged'])

    def test_preserves_animal_other_player_unknown_custom_and_stacked_leads(self):
        actors = [DroppedItem(100, thrower=99), DroppedItem(101, thrower=None), DroppedItem(102, item=stack(amount=2)), DroppedItem(103, item=stack(nbt={'display':'custom'}))]
        self.player.during_switch = lambda: [self.spawn(a) for a in actors]
        self.assertEqual(len(self.report(self.begin())['lead_spawns']), 4)
        for actor in actors:
            actor.remove.assert_not_called()

    def test_existing_ground_leads_and_distant_spawns_are_excluded(self):
        actors = [DroppedItem(100), DroppedItem(101, x=30), DroppedItem(102, dimension='nether')]
        self.player.dimension.actors.append(actors[0])
        self.player.during_switch = lambda: [self.spawn(a) for a in actors[1:]]
        entry = self.begin()
        self.assertFalse(entry.leads)
        for actor in actors:
            actor.remove.assert_not_called()

    def test_observes_later_enchantment_tick_drops(self):
        entry = self.begin()
        self.now = .25
        actor = DroppedItem(100)
        self.spawn(actor)
        report = self.report(entry)
        self.assertEqual(report['lead_spawns'][0]['phase'], 'after_mode_change')
        self.assertEqual(report['lead_spawns'][0]['after_ms'], 250)
        actor.remove.assert_not_called()

    def test_expired_window_and_finished_window_do_not_collect_spawns(self):
        entry = self.begin()
        self.now = 3
        self.spawn(DroppedItem(100))
        self.assertFalse(entry.leads)
        self.guard.finish(entry, 'expired')
        self.spawn(DroppedItem(101))
        self.assertFalse(entry.leads)

    def test_inventory_drops_are_observed_never_cancelled(self):
        entry = self.begin()
        self.guard.observe_inventory_drop(self.player, stack())
        self.spawn(DroppedItem(100))
        self.assertTrue(self.report(entry)['lead_inventory_drop'])

    def test_unknown_ownership_is_reported_without_attribution(self):
        entry = self.begin()
        self.spawn(DroppedItem(100, thrower=None))
        report = self.report(entry)
        self.assertIsNone(report['lead_spawns'][0]['thrower_at_spawn'])
        self.assertIn('not proof', report['attribution'])

    def test_ownership_can_be_resolved_after_spawn_without_keeping_wrappers(self):
        entry = self.begin()
        actor = DroppedItem(100, thrower=None)
        self.spawn(actor)
        actor.thrower = 10
        self.assertEqual(self.report(entry)['lead_spawns'][0]['thrower_at_check'], 10)
        actor.remove.assert_not_called()

    def test_equipment_changes_are_recorded_during_followup(self):
        self.player.inventory.chestplate = armor()
        entry = self.begin()
        self.player.inventory.chestplate.nbt['endstone_custom_enchants']['revision'] = nbt.LongTag(13)
        report = self.report(entry)
        self.assertEqual(report['equipment_before'][0]['custom_revision'], 12)
        self.assertEqual(report['equipment_after'][0]['custom_revision'], 13)
        self.assertEqual(len(report['equipment_changes']), 1)

    def test_cancelled_or_destroyed_spawn_can_be_reported_from_copied_data(self):
        entry = self.begin()
        actor = DroppedItem(100)
        self.guard.observe_spawn(actor)
        del actor
        self.assertEqual(self.report(entry)['lead_spawns'][0]['id'], 100)

    def test_same_mode_is_not_reapplied(self):
        self.assertTrue(self.guard.change(self.player, GameMode.SURVIVAL))
        self.assertEqual(self.player.writes, 0)
        self.assertFalse(self.guard.recent)

    def test_blocked_switch_reports_failure_and_never_removes_items(self):
        self.player.blocked = True
        actor = DroppedItem(100)
        self.player.during_switch = lambda: self.spawn(actor)
        self.assertFalse(self.guard.change(self.player, GameMode.SPECTATOR))
        report = self.report(self.guard.recent[self.player.id])
        self.assertFalse(report['changed'])
        actor.remove.assert_not_called()

    def test_exception_clears_active_scope_and_retains_diagnostic(self):
        def fail():
            self.spawn(DroppedItem(100))
            raise RuntimeError('native failure')
        self.player.during_switch = fail
        with self.assertRaises(RuntimeError):
            self.begin()
        self.assertFalse(self.guard.active)
        self.assertIn(self.player.id, self.guard.recent)

    def test_superseded_watch_reports_once_and_old_timer_cannot_touch_new_watch(self):
        self.player.inventory.chestplate = armor()
        old = self.begin()
        self.guard.change(self.player, GameMode.SURVIVAL)
        new = self.guard.recent[self.player.id]
        self.guard.sample(self.player, old, final=True)
        self.assertIs(self.guard.recent[self.player.id], new)
        self.assertEqual(self.logger.info.call_count, 1)

    def test_clear_invalidates_both_current_and_late_callbacks(self):
        entry = self.begin()
        self.guard.clear()
        self.guard.sample(self.player, entry, final=True)
        self.assertFalse(self.guard.recent)
        self.logger.info.assert_not_called()

    def test_quiet_for_unenchanted_players_with_no_drops(self):
        self.guard.sample(self.player, self.begin(), final=True)
        self.logger.info.assert_not_called()

    def test_malformed_gear_does_not_prevent_mode_change(self):
        self.player.inventory.helmet = object()
        self.assertTrue(self.guard.change(self.player, GameMode.SPECTATOR))
        self.assertTrue(equipment_snapshot(self.player)[0]['unavailable'])

    def test_item_snapshot_is_bounded_and_does_not_dump_other_nbt(self):
        item = armor()
        item.item_meta.lore = ['x'*1000] * 100
        item.nbt['unrelated_private_data'] = nbt.StringTag('do not dump')
        self.player.inventory.chestplate = item
        snapshot = equipment_snapshot(self.player)
        self.assertEqual(len(snapshot[0]['lore']), 8)
        self.assertTrue(all(len(line) <= 160 for line in snapshot[0]['lore']))
        self.assertNotIn('do not dump', str(snapshot))


if __name__ == '__main__':
    unittest.main()
