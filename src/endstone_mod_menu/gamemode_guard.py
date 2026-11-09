"""Observe mode changes and nearby lead spawns without changing any items."""

import json
import time
from dataclasses import dataclass, field


def is_lead(stack):
    return stack is not None and str(stack.type) in ("lead", "minecraft:lead")


def position(location):
    return (str(location.dimension.name).removeprefix("minecraft:"),
            float(location.x), float(location.y), float(location.z))


def at_origin(location, origin):
    current = position(location)
    return current[0] == origin[0] and sum((a - b) ** 2 for a, b in zip(current[1:], origin[1:])) <= 4.0


def value(tag):
    scalar = getattr(tag, "value", tag)
    if scalar is None or isinstance(scalar, (int, float, bool)):
        return scalar
    if isinstance(scalar, str):
        return scalar[:160]
    return "<non-scalar tag>"


def field_value(compound, key, default=None):
    try:
        return value(compound[key]) if key in compound else default
    except Exception:
        return default


def enchant_entries(entries, level_key):
    result = []
    for entry in entries:
        if len(result) == 64:
            break
        result.append({"id": field_value(entry, "id"), "level": field_value(entry, level_key)})
    return result


def equipment_snapshot(player):
    """Read IDs/levels and custom markers, never edit or strip enchantments."""
    result = []
    for slot in ("helmet", "chestplate", "leggings", "boots", "item_in_main_hand", "item_in_off_hand"):
        try:
            item = getattr(player.inventory, slot, None)
            if item is None or str(item.type) in ("air", "minecraft:air"):
                continue
            record = {"slot": slot, "item": str(item.type), "amount": int(item.amount)}
            try:
                meta = item.item_meta
                record["enchants"] = [{"id": str(getattr(ench, "id", ench)), "level": int(level)}
                                      for ench, level in list(meta.enchants.items())[:64]]
                record["name"] = str(meta.display_name or "")[:120]
                record["lore"] = [str(line)[:160] for line in (meta.lore or [])[:8]]
            except Exception:
                record["meta_unavailable"] = True
            try:
                nbt = item.nbt
                if nbt is not None:
                    record["nbt_keys"] = [str(key)[:100] for key in list(nbt)[:32]]
                    if "ench" in nbt:
                        record["raw_ench"] = enchant_entries(nbt["ench"], "lvl")
                    if "endstone_custom_enchants" in nbt:
                        root = nbt["endstone_custom_enchants"]
                        record["custom_enchants"] = enchant_entries(root["entries"], "level") if "entries" in root else []
                        record["custom_revision"] = field_value(root, "revision")
            except Exception:
                record["nbt_unavailable"] = True
            result.append(record)
        except Exception:
            result.append({"slot": slot, "unavailable": True})
    return result


def enchanted(equipment):
    return any(piece.get("enchants") or piece.get("raw_ench") or piece.get("custom_enchants") or piece.get("lore")
               for piece in equipment)


def lead_inventory(player):
    try:
        stacks = list(player.inventory.contents) + [player.inventory.item_in_off_hand]
        return tuple((slot, int(item.amount), int(item.data), str(item.nbt))
                     for slot, item in enumerate(stacks) if is_lead(item))
    except Exception:
        return None


@dataclass
class Transition:
    player_id: int
    player_name: str
    origin: tuple
    old_mode: str
    requested_mode: str
    started: float
    deadline: float
    inventory: tuple | None
    equipment_before: list
    equipment_after: list
    completed: bool = False
    inventory_drop: bool = False
    leads: dict = field(default_factory=dict)
    equipment_changes: list = field(default_factory=list)


