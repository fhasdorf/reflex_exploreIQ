"""
search.py — Prospektivitäts-Suche
Mineral auswählen · Proxy-Gewichte einstellen · Scoring starten · Karte öffnen
"""

import reflex as rx
from mineral_app.navbar import navbar
from mineral_app.search_state import SearchState, MINERALS


# ---------------------------------------------------------------------------
# Stil-Konstanten (konsistent mit dem Rest der App)
# ---------------------------------------------------------------------------

BG_DEEP   = "#12100E"
BG_CARD   = "#1A1814"
BG_HOVER  = "#221F1A"
BORDER    = "#2A2520"
GOLD      = "#C8A850"
GOLD_DIM  = "#C8A85020"
GOLD_BDR  = "#C8A85055"
GREEN     = "#5D8A6B"
MUTED     = "#6B6560"
TEXT_MAIN = "#E8E0D0"
TEXT_MID  = "#B8A898"
WARN      = "#D85A30"


# ---------------------------------------------------------------------------
# Mineral-Auswahl-Button
# ---------------------------------------------------------------------------

def mineral_tab(symbol: str, label: str) -> rx.Component:
    active = SearchState.mineral == symbol
    return rx.button(
        rx.hstack(
            rx.text(symbol, size="1", weight="bold", letter_spacing="0.12em"),
            rx.text(label, size="1"),
            spacing="2",
            align="center",
        ),
        on_click=SearchState.set_mineral(symbol),
        padding="5px 16px",
        border_radius="20px",
        background=rx.cond(active, GOLD, BG_CARD),
        color=rx.cond(active, BG_DEEP, MUTED),
        border=rx.cond(active, f"1px solid {GOLD}", f"1px solid {BORDER}"),
        cursor="pointer",
        style={"transition": "all 0.2s"},
    )


def mineral_selector() -> rx.Component:
    return rx.box(
        rx.text(
            "Mineral",
            size="1",
            color=MUTED,
            letter_spacing="0.12em",
            text_transform="uppercase",
            margin_bottom="10px",
        ),
        rx.hstack(
            *[mineral_tab(sym, cfg["label"]) for sym, cfg in MINERALS.items()],
            spacing="2",
            flex_wrap="wrap",
        ),
        margin_bottom="28px",
    )


# ---------------------------------------------------------------------------
# Balken-Diagramm (rx.recharts)
# ---------------------------------------------------------------------------

