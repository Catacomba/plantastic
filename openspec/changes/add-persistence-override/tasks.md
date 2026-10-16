# Tasks

## 1. Simulation

- [x] 1.1 Add `persistence` to `Plant` (and `to_dict`). Resolve it in `World.plant_seed(..., persistence=None)`, raising `SimError("bad_persistence")` for anything but `None` or an int from 0 to 100, and make `_detour` read `plant.persistence`. Update the plant-details equality checks in `backend/tests`. Verify with new tests in `backend/tests/test_growth.py`: a straight vine planted with 100 detours; a hydra without an override has 80; a custom plant with setting 0 planted with 100 has 100 and keeps its setting; 101, -1, 50.5 and `True` are rejected and leave the board unchanged.
- [x] 1.2 Add `persistence=None` to `World.scatter`, validated before any random draw and passed to every seed. Verify with tests in `backend/tests/test_clear_scatter.py`: a scatter with 70 gives every plant 70; one without gives species defaults; one with 150 plants nothing and leaves the rng state unchanged.

## 2. Protocol and room

- [x] 2.1 Add optional `persistence` (strict int or null) to `PlantCommand` and `ScatterCommand` in `backend/plantastic/server/protocol.py`, and pass it through in `rooms.py`. Verify with tests: in `backend/tests/test_protocol.py`, `50.5` and `"50"` give `bad_message`; in `backend/tests/test_rooms.py`, a plant with 90 is reported with persistence 90, a scatter with 40 reports 40 on each new plant, 150 gives `bad_persistence`, and leaving it out still works.
- [x] 2.2 Document the field on `plant` and `scatter`, `persistence` in plant details, and `bad_persistence` in `docs/protocol.md`. Verify against `protocol.py` and `Plant.to_dict`.

## 3. Client

- [x] 3.1 Add the Persistence % field and the Override checkbox after the Speed field in `frontend/index.html`, and wire them in `frontend/js/ui.js`: the field is disabled while unticked, and a `persistence` getter returns the number when ticked or `undefined`. Pass it from `net.plant` in `frontend/js/main.js` and from `onScatter`. Verify in the browser: unticked, a hydra shows persistence 80; ticked with 100, a straight vine goes around obstacles; Random with 20 gives each new plant 20; 150 shows the server's error toast and plants nothing.
- [x] 3.2 Make `describePlant` show `persistence N%` from the plant details, and leave the Custom `persistence` setting out of the settings text. Verify in the browser: a custom plant planted with Override 70 and setting 10 shows "persistence 70%" once.
- [x] 3.3 Describe the control in `README.md` (Play section and the Persistence paragraph), noting that Override wins over the Custom setting. Verify the text against the running app.
