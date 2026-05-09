"""
navbar.py — Gemeinsame Navigation für alle Mineral Intelligence Seiten
"""

import reflex as rx

PAGES = [
    {"label": "Dashboard",    "icon": "⊞", "href": "/"},
    {"label": "Claim-Karte",  "icon": "◈", "href": "/map"},
    {"label": "Prospektivität","icon": "⬡", "href": "/search"},
    {"label": "Tabelle",      "icon": "☰", "href": "/table"},
    {"label": "Statistik",    "icon": "◫", "href": "/stats"},
]

NAV_STYLE = {
    "background": "#12100E",
    "border_bottom": "1px solid #2A2520",
    "width": "100%",
    "padding": "0 24px",
    "height": "48px",
    "position": "sticky",
    "top": "0",
    "z_index": "100",
}


def pill_tab(label: str, icon: str, href: str, active: bool) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.text(icon, size="1", style={"font_size": "13px"}),
            rx.text(label, size="1", weight="medium", letter_spacing="0.06em"),
            spacing="1",
            align="center",
            padding="5px 14px",
            border_radius="20px",
            background=rx.cond(
                active,
                "#C8A850",
                "#1E1C18",
            ),
            color=rx.cond(
                active,
                "#12100E",
                "#6B6560",
            ),
            border=rx.cond(
                active,
                "1px solid #C8A850",
                "1px solid #2A2520",
            ),
            style={
                "transition": "all 0.2s",
                "_hover": {
                    "background": rx.cond(active, "#C8A850", "#2A2520"),
                    "color": rx.cond(active, "#12100E", "#B8A898"),
                },
            },
        ),
        href=href,
        text_decoration="none",
    )


def back_button() -> rx.Component:
    """Kleiner Back-Link zum Dashboard – für fullscreen Seiten."""
    return rx.link(
        rx.hstack(
            rx.text("←", size="1", color="#6B6560"),
            rx.text("Dashboard", size="1", color="#6B6560", letter_spacing="0.06em"),
            spacing="1",
            align="center",
            padding="4px 10px",
            border_radius="4px",
            border="1px solid #2A2520",
            background="#12100E",
            style={
                "_hover": {"border_color": "#3A3530", "color": "#B8A898"},
                "transition": "all 0.2s",
            },
        ),
        href="/",
        text_decoration="none",
        position="absolute",
        top="12px",
        left="12px",
        z_index="20",
    )


def navbar(current_page: str) -> rx.Component:
    """Vollständige Navigationsleiste mit Pill-Tabs."""
    return rx.box(
        rx.hstack(
            # Logo
            rx.hstack(
                rx.text(
                    "EMI",
                    size="2",
                    weight="bold",
                    color="#C8A850",
                    letter_spacing="0.15em",
                ),
                rx.text(
                    "ExploreIQ",
                    size="1",
                    color="#3A3530",
                    letter_spacing="0.2em",
                ),
                spacing="2",
                align="center",
            ),
            rx.divider(orientation="vertical", height="20px", color="#2A2520"),
            # Pill Tabs
            rx.hstack(
                *[
                    pill_tab(
                        p["label"],
                        p["icon"],
                        p["href"],
                        current_page == p["href"],
                    )
                    for p in PAGES
                ],
                spacing="2",
                align="center",
            ),
            # Live-Indikator rechts
            rx.spacer(),
            rx.hstack(
                rx.box(
                    width="7px",
                    height="7px",
                    border_radius="50%",
                    background="#5D8A6B",
                ),
                rx.text("NGU · DMF · Live", size="1", color="#3A3530"),
                spacing="2",
                align="center",
            ),
            spacing="4",
            align="center",
            height="48px",
            width="100%",
        ),
        **NAV_STYLE,
    )
