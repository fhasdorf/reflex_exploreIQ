"""
search_state.py — Gemeinsamer State für Prospektivitäts-Suche
Klebstoff zwischen Suchseite und Claim-Karte.
"""

import json
import re
import reflex as rx


# ---------------------------------------------------------------------------
# Mineral-Konfiguration
# ---------------------------------------------------------------------------

MINERALS: dict[str, dict] = {
    "Ag": {
        "label": "Silber",
        "symbol": "Ag",
        "proxies": [
            {
                "symbol": "Pb",
                "name": "Blei (Pb)",
                "desc": "Silber oft im Bleiglanz (Galenit) gebunden.",
                "default": 40,
            },
            {
                "symbol": "Zn",
                "name": "Zink (Zn)",
                "desc": "Zinkblende-Systeme führen häufig Silber.",
                "default": 35,
            },
            {
                "symbol": "Sb",
                "name": "Antimon (Sb)",
                "desc": "Typischer Begleiter in hydrothermalen Silbersystemen.",
                "default": 25,
            },
        ],
        "keywords": re.compile(
            r"\bAg\b|Sølv|Silver|Argentum|Sølvglans|Argentit|"
            r"Acanthit|Stephanit|Pyrargyrit|Proustit|Edelmetall",
            re.IGNORECASE,
        ),
        "proxy_keywords": {
            "Pb": re.compile(r"\bPb\b|Bly|Blei|Galenit|Blyglans", re.IGNORECASE),
            "Zn": re.compile(r"\bZn\b|Sink|Zink|Sphalerit|Zinkblende", re.IGNORECASE),
            "Sb": re.compile(r"\bSb\b|Antimon|Stibion|Stibnit", re.IGNORECASE),
        },
    },
    # Hier weitere Minerale ergänzen (Cu, Co, Li …)
}

# Spalten im Bergrettigheter-CSV, die als Suchtext herangezogen werden
TEXT_COLUMNS = [
    "Bergverkstype",   # z. B. "Statens Mineralrettigheter"
    "Søker",           # Antragsteller
    "Hjemmelshaver",   # Rechteinhaber
    "Merknad",         # Bemerkung / Freitext
    "Malm",            # Erz-Typ
    "Mineral",         # Mineraltyp
]


# ---------------------------------------------------------------------------
# Scoring-Logik (pure Python, kein GIS nötig)
# ---------------------------------------------------------------------------

def _score_feature(feature: dict, mineral_key: str, weights: dict[str, int]) -> float:
    """
    Berechnet den Prospektivitäts-Score für ein einzelnes GeoJSON-Feature.

    Score = Keyword-Match (Mineral) × 100
          + Σ(Proxy-Match_i × Gewicht_i)

    Gewichte werden normiert, damit die Summe immer auf 100 skaliert.
    Rückgabe: float [0, 200+] — höher = prospektiver.
    """
    cfg = MINERALS.get(mineral_key)
    if cfg is None:
        return 0.0

    props = feature.get("properties") or {}
    text = " ".join(str(props.get(c, "")) for c in TEXT_COLUMNS)

    # Mineral-Haupttreffer
    score = 100.0 if cfg["keywords"].search(text) else 0.0

    # Proxy-Treffer gewichtet
    total_weight = sum(weights.values()) or 1
    for proxy_symbol, pattern in cfg["proxy_keywords"].items():
        if pattern.search(text):
            w = weights.get(proxy_symbol, 0)
            score += (w / total_weight) * 100.0

    return round(score, 1)


