"""The board and its rules. Pure simulation: no networking, time, or rendering."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from fractions import Fraction

from .hex import Hex, neighbor
from .species import CATALOG, SettingsError, Species, _roll

ROOT = "root"
SEGMENT = "segment"
STUMP = "stump"

MAX_SPEED = Fraction(10)
DEFAULT_MAX_CELLS = 100_000
ONE = Fraction(1)


class SimError(Exception):
    """A rejected action. ``code`` is stable and safe to send to clients."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Cell:
    hex: Hex
    plant_id: int
    kind: str
    parent: Hex | None
    children: list[Hex] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "q": self.hex[0],
            "r": self.hex[1],
            "plant": self.plant_id,
            "kind": self.kind,
            "parent": list(self.parent) if self.parent is not None else None,
        }


@dataclass
class Plant:
    id: int
    species_id: str
    speed: Fraction
    owner: str
    root: Hex
    # Fixed when the seed is planted. Nothing changes them afterwards.
    settings: dict | None = None
    # What the species remembers about the plant, such as which way it turns.
    state: dict = field(default_factory=dict)
    # Percent chance that a blocked tip takes another path. Fixed at planting:
    # the persistence given then, or else the species' default.
    persistence: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "species": self.species_id,
            "speed": str(self.speed),
            "settings": self.settings,
            "persistence": self.persistence,
        }


@dataclass
class Tip:
    id: int
    plant_id: int
    cell: Hex
    heading: int
    progress: Fraction = Fraction(0)
    blocked: bool = False
    # What the species remembers about this tip between hexes.
    state: dict = field(default_factory=dict)
    # Whether the tip has made its growth decision for the hex it is about to enter.
    decided: bool = False
    # Whether the tip ends once it has entered that hex.
    last: bool = False
    # Whether the tip has rolled its persistence for that hex and lost, so it waits.
    gave_up: bool = False
    # While asleep: the hexes whose emptying wakes the tip. Empty while awake.
    watching: tuple[Hex, ...] = ()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plant": self.plant_id,
            "q": self.cell[0],
            "r": self.cell[1],
            "heading": self.heading,
            "progress": str(self.progress),
            "blocked": self.blocked,
        }


class Changes:
    """What a mutation did to the cells, in a form a client can replay.

    If ``cleared`` is set, empty the board first. Then apply ``removed``,
    then ``added``, then ``changed``.
    """

    def __init__(self) -> None:
        self._added: dict[Hex, dict] = {}
        self._changed: dict[Hex, dict] = {}
        self._removed: dict[Hex, None] = {}
        self._plants: dict[int, dict] = {}
        self.full = False
        # How many times an iteration tried to move a tip that was due,
        # whether or not it moved. The measure of the loop's work.
        self.visits = 0
        # Whether the whole board was emptied. Said once, not hex by hex.
        self.cleared = False
        # For a scatter: how many seeds were asked for and how many were planted.
        self.scattered: dict | None = None
        # Tips that fell asleep, as they were then, and the ids of tips that
        # left the sleeping set, by waking or by being removed. A client
        # applies ``woke`` before ``slept``.
        self._slept: dict[int, dict] = {}
        self._woke: set[int] = set()

    def add_plant(self, plant: Plant) -> None:
        self._plants[plant.id] = plant.to_dict()

    def add(self, cell: Cell) -> None:
        self._added[cell.hex] = cell.to_dict()

    def change(self, cell: Cell) -> None:
        if cell.hex in self._added:
            self._added[cell.hex] = cell.to_dict()
        else:
            self._changed[cell.hex] = cell.to_dict()

    def remove(self, hex: Hex) -> None:
        self._added.pop(hex, None)
        self._changed.pop(hex, None)
        self._removed[hex] = None

    def sleep(self, tip: Tip) -> None:
        self._slept[tip.id] = tip.to_dict()

    def wake(self, tip_id: int) -> None:
        if tip_id in self._slept:
            # It fell asleep within these changes, so no client knows it slept.
            del self._slept[tip_id]
        else:
            self._woke.add(tip_id)

    def merge(self, other: Changes) -> None:
        if other.cleared:
            # Nothing recorded before a clear still matters.
            self._added.clear()
            self._changed.clear()
            self._removed.clear()
            self._plants.clear()
            self._slept.clear()
            self._woke.clear()
            self.cleared = True
        if other.scattered is not None:
            self.scattered = other.scattered
        for hex in other._removed:
            self.remove(hex)
        for hex, cell in other._added.items():
            self._added[hex] = cell
        for hex, cell in other._changed.items():
            if hex in self._added:
                self._added[hex] = cell
            else:
                self._changed[hex] = cell
        self._plants.update(other._plants)
        for tip_id in other._woke:
            self.wake(tip_id)
        self._slept.update(other._slept)
        self.full = self.full or other.full
        self.visits += other.visits

    @property
    def plants(self) -> list[dict]:
        """Details of the plants created by these changes."""
        return list(self._plants.values())

    @property
    def added(self) -> list[dict]:
        return list(self._added.values())

    @property
    def changed(self) -> list[dict]:
        return list(self._changed.values())

    @property
    def removed(self) -> list[list[int]]:
        return [list(hex) for hex in self._removed]

    @property
    def slept(self) -> list[dict]:
        return list(self._slept.values())

    @property
    def woke(self) -> list[int]:
        return sorted(self._woke)

    def apply_to(self, cells: dict[Hex, dict]) -> None:
        """Replay onto a client-style cell map keyed by hex."""
        if self.cleared:
            cells.clear()
        for hex in self._removed:
            cells.pop(hex, None)
        for hex, cell in self._added.items():
            cells[hex] = cell
        for hex, cell in self._changed.items():
            cells[hex] = cell


