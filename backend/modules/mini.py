"""
Zugriff auf den Mac mini: Dateien lesen/schreiben und Befehle ausfuehren per SSH.

Der Schluessel liegt in /data (bleibt beim Neubau erhalten) und wird beim ersten
Zugriff erzeugt. Sein oeffentlicher Teil wird in den Einstellungen angezeigt und
muss am mini in ~/.ssh/authorized_keys stehen.

Weil am mini dieselben Arbeitskopien liegen, die auch VS Code geoeffnet hat,
sind Aenderungen sofort in beiden sichtbar - eine Synchronisation braucht es
dafuer nicht.
"""
import base64
import json
import logging
import os
import re
import shlex
import subprocess
import time

log = logging.getLogger("regis_lab.mini")

DEFAULT_KEY = "/data/regis_mini_key"
DEFAULT_ROOT = "/Users/sven/Vibe_Coding"
DEFAULT_CLINE_DIR = "/Users/sven/.cline/data"


def key_path(cfg):
    return (cfg.get("mini_key_path") or "").strip() or DEFAULT_KEY


def ensure_key(path=None):
    """Erzeugt das Schluesselpaar, falls noetig. Gibt (privat, oeffentlich)."""
    path = path or DEFAULT_KEY
    if os.path.exists(path) and os.path.exists(path + ".pub"):
        return path, path + ".pub"
    os.makedirs(os.path.dirname(path) or "/data", exist_ok=True)
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-C", "regis-lab", "-f", path],
        check=True, capture_output=True,
    )
    os.chmod(path, 0o600)
    return path, path + ".pub"


def pubkey_text(path=None):
    try:
        _priv, pub = ensure_key(path)
        with open(pub) as f:
            return f.read().strip()
    except Exception as e:
        log.error(f"Schluessel nicht lesbar: {e}")
        return ""


def ssh_run(cfg, command, timeout=60, stdin_data=None):
    """Fuehrt einen Befehl auf dem mini aus. Gibt (Rueckgabecode, Ausgabe)."""
    host = (cfg.get("mini_host") or "").strip()
    user = (cfg.get("mini_user") or "sven").strip()
    if not host:
        return 127, "kein Host konfiguriert"
    try:
        priv, _pub = ensure_key(cfg.get("mini_key_path"))
    except Exception as e:
        return 126, f"Schluessel nicht erzeugbar: {e}"
    args = [
        "ssh", "-i", priv,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=8",
        "-o", "ServerAliveInterval=30",
        f"{user}@{host}", command,
    ]
    try:
        r = subprocess.run(args, input=stdin_data, capture_output=True, text=True, timeout=timeout)
        out = r.stdout or ""
        err = r.stderr or ""
        # SSH-Warnungen (z. B. "Permanently added ... to the list of known hosts")
        # nicht in die Nutzausgabe mischen - sie zerstoeren sonst JSON-Antworten
        # (z. B. die sqlite3-Ausgabe fuer die Cline-Chats).
        err = "\n".join(l for l in err.splitlines() if l.strip()
                        and "Permanently added" not in l)
        if err.strip():
            out = out + ("" if (not out or out.endswith("\n")) else "\n") + err + "\n"
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return 124, f"Zeitueberschreitung nach {timeout}s"
    except Exception as e:
        return 125, str(e)


def root_of(cfg):
    return ((cfg.get("mini_root") or "").strip() or DEFAULT_ROOT).rstrip("/")


def safe_path(cfg, path):
    """Erzwingt einen Pfad innerhalb der Wurzel (kein Ausbruch nach oben)."""
    root = root_of(cfg)
    p = (path or "").strip()
    if not p:
        return None
    if p.startswith("~"):
        p = p[1:]
    absolute = p if p.startswith("/") else root + "/" + p
    parts = []
    for seg in absolute.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    norm = "/" + "/".join(parts)
    if norm != root and not norm.startswith(root + "/"):
        return None
    return norm


def read_file(cfg, path, max_bytes=200000):
    p = safe_path(cfg, path)
    if not p:
        return {"error": f"Pfad ausserhalb der Wurzel: {path}"}
    rc, out = ssh_run(cfg, f"cat {shlex.quote(p)}", timeout=30)
    if rc != 0:
        return {"error": out.strip()[:300]}
    if len(out) > max_bytes:
        return {"path": p, "content": out[:max_bytes], "truncated": True}
    return {"path": p, "content": out}


def write_file(cfg, path, content):
    p = safe_path(cfg, path)
    if not p:
        return {"error": f"Pfad ausserhalb der Wurzel: {path}"}
    data = base64.b64encode((content or "").encode("utf-8")).decode("ascii")
    cmd = "mkdir -p \"$(dirname %s)\" && base64 -d > %s" % (shlex.quote(p), shlex.quote(p))
    rc, out = ssh_run(cfg, cmd, timeout=60, stdin_data=data)
    if rc != 0:
        return {"error": out.strip()[:300]}
    return {"ok": True, "path": p, "bytes": len(content or "")}


def list_dir(cfg, path=""):
    p = safe_path(cfg, path or root_of(cfg))
    if not p:
        return {"error": f"Pfad ausserhalb der Wurzel: {path}"}
    rc, out = ssh_run(cfg, f"ls -la {shlex.quote(p)}", timeout=30)
    if rc != 0:
        return {"error": out.strip()[:300]}
    return {"path": p, "listing": out[:8000]}


