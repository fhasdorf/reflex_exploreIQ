# -*- coding: utf-8 -*-
# @Author: Frank Hasdorf / Claude
# @Date:   09-05-2026
"""
geochem_map.py — Geochemische Anomalien & Geophysik Karte
Nutzt anomalien_geochemie.geojson + anomalien_em/mag/rad.geojson
"""

import reflex as rx
import json
import os

# ---------------------------------------------------------------------------
# Daten laden
# ---------------------------------------------------------------------------

GEOCHEM_PATH  = "geodaten/anomalien_geochemie.geojson"
EM_PATH       = "geodaten/anomalien_em.geojson"
MAG_PATH      = "geodaten/anomalien_mag.geojson"
RAD_PATH      = "geodaten/anomalien_rad.geojson"


def _load_geojson(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Ladefehler {path}: {e}")
        return '{"type":"FeatureCollection","features":[]}'


_GEOCHEM_JSON = _load_geojson(GEOCHEM_PATH)
_EM_JSON      = _load_geojson(EM_PATH)
_MAG_JSON     = _load_geojson(MAG_PATH)
_RAD_JSON     = _load_geojson(RAD_PATH)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class GeochemState(rx.State):
    # Layer-Toggles
    show_geochem: bool  = True
    show_em: bool       = False
    show_mag: bool      = False
    show_rad: bool      = False

    # Filter
    medium_filter: str  = "Alle"       # Alle | Mineralboden | Humus | Till
    score_min: list[float] = [0]       # Anomalie-Score Minimum
    element_filter: str = "Au"         # Anzuzeigendes Element für Farbgebung

    # Popup
    popup_html: str     = ""
    popup_visible: bool = False

    # Karte config → wird als JSON-String an JS übergeben
    @rx.var
    def map_config_json(self) -> str:
        return json.dumps({
            "show_geochem":    self.show_geochem,
            "show_em":         self.show_em,
            "show_mag":        self.show_mag,
            "show_rad":        self.show_rad,
            "medium_filter":   self.medium_filter,
            "score_min":       self.score_min[0],
            "element_filter":  self.element_filter,
            "geochem_data":    json.loads(_GEOCHEM_JSON),
            "em_data":         json.loads(_EM_JSON),
            "mag_data":        json.loads(_MAG_JSON),
            "rad_data":        json.loads(_RAD_JSON),
        })

    def toggle_geochem(self):
        self.show_geochem = not self.show_geochem

    def toggle_em(self):
        self.show_em = not self.show_em

    def toggle_mag(self):
        self.show_mag = not self.show_mag

    def toggle_rad(self):
        self.show_rad = not self.show_rad

    def set_medium(self, val: str):
        self.medium_filter = val

    def set_score_min(self, val: list):
        self.score_min = val

    def set_element(self, val: str):
        self.element_filter = val

    def show_popup(self, html: str):
        self.popup_html = html
        self.popup_visible = True

    def close_popup(self):
        self.popup_visible = False


# ---------------------------------------------------------------------------
# UI-Komponenten
# ---------------------------------------------------------------------------

ELEMENTS = ["Au", "Ag", "Cu", "Ni", "Co", "Zn", "Pb", "Mo", "As"]
MEDIEN   = ["Alle", "Mineralboden", "Humus", "Till"]

BTN_BASE = {
    "font_family": "'IBM Plex Mono', monospace",
    "font_size": "10px",
    "letter_spacing": "0.08em",
    "border": "1px solid #1E3254",
    "cursor": "pointer",
    "padding": "4px 10px",
    "border_radius": "4px",
    "transition": "all 0.2s",
}


def toggle_btn(label: str, active: bool, on_click) -> rx.Component:
    return rx.button(
        label,
        on_click=on_click,
        style={
            **BTN_BASE,
            "background": rx.cond(active, "#C8A850", "#0F1A30"),
            "color": rx.cond(active, "#0B1222", "#4A6888"),
            "font_weight": rx.cond(active, "700", "400"),
            "border_color": rx.cond(active, "#C8A850", "#1E3254"),
        },
    )


def section_label(text: str) -> rx.Component:
    return rx.text(
        text,
        size="1",
        color="#284468",
        letter_spacing="0.15em",
        text_transform="uppercase",
        margin_bottom="8px",
        margin_top="16px",
    )


def geochem_sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Titel
            rx.text(
                "GEOCHEMIE · GEOPHYSIK",
                size="1",
                weight="bold",
                color="#C8A850",
                letter_spacing="0.15em",
            ),
            rx.text(
                "NGU MINS-Datensätze",
                size="1",
                color="#284468",
                margin_bottom="8px",
            ),
            rx.divider(color="#1E3254"),

            # Layer
            section_label("Layer"),
            rx.vstack(
                toggle_btn(
                    "⬡  Geochemie",
                    GeochemState.show_geochem,
                    GeochemState.toggle_geochem,
                ),
                toggle_btn(
                    "〜  EM (Leitfähigkeit)",
                    GeochemState.show_em,
                    GeochemState.toggle_em,
                ),
                toggle_btn(
                    "⊕  Magnetik",
                    GeochemState.show_mag,
                    GeochemState.toggle_mag,
                ),
                toggle_btn(
                    "◎  Radiometrie",
                    GeochemState.show_rad,
                    GeochemState.toggle_rad,
                ),
                spacing="2",
                align="stretch",
                width="100%",
            ),

            # Medium-Filter
            section_label("Medium"),
            rx.hstack(
                *[
                    rx.button(
                        m,
                        on_click=lambda v=m: GeochemState.set_medium(v),
                        style={
                            **BTN_BASE,
                            "background": rx.cond(
                                GeochemState.medium_filter == m,
                                "#4D9A7A", "#0F1A30"
                            ),
                            "color": rx.cond(
                                GeochemState.medium_filter == m,
                                "#0B1222", "#4A6888"
                            ),
                            "border_color": rx.cond(
                                GeochemState.medium_filter == m,
                                "#4D9A7A", "#1E3254"
                            ),
                            "font_size": "9px",
                        },
                    )
                    for m in MEDIEN
                ],
                wrap="wrap",
                spacing="1",
            ),

            # Element-Farbgebung
            section_label("Element (Farbe)"),
            rx.select(
                ELEMENTS,
                value=GeochemState.element_filter,
                on_change=GeochemState.set_element,
                style={
                    "background": "#0F1A30",
                    "border": "1px solid #1E3254",
                    "color": "#E0E8F4",
                    "font_family": "'IBM Plex Mono', monospace",
                    "font_size": "11px",
                    "width": "100%",
                },
            ),

            # Anomalie-Score Filter
            section_label("Min. Score"),
            rx.hstack(
                rx.slider(
                    min=0,
                    max=100,
                    step=10,
                    value=GeochemState.score_min,
                    on_change=GeochemState.set_score_min,
                    color_scheme="amber",
                    width="100%",
                ),
                rx.text(
                    GeochemState.score_min[0],
                    size="1",
                    color="#C8A850",
                    min_width="28px",
                    text_align="right",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),

            # Legende
            section_label("Legende (Score)"),
            rx.vstack(
                rx.hstack(
                    rx.box(width="12px", height="12px", border_radius="50%",
                           background="#E74C3C"),
                    rx.text("High  > 70", size="1", color="#4A6888"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="12px", height="12px", border_radius="50%",
                           background="#C8A850"),
                    rx.text("Mid   40–70", size="1", color="#4A6888"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="12px", height="12px", border_radius="50%",
                           background="#4D9A7A"),
                    rx.text("Low   < 40", size="1", color="#4A6888"),
                    spacing="2", align="center",
                ),
                spacing="1",
            ),

            rx.divider(color="#1E3254", margin_top="16px"),

            # Stats
            rx.text("2.918 Proben · 23 Elemente", size="1", color="#284468"),
            rx.text("7,6 Mio Geophysikpunkte", size="1", color="#284468"),
            rx.text("75 High-Anomalien (>70)", size="1", color="#C8A850"),

            spacing="2",
            align="start",
            width="100%",
        ),
        width="220px",
        min_width="220px",
        height="100vh",
        overflow_y="auto",
        background="#0B1222",
        border_right="1px solid #1E3254",
        padding="16px",
    )


