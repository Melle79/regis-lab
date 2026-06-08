"""
HA Client - Kommuniziert mit Home Assistant via REST + WebSocket
"""
import json
import logging
import threading
import requests
import websocket
from typing import Callable

log = logging.getLogger("ha_dashboard.ha_client")


class HAClient:
    def __init__(self, ha_url: str, token: str):
        self.ha_url = ha_url
        self.token  = token
        self._ws_clients: list = []          # Verbundene Frontend-WS-Clients
        self._entity_cache: dict = {}        # Letzter bekannter Zustand
        self._state_callbacks: list[Callable] = []
        self._lock = threading.Lock()

        self._start_ha_listener()

    # ── REST ────────────────────────────────────────────────────
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def get_states(self) -> list:
        """Alle Entity-Zustände von HA laden."""
        try:
            r = requests.get(f"{self.ha_url}/api/states", headers=self._headers(), timeout=10)
            r.raise_for_status()
            states = r.json()
            with self._lock:
                for s in states:
                    self._entity_cache[s["entity_id"]] = s
            return states
        except Exception as e:
            log.error(f"get_states fehlgeschlagen: {e}")
            return []

    def get_state(self, entity_id: str) -> dict | None:
        try:
            r = requests.get(f"{self.ha_url}/api/states/{entity_id}", headers=self._headers(), timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"get_state({entity_id}) fehlgeschlagen: {e}")
            return None

    def call_service(self, domain: str, service: str, data: dict = None) -> bool:
        try:
            r = requests.post(
                f"{self.ha_url}/api/services/{domain}/{service}",
                headers=self._headers(),
                json=data or {},
                timeout=10
            )
            r.raise_for_status()
            return True
        except Exception as e:
            log.error(f"call_service {domain}.{service} fehlgeschlagen: {e}")
            return False

    def get_cached_states(self) -> dict:
        with self._lock:
            return dict(self._entity_cache)

    def ws_request(self, msg: dict, timeout: int = 8):
        """Einmalige synchrone WebSocket-Anfrage an HA."""
        import threading, websocket as wslib
        result = [None]
        done   = threading.Event()
        msg_id = 99

        def on_message(ws, raw):
            d = json.loads(raw)
            if d.get("type") == "auth_required":
                ws.send(json.dumps({"type": "auth", "access_token": self.token}))
            elif d.get("type") == "auth_ok":
                ws.send(json.dumps({"id": msg_id, **msg}))
            elif d.get("id") == msg_id:
                result[0] = d.get("result")
                done.set()
                ws.close()

        ws_url = self.ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        w = wslib.WebSocketApp(ws_url, on_message=on_message)
        threading.Thread(target=w.run_forever, daemon=True).start()
        done.wait(timeout)
        return result[0]


    def register_ws_client(self, ws):
        with self._lock:
            self._ws_clients.append(ws)
            # Aktuellen Cache sofort senden
            snapshot = list(self._entity_cache.values())
        ws.send(json.dumps({"type": "state_snapshot", "data": snapshot}))

    def unregister_ws_client(self, ws):
        with self._lock:
            self._ws_clients = [c for c in self._ws_clients if c != ws]

    def _broadcast(self, msg: dict):
        payload = json.dumps(msg)
        with self._lock:
            dead = []
            for ws in self._ws_clients:
                try:
                    ws.send(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._ws_clients.remove(ws)

    def on_state_change(self, callback: Callable):
        self._state_callbacks.append(callback)

    # ── HA WebSocket Listener (Hintergrund-Thread) ───────────────
    def _start_ha_listener(self):
        t = threading.Thread(target=self._ha_ws_loop, daemon=True)
        t.start()

    def _ha_ws_loop(self):
        ws_url = self.ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        msg_id = [1]

        def on_open(ws):
            log.info("Verbunden mit HA WebSocket")

        def on_message(ws, raw):
            msg = json.loads(raw)
            t = msg.get("type")

            if t == "auth_required":
                ws.send(json.dumps({"type": "auth", "access_token": self.token}))

            elif t == "auth_ok":
                log.info("HA WebSocket Auth OK")
                ws.send(json.dumps({"id": msg_id[0], "type": "subscribe_events", "event_type": "state_changed"}))
                msg_id[0] += 1

            elif t == "event":
                event = msg.get("event", {})
                if event.get("event_type") == "state_changed":
                    new_state = event["data"].get("new_state")
                    if new_state:
                        eid = new_state["entity_id"]
                        with self._lock:
                            self._entity_cache[eid] = new_state
                        self._broadcast({"type": "state_changed", "data": new_state})
                        for cb in self._state_callbacks:
                            try:
                                cb(eid, new_state)
                            except Exception as e:
                                log.error(f"State-Callback Fehler: {e}")

        def on_error(ws, err):
            log.warning(f"HA WebSocket Fehler: {err}")

        def on_close(ws, *args):
            log.info("HA WebSocket getrennt, reconnect in 10s...")
            import time; time.sleep(10)
            self._start_ha_listener()

        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws.run_forever()