def weight_chart() -> rx.Component:
    """
    Einfaches Balkendiagramm der aktuellen Proxy-Gewichte.
    Nutzt rx.recharts für native Reflex-Integration.
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="weight",
                fill=GOLD,
                radius=[4, 4, 0, 0],
                label={
                    "position": "top",
                    "fill": GOLD,
                    "font_size": 11,
                },
            ),
            rx.recharts.x_axis(data_key="symbol", tick={"fill": MUTED, "font_size": 11}),
            rx.recharts.y_axis(domain=[0, 100], tick={"fill": MUTED, "font_size": 10}),
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke=BORDER),
            data=SearchState.proxies_config,
            height=140,
            margin={"top": 16, "right": 12, "left": -20, "bottom": 0},
        ),
        width="100%",
        margin_bottom="20px",
    )


# ---------------------------------------------------------------------------
# Proxy-Gewichtungs-Zeile
# ---------------------------------------------------------------------------

def proxy_row(proxy: dict) -> rx.Component:
    """
    Eine Zeile für einen Proxy: Icon · Name + Desc · Slider · Zahleneingabe
    proxy ist ein Dict aus proxies_config (mit 'weight'-Feld).
    """
    symbol = proxy["symbol"]
    return rx.box(
        rx.hstack(
            # Symbol-Badge
            rx.box(
                rx.text(symbol, size="1", weight="bold", color=GOLD),
                width="34px",
                height="34px",
                border_radius="7px",
                background=GOLD_DIM,
                border=f"1px solid {GOLD_BDR}",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            # Name + Beschreibung
            rx.vstack(
                rx.text(proxy["name"], size="2", weight="medium", color=TEXT_MAIN),
                rx.text(proxy["desc"], size="1", color=MUTED),
                spacing="0",
                align="start",
                flex="1",
            ),
            # Slider
            rx.slider(
                value=[proxy["weight"]],
                min=0,
                max=100,
                on_value_commit=lambda v: SearchState.set_weight(symbol, v[0]),
                color_scheme="amber",
                width="140px",
                flex_shrink="0",
            ),
            # Zahleneingabe
            rx.hstack(
                rx.input(
                    value=proxy["weight"].to(str),
                    on_change=lambda v: SearchState.set_weight(symbol, v),
                    width="48px",
                    size="1",
                    style={
                        "background": BG_DEEP,
                        "border": f"1px solid {BORDER}",
                        "color": TEXT_MAIN,
                        "text_align": "center",
                        "font_size": "12px",
                        "padding": "3px 4px",
                        "_focus": {"border_color": GOLD, "outline": "none"},
                    },
                ),
                rx.text("%", size="1", color=MUTED),
                spacing="1",
                align="center",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        padding="10px 14px",
        style={"transition": "border-color 0.2s", "_hover": {"border_color": "#3A3530"}},
    )


# ---------------------------------------------------------------------------
# Gewichtungs-Panel
# ---------------------------------------------------------------------------

def weight_total_badge() -> rx.Component:
    """Zeigt Summe der Gewichte — grün bei 100, orange sonst."""
    return rx.hstack(
        rx.text("Summe", size="1", color=MUTED),
        rx.text(
            SearchState.weight_total,
            size="2",
            weight="bold",
            color=rx.cond(SearchState.weight_total == 100, GREEN, WARN),
        ),
        rx.text(
            rx.cond(
                SearchState.weight_total == 100,
                "✓ ausgeglichen",
                rx.cond(
                    SearchState.weight_total < 100,
                    f"− {100 - SearchState.weight_total} fehlen",
                    "zu viel",
                ),
            ),
            size="1",
            color=rx.cond(SearchState.weight_total == 100, GREEN, WARN),
        ),
        spacing="2",
        align="center",
        justify="end",
        width="100%",
        margin_bottom="16px",
    )


def proxy_weight_panel() -> rx.Component:
    return rx.box(
        # Header
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.text("⬡", style={"font_size": "16px"}),
                    width="32px",
                    height="32px",
                    border_radius="7px",
                    background=GOLD_DIM,
                    border=f"1px solid {GOLD_BDR}",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            SearchState.mineral,
                            size="1",
                            weight="bold",
                            color=GOLD,
                            letter_spacing="0.12em",
                        ),
                        rx.text("·", size="1", color=MUTED),
                        rx.text(SearchState.mineral_label, size="1", color=MUTED),
                        spacing="1",
                        align="center",
                    ),
                    rx.text("Proxy-Gewichtung", size="1", color=MUTED, letter_spacing="0.1em"),
                    spacing="0",
                    align="start",
                ),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.text(
                    "Suchbegriffe aktiv",
                    size="1",
                    color=GREEN,
                    letter_spacing="0.06em",
                ),
                rx.box(
                    width="7px",
                    height="7px",
                    border_radius="50%",
                    background=GREEN,
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
        ),
        rx.divider(color=BORDER, margin_y="14px"),

        # Balkendiagramm
        weight_chart(),

        # Summen-Badge
        weight_total_badge(),

        # Proxy-Zeilen
        rx.vstack(
            rx.foreach(SearchState.proxies_config, proxy_row),
            spacing="2",
            width="100%",
        ),

        # Keyword-Chips
        rx.box(
            rx.text(
                "Suchbegriffe · Keyword-Regex",
                size="1",
                color=MUTED,
                letter_spacing="0.1em",
                text_transform="uppercase",
                margin_bottom="8px",
            ),
            rx.hstack(
                *[
                    rx.box(
                        rx.text(kw, size="1", color=TEXT_MID, letter_spacing="0.04em"),
                        padding="2px 9px",
                        border_radius="20px",
                        background=BG_DEEP,
                        border=f"1px solid {BORDER}",
                    )
                    for kw in [
                        "Ag", "Sølv", "Silver", "Argentum",
                        "Sølvglans", "Argentit", "Acanthit",
                        "Stephanit", "Pyrargyrit", "Edelmetall",
                    ]
                ],
                flex_wrap="wrap",
                spacing="1",
            ),
            margin_top="16px",
            padding="12px 14px",
            background=BG_CARD,
            border=f"1px solid {BORDER}",
            border_radius="8px",
        ),

        background="#1E1C18",
        border=f"1px solid {BORDER}",
        border_radius="10px",
        padding="18px 20px",
        margin_bottom="20px",
    )


# ---------------------------------------------------------------------------
# Such-Button & Status
# ---------------------------------------------------------------------------

def search_controls() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.cond(
                SearchState.is_running,
                rx.hstack(
                    rx.spinner(size="1", color=BG_DEEP),
                    rx.text("Suche läuft…", size="1"),
                    spacing="2",
                    align="center",
                ),
                rx.text("Scoring starten", size="1", weight="bold", letter_spacing="0.08em"),
            ),
            on_click=SearchState.run_search,
            disabled=SearchState.is_running,
            background=GOLD,
            color=BG_DEEP,
            border="none",
            border_radius="20px",
            padding="6px 20px",
            cursor="pointer",
            style={"transition": "opacity 0.2s", "_hover": {"opacity": "0.88"}},
        ),
        rx.button(
            rx.text("Zurücksetzen", size="1", color=MUTED, letter_spacing="0.06em"),
            on_click=SearchState.reset_search,
            background="transparent",
            border=f"1px solid {BORDER}",
            border_radius="20px",
            padding="6px 16px",
            cursor="pointer",
            style={"transition": "all 0.2s", "_hover": {"border_color": "#3A3530", "color": TEXT_MID}},
        ),
        rx.cond(
            SearchState.has_results,
            rx.link(
                rx.hstack(
                    rx.text("◈", size="1", color=GREEN),
                    rx.text(
                        SearchState.result_count.to_string() + " Treffer auf Karte",
                        size="1",
                        color=GREEN,
                        letter_spacing="0.06em",
                    ),
                    spacing="1",
                    align="center",
                    padding="5px 14px",
                    border_radius="20px",
                    background="#5D8A6B18",
                    border=f"1px solid {GREEN}40",
                ),
                href="/map",
                text_decoration="none",
            ),
        ),
        spacing="3",
        align="center",
        margin_bottom="24px",
    )


# ---------------------------------------------------------------------------
# Ergebnis-Tabelle
# ---------------------------------------------------------------------------

def result_row(row: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            # Score-Badge
            rx.box(
                rx.text(
                    row["score_label"],
                    size="1",
                    weight="bold",
                    color=GOLD,
                    letter_spacing="0.06em",
                ),
                padding="2px 10px",
                border_radius="20px",
                background=GOLD_DIM,
                border=f"1px solid {GOLD_BDR}",
                min_width="52px",
                text_align="center",
            ),
            # Name
            rx.text(row["name"], size="1", color=TEXT_MAIN, flex="2"),
            # Typ
            rx.text(row["type"], size="1", color=MUTED, flex="2"),
            # Mineral
            rx.text(row["mineral"], size="1", color=MUTED, flex="1"),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="8px 12px",
        border_bottom=f"1px solid {BORDER}",
        style={"_last": {"border_bottom": "none"}, "_hover": {"background": BG_HOVER}},
    )


def results_panel() -> rx.Component:
    return rx.cond(
        SearchState.has_results,
        rx.box(
            # Header
            rx.hstack(
                rx.text(
                    "Ergebnisse",
                    size="1",
                    color=MUTED,
                    letter_spacing="0.12em",
                    text_transform="uppercase",
                ),
                rx.spacer(),
                rx.text(
                    SearchState.result_count.to_string() + " Bergrettigheter mit Treffern",
                    size="1",
                    color=MUTED,
                ),
                width="100%",
                margin_bottom="12px",
            ),
            # Tabellen-Header
            rx.box(
                rx.hstack(
                    rx.text("Score", size="1", color=MUTED, min_width="52px"),
                    rx.text("Hjemmelshaver", size="1", color=MUTED, flex="2"),
                    rx.text("Bergverkstype", size="1", color=MUTED, flex="2"),
                    rx.text("Mineral", size="1", color=MUTED, flex="1"),
                    spacing="3",
                    width="100%",
                ),
                padding="6px 12px",
                background=BG_CARD,
                border_radius="6px 6px 0 0",
                border=f"1px solid {BORDER}",
                border_bottom="none",
            ),
            # Zeilen
            rx.box(
                rx.foreach(SearchState.result_rows, result_row),
                background=BG_CARD,
                border=f"1px solid {BORDER}",
                border_top="none",
                border_radius="0 0 8px 8px",
                max_height="420px",
                overflow_y="auto",
                style={"scrollbar_width": "thin"},
            ),
            width="100%",
        ),
    )


# ---------------------------------------------------------------------------
# Haupt-Seite
# ---------------------------------------------------------------------------

def search_page() -> rx.Component:
    return rx.box(
        navbar("/search"),
        rx.box(
            # Seiten-Titel
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "⬡",
                        style={"font_size": "20px", "color": GOLD},
                    ),
                    rx.vstack(
                        rx.text(
                            "Prospektivitäts-Suche",
                            size="4",
                            weight="bold",
                            color=TEXT_MAIN,
                        ),
                        rx.text(
                            "Keyword · Proxy-Mineralien · Score-Gewichtung",
                            size="1",
                            color=MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.link(
                        rx.hstack(
                            rx.text("?", size="1", weight="bold", color=MUTED),
                            spacing="1",
                            align="center",
                            padding="4px 10px",
                            border_radius="20px",
                            background=BG_CARD,
                            border=f"1px solid {BORDER}",
                            style={
                                "transition": "all 0.2s",
                                "_hover": {"border_color": GOLD, "color": GOLD},
                            },
                        ),
                        href="/faq/prospektivitaet",
                        text_decoration="none",
                        title="Dokumentation & Hilfe",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                align="start",
                margin_bottom="24px",
            ),

            # Mineral-Auswahl
            mineral_selector(),

            # Gewichtungs-Panel
            proxy_weight_panel(),

            # Aktions-Buttons
            search_controls(),

            # Ergebnisse
            results_panel(),

            # Footer
            rx.hstack(
                rx.text("Score = Σ(Proxy-Treffer × Gewicht) + 100 bei Mineral-Direkttreffer",
                        size="1", color="#3A3530"),
                rx.spacer(),
                rx.text("© NGU · DMF · Element29 AS", size="1", color="#3A3530"),
                width="100%",
                margin_top="40px",
                padding_top="16px",
                border_top=f"1px solid #1E1C18",
            ),

            max_width="860px",
            margin="0 auto",
            padding="32px 24px",
        ),
        background=BG_DEEP,
        min_height="100vh",
        color=TEXT_MAIN,
    )