def geochem_map_area() -> rx.Component:
    return rx.box(
        # State-Bridge für JS
        rx.box(
            id="geochem-state-bridge",
            data_config=GeochemState.map_config_json,
            display="none",
        ),
        # Karten-Container
        rx.box(
            id="geochem-map-container",
            width="100%",
            height="100vh",
            background="#0F1A30",
        ),
        # Popup
        rx.cond(
            GeochemState.popup_visible,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("PROBE", size="1", color="#C8A850",
                                letter_spacing="0.15em"),
                        rx.spacer(),
                        rx.button(
                            "✕",
                            on_click=GeochemState.close_popup,
                            style={
                                **BTN_BASE,
                                "padding": "2px 6px",
                                "background": "transparent",
                                "color": "#4A6888",
                                "border": "none",
                            },
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.html(GeochemState.popup_html),
                    spacing="2",
                    align="start",
                ),
                position="absolute",
                bottom="24px",
                right="24px",
                width="280px",
                background="#0F1A30",
                border="1px solid #C8A850",
                border_radius="8px",
                padding="16px",
                z_index="20",
                box_shadow="0 4px 24px rgba(0,0,0,0.6)",
            ),
        ),
        position="relative",
        flex="1",
        height="100vh",
        overflow="hidden",
    )


def geochem_page() -> rx.Component:
    return rx.box(
        # Back-Button
        rx.link(
            rx.hstack(
                rx.text("←", size="1", color="#4A6888"),
                rx.text("Dashboard", size="1", color="#4A6888",
                        letter_spacing="0.06em"),
                spacing="1",
                align="center",
                padding="4px 10px",
                border_radius="4px",
                border="1px solid #1E3254",
                background="rgba(18,16,14,0.85)",
                style={
                    "_hover": {"border_color": "#C8A850", "color": "#C8A850"},
                    "transition": "all 0.2s",
                },
            ),
            href="/",
            text_decoration="none",
            position="absolute",
            top="12px",
            left="232px",
            z_index="20",
        ),
        rx.hstack(
            geochem_sidebar(),
            geochem_map_area(),
            spacing="0",
            align="start",
            width="100%",
            height="100vh",
            overflow="hidden",
        ),
        position="relative",
        background="#0B1222",
        width="100%",
        height="100vh",
        overflow="hidden",
    )
