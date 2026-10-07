"""The board and its rules. Pure simulation: no networking, time, or rendering."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from fractions import Fraction

from .hex import Hex, neighbor
from .species import CATALOG, SettingsError, Species

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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "species": self.species_id,
            "speed": str(self.speed),
            "settings": self.settings,
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

    Apply ``removed`` first, then ``added``, then ``changed``.
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

    def merge(self, other: Changes) -> None:
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

    def apply_to(self, cells: dict[Hex, dict]) -> None:
        """Replay onto a client-style cell map keyed by hex."""
        for hex in self._removed:
            cells.pop(hex, None)
        for hex, cell in self._added.items():
            cells[hex] = cell
        for hex, cell in self._changed.items():
            cells[hex] = cell


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
        self._next_plant_id = 1
        self._next_tip_id = 1

    # -- queries -----------------------------------------------------------

    @property
    def is_full(self) -> bool:
        return len(self.cells) >= self.max_cells

    def cells_snapshot(self) -> list[dict]:
        return [cell.to_dict() for cell in self.cells.values()]

    def tips_snapshot(self) -> list[dict]:
        return [tip.to_dict() for tip in self.tips.values()]

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
    ) -> Changes:
        species = self.catalog.get(species_id)
        if species is None:
            raise SimError("unknown_species", f"There is no species called '{species_id}'.")
        speed = parse_speed(speed)
        try:
            settings = species.validate(settings)
        except SettingsError as error:
            raise SimError("bad_settings", str(error)) from None
        if hex in self.cells:
            raise SimError("occupied", "That hex is occupied.")
        if self.is_full:
            raise SimError("board_full", "The board is full.")
        if direction is None:
            direction = self.rng.randrange(6)

        plant = Plant(self._next_plant_id, species_id, speed, owner, hex, settings, species.new_plant_state())
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

        for tip in self.tips.values():
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
            order = sorted(self.tips.values(), key=lambda tip: (tip.plant_id, tip.id))
            for tip in order:
                if tip.id in stalled or tip.progress < 1 or tip.id not in self.tips:
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
            self._remove_tips_on(plant.id, removed)
            del self.plants[plant.id]
            return changes

        removed = self._descendants(hex)
        self._remove_cells(removed, changes)
        self._remove_tips_on(plant.id, removed | {hex})
        cell.kind = STUMP
        cell.children = []
        changes.change(cell)

        species = self.catalog[plant.species_id]
        for sprout in species.on_cut(plant, hex, self):
            heading = sprout.heading % 6
            if self.can_sprout(plant, sprout.cell, heading):
                self._add_tip(plant, sprout.cell, heading, sprout.state)
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
            tip.blocked = True
            tip.progress = ONE
            return False
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
        changes.add(segment)
        if tip.last:
            self._drop_tip(tip)
        return True

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

    def _drop_tip(self, tip: Tip) -> None:
        del self.tips[tip.id]
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

    def _remove_tips_on(self, plant_id: int, hexes: set[Hex]) -> None:
        for hex in hexes:
            for tip in list(self._tips_on.get(hex, ())):
                if tip.plant_id == plant_id:
                    self._drop_tip(tip)
