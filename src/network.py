"""
Peer-to-peer networking for World 1-1 online play.
TCP for lobby/control and input exchange.
"""

import socket
import struct
import threading
import time
import hashlib
from enum import IntEnum
from collections import OrderedDict


PROTOCOL_VERSION = 1
DEFAULT_PORT = 5150
INPUT_DELAY = 4
STATE_SYNC_INTERVAL = 300
INPUT_BUFFER_SIZE = 120
KEEPALIVE_INTERVAL = 1.0
KEEPALIVE_TIMEOUT = 5.0
LOBBY_TIMEOUT = 30.0

INPUT_ACTIONS = ["left", "right", "jump", "crouch", "attack", "attack_alt", "special", "shield"]


class MsgType(IntEnum):
    HANDSHAKE = 0x01
    HANDSHAKE_ACK = 0x02
    CHARACTER_SEL = 0x03
    STAGE_SEL = 0x04
    READY = 0x05
    INPUT = 0x10
    STATE_HASH = 0x11
    FULL_STATE_REQ = 0x12
    FULL_STATE = 0x13
    KEEPALIVE = 0x20
    DISCONNECT = 0x21


def encode_input_bitfield(actions_dict):
    bits = 0
    for i, action in enumerate(INPUT_ACTIONS):
        if actions_dict.get(action, False):
            bits |= (1 << i)
    return bits


def decode_input_bitfield(bits):
    return {action: bool(bits & (1 << i)) for i, action in enumerate(INPUT_ACTIONS)}


MSG_HEADER_FMT = "!BH"
MSG_HEADER_SIZE = struct.calcsize(MSG_HEADER_FMT)


def pack_msg(msg_type, payload):
    header = struct.pack(MSG_HEADER_FMT, msg_type, len(payload))
    return header + payload


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed")
        buf += chunk
    return buf


def recv_msg(sock):
    header = recv_exact(sock, MSG_HEADER_SIZE)
    msg_type, length = struct.unpack(MSG_HEADER_FMT, header)
    payload = recv_exact(sock, length) if length > 0 else b""
    return msg_type, payload


def compute_state_hash(frame, p1_state, p2_state):
    data = struct.pack("!I", frame)
    for p in (p1_state, p2_state):
        data += struct.pack("!iiiiBBIi",
            int(p["x"]), int(p["y"]),
            int(p.get("vx", 0) * 100), int(p.get("vy", 0) * 100),
            int(p.get("percentage", 0)),
            p.get("hearts", 3),
            p.get("facing", 1),
            int(p.get("attacking", False)),
            int(p.get("on_ground", False)),
        )
    return struct.unpack("!I", hashlib.md5(data).digest()[:4])[0]


