"""
Regis-Lab Addon - Backend
Flask serviert Frontend + API + WebSocket (Ingress-kompatibel)
"""
import os
import json
import logging
import requests as _requests
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from flask_sock import Sock

from core.ha_client import HAClient
from core.config import AddonConfig
from core.module_loader import ModuleLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("regis_lab")

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path="")
CORS(app)
sock = Sock(app)

config = AddonConfig()
ha     = HAClient(config.ha_url, config.ha_token)
loader = ModuleLoader(app, ha, config)
loader.load_all()

# Melchior Custom Icon als Lovelace Resource registrieren
def _register_icon_resource()

# regis-icon.js nach /config/www/ kopieren (für Lovelace Resource)
def _copy_icon_to_www():
    import shutil, os
    src = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist', 'regis-icon.js')
    dst_dir = '/config/www'
    dst = os.path.join(dst_dir, 'regis-icon.js')
    try:
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, dst)
        log.info(f"regis-icon.js nach {dst} kopiert")
    except Exception as e:
        log.warning(f"regis-icon.js konnte nicht kopiert werden: {e}")

_copy_icon_to_www():
    import time, threading
    def _do_register():
        time.sleep(15)  # Warten bis HA vollständig gestartet
        try:
            token = config.ha_long_token or config.ha_token
            if not token:
                log.info("Kein HA Token für Icon-Registrierung")
                return

            # Ingress URL ermitteln
            info = _requests.get(
                "http://supervisor/addons/self/info",
                headers={"Authorization": f"Bearer {config.ha_token}"},
                timeout=5,
            ).json().get("data", {})
            ingress_url = info.get("ingress_url", "")
            if not ingress_url:
                log.warning("Ingress URL nicht gefunden")
                return

            icon_url = f"{ingress_url}regis-icon.js"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            ha_base = "http://supervisor/core"

            # Bestehende Resources abrufen
            r = _requests.get(f"{ha_base}/api/lovelace/resources", headers=headers, timeout=5)
            if r.status_code != 200:
                log.warning(f"Lovelace Resources nicht erreichbar: {r.status_code} — bitte Long-Lived Token in Addon-Einstellungen hinterlegen")
                return

            resources = r.json()
            if any("regis-icon" in str(res.get("url","")) for res in resources):
                log.info("Regis-Lab Icon Resource bereits registriert")
                return

            # Resource registrieren
            r = _requests.post(
                f"{ha_base}/api/lovelace/resources",
                headers=headers,
                json={"res_type": "module", "url": icon_url},
                timeout=5,
            )
            if r.status_code in (200, 201):
                log.info(f"Regis-Lab Icon Resource registriert: {icon_url}")
            else:
                log.warning(f"Icon Resource Registrierung fehlgeschlagen: {r.status_code}")
        except Exception as e:
            log.warning(f"Icon Resource Registrierung Fehler: {e}")

    threading.Thread(target=_do_register, daemon=True).start()

_register_icon_resource()

# regis-icon.js nach /config/www/ kopieren (für Lovelace Resource)
def _copy_icon_to_www():
    import shutil, os
    src = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist', 'regis-icon.js')
    dst_dir = '/config/www'
    dst = os.path.join(dst_dir, 'regis-icon.js')
    try:
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, dst)
        log.info(f"regis-icon.js nach {dst} kopiert")
    except Exception as e:
        log.warning(f"regis-icon.js konnte nicht kopiert werden: {e}")

_copy_icon_to_www()

# ── WebSocket ─────────────────────────────────────────────────────
@sock.route("/ws")
def ws_root(ws):
    _ws_handler(ws)

@sock.route("/<path:prefix>/ws")
def ws_ingress(ws, prefix):
    _ws_handler(ws)

def _ws_handler(ws):
    log.info("WebSocket client verbunden")
    try:
        ha.register_ws_client(ws)
        while True:
            data = ws.receive()
            if data is None:
                break
            msg = json.loads(data)
            loader.handle_ws_message(ws, msg)
    except Exception as e:
        log.warning(f"WebSocket Fehler: {e}")
    finally:
        ha.unregister_ws_client(ws)