class GameModeLeadGuard:
    """Keep mode writes safe and gather evidence; never remove/cancel items."""
    def __init__(self, logger, clock=time.monotonic):
        self.logger, self.clock = logger, clock
        self.active, self.recent = {}, {}

    def clear(self):
        self.active.clear()
        self.recent.clear()

    def _watching(self):
        now = self.clock()
        return list(self.active.values()) + [entry for key, entry in self.recent.items()
                                            if key not in self.active and now <= entry.deadline]

    def observe_spawn(self, actor):
        watching = self._watching()
        if not watching:
            return
        try:
            if str(actor.type) not in ("item", "minecraft:item") or not is_lead(actor.item_stack):
                return
            for entry in watching:
                if len(entry.leads) < 32 and at_origin(actor.location, entry.origin):
                    # Copy scalar data only: later listeners can destroy the actor.
                    entry.leads[int(actor.id)] = {
                        "id": int(actor.id), "amount": int(actor.item_stack.amount),
                        "thrower_at_spawn": actor.thrower, "position": position(actor.location),
                        "phase": "native_setter" if entry.player_id in self.active else "after_mode_change",
                        "after_ms": round((self.clock() - entry.started) * 1000),
                    }
        except Exception as error:
            self.logger.debug(f"Could not inspect mode-switch item spawn: {error}")

    def observe_inventory_drop(self, player, item):
        if not is_lead(item):
            return
        for entry in self._watching():
            if entry.player_id == int(player.id):
                entry.inventory_drop = True

    def change(self, player, mode):
        if player.game_mode == mode:
            return True
        identity = int(player.id)
        if identity in self.active:
            self.logger.warning(f"Ignored a re-entrant game-mode change for {player.name}")
            return False
        previous = self.recent.get(identity)
        if previous is not None:
            self.finish(previous, "superseded")
        now = self.clock()
        gear = equipment_snapshot(player)
        entry = Transition(identity, player.name, position(player.location), player.game_mode.name, mode.name,
                           now, now + 2.0, lead_inventory(player), gear, gear)
        self.active[identity] = entry
        try:
            player.game_mode = mode
            entry.completed = player.game_mode == mode
            return entry.completed
        finally:
            if self.active.pop(identity, None) is entry:
                self.recent[identity] = entry

    def sample(self, player, entry, final=False):
        if self.recent.get(entry.player_id) is not entry:
            return
        try:
            gear = equipment_snapshot(player)
            if gear != entry.equipment_after:
                entry.equipment_changes.append({"after_ms": round((self.clock() - entry.started) * 1000), "equipment": gear})
            entry.equipment_after = gear
            entry.origin = position(player.location)
            # Resolve live actors by ID; never retain an event's actor wrapper.
            if entry.leads:
                for actor in player.dimension.actors:
                    record = entry.leads.get(int(actor.id))
                    if record is not None and actor.is_valid and is_lead(actor.item_stack):
                        record["thrower_at_check"] = actor.thrower
            if final:
                self.finish(entry, "sampled", lead_inventory(player))
        except Exception as error:
            self.logger.warning(f"Could not sample mode-switch equipment for {entry.player_name}: {error}")
            if final:
                self.finish(entry, "sample_failed")

    def finish(self, entry, reason, inventory_after=None):
        if self.recent.get(entry.player_id) is not entry:
            return
        self.recent.pop(entry.player_id, None)
        if not (entry.leads or enchanted(entry.equipment_before) or enchanted(entry.equipment_after)):
            return
        report = {"player": entry.player_name, "from": entry.old_mode, "requested": entry.requested_mode,
                  "changed": entry.completed, "end": reason, "equipment_before": entry.equipment_before,
                  "equipment_after": entry.equipment_after, "equipment_changes": entry.equipment_changes,
                  "lead_spawns": list(entry.leads.values()), "lead_inventory_drop": entry.inventory_drop,
                  "lead_inventory_unchanged": entry.inventory == inventory_after if inventory_after is not None else None,
                  "attribution": "Nearby spawns are observations, not proof of enchantment or player ownership"}
        self.logger.info("[ModeSwitchDiagnostics] " + json.dumps(report, ensure_ascii=True, separators=(",", ":")))
