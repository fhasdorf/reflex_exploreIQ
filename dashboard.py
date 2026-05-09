# -*- coding: utf-8 -*-
# @Author: Frank Hasdorf
# @Date:   05-05-2026 20:01:29
# @Last Modified by:   Frank Hasdorf / Claude
# @Last Modified time: 09-05-2026
"""
dashboard.py — Startseite / Übersicht
"""

import reflex as rx
from mineral_app.navbar import navbar


class DashState(rx.State):
    pass


def kpi_card(label: str, value: str, sub: str, sub_color: str = "#4A6888") -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                label,
                size="1",
                color="#4A6888",
                letter_spacing="0.1em",
                text_transform="uppercase",
            ),
            rx.text(value, size="6", weight="bold", color="#E0E8F4"),
            rx.text(sub, size="1", color=sub_color),
            spacing="1",
            align="start",
        ),
        background="#0F1A30",
        border="1px solid #1E3254",
        border_radius="8px",
        padding="16px 20px",
        flex="1",
    )


def app_card(
    icon: str,
    title: str,
    desc: str,
    href: str,
    status: str,
    status_color: str,
) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text(icon, style={"font_size": "20px"}),
                    width="40px",
                    height="40px",
                    border_radius="8px",
                    background="#0F1A30",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    border="1px solid #1E3254",
                ),
                rx.vstack(
                    rx.text(title, size="2", weight="bold", color="#E0E8F4"),
                    rx.text(desc, size="1", color="#4A6888"),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.box(
                    rx.text(
                        status,
                        size="1",
                        color=status_color,
                        letter_spacing="0.08em",
                    ),
                    padding="3px 10px",
                    border_radius="20px",
                    background=f"{status_color}18",
                    border=f"1px solid {status_color}40",
                ),
                spacing="3",
                align="center",
                margin_bottom="12px",
            ),
            rx.box(
                height="3px",
                border_radius="2px",
                background="#1E3254",
                width="100%",
                overflow="hidden",
                margin_top="4px",
            ),
            background="#132238",
            border="1px solid #1E3254",
            border_radius="10px",
            padding="16px 20px",
            width="100%",
            style={
                "transition": "all 0.2s",
                "_hover": {
                    "border_color": "#C8A850",
                    "background": "#172A48",
                },
            },
        ),
        href=href,
        text_decoration="none",
        width="100%",
    )


def dashboard_page() -> rx.Component:
    return rx.box(
        navbar("/"),
        rx.box(
            # KPI-Reihe
            rx.hstack(
                kpi_card("Claims total", "234", "↑ 12 diesen Monat", "#4D9A7A"),
                kpi_card("Gesamtfläche", "2.4 Gkm²", "Ø 10 km² / Claim"),
                kpi_card("Bergrettigheter", "1.847", "DMF · täglich aktuell"),
                kpi_card("EU Critical", "6", "Mineraltypen priorisiert", "#C8A850"),
                kpi_card("Flurstücke", "~180k", "Matrikkel · Geonorge", "#4A6888"),
                spacing="4",
                width="100%",
                margin_bottom="32px",
            ),

            # Sektions-Titel
            rx.text(
                "Analysetools",
                size="1",
                color="#284468",
                letter_spacing="0.15em",
                text_transform="uppercase",
                margin_bottom="12px",
            ),

            # App-Kacheln 2x4
            rx.grid(
                app_card(
                    "◈",
                    "Claim-Karte",
                    "NGU WMS · Element29 · Satellit · Dark",
                    "/map",
                    "AKTIV",
                    "#4D9A7A",
                ),
                app_card(
                    "⬡",
                    "Prospektivitäts-Suche",
                    "Keyword · Proxy-Mineralien · Score-Gewichtung",
                    "/search",
                    "AKTIV",
                    "#4D9A7A",
                ),
                # ── NEU ──────────────────────────────────────────────────────
                app_card(
                    "⊛",
                    "Geochemische Anomalien",
                    "NGU MINS · Till · Humus · EM · Mag · Rad · Kongsberg",
                    "/geochem",
                    "NEU",
                    "#C8A850",
                ),
                # ─────────────────────────────────────────────────────────────
                app_card(
                    "☰",
                    "Bergrettigheter-Tabelle",
                    "Filter · Sortierung · CSV-Export",
                    "/table",
                    "IN PLANUNG",
                    "#C8A850",
                ),
                app_card(
                    "◫",
                    "Statistik & Charts",
                    "Claims / Jahr · Mineralien · Fylke",
                    "/stats",
                    "IN PLANUNG",
                    "#C8A850",
                ),
                app_card(
                    "⊞",
                    "Flurkarten-Analyse",
                    "Matrikkel · Vereinnahmung % · Eigentümerkontakt",
                    "/flurkarte",
                    "IN PLANUNG",
                    "#C8A850",
                ),
                app_card(
                    "⬢",
                    "Konkurrenzanalyse",
                    "Explorer · Überschneidungen · Marktanteile",
                    "/konkurrenz",
                    "IN PLANUNG",
                    "#C8A850",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),

            # Footer
            rx.hstack(
                rx.text(
                    "EMI ExploreIQ · EMIAG · Reflex · AWS S3",
                    size="1",
                    color="#284468",
                ),
                rx.spacer(),
                rx.text(
                    "© NGU · DMF · Element29 AS",
                    size="1",
                    color="#284468",
                ),
                width="100%",
                margin_top="40px",
                padding_top="16px",
                border_top="1px solid #132238",
            ),

            max_width="1100px",
            margin="0 auto",
            padding="32px 24px",
        ),
        background="#0B1222",
        min_height="100vh",
        color="#E0E8F4",
    )
