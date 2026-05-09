# -*- coding: utf-8 -*-
# @Author: Frank Hasdorf
# @Date:   06-05-2026 18:11:40
# @Last Modified by:   Frank Hasdorf
# @Last Modified time: 06-05-2026 19:00:01
"""
mineral_app.py — NGU WMS + Claims Dashboard (Reflex)
Ersetzt die Streamlit map3.py
"""

import reflex as rx
import json
import os

# ---------------------------------------------------------------------------
# WMS Layer Konfiguration
# ---------------------------------------------------------------------------

WMS_LAYERS = {
    "Berggrunn — Kombiniert (alle Maßstäbe)": {
        "url": "https://geo.ngu.no/mapserver/BerggrunnWMS3?",
        "layer": "Berggrunn_sammenstilt_hovedbergarter",
        "opacity": 0.55,
        "gruppe": "Berggrunn",
        "desc": "Wechselt automatisch zwischen N50/N250/N1350 je Zoom.",
    },
    "Berggrunn — National 1:1.35M": {
        "url": "https://geo.ngu.no/mapserver/BerggrunnWMS3?",
        "layer": "Berggrunn_nasjonal_hovedbergarter",
        "opacity": 0.55,
        "gruppe": "Berggrunn",
        "desc": "Nationaler Überblick 1:1.350.000 — für geringen Zoom.",
    },
    "Berggrunn — Regional 1:250k": {
        "url": "https://geo.ngu.no/mapserver/BerggrunnWMS3?",
        "layer": "Berggrunn_regional_hovedbergarter",
        "opacity": 0.55,
        "gruppe": "Berggrunn",
        "desc": "Regionaler Maßstab 1:250.000 — mittlerer Zoom.",
    },
    "Berggrunn — Störungszonen": {
        "url": "https://geo.ngu.no/mapserver/BerggrunnWMS3?",
        "layer": "Berggrunn_sammenstilt_linearstrukturer",
        "opacity": 0.85,
        "gruppe": "Berggrunn",
        "desc": "Störungszonen — hydrothermale Kontrolle.",
    },
    "Metalle — Silber": {
        "url": "https://geo.ngu.no/mapserver/MetalsWMS2?",
        "layer": "Silver",
        "opacity": 0.9,
        "gruppe": "Metalle",
        "desc": "Alle NGU-Silbervorkommen.",
    },
    "Metalle — Edelmetalle gesamt": {
        "url": "https://geo.ngu.no/mapserver/MetalsWMS2?",
        "layer": "Precious_metals_compile",
        "opacity": 0.8,
        "gruppe": "Metalle",
        "desc": "Au + Ag + PGE Vorkommen.",
    },
    "Metalle — Gold": {
        "url": "https://geo.ngu.no/mapserver/MetalsWMS2?",
        "layer": "Gold",
        "opacity": 0.9,
        "gruppe": "Metalle",
        "desc": "Goldvorkommen — Paragenese mit Silber.",
    },
    "Metalle — Kobalt": {
        "url": "https://geo.ngu.no/mapserver/MetalsWMS2?",
        "layer": "Cobalt",
        "opacity": 0.9,
        "gruppe": "Metalle",
        "desc": "Kobalt — EU Critical Mineral.",
    },
    "Metalle — Basismetalle": {
        "url": "https://geo.ngu.no/mapserver/MetalsWMS2?",
        "layer": "Base_metals_compile",
        "opacity": 0.7,
        "gruppe": "Metalle",
        "desc": "Pb/Zn/Cu — Proxy für Silber.",
    },
    "Industrimineral — Flusspat": {
        "url": "https://geo.ngu.no/mapserver/IndustrialMineralsWMS3?",
        "layer": "Fluorspar",
        "opacity": 0.9,
        "gruppe": "Industrimineral",
        "desc": "Flusspat — EU Critical Mineral.",
    },
    "Industrimineral — Baryt": {
        "url": "https://geo.ngu.no/mapserver/IndustrialMineralsWMS3?",
        "layer": "Barite",
        "opacity": 0.9,
        "gruppe": "Industrimineral",
        "desc": "Baryt — Proxy hydrothermale Systeme.",
    },
    "Industrimineral — Alle Punkte": {
        "url": "https://geo.ngu.no/mapserver/IndustrialMineralsWMS3?",
        "layer": "Point_Industrial_minerals",
        "opacity": 0.8,
        "gruppe": "Industrimineral",
        "desc": "Alle Industrimineral-Vorkommen.",
    },
    "Geophysik — Magnetische Anomalie": {
        "url": "https://geo.ngu.no/mapserver/GeofysikkWMS4?",
        "layer": "Magnetic_anomaly_compilation_norway_raster",
        "opacity": 0.6,
        "gruppe": "Geophysik",
        "desc": "Magnetische Anomaliekarte.",
    },
    "Geophysik — Airborne Survey": {
        "url": "https://geo.ngu.no/mapserver/GeofysikkWMS4?",
        "layer": "Airborne_geophysics_surveys",
        "opacity": 0.7,
        "gruppe": "Geophysik",
        "desc": "Gebiete mit Airborne-Surveys.",
    },
    "Geophysik — Bodengeophysik": {
        "url": "https://geo.ngu.no/mapserver/GeofysikkWMS4?",
        "layer": "Ground_purpose_overview_minres",
        "opacity": 0.8,
        "gruppe": "Geophysik",
        "desc": "Bodengeophysik Mineralressourcen.",
    },
}

