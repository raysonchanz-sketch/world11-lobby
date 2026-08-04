"""
World 1-1 Lobby Server

A lightweight matchmaking server for online play.
Rooms are created by hosts and discovered by joiners.
Stale rooms (no heartbeat for 30s) are automatically cleaned up.

Usage:
    python lobby_server.py                    # Run on port 8080
    PORT=5000 python lobby_server.py          # Custom port

Deploy to Render/Railway/Fly.io:
    - Build: pip install -r requirements-server.txt
    - Start: python lobby_server.py
"""

import os
import time
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

PORT = int(os.environ.get("PORT", 8080))
HEARTBEAT_TIMEOUT = 30.0
CLEANUP_INTERVAL = 10.0

rooms = {}
rooms_lock = threading.Lock()


def cleanup_stale_rooms():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        now = time.time()
        with rooms_lock:
            stale = [rid for rid, r in rooms.items()
                     if now - r["last_heartbeat"] > HEARTBEAT_TIMEOUT]
            for rid in stale:
                del rooms[rid]
            if stale:
                print(f"Cleaned up {len(stale)} stale rooms")


class LobbyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return json.loads(self.rfile.read(length))
        return {}

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path == "/rooms":
            with rooms_lock:
                room_list = []
                for rid, r in rooms.items():
                    room_list.append({
                        "id": rid,
                        "name": r["name"],
                        "host_ip": r["host_ip"],
                        "host_port": r["host_port"],
                        "host_name": r["host_name"],
                        "character": r.get("character", ""),
                        "stage": r.get("stage", ""),
                        "players": r.get("players", 1),
                        "max_players": r.get("max_players", 2),
                        "created": r["created"],
                        "age": int(time.time() - r["created"]),
                    })
            self._set_headers(200)
            self.wfile.write(json.dumps({"rooms": room_list}).encode())

        elif self.path == "/health":
            with rooms_lock:
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "rooms": len(rooms),
                    "uptime": int(time.time() - server_start_time),
                }).encode())

        elif self.path.startswith("/rooms/") and self.path.count("/") == 2:
            room_id = self.path.split("/")[2]
            with rooms_lock:
                if room_id in rooms:
                    r = rooms[room_id]
                    self._set_headers(200)
                    self.wfile.write(json.dumps({
                        "id": room_id,
                        "name": r["name"],
                        "host_name": r["host_name"],
                        "character": r.get("character", ""),
                        "opp_character": r.get("opp_character", ""),
                        "p1_character": r.get("p1_character", ""),
                        "p2_character": r.get("p2_character", ""),
                        "p1_locked": r.get("p1_locked", False),
                        "p2_locked": r.get("p2_locked", False),
                        "stage": r.get("stage", ""),
                        "players": r.get("players", 1),
                        "state": r.get("state", "lobby"),
                    }).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "room not found"}).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        if self.path == "/rooms":
            data = self._read_body()
            room_id = uuid.uuid4().hex[:8]
            room = {
                "name": data.get("name", f"Room {room_id[:4]}"),
                "host_ip": data.get("host_ip", self.client_address[0]),
                "host_port": data.get("host_port", 5150),
                "host_name": data.get("host_name", "Host"),
                "character": data.get("character", ""),
                "stage": data.get("stage", ""),
                "players": 1,
                "max_players": 2,
                "created": time.time(),
                "last_heartbeat": time.time(),
            }
            with rooms_lock:
                rooms[room_id] = room
            self._set_headers(201)
            self.wfile.write(json.dumps({
                "id": room_id,
                "host_ip": room["host_ip"],
                "host_port": room["host_port"],
                "your_ip": self.client_address[0],
            }).encode())

        elif self.path.startswith("/rooms/") and "/heartbeat" in self.path:
            room_id = self.path.split("/")[2]
            with rooms_lock:
                if room_id in rooms:
                    rooms[room_id]["last_heartbeat"] = time.time()
                    data = self._read_body()
                    for key in ("players", "character", "opp_character", "p1_character", "p2_character", "p1_locked", "p2_locked", "stage", "state"):
                        if key in data:
                            rooms[room_id][key] = data[key]
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"ok": True}).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "room not found"}).encode())

        elif self.path.startswith("/rooms/") and "/join" in self.path:
            room_id = self.path.split("/")[2]
            with rooms_lock:
                if room_id in rooms:
                    rooms[room_id]["players"] = min(
                        rooms[room_id].get("players", 1) + 1,
                        rooms[room_id].get("max_players", 2)
                    )
                    self._set_headers(200)
                    self.wfile.write(json.dumps({
                        "host_ip": rooms[room_id]["host_ip"],
                        "host_port": rooms[room_id]["host_port"],
                    }).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "room not found"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_DELETE(self):
        if self.path.startswith("/rooms/"):
            room_id = self.path.split("/")[2]
            with rooms_lock:
                if room_id in rooms:
                    del rooms[room_id]
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"ok": True}).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "room not found"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())


server_start_time = time.time()

if __name__ == "__main__":
    cleanup_thread = threading.Thread(target=cleanup_stale_rooms, daemon=True)
    cleanup_thread.start()

    server = HTTPServer(("0.0.0.0", PORT), LobbyHandler)
    print(f"World 1-1 Lobby Server running on port {PORT}")
    print(f"Rooms will auto-expire after {HEARTBEAT_TIMEOUT}s without heartbeat")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()
