"""The board and its rules. Pure simulation: no networking, time, or rendering."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from fractions import Fraction

from .hex import Hex, neighbor
from .species import CATALOG, Species

ROOT = "root"
SEGMENT = "segment"
STUMP = "stump"

MAX_SPEED = Fraction(10)
DEFAULT_MAX_CELLS = 20_000
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


@dataclass
class Tip:
    id: int
    plant_id: int
    cell: Hex
    heading: int
    progress: Fraction = Fraction(0)
    blocked: bool = False

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
        self.full = False

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
        self.full = self.full or other.full

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

    def can_sprout(self, plant: Plant, cell: Hex, heading: int) -> bool:
        """Whether a new tip at ``cell`` with ``heading`` has room and is not a duplicate."""
        if neighbor(cell, heading) in self.cells:
            return False
        return not any(
            tip.plant_id == plant.id and tip.cell == cell and tip.heading == heading
            for tip in self.tips.values()
        )

    # -- actions -----------------------------------------------------------

    def plant_seed(
        self,
        hex: Hex,
        species_id: str,
        speed: object,
        owner: str,
        direction: int | None = None,
    ) -> Changes:
        species = self.catalog.get(species_id)
        if species is None:
            raise SimError("unknown_species", f"There is no species called '{species_id}'.")
        speed = parse_speed(speed)
        if hex in self.cells:
            raise SimError("occupied", "That hex is occupied.")
        if self.is_full:
            raise SimError("board_full", "The board is full.")
        if direction is None:
            direction = self.rng.randrange(6)

        plant = Plant(self._next_plant_id, species_id, speed, owner, hex)
        self._next_plant_id += 1
        self.plants[plant.id] = plant
        root = Cell(hex, plant.id, ROOT, None)
        self.cells[hex] = root
        self._add_tip(plant, hex, direction % 6)

        changes = Changes()
        changes.add(root)
        return changes

    def step(self) -> Changes:
        """Advance the board by one iteration."""
        changes = Changes()
        self.tick += 1

        for tip in self.tips.values():
            tip.progress += self.plants[tip.plant_id].speed
            if tip.blocked:
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
        for sprout_cell, heading in species.on_cut(plant, hex, self):
            self._add_tip(plant, sprout_cell, heading)
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

    def _add_tip(self, plant: Plant, cell: Hex, heading: int) -> Tip:
        tip = Tip(self._next_tip_id, plant.id, cell, heading)
        self._next_tip_id += 1
        self.tips[tip.id] = tip
        return tip

    def _advance(self, tip: Tip, changes: Changes) -> bool:
        """Try to move a due tip one hex. Returns whether it moved."""
        plant = self.plants[tip.plant_id]
        if not tip.blocked:
            # A blocked tip keeps its heading, so the species is not asked again.
            headings = self.catalog[plant.species_id].grow(tip, self)
            if not headings:
                del self.tips[tip.id]
                return False
            tip.heading = headings[0] % 6
            for heading in headings[1:]:
                if self.can_sprout(plant, tip.cell, heading % 6):
                    self._add_tip(plant, tip.cell, heading % 6)

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
        tip.cell = target
        tip.progress -= 1
        tip.blocked = False
        changes.add(segment)
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

    def _remove_tips_on(self, plant_id: int, hexes: set[Hex]) -> None:
        for tip in list(self.tips.values()):
            if tip.plant_id == plant_id and tip.cell in hexes:
                del self.tips[tip.id]
