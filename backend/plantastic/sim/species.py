"""Plant species: how tips grow and how a plant responds to a cut.

Rules receive the world so that species can react to their surroundings.
Any randomness a rule needs must come from ``world.rng``, and a rule must draw
the same number of values on every replay.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING

from .hex import Hex, direction_between, turn_left, turn_right

if TYPE_CHECKING:
    from .world import Plant, Tip, World


class SettingsError(ValueError):
    """Settings a species cannot accept. The message is safe to show to players."""


@dataclass(frozen=True)
class Shoot:
    """One result of a tip's growth decision.

    The first shoot of a decision is the tip itself: its heading, its new
    state when given, and ``last`` to remove the tip right after it enters its
    next hex. Further shoots are new tips on the same cell.
    """

    heading: int
    state: dict | None = None
    last: bool = False


@dataclass(frozen=True)
class Sprout:
    """A new tip created by a cut response. Without a state it starts fresh."""

    cell: Hex
    heading: int
    state: dict | None = None


@dataclass(frozen=True)
class Setting:
    """One value a player chooses when planting. Sent to clients to build the form."""

    id: str
    label: str
    kind: str  # "percent", "int", "optional_int" (None allowed), or "choice"
    min: int | None = None
    max: int | None = None
    default: object = None
    choices: tuple[tuple[str, str], ...] = ()  # (id, label) pairs

    def describe(self) -> dict:
        description = {"id": self.id, "label": self.label, "kind": self.kind, "default": self.default}
        if self.kind == "choice":
            description["choices"] = [{"id": id, "label": label} for id, label in self.choices]
        else:
            description["min"] = self.min
            description["max"] = self.max
        return description

    def check(self, value: object) -> None:
        if self.kind == "choice":
            if not isinstance(value, str) or value not in {id for id, _ in self.choices}:
                options = ", ".join(id for id, _ in self.choices)
                raise SettingsError(f"{self.label} must be one of: {options}.")
            return
        if value is None and self.kind == "optional_int":
            return
        if isinstance(value, bool) or not isinstance(value, int):
            raise SettingsError(f"{self.label} must be a whole number.")
        if not self.min <= value <= self.max:
            raise SettingsError(f"{self.label} must be from {self.min} to {self.max}.")


# -- cut responses -----------------------------------------------------------


def _behind(world: World, stump: Hex) -> Hex:
    """The cell behind a stump, toward the root. A stump is never a root, so it exists."""
    return world.cells[stump].parent


def _fork_at(plant: Plant, world: World, cell: Hex, toward: Hex) -> list[Sprout]:
    """Forward-left and forward-right of the way ``cell`` leads to ``toward``, where there is room."""
    forward = direction_between(cell, toward)
    return [
        Sprout(cell, heading)
        for heading in (turn_left(forward), turn_right(forward))
        if world.can_sprout(plant, cell, heading)
    ]


def fork(plant: Plant, stump: Hex, world: World) -> list[Sprout]:
    """Two tips from the cell two back from the stump, or from the root if it is nearer."""
    sprout = stump
    toward_stump = stump
    for _ in range(2):
        parent = world.cells[sprout].parent
        if parent is None:
            break
        toward_stump = sprout
        sprout = parent
    return _fork_at(plant, world, sprout, toward_stump)


def regrow(plant: Plant, stump: Hex, world: World) -> list[Sprout]:
    """One tip from the cell behind the stump, into a random empty neighbour."""
    cell = _behind(world, stump)
    free = [heading for heading in range(6) if world.can_sprout(plant, cell, heading)]
    if not free:
        return []
    return [Sprout(cell, world.rng.choice(free))]


def no_response(plant: Plant, stump: Hex, world: World) -> list[Sprout]:
    return []


def multiply(plant: Plant, stump: Hex, world: World) -> list[Sprout]:
    """Forks from both of the two cells behind the stump."""
    first = _behind(world, stump)
    sprouts = _fork_at(plant, world, first, stump)
    second = world.cells[first].parent
    if second is not None:
        sprouts += _fork_at(plant, world, second, first)
    return sprouts


CUT_RESPONSES = {"fork": fork, "regrow": regrow, "none": no_response, "multiply": multiply}


# -- species -----------------------------------------------------------------


class Species:
    """A straight grower that forks when cut, unless a subclass says otherwise."""

    id: str
    name: str
    default_speed = Fraction(1)
    settings: tuple[Setting, ...] = ()

    def validate(self, raw: object) -> dict | None:
        """Check the settings a seed was planted with and return them, or raise SettingsError."""
        if not self.settings:
            if raw is not None:
                raise SettingsError(f"{self.name} has no settings.")
            return None
        if not isinstance(raw, dict):
            raise SettingsError(f"{self.name} needs settings.")
        known = {setting.id for setting in self.settings}
        unknown = sorted(str(key) for key in raw if key not in known)
        if unknown:
            raise SettingsError(f"Unknown setting: {unknown[0]}.")
        for setting in self.settings:
            if setting.id not in raw:
                raise SettingsError(f"{setting.label} is missing.")
            setting.check(raw[setting.id])
        return {setting.id: raw[setting.id] for setting in self.settings}

    def new_plant_state(self) -> dict:
        """What the species remembers about a whole plant."""
        return {}

    def new_tip_state(self, plant: Plant, heading: int) -> dict:
        """What a new tip remembers: the seed's tip, and any shoot or sprout without its own state."""
        return {}

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        """Decide a tip's next step. Called once for each hex the tip enters.

        An empty list ends the tip.
        """
        return [Shoot(tip.heading)]

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[Sprout]:
        """New tips to create after a cut."""
        return fork(plant, stump, world)


