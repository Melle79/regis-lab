"""
Modul: settings
Liest und speichert Dashboard-Einstellungen.
"""
import requests
from flask import jsonify, request
from modules.base import BaseModule


class Module(BaseModule):
    name    = "settings"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/settings")
        def get_settings():
            return jsonify(self.config.frontend_config())

        @self.app.route("/api/settings", methods=["POST"])
        def save_settings():
            data = request.get_json() or {}
            allowed = [
                "title", "theme", "show_clock", "show_weather", "weather_entity",
                "ki_name", "ha_token", "jarvis_ollama_url", "jarvis_model",
                "jarvis_temperature", "jarvis_max_tokens", "jarvis_system_prompt", "jarvis_ha_control", "tab_order", "filter_labels", "briefing_targets", "briefing_time", "briefing_enabled", "ha_external_url", "jarvis_provider", "anthropic_api_key", "use_anthropic_fallback", "suggestions_enabled", "suggestions_time",
            ]
            updates = {k: v for k, v in data.items() if k in allowed}
            # Token nur speichern wenn nicht leer
            if "ha_token" in updates and not updates["ha_token"]:
                del updates["ha_token"]
            self.config.save_settings(updates)
            # Label-Filter Cache aktualisieren
            if "filter_labels" in updates:
                import threading
                threading.Thread(target=self._reload_label_cache, daemon=True).start()
            return jsonify({"ok": True})

        @self.app.route("/api/validate-token", methods=["POST"])
        def validate_token():
            """HA Long-Lived Token validieren."""
            data  = request.get_json() or {}
            token = data.get("token", "")
            if not token:
                return jsonify({"ok": False, "error": "Kein Token"})
            try:
                import requests as _req
                # Direkt gegen HA (Long-Lived Token funktioniert nur hier)
                r = _req.get(
                    "http://homeassistant.local.hass.io:8123/api/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5,
                )
                return jsonify({"ok": r.status_code == 200})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)})

        @self.app.route("/api/user")
        def get_user():
            """Gibt den aktuell konfigurierten HA-Benutzer zurück."""
            import requests as _req
            token = self.config.ha_long_token
            try:
                r = _req.get(
                    "http://homeassistant.local.hass.io:8123/api/",
                    headers={"Authorization": "Bearer " + token},
                    timeout=5,
                )
                # Token-Info via /auth/token endpoint
                r2 = _req.get(
                    "http://homeassistant.local.hass.io:8123/auth/userinfo",
                    headers={"Authorization": "Bearer " + token},
                    timeout=5,
                )
                if r2.status_code == 200:
                    d = r2.json()
                    return jsonify({"name": d.get("name", ""), "username": d.get("username", "")})
            except Exception:
                pass
            return jsonify({"name": "", "username": ""})

        @self.app.route("/api/settings/labels")
        def get_labels():
            """Alle Labels aus gecachter Registry."""
            all_labels = list(getattr(self.config, "_all_labels", {}).values())
            filtered   = self.config._settings.get("filter_labels", [])
            return jsonify({"labels": all_labels, "filter_labels": filtered})

        @self.app.route("/api/settings/notify-services")
        def get_notify_services():
            """Alle verfügbaren notify.*-Services aus HA laden."""
            token = self.config.ha_long_token
            ha    = "http://homeassistant.local.hass.io:8123"
            hdrs  = {"Authorization": "Bearer " + token}
            try:
                r = requests.get(ha + "/api/services", headers=hdrs, timeout=10)
                services = r.json() if r.status_code == 200 else []
                notify = []
                for domain in services:
                    if domain.get("domain") == "notify":
                        for svc_name in domain.get("services", {}).keys():
                            if svc_name.startswith("mobile_app_"):
                                notify.append({
                                    "id":   svc_name,
                                    "name": svc_name.replace("mobile_app_", "").replace("_", " ").title()
                                })
                return jsonify({"services": notify})
            except Exception as e:
                return jsonify({"services": [], "error": str(e)})

        self.log.info("Settings-Modul registriert")

    def _reload_label_cache(self):
        """Label-Filter Cache nach Einstellungsänderung neu laden."""
        try:
            # areas Modul finden und _preload_labels aufrufen
            from modules.areas import Module as AreasModule
            for mod in getattr(self, '_siblings', []):
                if isinstance(mod, AreasModule):
                    mod._preload_labels()
                    return
            # Fallback: nur filter_ids aus vorhandenem _all_labels neu berechnen
            all_labels = getattr(self.config, '_all_labels', {})
            if not all_labels:
                self.log.warning("Label-Cache leer, überspringe Reload")
                return
            filter_labels = set(self.config._settings.get("filter_labels", []))
            # Entity-IDs aus HA holen und filtern
            import requests
            ha   = "http://homeassistant.local.hass.io:8123"
            hdrs = {"Authorization": "Bearer " + self.config.ha_long_token}
            r = requests.get(ha + "/api/template", headers=hdrs,
                json={"template": "{{ states | map(attribute='entity_id') | list }}"}, timeout=10)
            filtered = set()
            if r.status_code == 200:
                # Vereinfacht: Labels aus gecachtem _all_labels verwenden
                pass
            self.config._label_filtered_ids = filtered
            self.log.info(f"Label-Cache aktualisiert (Fallback): {len(filtered)} gefiltert")
        except Exception as e:
            self.log.warning(f"Label-Cache-Reload fehlgeschlagen: {e}")