GRUPPEN = ["Berggrunn", "Metalle", "Industrimineral", "Geophysik"]

# Pfade zu Geodaten (relativ zum Projektroot)
E29_PATH = "../geodaten/element29_claims.geojson"
BERGR_PATH = "../geodaten/bergrettigheter.csv"


# ---------------------------------------------------------------------------
# GeoJSON laden (einmalig beim Start)
# ---------------------------------------------------------------------------

def _load_e29_geojson() -> str:
    """Lädt Element29 GeoJSON und gibt es als JSON-String zurück."""
    try:
        import geopandas as gpd
        import pandas as pd
        gdf = gpd.read_file(E29_PATH)
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")
        # BOM und Encoding-Artefakte in Spaltennamen fixen
        gdf.columns = [c.encode("utf-8").decode("utf-8-sig").strip() for c in gdf.columns]
        # Datetime → String
        for col in gdf.columns:
            if col == "geometry":
                continue
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.strftime("%Y-%m-%d").fillna("")
            else:
                gdf[col] = gdf[col].astype(str).replace("NaT", "").replace("nan", "")
        return gdf.to_json()
    except Exception as e:
        print(f"E29 Ladefehler: {e}")
        return '{"type":"FeatureCollection","features":[]}'


def _load_bergr_geojson() -> str:
    """Lädt Bergrettigheter CSV, konvertiert Polygone und gibt GeoJSON zurück."""
    try:
        import geopandas as gpd
        import pandas as pd
        from shapely import wkt
        from datetime import datetime

        df = pd.read_csv(BERGR_PATH, sep=";", encoding="utf-8-sig")
        # Geometrie-Spalte parsen
        geom_col = next((c for c in df.columns if "Geometri" in c or "geom" in c.lower()), None)
        if geom_col is None:
            return '{"type":"FeatureCollection","features":[]}'
        df["geometry"] = df[geom_col].apply(lambda x: wkt.loads(x) if pd.notna(x) else None)
        gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
        gdf = gdf.drop(columns=[geom_col], errors="ignore")

        # Alters-Farbe berechnen
        dato_col = next((c for c in gdf.columns if c.lower() == "mottatt"), None)
        def age_color(val):
            if not val or str(val) in ("", "nan", "NaT"):
                return "#9E9E9E"
            try:
                age = (datetime.now() - datetime.strptime(str(val)[:10], "%Y-%m-%d")).days
                if age < 365:      return "#5D8A6B"
                elif age < 1095:   return "#8A7D5D"
                elif age < 3650:   return "#8A6040"
                else:              return "#6B4226"
            except Exception:
                return "#9E9E9E"

        if dato_col:
            gdf["_fill"] = gdf[dato_col].apply(age_color)
        else:
            gdf["_fill"] = "#8A7D5D"

        # Datetime → String
        for col in gdf.columns:
            if col == "geometry":
                continue
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.strftime("%Y-%m-%d").fillna("")
            else:
                gdf[col] = gdf[col].astype(str).replace("NaT", "").replace("nan", "")

        return gdf.to_json()
    except Exception as e:
        print(f"Bergrettigheter Ladefehler: {e}")
        return '{"type":"FeatureCollection","features":[]}'


# GeoJSON einmalig laden
_E29_GEOJSON   = _load_e29_geojson()
_BERGR_GEOJSON = _load_bergr_geojson()



