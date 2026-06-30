import random
import string
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from monopy.state.game_manager import GameManager

app = FastAPI(title="Monopy Online", version="0.1.0")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory lobby database
LOBBIES: dict[str, dict[str, Any]] = {}

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


class CreateLobbyRequest(BaseModel):
    creator_name: str


class JoinLobbyRequest(BaseModel):
    lobby_code: str
    player_name: str


def generate_lobby_code() -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4))
        if code not in LOBBIES:
            return code


def serialize_lobby(lobby: dict[str, Any]) -> dict[str, Any]:
    """Serializes lobby state to be WebSocket-safe."""
    serialized_players = []
    gm: GameManager | None = lobby.get("game_manager")

    if gm:
        # Use live data from game_manager
        for p in gm.players:
            serialized_players.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "balance": p.balance,
                    "position": p.position,
                    "in_jail": p.in_jail,
                    "jail_turns": p.jail_turns,
                    "properties": list(p.properties),
                    "is_online": p.id in lobby["connections"],
                }
            )

        board_spaces = []
        for s in gm.board.spaces:
            board_spaces.append(
                {
                    "index": s.index,
                    "name": s.name,
                    "space_type": s.space_type.name,
                    "price": s.price,
                    "rent": s.rent,
                    "color_group": s.color_group,
                    "owner_id": s.owner_id,
                }
            )

        return {
            "lobby_code": lobby["lobby_code"],
            "status": lobby["status"],
            "creator_id": lobby["creator_id"],
            "players": serialized_players,
            "chat_messages": lobby["chat_messages"],
            "game_state": {
                "current_player_index": gm.current_player_index,
                "phase": gm.phase,
                "last_roll": gm.last_roll,
                "history": gm.history,
                "winner_name": gm.winner_name,
                "board": board_spaces,
            },
        }
    else:
        # Before game starts
        for p in lobby["players"]:
            serialized_players.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "balance": 1500,
                    "position": 0,
                    "in_jail": False,
                    "is_online": p["id"] in lobby["connections"],
                }
            )
        return {
            "lobby_code": lobby["lobby_code"],
            "status": lobby["status"],
            "creator_id": lobby["creator_id"],
            "players": serialized_players,
            "chat_messages": lobby["chat_messages"],
            "game_state": None,
        }


async def broadcast_state(lobby_code: str):
    lobby = LOBBIES.get(lobby_code)
    if not lobby:
        return

    payload = {"type": "state_update", "data": serialize_lobby(lobby)}

    # Send to all connected clients
    for pid, ws in list(lobby["connections"].items()):
        try:
            await ws.send_json(payload)
        except Exception:
            # Stale connection
            lobby["connections"].pop(pid, None)


@app.post("/api/lobby/create")
def create_lobby(req: CreateLobbyRequest):
    code = generate_lobby_code()
    player_id = f"p-{code}-1"

    LOBBIES[code] = {
        "lobby_code": code,
        "status": "LOBBY",
        "creator_id": player_id,
        "players": [{"id": player_id, "name": req.creator_name}],
        "connections": {},
        "chat_messages": [
            {
                "player_name": "System",
                "text": f"Lobby {code} created by {req.creator_name}.",
            }
        ],
        "game_manager": None,
    }

    return {
        "lobby_code": code,
        "player_id": player_id,
        "player_name": req.creator_name,
    }


@app.post("/api/lobby/join")
def join_lobby(req: JoinLobbyRequest):
    code = req.lobby_code.upper().strip()
    lobby = LOBBIES.get(code)

    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")

    if lobby["status"] != "LOBBY":
        raise HTTPException(status_code=400, detail="Game already started or finished")

    if len(lobby["players"]) >= 8:
        raise HTTPException(status_code=400, detail="Lobby is full (max 8 players)")

    # Avoid duplicate name issues
    if any(p["name"].lower() == req.player_name.lower() for p in lobby["players"]):
        req.player_name = f"{req.player_name} ({len(lobby['players']) + 1})"

    player_id = f"p-{code}-{len(lobby['players']) + 1}"

    lobby["players"].append({"id": player_id, "name": req.player_name})
    lobby["chat_messages"].append(
        {
            "player_name": "System",
            "text": f"{req.player_name} joined the lobby.",
        }
    )

    return {"lobby_code": code, "player_id": player_id, "player_name": req.player_name}


@app.websocket("/ws/lobby/{lobby_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_code: str, player_id: str):
    lobby_code = lobby_code.upper().strip()
    lobby = LOBBIES.get(lobby_code)

    if not lobby:
        await websocket.close(code=4000, reason="Lobby not found")
        return

    # Check if player is part of lobby
    if not any(p["id"] == player_id for p in lobby["players"]):
        await websocket.close(code=4001, reason="Player not registered in lobby")
        return

    await websocket.accept()
    lobby["connections"][player_id] = websocket

    # Broadcast join
    await broadcast_state(lobby_code)

    try:
        while True:
            data = await websocket.receive_json()
            action_type = data.get("action")

            gm: GameManager | None = lobby.get("game_manager")
            player_name = next(
                p["name"] for p in lobby["players"] if p["id"] == player_id
            )

            if action_type == "start_game":
                if player_id == lobby["creator_id"] and lobby["status"] == "LOBBY":
                    # Initialize GameManager with current players
                    defs = [
                        {"id": p["id"], "name": p["name"]} for p in lobby["players"]
                    ]
                    lobby["game_manager"] = GameManager(defs)
                    lobby["status"] = "PLAYING"
                    lobby["chat_messages"].append(
                        {
                            "player_name": "System",
                            "text": "The game has started!",
                        }
                    )
                    await broadcast_state(lobby_code)

            elif action_type == "roll_dice":
                is_curr = gm and gm.current_player.id == player_id
                if gm and gm.phase in ("ROLL", "JAIL_DECISION") and is_curr:
                    d1 = random.randint(1, 6)
                    d2 = random.randint(1, 6)
                    gm.roll_dice(d1, d2)
                    await broadcast_state(lobby_code)

            elif action_type == "buy_property":
                is_curr = gm and gm.current_player.id == player_id
                if gm and gm.phase == "BUY_DECISION" and is_curr:
                    gm.buy_current_property()
                    await broadcast_state(lobby_code)

            elif action_type == "pass_property":
                is_curr = gm and gm.current_player.id == player_id
                if gm and gm.phase == "BUY_DECISION" and is_curr:
                    gm.pass_current_property()
                    await broadcast_state(lobby_code)

            elif action_type == "pay_fine":
                is_curr = gm and gm.current_player.id == player_id
                if gm and gm.phase == "JAIL_DECISION" and is_curr:
                    gm.pay_jail_fine()
                    await broadcast_state(lobby_code)

            elif action_type == "end_turn":
                is_curr = gm and gm.current_player.id == player_id
                if gm and gm.phase == "END_TURN" and is_curr:
                    gm.end_turn()
                    await broadcast_state(lobby_code)

            elif action_type == "chat":
                msg_text = data.get("text", "").strip()
                if msg_text:
                    lobby["chat_messages"].append(
                        {"player_name": player_name, "text": msg_text}
                    )
                    await broadcast_state(lobby_code)

    except WebSocketDisconnect:
        # Remove connection
        lobby["connections"].pop(player_id, None)
        await broadcast_state(lobby_code)


@app.get("/")
def get_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Welcome to Monopy. Static assets not generated yet."}


# Serve static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main():
    uvicorn.run("monopy.web.server:app", host="0.0.0.0", port=1997, reload=True)


if __name__ == "__main__":
    main()
