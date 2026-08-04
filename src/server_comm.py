"""
Client-side communication with the World 1-1 lobby server.
Handles room creation, listing, heartbeats, and joining.
"""

import json
import urllib.request
import urllib.error
import ssl
import time
import threading


DEFAULT_LOBBY_URL = "http://localhost:8080"

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


class LobbyClient:
    def __init__(self, server_url=DEFAULT_LOBBY_URL):
        self.server_url = server_url.rstrip("/")
        self.room_id = None
        self._heartbeat_thread = None
        self._heartbeat_running = False
        self.connected = False
        self.last_error = None
        self.is_ssl = self.server_url.startswith("https")

    def _request(self, path, method="GET", data=None):
        url = f"{self.server_url}{path}"
        kwargs = {"timeout": 10}
        if data is not None:
            kwargs["data"] = json.dumps(data).encode()
            kwargs["headers"] = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, method=method, **kwargs)
        if self.is_ssl:
            resp = urllib.request.urlopen(req, context=_ssl_ctx, timeout=10)
        else:
            resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())

    def check_server(self):
        try:
            data = self._request("/health")
            self.connected = True
            return data
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            return None

    def list_rooms(self):
        try:
            data = self._request("/rooms")
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
            result = self._request("/rooms", method="POST", data=payload)
            self.room_id = result.get("id")
            self.connected = True
            self._start_heartbeat()
            return result
        except Exception as e:
            self.last_error = str(e)
            return None

    def update_room(self, character="", stage=""):
        if not self.room_id:
            return
        try:
            self._request(f"/rooms/{self.room_id}/heartbeat",
                         method="POST", data={"players": 1, "character": character, "stage": stage})
        except Exception:
            pass

    def get_room(self, room_id=None):
        rid = room_id or self.room_id
        if not rid:
            return None
        try:
            return self._request(f"/rooms/{rid}")
        except Exception:
            return None

    def update_character(self, character, is_host=True):
        if not self.room_id:
            return
        try:
            field = "character" if is_host else "opp_character"
            self._request(f"/rooms/{self.room_id}/heartbeat",
                         method="POST", data={field: character})
        except Exception:
            pass

    def join_room(self, room_id):
        try:
            result = self._request(f"/rooms/{room_id}/join", method="POST", data={})
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
            self._request(f"/rooms/{rid}", method="DELETE")
        except Exception:
            pass
        if rid == self.room_id:
            self.room_id = None

    def send_heartbeat(self, players=1, character=""):
        if not self.room_id:
            return
        try:
            self._request(f"/rooms/{self.room_id}/heartbeat",
                         method="POST", data={"players": players, "character": character})
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