class StraightVine(Species):
    id = "straight-vine"
    name = "Straight vine"


class _Handed(Species):
    """A species whose tips turn to one side, and whose side flips with every cut."""

    def new_plant_state(self) -> dict:
        return {"hand": 1}  # 1 turns right, -1 turns left

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[Sprout]:
        plant.state["hand"] = -plant.state["hand"]
        cell = _behind(world, stump)
        heading = (direction_between(cell, stump) + plant.state["hand"]) % 6
        if not world.can_sprout(plant, cell, heading):
            return []
        return [Sprout(cell, heading)]


class Zigzag(_Handed):
    id = "zigzag"
    name = "Zigzag"

    def new_tip_state(self, plant: Plant, heading: int) -> dict:
        return {"base": heading, "hand": plant.state["hand"], "step": 0}

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        state = tip.state
        heading = state["base"] if state["step"] % 2 == 0 else state["base"] + state["hand"]
        return [Shoot(heading % 6, {**state, "step": state["step"] + 1})]


class Spiral(_Handed):
    id = "spiral"
    name = "Spiral"

    def new_tip_state(self, plant: Plant, heading: int) -> dict:
        return {"hand": plant.state["hand"], "run": 1, "left": 1, "turns": 0}

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        state = dict(tip.state)
        heading = tip.heading
        if state["left"] == 0:
            # Runs go 1, 1, 2, 2, 3, 3: one cell longer after every second turn.
            heading = (heading + state["hand"]) % 6
            state["turns"] += 1
            if state["turns"] % 2 == 0:
                state["run"] += 1
            state["left"] = state["run"]
        state["left"] -= 1
        return [Shoot(heading, state)]