def check_persistence(value: object) -> int | None:
    """Check a persistence given at planting: None, or a whole percentage."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise SimError("bad_persistence", "Persistence must be a whole number from 0 to 100.")
    return value


def parse_speed(value: object) -> Fraction:
    """Parse a speed exactly. Accepts "0.25", "1/4", ints, and Fractions."""
    error = SimError("bad_speed", f"Speed must be a number above 0 and at most {MAX_SPEED}.")
    if isinstance(value, bool):
        raise error
    try:
        if isinstance(value, float):
            if not math.isfinite(value):
                raise error
            speed = Fraction(str(value))
        elif isinstance(value, (int, Fraction)):
            speed = Fraction(value)
        elif isinstance(value, str):
            speed = Fraction(value.strip())
        else:
            raise error
    except (ValueError, ZeroDivisionError):
        raise error from None
    if not 0 < speed <= MAX_SPEED:
        raise error
    return speed


class World:
    def __init__(
        self,
        seed: int,
        catalog: dict[str, Species] | None = None,
        max_cells: int = DEFAULT_MAX_CELLS,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.catalog = CATALOG if catalog is None else catalog
        self.max_cells = max_cells
        self.tick = 0
        self.cells: dict[Hex, Cell] = {}
        self.plants: dict[int, Plant] = {}
        self.tips: dict[int, Tip] = {}
        # Tips by the cell they sit on, kept in step with ``tips``.
        self._tips_on: dict[Hex, list[Tip]] = {}
        # Whether stuck tips sleep. Either way the game is the same; sleeping
        # tips just cost nothing until a removed cell could let them move.
        self.skip_stuck = True
        # ``tips`` split in two: tips that are worked on each iteration, and
        # sleeping ones, with the hexes they wait on.
        self._awake: dict[int, Tip] = {}
        self._sleeping: dict[int, Tip] = {}
        self._watchers: dict[Hex, set[int]] = {}
        self._next_plant_id = 1
        self._next_tip_id = 1

    # -- queries -----------------------------------------------------------

    @property
    def is_full(self) -> bool:
        return len(self.cells) >= self.max_cells

    def cells_snapshot(self) -> list[dict]:
        return [cell.to_dict() for cell in self.cells.values()]

    def tips_snapshot(self) -> list[dict]:
        """Every tip, awake or asleep."""
        return [tip.to_dict() for tip in self.tips.values()]

    def awake_snapshot(self) -> list[dict]:
        return [tip.to_dict() for tip in self._awake.values()]

    def sleeping_snapshot(self) -> list[dict]:
        return [tip.to_dict() for tip in self._sleeping.values()]

    @property
    def sleeping_count(self) -> int:
        return len(self._sleeping)

    def plants_snapshot(self) -> list[dict]:
        return [plant.to_dict() for plant in self.plants.values()]

    def can_sprout(self, plant: Plant, cell: Hex, heading: int) -> bool:
        """Whether a new tip at ``cell`` with ``heading`` has room and is not a duplicate."""
        if neighbor(cell, heading) in self.cells:
            return False
        return not any(
            tip.plant_id == plant.id and tip.heading == heading for tip in self._tips_on.get(cell, ())
        )

    # -- actions -----------------------------------------------------------

    def plant_seed(
        self,
        hex: Hex,
        species_id: str,
        speed: object,
        owner: str,
        direction: int | None = None,
        settings: object = None,
        persistence: object = None,
    ) -> Changes:
        species = self.catalog.get(species_id)
        if species is None:
            raise SimError("unknown_species", f"There is no species called '{species_id}'.")
        speed = parse_speed(speed)
        try:
            settings = species.validate(settings)
        except SettingsError as error:
            raise SimError("bad_settings", str(error)) from None
        persistence = check_persistence(persistence)
        if hex in self.cells:
            raise SimError("occupied", "That hex is occupied.")
        if self.is_full:
            raise SimError("board_full", "The board is full.")
        if direction is None:
            direction = self.rng.randrange(6)

        plant = Plant(self._next_plant_id, species_id, speed, owner, hex, settings, species.new_plant_state())
        # Read after the plant exists, since a custom plant's default is in its settings.
        plant.persistence = species.persistence_of(plant) if persistence is None else persistence
        self._next_plant_id += 1
        self.plants[plant.id] = plant
        root = Cell(hex, plant.id, ROOT, None)
        self.cells[hex] = root
        self._add_tip(plant, hex, direction % 6)

        changes = Changes()
        changes.add(root)
        changes.add_plant(plant)
        return changes

    def step(self) -> Changes:
        """Advance the board by one iteration."""
        changes = Changes()
        self.tick += 1

        for tip in self._awake.values():
            tip.progress += self.plants[tip.plant_id].speed
            if tip.decided:
                # Still waiting to enter the hex it chose, behind a cell or a
                # full board. Waiting banks no more than that one hex.
                tip.progress = min(tip.progress, ONE)

        # Tips take turns one hex at a time, earliest plant then earliest tip
        # first, so a contested hex always goes to the same tip.
        stalled: set[int] = set()
        advanced = True
        while advanced:
            advanced = False
            order = sorted(self._awake.values(), key=lambda tip: (tip.plant_id, tip.id))
            for tip in order:
                # A tip may have ended, or fallen asleep, earlier in this pass.
                if tip.id in stalled or tip.progress < 1 or tip.id not in self._awake:
                    continue
                changes.visits += 1
                if self._advance(tip, changes):
                    advanced = True
                else:
                    stalled.add(tip.id)
        return changes

    def cut(self, hex: Hex) -> Changes:
        cell = self.cells.get(hex)
        if cell is None:
            raise SimError("nothing_to_cut", "There is nothing to cut there.")
        if cell.kind == STUMP:
            raise SimError("nothing_to_cut", "A stump cannot be cut.")

        changes = Changes()
        plant = self.plants[cell.plant_id]

        if cell.kind == ROOT:
            removed = self._descendants(hex) | {hex}
            self._remove_cells(removed, changes)
            self._remove_tips_on(plant.id, removed, changes)
            del self.plants[plant.id]
            return changes

        removed = self._descendants(hex)
        self._remove_cells(removed, changes)
        self._remove_tips_on(plant.id, removed | {hex}, changes)
        cell.kind = STUMP
        cell.children = []
        changes.change(cell)

        species = self.catalog[plant.species_id]
        for sprout in species.on_cut(plant, hex, self):
            heading = sprout.heading % 6
            if self.can_sprout(plant, sprout.cell, heading):
                self._add_tip(plant, sprout.cell, heading, sprout.state)
        return changes

    def clear(self) -> Changes:
        """Remove every plant, cell, and tip.

        The iteration number, the random generator, and the id counters are
        left alone, so later plants get ids that were never used.
        """
        self.cells.clear()
        self.plants.clear()
        self.tips.clear()
        self._tips_on.clear()
        self._awake.clear()
        self._sleeping.clear()
        self._watchers.clear()
        changes = Changes()
        changes.cleared = True
        return changes

    def set_skip_stuck(self, enabled: bool) -> Changes:
        """Switch sleeping on or off. Off wakes every sleeping tip at once."""
        changes = Changes()
        self.skip_stuck = enabled
        if not enabled:
            for tip in list(self._sleeping.values()):
                self._wake(tip, changes)
        return changes

    def scatter(
        self,
        count: int,
        center: Hex,
        half_width: int,
        half_height: int,
        owner: str,
        persistence: object = None,
    ) -> Changes:
        """Plant up to ``count`` seeds of random species on random empty hexes of a region.

        The region is a rectangle as seen on screen: ``half_height`` rows above
        and below the centre, and ``half_width`` hex widths to either side. A
        hex's screen column is ``q + r / 2``, which is why rows are offset.

        Species are drawn independently from those that take no settings. If
        the region or the board has room for fewer seeds, as many as fit are
        planted. Every choice comes from the board's random generator. A given
        persistence goes to every seed; it is checked before anything is drawn,
        so a bad one plants nothing and leaves the generator alone.
        """
        persistence = check_persistence(persistence)
        free = []
        for dr in range(-half_height, half_height + 1):
            # |dq + dr / 2| <= half_width, kept in whole numbers.
            low = -((2 * half_width + dr) // 2)
            high = (2 * half_width - dr) // 2
            for dq in range(low, high + 1):
                hex = (center[0] + dq, center[1] + dr)
                if hex not in self.cells:
                    free.append(hex)

        presets = [species for species in self.catalog.values() if not species.settings]
        room = max(0, self.max_cells - len(self.cells))
        planted = min(count, len(free), room) if presets else 0
        chosen = free if planted == len(free) else sorted(self.rng.sample(free, planted))

        changes = Changes()
        for hex in chosen:
            species = self.rng.choice(presets)
            changes.merge(self.plant_seed(hex, species.id, species.default_speed, owner, persistence=persistence))
        changes.scattered = {"asked": count, "planted": planted}
        return changes

    def slice(self, hexes) -> Changes:
        """Cut along a path, in order.

        Each hex is judged when its turn comes, so a hex removed by an earlier
        cut in the same path is simply skipped. Empty hexes and stumps are
        skipped too, and roots are never cut: removing a plant takes a ``cut``.
        """
        changes = Changes()
        for hex in hexes:
            cell = self.cells.get(hex)
            if cell is not None and cell.kind == SEGMENT:
                changes.merge(self.cut(hex))
        return changes

    # -- internals ---------------------------------------------------------

    def _add_tip(self, plant: Plant, cell: Hex, heading: int, state: dict | None = None) -> Tip:
        if state is None:
            state = self.catalog[plant.species_id].new_tip_state(plant, heading)
        tip = Tip(self._next_tip_id, plant.id, cell, heading, state=state)
        self._next_tip_id += 1
        self.tips[tip.id] = tip
        self._awake[tip.id] = tip
        self._tips_on.setdefault(cell, []).append(tip)
        return tip

    def _advance(self, tip: Tip, changes: Changes) -> bool:
        """Try to move a due tip one hex. Returns whether it moved."""
        plant = self.plants[tip.plant_id]
        if not tip.decided:
            # One decision for each hex entered. A tip that then has to wait
            # keeps it, so waiting never rolls the dice again.
            shoots = self.catalog[plant.species_id].grow(tip, plant, self)
            if not shoots:
                self._drop_tip(tip)
                return False
            own = shoots[0]
            tip.heading = own.heading % 6
            if own.state is not None:
                tip.state = own.state
            tip.last = own.last
            tip.decided = True
            for shoot in shoots[1:]:
                heading = shoot.heading % 6
                if self.can_sprout(plant, tip.cell, heading):
                    self._add_tip(plant, tip.cell, heading, shoot.state)

        target = neighbor(tip.cell, tip.heading)
        if target in self.cells:
            detour = None if self.is_full else self._detour(tip, plant)
            if detour is None:
                tip.blocked = True
                tip.progress = ONE
                if self.skip_stuck and not self.is_full:
                    self._sleep(tip, target, changes)
                return False
            tip.heading = detour
            target = neighbor(tip.cell, detour)
        if self.is_full:
            changes.full = True
            tip.progress = ONE
            return False

        segment = Cell(target, plant.id, SEGMENT, tip.cell)
        self.cells[target] = segment
        self.cells[tip.cell].children.append(target)
        self._move_tip(tip, target)
        tip.progress -= 1
        tip.blocked = False
        tip.decided = False
        tip.gave_up = False
        changes.add(segment)
        if tip.last:
            self._drop_tip(tip)
        return True

    def _detour(self, tip: Tip, plant: Plant) -> int | None:
        """The heading of another path around a blocked tip's next hex, or None to wait.

        The plant's persistence is rolled once per hex: a tip that lost the
        roll waits for that hex without rolling again. A roll is only made
        when a turn is free, so a tip with nowhere to go draws nothing. The
        tip takes the gentlest free turn: 60 degrees, else 120, never back.
        """
        if tip.gave_up:
            return None
        tiers = [
            [
                heading
                for heading in ((tip.heading - turn) % 6, (tip.heading + turn) % 6)
                if neighbor(tip.cell, heading) not in self.cells
            ]
            for turn in (1, 2)
        ]
        sides = next((tier for tier in tiers if tier), None)
        if sides is None:
            return None
        if not _roll(self, plant.persistence):
            tip.gave_up = True
            return None
        return sides[0] if len(sides) == 1 else self.rng.choice(sides)

    def _sleep(self, tip: Tip, target: Hex, changes: Changes) -> None:
        """Put a stuck tip to sleep until one of the hexes it depends on is emptied.

        Only a removed cell can let it move: its next hex freeing up, or, if
        it has not lost its roll, one of its turns. Until then each visit
        would change nothing and draw nothing, so it is skipped.
        """
        watching = [target]
        if not tip.gave_up:
            watching += [neighbor(tip.cell, (tip.heading + turn) % 6) for turn in (-1, 1, -2, 2)]
        tip.watching = tuple(watching)
        for hex in tip.watching:
            self._watchers.setdefault(hex, set()).add(tip.id)
        del self._awake[tip.id]
        self._sleeping[tip.id] = tip
        changes.sleep(tip)

    def _unwatch(self, tip: Tip) -> None:
        for hex in tip.watching:
            watchers = self._watchers[hex]
            watchers.discard(tip.id)
            if not watchers:
                del self._watchers[hex]
        tip.watching = ()

    def _wake(self, tip: Tip, changes: Changes) -> None:
        """Wake a sleeping tip. It carries on as if it had waited awake."""
        self._unwatch(tip)
        del self._sleeping[tip.id]
        self._awake[tip.id] = tip
        changes.wake(tip.id)

    def _descendants(self, hex: Hex) -> set[Hex]:
        found: set[Hex] = set()
        pending = list(self.cells[hex].children)
        while pending:
            current = pending.pop()
            found.add(current)
            pending.extend(self.cells[current].children)
        return found

    def _remove_cells(self, hexes: set[Hex], changes: Changes) -> None:
        for hex in hexes:
            del self.cells[hex]
            changes.remove(hex)
            for tip_id in list(self._watchers.get(hex, ())):
                self._wake(self._sleeping[tip_id], changes)

    def _drop_tip(self, tip: Tip, changes: Changes | None = None) -> None:
        del self.tips[tip.id]
        if tip.id in self._sleeping:
            # Only a cut removes a sleeping tip, and a cut always reports it.
            self._unwatch(tip)
            del self._sleeping[tip.id]
            changes.wake(tip.id)
        else:
            del self._awake[tip.id]
        here = self._tips_on[tip.cell]
        here.remove(tip)
        if not here:
            del self._tips_on[tip.cell]

    def _move_tip(self, tip: Tip, cell: Hex) -> None:
        here = self._tips_on[tip.cell]
        here.remove(tip)
        if not here:
            del self._tips_on[tip.cell]
        tip.cell = cell
        self._tips_on.setdefault(cell, []).append(tip)

    def _remove_tips_on(self, plant_id: int, hexes: set[Hex], changes: Changes) -> None:
        for hex in hexes:
            for tip in list(self._tips_on.get(hex, ())):
                if tip.plant_id == plant_id:
                    self._drop_tip(tip, changes)
