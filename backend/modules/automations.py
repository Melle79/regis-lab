"""
Modul: automations
Zeigt HA-interne Entities: Automationen, Skripte, Szenen, Helfer, Timer etc.
"""
from flask import jsonify, request
from modules.base import BaseModule

# Domains die zu diesem Modul gehören
AUTOMATION_DOMAINS = {
    'automation', 'script', 'scene',
    'input_boolean', 'input_number', 'input_select', 'input_text',
    'input_datetime', 'input_button', 'timer', 'counter',
    'schedule', 'todo', 'calendar',
}

PERSON_DOMAINS = {
    'person', 'device_tracker', 'zone',
}

# Diese Domains gehören zu echten Geräten und sollen in Bereiche
DEVICE_DOMAINS = {
    'light', 'switch', 'sensor', 'binary_sensor', 'climate', 'cover',
    'fan', 'media_player', 'camera', 'lock', 'alarm_control_panel',
    'vacuum', 'water_heater', 'humidifier', 'valve', 'lawn_mower',
    'remote', 'siren', 'update', 'number', 'select', 'button', 'text',
    'weather', 'air_quality', 'event',
}


class Module(BaseModule):
    name    = "automations"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/automations")
        def get_automations():
            states  = self.ha.get_cached_states()
            result  = {}

            for eid, state in states.items():
                domain = eid.split('.')[0]
                if domain in AUTOMATION_DOMAINS:
                    if domain not in result:
                        result[domain] = []
                    result[domain].append(state)

            # Sortieren
            for domain in result:
                result[domain].sort(key=lambda e: e.get('attributes', {}).get('friendly_name', e['entity_id']))

            return jsonify({
                "groups": [
                    {"domain": d, "label": DOMAIN_LABELS.get(d, d), "entities": result[d]}
                    for d in sorted(result.keys(), key=lambda d: DOMAIN_ORDER.get(d, 99))
                ]
            })

        @self.app.route("/api/persons")
        def get_persons():
            states = self.ha.get_cached_states()
            persons = []
            trackers = []
            zones = []

            for eid, state in states.items():
                domain = eid.split('.')[0]
                if domain == 'person':
                    persons.append(state)
                elif domain == 'device_tracker':
                    trackers.append(state)
                elif domain == 'zone':
                    zones.append(state)

            return jsonify({
                "persons":  sorted(persons,  key=lambda e: e.get('attributes', {}).get('friendly_name', e['entity_id'])),
                "trackers": sorted(trackers, key=lambda e: e.get('attributes', {}).get('friendly_name', e['entity_id'])),
                "zones":    sorted(zones,    key=lambda e: e.get('attributes', {}).get('friendly_name', e['entity_id'])),
            })

        self.log.info("Automations-Modul registriert")


DOMAIN_LABELS = {
    'automation':     'Automationen',
    'script':         'Skripte',
    'scene':          'Szenen',
    'input_boolean':  'Schalter (Helfer)',
    'input_number':   'Zahlen (Helfer)',
    'input_select':   'Auswahl (Helfer)',
    'input_text':     'Text (Helfer)',
    'input_datetime': 'Datum/Zeit (Helfer)',
    'input_button':   'Buttons (Helfer)',
    'timer':          'Timer',
    'counter':        'Zähler',
    'schedule':       'Zeitpläne',
    'todo':           'To-do Listen',
    'calendar':       'Kalender',
}

DOMAIN_ORDER = {
    'automation': 0, 'script': 1, 'scene': 2,
    'input_boolean': 3, 'input_number': 4, 'input_select': 5,
    'input_text': 6, 'input_datetime': 7, 'input_button': 8,
    'timer': 9, 'counter': 10, 'schedule': 11,
    'todo': 12, 'calendar': 13,
}