def run_shell(cfg, cmd, cwd=""):
    if not (cmd or "").strip():
        return {"error": "cmd fehlt"}
    work = safe_path(cfg, cwd) if (cwd or "").strip() else root_of(cfg)
    if not work:
        return {"error": f"Arbeitsordner ausserhalb der Wurzel: {cwd}"}
    rc, out = ssh_run(cfg, f"cd {shlex.quote(work)} && {cmd}", timeout=180)
    return {"rc": rc, "cwd": work, "output": out[-8000:]}


def run_tool(cfg, tool):
    """Fuehrt ein vom Modell angefragtes mini-Werkzeug aus."""
    action = (tool.get("action") or "").strip().lower()
    if action in ("run", "shell", "cmd", "bash"):
        return run_shell(cfg, tool.get("cmd") or "", tool.get("cwd") or "")
    if action in ("read", "cat", "read_file"):
        return read_file(cfg, tool.get("path") or "")
    if action in ("write", "write_file", "save"):
        return write_file(cfg, tool.get("path") or "", tool.get("content") or "")
    if action in ("list", "ls", "list_dir"):
        return list_dir(cfg, tool.get("path") or "")
    if action == "cline":
        op = (tool.get("op") or "list").strip().lower()
        if op in ("show", "read", "get", "verlauf"):
            return cline_show(cfg, tool.get("id") or "", int(tool.get("limit") or 20))
        return cline_list(cfg, int(tool.get("limit") or 40))
    return {"error": f"unbekannte Aktion: {action}"}


def status(cfg):
    """Kurzbericht ueber die Verbindung zum mini."""
    if not (cfg.get("mini_host") or "").strip():
        return {"ok": False, "error": "kein Host konfiguriert"}
    rc, out = ssh_run(cfg, "hostname; sw_vers -productVersion 2>/dev/null; pwd", timeout=20)
    return {
        "ok": rc == 0,
        "host": (cfg.get("mini_host") or "").strip(),
        "user": (cfg.get("mini_user") or "sven").strip(),
        "root": root_of(cfg),
        "output": out.strip()[:500],
        "rc": rc,
    }


# --------------------------------------------------------------- Cline-Chats

def cline_dir(cfg) -> str:
    return ((cfg.get("cline_dir") or "").strip() or DEFAULT_CLINE_DIR).rstrip("/")


def _message_text(content):
    """Text aus einem Cline-Inhalt holen (String oder Blockliste)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text"):
                parts.append(str(block["text"]).strip())
            elif block.get("type") == "tool_use":
                parts.append("[%s %s]" % (block.get("name", "werkzeug"),
                                          str(block.get("input"))[:120]))
        return "\n".join(p for p in parts if p)
    return ""


def cline_list(cfg, limit=40):
    """Liste der Cline-Chats (Titel, Modell, Zeit) vom mini.

    Die Cline-Datenbank ist waehrend der Arbeit in VS Code oft kurz gesperrt;
    deshalb wird ein unlesbares Ergebnis einmal wiederholt.
    """
    db = cline_dir(cfg) + "/db/sessions.db"
    sql = ("select session_id, provider, model, substr(prompt,1,120) as title, "
           "updated_at from sessions order by updated_at desc limit %d;" % int(limit))
    cmd = "sqlite3 -json %s %s" % (shlex.quote(db), shlex.quote(sql))
    raw = ""
    for attempt in (1, 2):
        rc, out = ssh_run(cfg, cmd, timeout=40)
        raw = out or ""
        if rc != 0:
            return {"error": raw.strip()[:300], "chats": []}
        try:
            return {"chats": json.loads(raw or "[]")}
        except Exception:
            if attempt == 1:
                time.sleep(2)
    return {"error": "Datenbank-Antwort nicht lesbar: " + raw.strip()[:200], "chats": []}


def cline_show(cfg, sid, limit=30, max_chars=1500):
    """Verlauf eines Cline-Chats (letzte Nachrichten) vom mini."""
    if not re.match(r"^[A-Za-z0-9_.-]{1,80}$", sid or ""):
        return {"error": "ungueltige Chat-Kennung"}
    path = "%s/sessions/%s/%s.messages.json" % (cline_dir(cfg), sid, sid)
    raw = ""
    data = None
    for attempt in (1, 2):
        rc, out = ssh_run(cfg, "cat %s" % shlex.quote(path), timeout=90)
        raw = out or ""
        if rc != 0:
            return {"error": raw.strip()[:300]}
        try:
            data = json.loads(raw)
            break
        except Exception:
            data = None
            if attempt == 1:
                time.sleep(1.5)
    if data is None:
        return {"error": "Verlauf nicht lesbar: " + raw.strip()[:200]}
    messages = data.get("messages") or []
    picked = []
    for msg in messages[-int(limit):]:
        text = _message_text(msg.get("content"))
        if not text:
            continue
        picked.append({
            "role": msg.get("role"),
            "ts": msg.get("ts"),
            "text": text[:max_chars],
        })
    return {
        "session": sid,
        "total_messages": len(messages),
        "updated_at": data.get("updated_at"),
        "messages": picked,
    }
