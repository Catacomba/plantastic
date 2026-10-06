# Proposal

## Why

Plantastic is a game about steering growing plants by cutting them, and nothing of it exists yet. Before levels or competitive modes can be designed, we need a sandbox where plant species can be planted, grown, and cut, so that growth and cut rules can be tried out and tuned.

## What Changes

- Add an authoritative, deterministic, tick-based plant simulation in Python on an infinite hexagonal grid.
- Add the first plant species: it grows in a straight line, and when cut it leaves a stump and forks into two new tips from two cells behind the cut.
- Add a per-plant growth speed expressed in hexagons per iteration, including fractional values (for example 0.25 means one hexagon every 4 iterations).
- Add a Python game server that hosts rooms, accepts player commands over a websocket, and pushes board state to clients.
- Add the sandbox room mode: one player, one board, with pause, resume, and "grow for N iterations" controls.
- Add a browser client (HTML, CSS, JS, three.js) that renders the board, lets the player plant seeds and cut with universal scissors, and offers a hex size display setting.
- Prepare for later modes without building them: plants carry an owner, rooms carry a mode that decides which commands are allowed, and all randomness comes from a room seed.

Out of scope for this change: levels, light, additional species, plant-specific scissors, the race and shared-board competitive modes, accounts, matchmaking, and persistence.

## Capabilities

### New Capabilities

- `plant-simulation`: The hex grid world and its tick rules: seeds, tips, growth by speed, blocking and collisions, cutting, stumps, and determinism.
- `plant-species`: The catalog of species and the growth and cut-response behavior of each; starts with the straight vine.
- `game-rooms`: Server-side rooms: connecting, room modes and their permitted commands, the clock (run, pause, step N), state synchronization to clients, and room limits.
- `game-client`: The browser experience: rendering the board, camera and hex size, the seed and scissors tools, and the clock controls.

### Modified Capabilities

None.

## Impact

- New Python backend package (simulation core, room server) with FastAPI, uvicorn, and pytest as dependencies.
- New static frontend served by the backend, with three.js as its only library and no build step.
- New websocket message protocol between client and server.
- The repository has no code yet, so nothing existing is affected.