class Fern(Species):
    id = "fern"
    name = "Fern"

    BRANCH_EVERY = 3
    BRANCH_LENGTH = 3

    def new_tip_state(self, plant: Plant, heading: int) -> dict:
        return {"stem": 0}  # cells of stem grown so far

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        if "life" in tip.state:
            life = tip.state["life"]
            return [Shoot(tip.heading, {"life": life - 1}, last=life == 1)]
        grown = tip.state["stem"]
        shoots = [Shoot(tip.heading, {"stem": grown + 1})]
        if grown and grown % self.BRANCH_EVERY == 0:
            left_side = (grown // self.BRANCH_EVERY) % 2 == 1
            side = turn_left(tip.heading) if left_side else turn_right(tip.heading)
            shoots.append(Shoot(side, {"life": self.BRANCH_LENGTH}))
        return shoots

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[Sprout]:
        return no_response(plant, stump, world)


class Wanderer(Species):
    id = "wanderer"
    name = "Wanderer"

    TURN_CHANCE = 20  # percent

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        heading = tip.heading
        if world.rng.randrange(100) < self.TURN_CHANCE:
            heading = (heading + world.rng.choice((-1, 1))) % 6
        return [Shoot(heading)]

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[Sprout]:
        return regrow(plant, stump, world)


class Hydra(Species):
    id = "hydra"
    name = "Hydra"

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[Sprout]:
        return multiply(plant, stump, world)


class Burst(Species):
    id = "burst"
    name = "Burst"

    FAN_EVERY = 4

    def new_tip_state(self, plant: Plant, heading: int) -> dict:
        return {"arm": 0}  # cells grown since the last fan

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        grown = tip.state["arm"]
        if grown < self.FAN_EVERY:
            return [Shoot(tip.heading, {"arm": grown + 1})]
        return [
            Shoot(tip.heading, {"arm": 1}),
            Shoot(turn_left(tip.heading), {"arm": 0}),
            Shoot(turn_right(tip.heading), {"arm": 0}),
        ]


def _roll(world: World, percent: int) -> bool:
    """A chance roll. Certain outcomes draw nothing, so they never shift later rolls."""
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    return world.rng.randrange(100) < percent


class Custom(Species):
    """A plant whose growth is set by the player when it is planted."""

    id = "custom"
    name = "Custom"
    settings = (
        Setting("branch_chance", "Branch chance %", "percent", 0, 100, 10),
        Setting("branch_min", "Branches min", "int", 1, 4, 1),
        Setting("branch_max", "Branches max", "int", 1, 4, 1),
        Setting("calm_min", "Calm stretch min", "int", 0, 1000, 2),
        Setting("calm_max", "Calm stretch max", "optional_int", 0, 1000, None),
        Setting("turn_chance", "Turn chance %", "percent", 0, 100, 10),
        Setting(
            "cut_response",
            "When cut",
            "choice",
            default="fork",
            choices=(("fork", "Fork"), ("regrow", "Regrow"), ("none", "Nothing"), ("multiply", "Multiply")),
        ),
    )

    def validate(self, raw: object) -> dict | None:
        settings = super().validate(raw)
        if settings["branch_min"] > settings["branch_max"]:
            raise SettingsError("Branches min cannot be above branches max.")
        if settings["calm_max"] is not None and settings["calm_max"] < settings["calm_min"]:
            raise SettingsError("Calm stretch max cannot be below calm stretch min.")
        return settings

    def new_tip_state(self, plant: Plant, heading: int) -> dict:
        return {"calm": 0}  # hexes entered since the last branch or turn

    def grow(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        settings = plant.settings
        calm = tip.state["calm"]
        event = self._event(settings, calm, world)
        if event == "turn":
            heading = (tip.heading + world.rng.choice((-1, 1))) % 6
            return [Shoot(heading, {"calm": 0})]
        if event == "branch":
            return [Shoot(tip.heading, {"calm": 0}), *self._branches(tip, plant, world)]
        return [Shoot(tip.heading, {"calm": calm + 1})]

    def _event(self, settings: dict, calm: int, world: World) -> str | None:
        branch, turn = settings["branch_chance"], settings["turn_chance"]
        if calm < settings["calm_min"]:
            return None
        if settings["calm_max"] is not None and calm >= settings["calm_max"]:
            # Something has to happen: a branch or a turn, in proportion to their chances.
            if branch == 0:
                return "turn"
            if turn == 0:
                return "branch"
            return "branch" if world.rng.randrange(branch + turn) < branch else "turn"
        if _roll(world, branch):
            return "branch"
        if _roll(world, turn):
            return "turn"
        return None

    def _branches(self, tip: Tip, plant: Plant, world: World) -> list[Shoot]:
        settings = plant.settings
        low, high = settings["branch_min"], settings["branch_max"]
        count = low if low == high else world.rng.randint(low, high)
        # Forward-left, forward-right, back-left, back-right.
        sides = [(tip.heading + turn) % 6 for turn in (-1, 1, -2, 2)]
        free = [heading for heading in sides if world.can_sprout(plant, tip.cell, heading)]
        chosen = free if len(free) <= count else world.rng.sample(free, count)
        return [Shoot(heading, {"calm": 0}) for heading in chosen]

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[Sprout]:
        return CUT_RESPONSES[plant.settings["cut_response"]](plant, stump, world)


CATALOG: dict[str, Species] = {
    species.id: species
    for species in (StraightVine(), Zigzag(), Spiral(), Fern(), Wanderer(), Hydra(), Burst(), Custom())
}