# ── Brand-Icon Proxy ──────────────────────────────────────────────
@app.route("/api/brand-icon/<path:domain>")
def brand_icon(domain):
    """Proxy für HA Brand-Icons — nutzt Supervisor-Token."""
    try:
        r = _requests.get(
            f"http://supervisor/core/api/brands/integration/{domain}/dark_icon.png",
            headers={"Authorization": f"Bearer {config.ha_token}"},
            timeout=5,
        )
        if r.status_code == 200:
            return Response(
                r.content,
                content_type=r.headers.get("content-type", "image/png"),
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        log.warning(f"Brand-Icon Fehler für {domain}: {e}")
    return Response(status=404)

# ── Core API ──────────────────────────────────────────────────────
@app.route("/api/health")
@app.route("/<path:p>/api/health")
def health(p=None):
    return jsonify({"status": "ok", "version": config.version if hasattr(config, "version") else "1.0.14"})

@app.route("/api/config")
@app.route("/<path:p>/api/config")
def get_config(p=None):
    return jsonify(config.frontend_config())

@app.route("/api/modules")
@app.route("/<path:p>/api/modules")
def list_modules(p=None):
    return jsonify(loader.module_info())

# ── Icon-Registrierung on-demand ─────────────────────────────────────
@app.route("/api/register-icon", methods=["POST"])
def register_icon():
    """Registriert das Melchior Custom Icon als Lovelace Resource via WebSocket."""
    import json as _json
    import threading as _threading
    import websocket as _ws_lib

    token = config.ha_long_token
    if not token:
        return jsonify({"ok": False, "error": "Kein Token konfiguriert"})
    try:
        # Ingress URL ermitteln
        info = _requests.get(
            "http://supervisor/addons/self/info",
            headers={"Authorization": f"Bearer {config.ha_token}"},
            timeout=5,
        ).json().get("data", {})
        ingress_url = info.get("ingress_url", "")
        if not ingress_url:
            return jsonify({"ok": False, "error": "Ingress URL nicht gefunden"})
        icon_url = f"{ingress_url}regis-icon.js"

        result = [None]
        done   = _threading.Event()

        def on_message(ws, raw):
            msg = _json.loads(raw)
            t   = msg.get("type")
            if t == "auth_required":
                ws.send(_json.dumps({"type": "auth", "access_token": token}))
            elif t == "auth_ok":
                ws.send(_json.dumps({"id": 1, "type": "lovelace/resources"}))
            elif t == "result" and msg.get("id") == 1:
                resources = msg.get("result", [])
                if any("regis-icon" in str(r.get("url","")) for r in resources):
                    result[0] = {"ok": True, "msg": "Bereits registriert"}
                    ws.close()
                    done.set()
                    return
                # Resource hinzufügen
                ws.send(_json.dumps({
                    "id": 2,
                    "type": "lovelace/resources/create",
                    "res_type": "module",
                    "url": icon_url,
                }))
            elif t == "result" and msg.get("id") == 2:
                if msg.get("success"):
                    result[0] = {"ok": True}
                    log.info(f"Regis-Lab Icon registriert: {icon_url}")
                else:
                    result[0] = {"ok": False, "error": str(msg.get("error", "Unbekannt"))}
                ws.close()
                done.set()

        def on_error(ws, err):
            result[0] = {"ok": False, "error": str(err)}
            done.set()

        def on_close(ws, *args): done.set()

        ws_url = "ws://192.168.0.222:8123/api/websocket"
        ws = _ws_lib.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        _threading.Thread(target=ws.run_forever, daemon=True).start()
        done.wait(timeout=10)

        return jsonify(result[0] or {"ok": False, "error": "Timeout"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ── Frontend (SPA-Fallback) ───────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if any(path.startswith(x) for x in ("api/", "ws")):
        return jsonify({"error": "not found"}), 404
    full = os.path.join(FRONTEND_DIST, path)
    if path and os.path.exists(full):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8099))
    log.info(f"Regis-Lab startet auf Port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
