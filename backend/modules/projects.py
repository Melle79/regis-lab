"""
Projektverwaltung fuer Regis-Lab.

Ein Projekt buendelt Chats, Regeln und ein Gedaechtnis - gedacht als
Arbeitsverzeichnis auf dem Mac mini. Das Gedaechtnis liegt im selben Ordner,
den auch Claude Code benutzt (~/.claude/projects/<pfad>/memory/), damit beide
dasselbe wissen.

Sicherheitsnetz: Der Gedaechtnisordner wird aus dem Projektpfad abgeleitet (kein
freier Pfad). Bestehende Notizen werden nie ueberschrieben - neue Notizen kommen
als eigene Datei dazu, in MEMORY.md wird nur eine Zeile angehaengt.
"""
import json
import logging
import os
import re
import uuid
from datetime import datetime

from flask import jsonify, request

from modules import mini
from modules.base import BaseModule
from modules.mini_tools import cfg_of

log = logging.getLogger("regis_lab.projects")

PROJECTS_FILE = "/data/regis_projects.json"
CLAUDE_PROJECTS = "/Users/sven/.claude/projects"
MEMORY_INDEX = "MEMORY.md"
NOTE_MAX = 8000
CONTEXT_MAX = 6000


def load_projects() -> list:
    try:
        with open(PROJECTS_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("projects", [])
        return [p for p in data if isinstance(p, dict) and p.get("id")]
    except FileNotFoundError:
        return []
    except Exception as e:
        log.warning("Projektliste nicht lesbar: %s", e)
        return []


def save_projects(items: list):
    tmp = PROJECTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, PROJECTS_FILE)


def find_project(pid: str):
    for p in load_projects():
        if p.get("id") == pid:
            return p
    return None


def slug_for(path: str) -> str:
    """Aus /Users/sven/Vibe_Coding/x wird -Users-sven-Vibe-Coding-x."""
    p = (path or "").strip().rstrip("/")
    return p.replace("/", "-") if p else ""


def memory_dir(project, cfg=None) -> str:
    """Absoluter Pfad des Gedaechtnisordners auf dem mini.

    Vorrang hat ein direkt hinterlegter Ordner (dann kann das Gedaechtnis von
    Claude Code mitbenutzt werden); sonst wird er aus dem Arbeitspfad abgeleitet.
    """
    explicit = (project.get("memory_dir") or "").strip().rstrip("/")
    if explicit:
        return explicit
    rel = (project.get("path") or "").strip().strip("/")
    if not rel:
        return ""
    cfg = cfg or mini_cfg()
    root = mini.root_of(cfg)
    return "%s/%s/memory" % (CLAUDE_PROJECTS, slug_for("%s/%s" % (root, rel)))


def mini_cfg() -> dict:
    """mini-Konfiguration aus der laufenden App (in register() hinterlegt)."""
    from flask import current_app
    config = current_app.extensions.get("regis_config")
    return cfg_of(config) if config else {}


def _read_mini_file(cfg, abspath: str, max_bytes=NOTE_MAX):
    """Feste Basis (Claude-Code-Ordner) - kein freier Pfad aus der Anfrage."""
    import shlex
    rc, out = mini.ssh_run(cfg, "cat %s" % shlex.quote(abspath), timeout=40)
    return None if rc != 0 else out[:max_bytes]


def _list_mini_dir(cfg, abspath: str):
    import shlex
    rc, out = mini.ssh_run(
        cfg, "ls -1 %s 2>/dev/null | head -400" % shlex.quote(abspath), timeout=40)
    return [l.strip() for l in out.splitlines() if l.strip()] if rc == 0 else []


def _write_mini_file(cfg, abspath: str, content: str):
    import base64
    import shlex
    data = base64.b64encode(content.encode("utf-8")).decode("ascii")
    cmd = 'mkdir -p "$(dirname %s)" && base64 -d > %s' % (
        shlex.quote(abspath), shlex.quote(abspath))
    rc, out = mini.ssh_run(cfg, cmd, timeout=60, stdin_data=data)
    if rc != 0:
        return {"error": out.strip()[:300]}
    return {"ok": True, "path": abspath, "bytes": len(content)}


def memory_overview(project, cfg=None) -> dict:
    """Index und Notiznamen des Projektgedaechtnisses."""
    cfg = cfg or mini_cfg()
    mdir = memory_dir(project, cfg)
    if not mdir:
        return {"dir": "", "index": [], "notes": []}
    names = _list_mini_dir(cfg, mdir)
    idx = _read_mini_file(cfg, "%s/%s" % (mdir, MEMORY_INDEX), 20000) or ""
    return {
        "dir": mdir,
        "index": [l for l in idx.splitlines() if l.strip().startswith("- [")],
        "notes": [n for n in names if n.endswith(".md") and n != MEMORY_INDEX],
    }


def memory_context(project, cfg=None, limit=CONTEXT_MAX) -> str:
    """Regeln + Gedaechtnis eines Projekts als Text fuer den System-Prompt."""
    if not project:
        return ""
    parts = ["\n\nPROJEKT: %s" % (project.get("name") or "ohne Namen")]
    if project.get("path"):
        parts.append("Arbeitsordner auf dem mini (relativ zur Wurzel): %s" % project["path"])
    if project.get("rules"):
        parts.append("Regeln fuer dieses Projekt:\n%s" % project["rules"][:2000])
    try:
        ov = memory_overview(project, cfg)
        if ov.get("index"):
            parts.append("Gedaechtnis - vorhandene Notizen (Index):\n%s"
                         % "\n".join(ov["index"][:60]))
    except Exception as e:
        log.warning("Gedaechtnis nicht lesbar: %s", e)
    return "\n".join(parts)[:limit]


