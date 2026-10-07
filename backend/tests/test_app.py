from fastapi.testclient import TestClient

from plantastic.server.app import create_app


class ClientBoard:
    """What a browser would hold: the welcome snapshot plus every update applied in order."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.cells = {}
        self.plants = {}
        self.tips = []
        self.tick = 0
        self.clock = None
        self.errors = []
        self.notices = []
        welcome = self.receive()
        assert welcome["type"] == "welcome"
        self.welcome = welcome

    def receive(self) -> dict:
        message = self.websocket.receive_json()
        if message["type"] == "welcome":
            self.cells = {(cell["q"], cell["r"]): cell for cell in message["cells"]}
        elif message["type"] == "update":
            if message["cleared"]:
                self.cells.clear()
            for q, r in message["removed"]:
                self.cells.pop((q, r), None)
            for cell in message["added"] + message["changed"]:
                self.cells[(cell["q"], cell["r"])] = cell
        elif message["type"] == "error":
            self.errors.append(message["code"])
        elif message["type"] == "notice":
            self.notices.append(message["code"])
        if message["type"] in ("welcome", "update"):
            for details in message["plants"]:
                self.plants[details["id"]] = details
            # A plant with no cells left is gone.
            alive = {cell["plant"] for cell in self.cells.values()}
            self.plants = {id: details for id, details in self.plants.items() if id in alive}
            self.tips = message["tips"]
            self.tick = message["tick"]
            self.clock = message["clock"]
        return message

    def send(self, **command) -> dict:
        self.websocket.send_json(command)
        return self.receive()

    def matches(self, room) -> bool:
        board = room.board
        server_cells = {(cell["q"], cell["r"]): cell for cell in board.cells_snapshot()}
        return (
            self.cells == server_cells
            and self.tips == board.tips_snapshot()
            and self.tick == board.tick
            and self.clock == room.clock
        )


def only_room(app):
    (room,) = app.state.rooms.values()
    return room


def test_session_keeps_client_and_server_boards_identical():
    # A long interval keeps the clock out of the way so every reply is predictable.
    app = create_app(tick_interval=3600, frontend_dir=None)
    with TestClient(app).websocket_connect("/ws") as websocket:
        client = ClientBoard(websocket)
        room = only_room(app)

        assert client.welcome["mode"] == "sandbox"
        assert client.welcome["clock"] == "running"
        assert client.welcome["cells"] == []
        assert len(client.welcome["species"]) == 8
        assert client.welcome["species"][0]["id"] == "straight-vine"

        assert client.send(type="pause")["clock"] == "paused"
        client.send(type="plant", q=0, r=0, species="straight-vine", speed="1")
        client.send(type="plant", q=0, r=60, species="straight-vine", speed="0.25")  # far enough never to meet the first
        growth = client.send(type="step", n=6)
        assert growth["tick"] == 6
        assert growth["stats"]["iterations"] == 6 and growth["stats"]["step_ms"] >= 0
        assert growth["stats"]["visits"] == 7  # six hexes at speed 1, one at speed 0.25
        assert client.welcome["tick_ms"] == 3600 * 1000
        assert len(growth["added"]) == 7  # six cells at speed 1, one at speed 0.25
        assert client.matches(room)

        fast_tip = next(tip for tip in client.tips if tip["plant"] == 1)
        cut = client.send(type="cut", q=fast_tip["q"], r=fast_tip["r"])
        assert [cell["kind"] for cell in cut["changed"]] == ["stump"]
        assert client.matches(room)

        client.send(type="step", n=5)
        root = next(cell for cell in client.cells.values() if cell["plant"] == 2 and cell["kind"] == "root")
        removed = client.send(type="cut", q=root["q"], r=root["r"])
        assert len(removed["removed"]) == 3
        assert client.matches(room)

        assert client.send(type="plant", q=0, r=0, species="straight-vine", speed="1")["code"] == "occupied"
        assert client.send(type="launch")["code"] == "bad_message"
        websocket.send_text("not json")
        assert client.receive()["code"] == "bad_message"
        assert client.matches(room)


def test_slices_while_paused_land_on_the_same_tick():
    app = create_app(tick_interval=0.02, frontend_dir=None)
    with TestClient(app).websocket_connect("/ws") as websocket:
        client = ClientBoard(websocket)
        room = only_room(app)

        websocket.send_json({"type": "pause"})
        while client.clock != "paused":
            client.receive()
        client.send(type="plant", q=0, r=0, species="straight-vine", speed="1")
        client.send(type="plant", q=0, r=60, species="straight-vine", speed="1")
        client.send(type="step", n=6)
        tick = client.tick
        vines = {
            plant: [cell for cell in client.cells.values() if cell["plant"] == plant and cell["kind"] == "segment"]
            for plant in (1, 2)
        }

        first = client.send(type="slice", hexes=[[vines[1][3]["q"], vines[1][3]["r"]], [40, 40]])
        second = client.send(type="slice", hexes=[[41, 40], [vines[2][3]["q"], vines[2][3]["r"]]])
        assert first["tick"] == second["tick"] == tick
        assert [cell["kind"] for cell in first["changed"] + second["changed"]] == ["stump", "stump"]
        assert client.errors == []
        assert client.matches(room)

        assert client.send(type="slice", hexes=[])["code"] == "bad_message"
        assert client.send(type="resume")["clock"] == "running"
        while client.tick < tick + 3:
            client.receive()


def test_client_knows_the_details_of_exactly_the_plants_on_its_board():
    settings = {
        "branch_chance": 30,
        "branch_min": 1,
        "branch_max": 2,
        "calm_min": 0,
        "calm_max": 5,
        "turn_chance": 20,
        "cut_response": "multiply",
    }
    app = create_app(tick_interval=3600, frontend_dir=None)
    with TestClient(app).websocket_connect("/ws") as websocket:
        client = ClientBoard(websocket)
        room = only_room(app)
        custom = next(species for species in client.welcome["species"] if species["id"] == "custom")
        assert len(custom["settings"]) == 7
        assert client.plants == {}

        client.send(type="pause")
        client.send(type="plant", q=0, r=0, species="straight-vine", speed="0.5")
        client.send(type="plant", q=0, r=30, species="custom", speed="1", settings=settings)
        client.send(type="step", n=8)
        assert client.plants == {
            1: {"id": 1, "species": "straight-vine", "speed": "1/2", "settings": None},
            2: {"id": 2, "species": "custom", "speed": "1", "settings": settings},
        }
        assert client.matches(room)

        rejected = client.send(type="plant", q=9, r=9, species="custom", speed="1", settings={**settings, "branch_max": 9})
        assert rejected["code"] == "bad_settings"
        assert rejected["message"] == "Branches max must be from 1 to 4."

        client.send(type="cut", q=0, r=0)  # the vine's root
        assert list(client.plants) == [2]
        assert {plant["id"] for plant in room.board.plants_snapshot()} == {2}
        assert client.matches(room)


def test_scatter_grow_clear_keeps_client_and_server_identical():
    app = create_app(tick_interval=3600, frontend_dir=None)
    with TestClient(app).websocket_connect("/ws") as websocket:
        client = ClientBoard(websocket)
        room = only_room(app)
        region = {"q": 0, "r": 0, "half_width": 25, "half_height": 15}

        client.send(type="pause")
        first = client.send(type="scatter", count=40, **region)
        assert first["scattered"] == {"asked": 40, "planted": 40}
        assert len(client.plants) == 40
        client.send(type="step", n=10)
        assert len(client.cells) > 100
        assert client.matches(room)

        cleared = client.send(type="clear")
        assert cleared["cleared"] is True
        assert client.cells == {} and client.plants == {} and client.tips == []
        assert client.tick == 10
        assert client.matches(room)

        client.send(type="scatter", count=15, **region)
        client.send(type="step", n=5)
        assert len(client.plants) == 15
        assert min(client.plants) > 40  # ids are never reused after a clear
        assert {details["id"] for details in room.board.plants_snapshot()} == set(client.plants)
        assert client.matches(room)

        assert client.send(type="scatter", count=0, **region)["code"] == "bad_message"
        assert client.errors == ["bad_message"]


def test_running_room_pushes_growth():
    app = create_app(tick_interval=0.02, frontend_dir=None)
    with TestClient(app).websocket_connect("/ws") as websocket:
        client = ClientBoard(websocket)
        room = only_room(app)

        websocket.send_json({"type": "plant", "q": 0, "r": 0, "species": "straight-vine", "speed": "1"})
        while client.tick < 5:
            client.receive()
        assert len(client.cells) >= 6

        websocket.send_json({"type": "pause"})
        while client.clock != "paused":
            client.receive()
        assert client.matches(room)


def test_full_board_notice_reaches_the_client():
    app = create_app(tick_interval=0.02, max_cells=4, frontend_dir=None)
    with TestClient(app).websocket_connect("/ws") as websocket:
        client = ClientBoard(websocket)
        websocket.send_json({"type": "plant", "q": 0, "r": 0, "species": "straight-vine", "speed": "1"})
        while not client.notices:
            client.receive()
        assert client.notices == ["board_full"]
        assert client.clock == "paused"
        assert len(client.cells) == 4


def test_rooms_are_isolated_and_removed_on_disconnect():
    app = create_app(tick_interval=3600, frontend_dir=None)
    test_client = TestClient(app)
    with test_client.websocket_connect("/ws") as first_socket:
        first = ClientBoard(first_socket)
        with test_client.websocket_connect("/ws") as second_socket:
            second = ClientBoard(second_socket)
            assert len(app.state.rooms) == 2
            assert first.welcome["room"] != second.welcome["room"]

            first.send(type="plant", q=0, r=0, species="straight-vine", speed="1")
            second_room = app.state.rooms[second.welcome["room"]]
            assert not second_room.board.cells
        first.send(type="pause")  # round trip, so the second room's cleanup has run
        assert list(app.state.rooms) == [first.welcome["room"]]
    assert not app.state.rooms


def test_frontend_is_served():
    response = TestClient(create_app()).get("/")
    assert response.status_code == 200
    assert "<title>Plantastic</title>" in response.text


def test_frontend_files_are_always_revalidated():
    client = TestClient(create_app())
    for path in ("/", "/js/main.js", "/css/style.css"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"

    script = client.get("/js/main.js")
    unchanged = client.get("/js/main.js", headers={"If-None-Match": script.headers["etag"]})
    assert unchanged.status_code == 304
    assert unchanged.headers["cache-control"] == "no-cache"
