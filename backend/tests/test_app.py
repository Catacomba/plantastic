from fastapi.testclient import TestClient

from plantastic.server.app import create_app


class ClientBoard:
    """What a browser would hold: the welcome snapshot plus every update applied in order."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.cells = {}
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
            for q, r in message["removed"]:
                self.cells.pop((q, r), None)
            for cell in message["added"] + message["changed"]:
                self.cells[(cell["q"], cell["r"])] = cell
        elif message["type"] == "error":
            self.errors.append(message["code"])
        elif message["type"] == "notice":
            self.notices.append(message["code"])
        if message["type"] in ("welcome", "update"):
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
        assert [species["id"] for species in client.welcome["species"]] == ["straight-vine"]

        assert client.send(type="pause")["clock"] == "paused"
        client.send(type="plant", q=0, r=0, species="straight-vine", speed="1")
        client.send(type="plant", q=0, r=8, species="straight-vine", speed="0.25")
        growth = client.send(type="step", n=6)
        assert growth["tick"] == 6
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