class NetworkSession:
    def __init__(self):
        self.is_host = False
        self.connected = False
        self.peer_addr = None

        self._sock = None
        self._send_lock = threading.Lock()
        self._recv_thread = None

        self._input_buffer = OrderedDict()
        self._input_lock = threading.Lock()

        self._state_hashes = {}
        self._state_lock = threading.Lock()
        self._desync_detected = False
        self._desync_frame = -1

        self._full_state_requested = False
        self._pending_full_state = None

        self._lobby_ready = False
        self._lobby_seed = 0
        self._opp_seed = 0

        self._last_recv_time = 0.0
        self._last_send_time = 0.0

        self.rtt_ms = 0.0
        self._ping_sent_time = 0.0
        self._pong_received = False

    def start_recv_thread(self):
        self._start_recv_thread()

    @property
    def is_hosting(self):
        return self.is_host

    def host(self, port=DEFAULT_PORT):
        self.is_host = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("0.0.0.0", port))
        self._sock.listen(1)
        self._sock.setblocking(False)
        local_ip = self._get_local_ip()
        return f"{local_ip}:{port}"

    def wait_for_connection(self, timeout=LOBBY_TIMEOUT):
        start = time.time()
        while time.time() - start < timeout:
            try:
                conn, addr = self._sock.accept()
                conn.setblocking(True)
                self._sock.close()
                self._sock = conn
                self.peer_addr = addr
                self.connected = True
                self._last_recv_time = time.time()
                return True
            except BlockingIOError:
                time.sleep(0.1)
        return False

    def join(self, host_ip, port=DEFAULT_PORT):
        self.is_host = False
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(10.0)
        try:
            self._sock.connect((host_ip, port))
            self._sock.setblocking(True)
            self.peer_addr = (host_ip, port)
            self.connected = True
            self._last_recv_time = time.time()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def send_character_select(self, char_name):
        payload = struct.pack("!B", len(char_name)) + char_name.encode("ascii")
        self._send_msg(MsgType.CHARACTER_SEL, payload)

    def recv_character_select(self, timeout=LOBBY_TIMEOUT):
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(0.01)
            try:
                msg_type, payload = recv_msg(self._sock)
                self._last_recv_time = time.time()
                if msg_type == MsgType.CHARACTER_SEL:
                    name_len = struct.unpack("!B", payload[:1])[0]
                    return payload[1:1 + name_len].decode("ascii")
                elif msg_type == MsgType.KEEPALIVE:
                    pass
            except (ConnectionError, BlockingIOError, OSError):
                return None
        return None

    def send_stage_select(self, stage_index):
        payload = struct.pack("!B", stage_index)
        self._send_msg(MsgType.STAGE_SEL, payload)

    def recv_stage_select(self, timeout=LOBBY_TIMEOUT):
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(0.01)
            try:
                msg_type, payload = recv_msg(self._sock)
                self._last_recv_time = time.time()
                if msg_type == MsgType.STAGE_SEL:
                    return struct.unpack("!B", payload[:1])[0]
                elif msg_type == MsgType.KEEPALIVE:
                    pass
            except (ConnectionError, BlockingIOError, OSError):
                return -1
        return -1

    def send_ready(self, seed):
        payload = struct.pack("!I", seed)
        self._send_msg(MsgType.READY, payload)

    def recv_ready(self, timeout=LOBBY_TIMEOUT):
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(0.01)
            try:
                msg_type, payload = recv_msg(self._sock)
                self._last_recv_time = time.time()
                if msg_type == MsgType.READY:
                    return struct.unpack("!I", payload[:4])[0]
                elif msg_type == MsgType.KEEPALIVE:
                    pass
            except (ConnectionError, BlockingIOError, OSError):
                return None
        return None

    def send_input(self, frame, input_bits):
        payload = struct.pack("!IB", frame, input_bits)
        self._send_msg(MsgType.INPUT, payload)

    def get_opponent_input(self, frame):
        target_frame = frame - INPUT_DELAY
        with self._input_lock:
            if target_frame in self._input_buffer:
                return self._input_buffer.pop(target_frame)
        return 0

    def _buffer_input(self, frame, input_bits):
        with self._input_lock:
            self._input_buffer[frame] = input_bits
            while len(self._input_buffer) > INPUT_BUFFER_SIZE:
                self._input_buffer.popitem(last=False)

    def send_state_hash(self, frame, state_hash):
        payload = struct.pack("!II", frame, state_hash)
        self._send_msg(MsgType.STATE_HASH, payload)

    def check_desync(self, frame, local_hash):
        with self._state_lock:
            if frame in self._state_hashes:
                if self._state_hashes[frame] != local_hash:
                    self._desync_detected = True
                    self._desync_frame = frame
                    return True
        return False

    def send_keepalive(self):
        now = time.time()
        if now - self._last_send_time >= KEEPALIVE_INTERVAL:
            self._send_msg(MsgType.KEEPALIVE, b"")
            self._last_send_time = now

    def send_ping(self):
        self._ping_sent_time = time.time()
        self._pong_received = False
        self._send_msg(MsgType.KEEPALIVE, b"ping")

    def update_rtt(self):
        if self._pong_received:
            rtt = (time.time() - self._ping_sent_time) * 1000
            self.rtt_ms = rtt
            self._pong_received = False
            return True
        return False

    def is_alive(self):
        if not self.connected:
            return False
        return (time.time() - self._last_recv_time) < KEEPALIVE_TIMEOUT

    def send_disconnect(self):
        try:
            self._send_msg(MsgType.DISCONNECT, b"")
        except Exception:
            pass

    def close(self):
        self.connected = False
        try:
            self.send_disconnect()
        except Exception:
            pass
        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=1.0)
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _send_msg(self, msg_type, payload):
        data = pack_msg(msg_type, payload)
        with self._send_lock:
            try:
                self._sock.sendall(data)
            except (ConnectionError, OSError):
                self.connected = False

    def _start_recv_thread(self):
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def _recv_loop(self):
        while self.connected:
            try:
                msg_type, payload = recv_msg(self._sock)
                self._last_recv_time = time.time()

                if msg_type == MsgType.INPUT:
                    frame, bits = struct.unpack("!IB", payload[:5])
                    self._buffer_input(frame, bits)

                elif msg_type == MsgType.STATE_HASH:
                    frame, hash_val = struct.unpack("!II", payload[:8])
                    with self._state_lock:
                        self._state_hashes[frame] = hash_val

                elif msg_type == MsgType.KEEPALIVE:
                    pass

                elif msg_type == MsgType.DISCONNECT:
                    self.connected = False

                elif msg_type == MsgType.FULL_STATE_REQ:
                    self._full_state_requested = True

                elif msg_type == MsgType.FULL_STATE:
                    self._pending_full_state = payload

            except ConnectionError:
                self.connected = False
            except struct.error:
                self.connected = False

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


class NetworkKeyProxy:
    def __init__(self, real_keys, network_session, is_local_player, frame_ref, controls):
        self.real_keys = real_keys
        self.session = network_session
        self.is_local = is_local_player
        self.frame_ref = frame_ref
        self.controls = controls
        self._key_to_action = {v: k for k, v in controls.items()}
        self._current_opponent_input = {}
        self._last_frame = -1

    def refresh(self):
        current_frame = self.frame_ref[0]
        if current_frame != self._last_frame:
            self._last_frame = current_frame
            if not self.is_local:
                input_bits = self.session.get_opponent_input(current_frame)
                self._current_opponent_input = decode_input_bitfield(input_bits)

    def __getitem__(self, key_code):
        action = self._key_to_action.get(key_code)
        if action:
            if self.is_local:
                return self.real_keys[key_code]
            else:
                return self._current_opponent_input.get(action, False)
        return self.real_keys[key_code]

    def __len__(self):
        return len(self.real_keys)

    def send_local_input(self, frame):
        actions = {}
        for action_name in INPUT_ACTIONS:
            key_code = self.controls.get(action_name)
            if key_code is not None:
                actions[action_name] = self.real_keys[key_code]
        input_bits = encode_input_bitfield(actions)
        self.session.send_input(frame, input_bits)
