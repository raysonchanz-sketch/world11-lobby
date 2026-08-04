"""
Client-side communication with the World 1-1 lobby server.
Handles room creation, listing, heartbeats, and joining.
"""

import json
import urllib.request
import urllib.error
import time
import threading


DEFAULT_LOBBY_URL = "http://localhost:8080"


class LobbyClient:
    def __init__(self, server_url=DEFAULT_LOBBY_URL):
        self.server_url = server_url.rstrip("/")
        self.room_id = None
        self._heartbeat_thread = None
        self._heartbeat_running = False
        self.connected = False
        self.last_error = None

    def check_server(self):
        try:
            req = urllib.request.Request(f"{self.server_url}/health")
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode())
            self.connected = True
            return data
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            return None

    def list_rooms(self):
        try:
            req = urllib.request.Request(f"{self.server_url}/rooms")
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode())
            self.connected = True
            return data.get("rooms", [])
        except Exception as e:
            self.last_error = str(e)
            return []

    def create_room(self, name, host_port=5150, host_name="Host",
                    character="", stage="", host_ip=None):
        try:
            payload = {
                "name": name,
                "host_port": host_port,
                "host_name": host_name,
                "character": character,
                "stage": stage,
            }
            if host_ip:
                payload["host_ip"] = host_ip
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.server_url}/rooms",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=5)
            result = json.loads(resp.read().decode())
            self.room_id = result.get("id")
            self.connected = True
            self._start_heartbeat()
            return result
        except Exception as e:
            self.last_error = str(e)
            return None

    def join_room(self, room_id):
        try:
            req = urllib.request.Request(
                f"{self.server_url}/rooms/{room_id}/join",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=5)
            result = json.loads(resp.read().decode())
            self.connected = True
            return result
        except Exception as e:
            self.last_error = str(e)
            return None

    def delete_room(self, room_id=None):
        rid = room_id or self.room_id
        if not rid:
            return
        self._stop_heartbeat()
        try:
            req = urllib.request.Request(
                f"{self.server_url}/rooms/{rid}",
                method="DELETE"
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
        if rid == self.room_id:
            self.room_id = None

    def send_heartbeat(self, players=1, character=""):
        if not self.room_id:
            return
        try:
            payload = {"players": players, "character": character}
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.server_url}/rooms/{self.room_id}/heartbeat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass

    def _start_heartbeat(self):
        self._stop_heartbeat()
        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self):
        self._heartbeat_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)
            self._heartbeat_thread = None

    def _heartbeat_loop(self):
        while self._heartbeat_running and self.room_id:
            self.send_heartbeat()
            time.sleep(10)

    def close(self):
        self._stop_heartbeat()
        if self.room_id:
            self.delete_room()