def write_note(project, title: str, text: str, cfg=None) -> dict:
    """Neue Gedaechtnisnotiz anlegen und im Index eintragen."""
    cfg = cfg or mini_cfg()
    title = (title or "").strip()
    text = (text or "").strip()
    if not title or not text:
        return {"error": "Titel und Text noetig"}
    if not project.get("writable"):
        return {"error": "Gedaechtnis ist fuer dieses Projekt nur lesbar"}
    mdir = memory_dir(project, cfg)
    if not mdir:
        return {"error": "Kein Arbeitsordner im Projekt hinterlegt"}

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "notiz"
    fname = "%s.md" % slug
    if fname in _list_mini_dir(cfg, mdir):
        fname = "%s-%s.md" % (slug, datetime.now().strftime("%Y%m%d-%H%M"))

    body = ("---\nname: %s\ndescription: %s\nmetadata:\n  type: project\n"
            "  source: regis-lab\n---\n\n%s\n" % (slug, title[:120], text))
    res = _write_mini_file(cfg, "%s/%s" % (mdir, fname), body)
    if res.get("error"):
        return res

    old = _read_mini_file(cfg, "%s/%s" % (mdir, MEMORY_INDEX), 40000) or ""
    line = "- [%s](%s) - %s" % (title[:60], fname, text.splitlines()[0][:120])
    if line not in old:
        new = (old.rstrip() + "\n" + line + "\n") if old.strip() \
            else ("# Gedaechtnis\n\n" + line + "\n")
        _write_mini_file(cfg, "%s/%s" % (mdir, MEMORY_INDEX), new)
    return {"ok": True, "file": fname, "dir": mdir, "index": MEMORY_INDEX}

class Module(BaseModule):
    name    = "projects"
    version = "1.0.0"

    def register(self):
        # Konfiguration fuer die Modul-Funktionen bereitstellen
        self.app.extensions["regis_config"] = self.config

        @self.app.route("/api/projects")
        def list_projects():
            items = []
            for p in load_projects():
                items.append({
                    "id":         p.get("id"),
                    "name":       p.get("name"),
                    "path":       p.get("path", ""),
                    "memory_dir": p.get("memory_dir", ""),
                    "rules":      p.get("rules", ""),
                    "writable":   bool(p.get("writable")),
                    "updated_at": p.get("updated_at", ""),
                })
            return jsonify({"projects": items})

        @self.app.route("/api/projects/<pid>")
        def get_project(pid):
            p = find_project(pid)
            if not p:
                return jsonify({"error": "Projekt nicht gefunden"}), 404
            cfg = cfg_of(self.config)
            out = dict(p)
            try:
                ov = memory_overview(p, cfg)
                out["memory"] = {"dir": ov["dir"], "count": len(ov["notes"]),
                                 "index": ov["index"][:80], "notes": ov["notes"][:200]}
            except Exception as e:
                out["memory"] = {"dir": "", "count": 0, "index": [], "notes": [],
                                 "error": str(e)}
            return jsonify(out)

        @self.app.route("/api/projects", methods=["POST"])
        def create_project():
            data = request.get_json() or {}
            name = (data.get("name") or "").strip()
            if not name:
                return jsonify({"error": "Name fehlt"}), 400
            now = datetime.now().isoformat()
            item = {
                "id":         str(uuid.uuid4()),
                "name":       name[:80],
                "path":       (data.get("path") or "").strip().strip("/")[:300],
                "memory_dir": (data.get("memory_dir") or "").strip()[:400],
                "rules":      (data.get("rules") or "")[:4000],
                "writable":   bool(data.get("writable")),
                "created_at": now,
                "updated_at": now,
            }
            items = load_projects() + [item]
            save_projects(items)
            return jsonify(item)

        @self.app.route("/api/projects/<pid>", methods=["PATCH"])
        def update_project(pid):
            data = request.get_json() or {}
            items = load_projects()
            for p in items:
                if p.get("id") != pid:
                    continue
                if "name" in data:
                    p["name"] = (data.get("name") or "").strip()[:80] or p.get("name")
                if "path" in data:
                    p["path"] = (data.get("path") or "").strip().strip("/")[:300]
                if "memory_dir" in data:
                    p["memory_dir"] = (data.get("memory_dir") or "").strip()[:400]
                if "rules" in data:
                    p["rules"] = (data.get("rules") or "")[:4000]
                if "writable" in data:
                    p["writable"] = bool(data.get("writable"))
                p["updated_at"] = datetime.now().isoformat()
                save_projects(items)
                return jsonify(p)
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        @self.app.route("/api/projects/<pid>", methods=["DELETE"])
        def delete_project(pid):
            items = [p for p in load_projects() if p.get("id") != pid]
            save_projects(items)
            return jsonify({"ok": True})

        @self.app.route("/api/projects/<pid>/note", methods=["POST"])
        def add_note(pid):
            p = find_project(pid)
            if not p:
                return jsonify({"error": "Projekt nicht gefunden"}), 404
            data = request.get_json() or {}
            res = write_note(p, data.get("title") or "", data.get("text") or "",
                             cfg_of(self.config))
            if res.get("error"):
                return jsonify(res), 400
            return jsonify(res)