# ---------------------------------------------------------------------------
# App State
# ---------------------------------------------------------------------------

class MapState(rx.State):
    # Basemap
    basemap: str = "dark"  # "dark" | "satellite"

    # Aktive WMS-Layer (Set als Dict wegen Reflex-Serialisierung)
    active_layers: dict[str, bool] = {name: False for name in WMS_LAYERS}

    # Overlay-Layer
    show_e29: bool = False
    show_bergr: bool = False
    show_dmf_live: bool = False
    # NGU Lagerstätten
    show_malm_forekomst_flate: bool = False
    show_malm_registrering_flate: bool = False
    show_industri_forekomst_flate: bool = False
    show_industri_forekomst_punkt: bool = False
    show_industri_registrering_flate: bool = False
    show_industri_registrering_punkt: bool = False
    show_malm_forekomst_punkt: bool = False
    show_malm_registrering_punkt: bool = False

    # Kartenzenrum
    lat: float = 62.0
    lon: float = 10.0
    zoom: int = 6

    # Prospektivitäts-Scoring (von SearchState befüllt)
    scored_geojson: str = ""

    # Passwortschutz
    authenticated: bool = False
    password_input: str = ""
    password_error: bool = False

    def set_basemap(self, val: str):
        self.basemap = val

    def set_scored_geojson(self, val: str):
        self.scored_geojson = val

    def set_password_input(self, val: str):
        self.password_input = val

    def check_password(self):
        # Passwort aus rx.Secret oder Umgebungsvariable
        correct = os.environ.get("APP_PASSWORD", "demo")
        if self.password_input == correct:
            self.authenticated = True
            self.password_error = False
        else:
            self.password_error = True

    def toggle_layer(self, name: str):
        self.active_layers[name] = not self.active_layers.get(name, False)

    def toggle_e29(self):
        self.show_e29 = not self.show_e29

    def toggle_bergr(self):
        self.show_bergr = not self.show_bergr

    def toggle_dmf(self):
        self.show_dmf_live = not self.show_dmf_live
    def toggle_malm_forekomst_flate(self):      self.show_malm_forekomst_flate = not self.show_malm_forekomst_flate
    def toggle_malm_registrering_flate(self):   self.show_malm_registrering_flate = not self.show_malm_registrering_flate
    def toggle_malm_forekomst_punkt(self):      self.show_malm_forekomst_punkt = not self.show_malm_forekomst_punkt
    def toggle_malm_registrering_punkt(self):   self.show_malm_registrering_punkt = not self.show_malm_registrering_punkt
    def toggle_industri_forekomst_flate(self):  self.show_industri_forekomst_flate = not self.show_industri_forekomst_flate
    def toggle_industri_registrering_flate(self): self.show_industri_registrering_flate = not self.show_industri_registrering_flate
    def toggle_industri_forekomst_punkt(self):  self.show_industri_forekomst_punkt = not self.show_industri_forekomst_punkt
    def toggle_industri_registrering_punkt(self): self.show_industri_registrering_punkt = not self.show_industri_registrering_punkt

    def set_lat(self, val: str):
        try:
            self.lat = float(val)
        except Exception:
            pass

    def set_lon(self, val: str):
        try:
            self.lon = float(val)
        except Exception:
            pass

    def set_zoom(self, val: list):
        self.zoom = int(val[0])

    @rx.var
    def map_config_json(self) -> str:
        """Gibt die komplette Map-Konfiguration als JSON-String für das Frontend."""
        wms_active = [
            {
                "id": name.replace(" ", "_").replace("—", "").replace("/", "_"),
                "name": name,
                "url": cfg["url"],
                "layer": cfg["layer"],
                "opacity": cfg["opacity"],
            }
            for name, cfg in WMS_LAYERS.items()
            if self.active_layers.get(name, False)
        ]
        return json.dumps({
            "center": [self.lon, self.lat],
            "zoom": self.zoom,
            "basemap": self.basemap,
            "wms_layers": wms_active,
            "show_e29": self.show_e29,
            "show_bergr": self.show_bergr,
            "show_dmf_live": self.show_dmf_live,
            "e29_geojson": _E29_GEOJSON,
            "bergr_geojson": _BERGR_GEOJSON,
            "scored_geojson": self.scored_geojson,
            "ngu_show": {
                "malm_forekomst_flate":        self.show_malm_forekomst_flate,
                "malm_registrering_flate":     self.show_malm_registrering_flate,
                "malm_forekomst_punkt":        self.show_malm_forekomst_punkt,
                "malm_registrering_punkt":     self.show_malm_registrering_punkt,
                "industri_forekomst_flate":    self.show_industri_forekomst_flate,
                "industri_registrering_flate": self.show_industri_registrering_flate,
                "industri_forekomst_punkt":    self.show_industri_forekomst_punkt,
                "industri_registrering_punkt": self.show_industri_registrering_punkt,
            },
        })