def _run_search(
    bergr_geojson_str: str,
    mineral_key: str,
    weights: dict[str, int],
) -> tuple[str, list[dict]]:
    """
    Führt die Suche auf dem Bergrettigheter-GeoJSON durch.

    Gibt zurück:
      - scored_geojson: GeoJSON-String mit feature.properties.score
      - result_rows: Liste von Dicts für die Ergebnis-Tabelle
    """
    try:
        fc = json.loads(bergr_geojson_str)
    except Exception:
        return bergr_geojson_str, []

    result_rows: list[dict] = []

    for feature in fc.get("features", []):
        s = _score_feature(feature, mineral_key, weights)
        props = feature.setdefault("properties", {})
        props["_score"] = s
        props["_score_label"] = f"{s:.0f} Pkt"

        if s > 0:
            result_rows.append(
                {
                    "name": props.get("Hjemmelshaver") or props.get("Søker") or "–",
                    "type": props.get("Bergverkstype", "–"),
                    "mineral": props.get("Mineral") or props.get("Malm") or "–",
                    "score": s,
                    "score_label": f"{s:.0f}",
                }
            )

    result_rows.sort(key=lambda r: r["score"], reverse=True)
    return json.dumps(fc), result_rows


# ---------------------------------------------------------------------------
# Reflex State
# ---------------------------------------------------------------------------

class SearchState(rx.State):
    """
    Gemeinsamer State für Prospektivitäts-Suche und Claim-Karte.

    Felder:
      mineral         — aktives Mineral ("Ag", "Cu" …)
      weights         — {proxy_symbol: int} — Nutzer-Gewichtung
      is_running      — Spinner während der Suche
      scored_geojson  — GeoJSON-String mit _score-Feld je Feature
      result_rows     — Tabellen-Zeilen [{name, type, mineral, score_label}]
      result_count    — Anzahl Treffer (Score > 0)
    """

    mineral: str = "Ag"
    weights: dict[str, int] = {"Pb": 40, "Zn": 35, "Sb": 25}

    is_running: bool = False
    scored_geojson: str = ""
    result_rows: list[dict] = []
    result_count: int = 0

    # ----- Setter -----

    def set_mineral(self, mineral: str):
        """Mineral wechseln und Gewichte auf Defaults zurücksetzen."""
        self.mineral = mineral
        cfg = MINERALS.get(mineral, {})
        self.weights = {
            p["symbol"]: p["default"] for p in cfg.get("proxies", [])
        }
        self.scored_geojson = ""
        self.result_rows = []
        self.result_count = 0

    def set_weight(self, symbol: str, value: int):
        """Einzelnes Proxy-Gewicht aktualisieren."""
        try:
            self.weights = {**self.weights, symbol: max(0, min(100, int(value)))}
        except (ValueError, TypeError):
            pass

    # ----- Computed Vars -----

    @rx.var
    def weight_total(self) -> int:
        return sum(self.weights.values())

    @rx.var
    def proxies_config(self) -> list[dict]:
        """Gibt die Proxy-Konfiguration des aktiven Minerals zurück."""
        cfg = MINERALS.get(self.mineral, {})
        return [
            {**p, "weight": self.weights.get(p["symbol"], p["default"])}
            for p in cfg.get("proxies", [])
        ]

    @rx.var
    def mineral_label(self) -> str:
        cfg = MINERALS.get(self.mineral, {})
        return cfg.get("label", self.mineral)

    @rx.var
    def has_results(self) -> bool:
        return self.result_count > 0

    # ----- Events -----

    async def run_search(self):
        """
        Hauptevent: Startet Scoring auf dem Bergrettigheter-GeoJSON.
        Läuft als async Generator (yield für Spinner).
        """
        # Lazy import verhindert zirkulären Import beim App-Start
        import importlib
        _mod = importlib.import_module("mineral_app.mineral_app")
        _BERGR_GEOJSON = _mod._BERGR_GEOJSON

        self.is_running = True
        self.result_rows = []
        self.result_count = 0
        yield  # UI aktualisieren → Spinner sichtbar

        scored, rows = _run_search(_BERGR_GEOJSON, self.mineral, self.weights)
        self.scored_geojson = scored
        self.result_rows = rows
        self.result_count = len(rows)
        self.is_running = False
        # MapState informieren — so wird scored_geojson JSON-serialisierbar übergeben
        from mineral_app.mineral_app import MapState
        yield MapState.set_scored_geojson(scored)

    def reset_search(self):
        self.scored_geojson = ""
        self.result_rows = []
        self.result_count = 0
        from mineral_app.mineral_app import MapState
        return MapState.set_scored_geojson("")