# ---------------------------------------------------------------------------
# UI-Komponenten
# ---------------------------------------------------------------------------

def layer_toggle(name: str, gruppe: str) -> rx.Component:
    cfg = WMS_LAYERS[name]
    return rx.box(
        rx.hstack(
            rx.switch(
                checked=MapState.active_layers[name],
                on_change=lambda _: MapState.toggle_layer(name),
                size="1",
                color_scheme="amber",
            ),
            rx.vstack(
                rx.text(name.split("—")[-1].strip(), size="1", weight="medium", color="#E8E0D0"),
                rx.text(cfg["desc"], size="1", color="#6B6560"),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="start",
        ),
        padding_y="4px",
    )


def gruppe_section(gruppe: str) -> rx.Component:
    layer_names = [n for n, c in WMS_LAYERS.items() if c["gruppe"] == gruppe]
    gruppe_icons = {
        "Berggrunn": "🪨",
        "Metalle": "⚗️",
        "Industrimineral": "🏭",
        "Geophysik": "📡",
    }
    return rx.box(
        rx.text(
            f"{gruppe_icons.get(gruppe, '•')} {gruppe}",
            size="1",
            weight="bold",
            color="#B8A898",
            letter_spacing="0.08em",
            text_transform="uppercase",
            padding_bottom="6px",
        ),
        *[layer_toggle(n, gruppe) for n in layer_names],
        padding_bottom="16px",
    )


def overlay_section() -> rx.Component:
    return rx.box(
        rx.text(
            "📁 Eigene Daten",
            size="1",
            weight="bold",
            color="#B8A898",
            letter_spacing="0.08em",
            text_transform="uppercase",
            padding_bottom="6px",
        ),
        rx.hstack(
            rx.switch(
                checked=MapState.show_e29,
                on_change=lambda _: MapState.toggle_e29(),
                size="1",
                color_scheme="red",
            ),
            rx.vstack(
                rx.text("Element29 Claims", size="1", weight="medium", color="#E8E0D0"),
                rx.text("234 Explorations-Polygone", size="1", color="#6B6560"),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="start",
            padding_y="4px",
        ),
        rx.hstack(
            rx.switch(
                checked=MapState.show_bergr,
                on_change=lambda _: MapState.toggle_bergr(),
                size="1",
                color_scheme="orange",
            ),
            rx.vstack(
                rx.text("DMF Bergrettigheter CSV", size="1", weight="medium", color="#E8E0D0"),
                rx.text("Lokal · Alters-Färbung", size="1", color="#6B6560"),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="start",
            padding_y="4px",
        ),
        rx.hstack(
            rx.switch(
                checked=MapState.show_dmf_live,
                on_change=lambda _: MapState.toggle_dmf(),
                size="1",
                color_scheme="yellow",
            ),
            rx.vstack(
                rx.text("DMF Live WMS", size="1", weight="medium", color="#E8E0D0"),
                rx.text("Täglich aktuell · Klick-Info", size="1", color="#6B6560"),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="start",
            padding_y="4px",
        ),
        padding_bottom="16px",
    )


def ngu_lagerstaetten_section() -> rx.Component:
    """NGU Lagerstätten Layer-Gruppe."""
    def ngu_toggle(label: str, desc: str, checked, on_change, color: str) -> rx.Component:
        return rx.hstack(
            rx.switch(checked=checked, on_change=on_change, size="1", color_scheme=color),
            rx.vstack(
                rx.text(label, size="1", weight="medium", color="#E8E0D0"),
                rx.text(desc, size="1", color="#6B6560"),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="start",
            padding_y="3px",
        )

    return rx.box(
        rx.text(
            "⛏ NGU Lagerstätten",
            size="1", weight="bold", color="#B8A898",
            letter_spacing="0.08em", text_transform="uppercase",
            padding_bottom="6px",
        ),
        rx.text("Malm", size="1", color="#6B6560", margin_bottom="4px"),
        rx.hstack(
            rx.switch(checked=MapState.show_malm_forekomst_flate, on_change=lambda _: MapState.toggle_malm_forekomst_flate(), size="1", color_scheme="amber"),
            rx.vstack(
                rx.text("Malm-Forekomst Fläche", size="1", weight="medium", color="#E8E0D0"),
                rx.text("105 Polygone · nach Erztyp", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.hstack(
            rx.switch(checked=MapState.show_malm_registrering_flate, on_change=lambda _: MapState.toggle_malm_registrering_flate(), size="1", color_scheme="amber"),
            rx.vstack(
                rx.text("Malm-Registrierung Fläche", size="1", weight="medium", color="#E8E0D0"),
                rx.text("168 Polygone · nach Erztyp", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.hstack(
            rx.switch(checked=MapState.show_malm_forekomst_punkt, on_change=lambda _: MapState.toggle_malm_forekomst_punkt(), size="1", color_scheme="orange"),
            rx.vstack(
                rx.text("Malm-Forekomst Punkt", size="1", weight="medium", color="#E8E0D0"),
                rx.text("108 Punkte", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.hstack(
            rx.switch(checked=MapState.show_malm_registrering_punkt, on_change=lambda _: MapState.toggle_malm_registrering_punkt(), size="1", color_scheme="orange"),
            rx.vstack(
                rx.text("Malm-Registrierung Punkt", size="1", weight="medium", color="#E8E0D0"),
                rx.text("4.543 Punkte", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.text("Industrimineral", size="1", color="#6B6560", margin_top="8px", margin_bottom="4px"),
        rx.hstack(
            rx.switch(checked=MapState.show_industri_forekomst_flate, on_change=lambda _: MapState.toggle_industri_forekomst_flate(), size="1", color_scheme="blue"),
            rx.vstack(
                rx.text("Industri-Forekomst Fläche", size="1", weight="medium", color="#E8E0D0"),
                rx.text("127 Polygone · nach Mineraltyp", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.hstack(
            rx.switch(checked=MapState.show_industri_registrering_flate, on_change=lambda _: MapState.toggle_industri_registrering_flate(), size="1", color_scheme="blue"),
            rx.vstack(
                rx.text("Industri-Registrierung Fläche", size="1", weight="medium", color="#E8E0D0"),
                rx.text("179 Polygone", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.hstack(
            rx.switch(checked=MapState.show_industri_forekomst_punkt, on_change=lambda _: MapState.toggle_industri_forekomst_punkt(), size="1", color_scheme="cyan"),
            rx.vstack(
                rx.text("Industri-Forekomst Punkt", size="1", weight="medium", color="#E8E0D0"),
                rx.text("134 Punkte", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        rx.hstack(
            rx.switch(checked=MapState.show_industri_registrering_punkt, on_change=lambda _: MapState.toggle_industri_registrering_punkt(), size="1", color_scheme="cyan"),
            rx.vstack(
                rx.text("Industri-Registrierung Punkt", size="1", weight="medium", color="#E8E0D0"),
                rx.text("2.428 Punkte", size="1", color="#6B6560"),
                spacing="0", align="start",
            ),
            spacing="2", align="start", padding_y="3px",
        ),
        padding_bottom="16px",
    )


def koordinaten_section() -> rx.Component:
    return rx.box(
        rx.text(
            "🎯 Kartenzentrum",
            size="1",
            weight="bold",
            color="#B8A898",
            letter_spacing="0.08em",
            text_transform="uppercase",
            padding_bottom="8px",
        ),
        rx.vstack(
            rx.hstack(
                rx.text("Lat", size="1", color="#6B6560", width="28px"),
                rx.input(
                    default_value="62.0",
                    on_blur=MapState.set_lat,
                    size="1",
                    width="80px",
                    style={
                        "background": "#1A1814",
                        "border": "1px solid #3A3530",
                        "color": "#E8E0D0",
                        "font_size": "11px",
                        "padding": "2px 6px",
                    },
                ),
                rx.text("Lon", size="1", color="#6B6560", width="28px"),
                rx.input(
                    default_value="10.0",
                    on_blur=MapState.set_lon,
                    size="1",
                    width="80px",
                    style={
                        "background": "#1A1814",
                        "border": "1px solid #3A3530",
                        "color": "#E8E0D0",
                        "font_size": "11px",
                        "padding": "2px 6px",
                    },
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.text("Zoom", size="1", color="#6B6560", width="36px"),
                rx.slider(
                    default_value=[6],
                    min=4,
                    max=14,
                    on_value_commit=MapState.set_zoom,
                    width="120px",
                    color_scheme="amber",
                ),
                rx.text(MapState.zoom, size="1", color="#B8A898"),
                spacing="2",
                align="center",
            ),
            spacing="2",
        ),
        padding_bottom="16px",
    )


def sidebar() -> rx.Component:
    return rx.box(
        # Header
        rx.box(
            rx.text("EMI", size="2", weight="bold", color="#C8A850", letter_spacing="0.15em"),
            rx.text("ExploreIQ", size="1", color="#6B6560", letter_spacing="0.2em"),
            rx.divider(color_scheme="amber", margin_y="12px"),
            padding_bottom="4px",
        ),
        # Layer-Gruppen
        *[gruppe_section(g) for g in GRUPPEN],
        rx.divider(color="#2A2520", margin_y="8px"),
        overlay_section(),
        rx.divider(color="#2A2520", margin_y="8px"),
        ngu_lagerstaetten_section(),
        rx.divider(color="#2A2520", margin_y="8px"),
        koordinaten_section(),
        # Footer
        rx.box(
            rx.text("© NGU · DMF · Element29", size="1", color="#3A3530"),
            padding_top="8px",
        ),
        width="280px",
        min_width="280px",
        height="100vh",
        overflow_y="auto",
        padding="16px",
        background="#12100E",
        border_right="1px solid #2A2520",
        style={"scrollbar_width": "thin"},
    )


def basemap_tabs() -> rx.Component:
    """Tab-Leiste zur Basemap-Auswahl."""
    tab_style_base = {
        "padding": "5px 16px",
        "font_size": "11px",
        "font_family": "'IBM Plex Mono', monospace",
        "letter_spacing": "0.08em",
        "cursor": "pointer",
        "border": "none",
        "transition": "all 0.2s",
    }
    return rx.box(
        rx.hstack(
            rx.button(
                "🌑  DARK",
                on_click=MapState.set_basemap("dark"),
                style={
                    **tab_style_base,
                    "background": rx.cond(MapState.basemap == "dark", "#C8A850", "#1E1C18"),
                    "color": rx.cond(MapState.basemap == "dark", "#12100E", "#6B6560"),
                    "border_radius": "4px 0 0 4px",
                    "font_weight": rx.cond(MapState.basemap == "dark", "700", "400"),
                },
            ),
            rx.button(
                "☀  HELL",
                on_click=MapState.set_basemap("light"),
                style={
                    **tab_style_base,
                    "background": rx.cond(MapState.basemap == "light", "#C8A850", "#1E1C18"),
                    "color": rx.cond(MapState.basemap == "light", "#12100E", "#6B6560"),
                    "border_radius": "0",
                    "font_weight": rx.cond(MapState.basemap == "light", "700", "400"),
                },
            ),
            rx.button(
                "🛰  SATELLIT",
                on_click=MapState.set_basemap("satellite"),
                style={
                    **tab_style_base,
                    "background": rx.cond(MapState.basemap == "satellite", "#C8A850", "#1E1C18"),
                    "color": rx.cond(MapState.basemap == "satellite", "#12100E", "#6B6560"),
                    "border_radius": "0 4px 4px 0",
                    "font_weight": rx.cond(MapState.basemap == "satellite", "700", "400"),
                },
            ),
            spacing="0",
        ),
        position="absolute",
        top="12px",
        left="50%",
        transform="translateX(-50%)",
        z_index="10",
        background="#12100E",
        border="1px solid #3A3530",
        border_radius="6px",
        padding="4px",
        box_shadow="0 2px 12px rgba(0,0,0,0.5)",
    )


def map_area() -> rx.Component:
    """Karte + State-Bridge kombiniert."""
    return rx.box(
        rx.box(
            id="map-state-bridge",
            data_config=MapState.map_config_json,
            display="none",
        ),
        rx.box(
            id="map-container",
            width="100%",
            height="100vh",
            background="#1A1814",
        ),
        basemap_tabs(),
        position="relative",
        flex="1",
        height="100vh",
        overflow="hidden",
    )


# ---------------------------------------------------------------------------
# Passwort-Screen
# ---------------------------------------------------------------------------

def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text("EMI ExploreIQ", size="6", weight="bold", color="#C8A850", letter_spacing="0.15em"),
            rx.text("Restricted Access", size="2", color="#6B6560", letter_spacing="0.1em"),
            rx.divider(width="200px", color_scheme="amber"),
            rx.input(
                placeholder="Passwort",
                type="password",
                on_change=MapState.set_password_input,
                width="220px",
                style={
                    "background": "#1A1814",
                    "border": "1px solid #3A3530",
                    "color": "#E8E0D0",
                    "text_align": "center",
                },
            ),
            rx.button(
                "Einloggen",
                on_click=MapState.check_password,
                color_scheme="amber",
                width="220px",
            ),
            rx.cond(
                MapState.password_error,
                rx.text("Passwort falsch", size="1", color="#E74C3C"),
            ),
            spacing="4",
            align="center",
        ),
        height="100vh",
        background="#12100E",
    )


# ---------------------------------------------------------------------------
# Haupt-Layout
# ---------------------------------------------------------------------------

def map_page() -> rx.Component:
    return rx.cond(
        MapState.authenticated,
        rx.box(
            # Back-Button oben links
            rx.link(
                rx.hstack(
                    rx.text("←", size="1", color="#6B6560"),
                    rx.text("Dashboard", size="1", color="#6B6560", letter_spacing="0.06em"),
                    spacing="1",
                    align="center",
                    padding="4px 10px",
                    border_radius="4px",
                    border="1px solid #2A2520",
                    background="rgba(18,16,14,0.85)",
                    style={
                        "_hover": {"border_color": "#C8A850", "color": "#C8A850"},
                        "transition": "all 0.2s",
                        "backdrop_filter": "blur(4px)",
                    },
                ),
                href="/",
                text_decoration="none",
                position="absolute",
                top="12px",
                left="12px",
                z_index="20",
            ),
            rx.hstack(
                sidebar(),
                map_area(),
                spacing="0",
                align="start",
                width="100%",
                height="100vh",
                overflow="hidden",
            ),
            position="relative",
            background="#12100E",
            width="100%",
            height="100vh",
            overflow="hidden",
        ),
        login_page(),
    )


def index() -> rx.Component:
    return rx.cond(
        MapState.authenticated,
        dashboard_page(),
        login_page(),
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
from mineral_app.navbar import navbar
from mineral_app.dashboard import dashboard_page
from mineral_app.search import search_page
from mineral_app.search_state import SearchState
from mineral_app.faq.prospektivitaet import faq_prospektivitaet_page

app = rx.App(
    style={
        "font_family": "'IBM Plex Mono', monospace",
        "background": "#12100E",
        "color": "#E8E0D0",
    },
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&display=swap",
        "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css",
    ],
    head_components=[
        rx.el.script(src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"),
        rx.el.script(src="/map_init.js", defer=True),
    ],
)
app.add_page(index, route="/", title="EMI ExploreIQ · Dashboard")
app.add_page(map_page, route="/map", title="EMI ExploreIQ · Claim-Karte")
app.add_page(search_page, route="/search", title="EMI ExploreIQ · Prospektivität")


def _placeholder(title: str, icon: str) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text(icon, style={"font_size": "40px"}),
            rx.text(title, size="4", weight="bold", color="#C8A850"),
            rx.text("In Planung", size="2", color="#6B6560"),
            rx.link("← Dashboard", href="/", color="#6B6560", size="1", margin_top="16px"),
            spacing="3",
            align="center",
        ),
        height="100vh",
        background="#12100E",
    )


app.add_page(lambda: _placeholder("Bergrettigheter-Tabelle", "☰"), route="/table", title="EMI ExploreIQ · Tabelle")
app.add_page(lambda: _placeholder("Statistik & Charts", "◫"), route="/stats", title="EMI ExploreIQ · Statistik")
app.add_page(lambda: _placeholder("Flurkarten-Analyse", "⊞"), route="/flurkarte", title="EMI ExploreIQ · Flurkarten")
app.add_page(lambda: _placeholder("Konkurrenzanalyse", "⬢"), route="/konkurrenz", title="EMI ExploreIQ · Konkurrenz")
app.add_page(faq_prospektivitaet_page, route="/faq/prospektivitaet", title="EMI ExploreIQ · Hilfe Prospektivität")
