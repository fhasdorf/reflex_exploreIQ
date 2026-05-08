"""
faq/prospektivitaet.py — Hilfe & Dokumentation: Prospektivitäts-Suche
Abgelegt in mineral_app/faq/prospektivitaet.py
"""

import reflex as rx
from mineral_app.navbar import navbar

BG_DEEP   = "#12100E"
BG_CARD   = "#1A1814"
BORDER    = "#2A2520"
GOLD      = "#C8A850"
GOLD_DIM  = "#C8A85018"
GREEN     = "#5D8A6B"
MUTED     = "#6B6560"
TEXT_MAIN = "#E8E0D0"
TEXT_MID  = "#B8A898"
WARN      = "#D85A30"


def section_title(text: str) -> rx.Component:
    return rx.text(
        text,
        size="3",
        weight="bold",
        color=GOLD,
        letter_spacing="0.06em",
        margin_top="32px",
        margin_bottom="10px",
    )


def subsection(text: str) -> rx.Component:
    return rx.text(
        text,
        size="2",
        weight="bold",
        color=TEXT_MID,
        margin_top="20px",
        margin_bottom="6px",
    )


def para(text: str) -> rx.Component:
    return rx.text(text, size="2", color=TEXT_MID, line_height="1.7", margin_bottom="8px")


def chip(text: str) -> rx.Component:
    return rx.box(
        rx.text(text, size="1", color=TEXT_MID, letter_spacing="0.04em"),
        padding="2px 9px",
        border_radius="20px",
        background=BG_DEEP,
        border=f"1px solid {BORDER}",
    )


def formula_box(text: str) -> rx.Component:
    return rx.box(
        rx.text(text, size="1", color=GOLD, font_family="'IBM Plex Mono', monospace",
                white_space="pre", line_height="1.8"),
        background=BG_CARD,
        border_left=f"3px solid {GOLD}",
        border_radius="0 6px 6px 0",
        padding="14px 20px",
        margin_y="16px",
        overflow_x="auto",
    )


def score_table() -> rx.Component:
    def header(t):
        return rx.box(rx.text(t, size="1", weight="bold", color=GOLD,
                               letter_spacing="0.06em"),
                      padding="8px 12px", flex="1")

    def cell(t, color=TEXT_MID):
        return rx.box(rx.text(t, size="1", color=color),
                      padding="8px 12px", flex="1")

    rows = [
        ("Direkttreffer",       "Silber-Keyword im Text",        "+100 Pkt",  GREEN, '"Sølv" in Merknad'),
        ("Proxy-Treffer",       "Pb / Zn / Sb-Keyword im Text",  "0–100 Pkt", GOLD,  '"Galenit" → Pb'),
        ("Kombination",         "Direkt + alle Proxies",          "200+ Pkt",  WARN,  '"Argentit" + Galenit + Sphalerit'),
    ]

    return rx.box(
        # Header
        rx.hstack(
            header("Treffer-Typ"), header("Bedingung"), header("Score"), header("Beispiel"),
            width="100%", background="#1E1C18", border_radius="6px 6px 0 0",
            border=f"1px solid {BORDER}", border_bottom="none",
        ),
        # Rows
        *[
            rx.hstack(
                cell(r[0]), cell(r[1]), cell(r[2], r[3]), cell(r[4]),
                width="100%",
                border=f"1px solid {BORDER}",
                border_top="none",
                background=BG_CARD,
                style={"_last": {"border_radius": "0 0 6px 6px"}},
            )
            for r in rows
        ],
        width="100%",
        margin_y="16px",
    )


def faq_prospektivitaet_page() -> rx.Component:
    return rx.box(
        navbar("/search"),
        rx.box(
            # Back-Link
            rx.link(
                rx.hstack(
                    rx.text("←", size="1", color=MUTED),
                    rx.text("Zurück zur Suche", size="1", color=MUTED),
                    spacing="1", align="center",
                    padding="4px 10px", border_radius="4px",
                    border=f"1px solid {BORDER}", background=BG_CARD,
                    style={"_hover": {"border_color": GOLD, "color": GOLD},
                           "transition": "all 0.2s"},
                ),
                href="/search", text_decoration="none",
            ),

            # Titel
            rx.hstack(
                rx.text("⬡", style={"font_size": "24px", "color": GOLD}),
                rx.vstack(
                    rx.text("Prospektivitäts-Suche", size="5", weight="bold", color=TEXT_MAIN),
                    rx.text("Dokumentation & Hilfe", size="1", color=MUTED, letter_spacing="0.1em"),
                    spacing="0", align="start",
                ),
                spacing="3", align="center", margin_top="24px", margin_bottom="8px",
            ),

            rx.divider(color=BORDER, margin_y="24px"),

            # 1. Überblick
            section_title("1. Was macht die Prospektivitäts-Suche?"),
            para("Die Prospektivitäts-Suche bewertet alle norwegischen Bergbaurechte (Bergrettigheter) automatisch auf ihr Potenzial für ein ausgewähltes Zielmineral — ohne manuelle Durchsicht von tausenden Einträgen."),
            para("Jede Bergrettighet enthält Textfelder in der DMF-Datenbank: Erz-Typ, Mineralangabe, Antragsteller und Bemerkungen. Der Algorithmus durchforstet diese Felder nach zwei Treffer-Typen und vergibt Punkte."),

            # 2. Treffer-Typen
            section_title("2. Die zwei Treffer-Typen"),

            subsection("2.1  Direkt-Treffer (Keyword-Match)"),
            para("Steht in einem Textfeld der Bergrettighet ein Silber-spezifisches Keyword — wie Ag, Sølv, Argentit oder Stephanit — erhält sie sofort 100 Punkte. Der Direkt-Treffer ist binär: ja (+100) oder nein (0)."),
            para("Alle Keywords sind immer aktiv und lassen sich nicht deaktivieren."),
            rx.hstack(
                *[chip(k) for k in ["Ag", "Sølv", "Silver", "Argentum", "Sølvglans",
                                     "Argentit", "Acanthit", "Stephanit", "Pyrargyrit", "Edelmetall"]],
                flex_wrap="wrap", spacing="1", margin_y="10px",
            ),

            subsection("2.2  Proxy-Treffer (gewichteter Match)"),
            para("Silber tritt in der Natur selten allein auf. Häufige Begleitminerale (Proxies) deuten indirekt auf Silber hin:"),
            rx.vstack(
                rx.hstack(rx.box(rx.text("Pb", size="1", weight="bold", color=GOLD),
                                  width="34px", height="34px", border_radius="7px",
                                  background=GOLD_DIM, border=f"1px solid {GOLD}40",
                                  display="flex", align_items="center", justify_content="center"),
                           rx.text("Blei — Silber ist oft im Bleiglanz (Galenit) eingeschlossen", size="2", color=TEXT_MID),
                           spacing="3", align="center"),
                rx.hstack(rx.box(rx.text("Zn", size="1", weight="bold", color=GOLD),
                                  width="34px", height="34px", border_radius="7px",
                                  background=GOLD_DIM, border=f"1px solid {GOLD}40",
                                  display="flex", align_items="center", justify_content="center"),
                           rx.text("Zink — Zinkblende-Systeme führen häufig Silber", size="2", color=TEXT_MID),
                           spacing="3", align="center"),
                rx.hstack(rx.box(rx.text("Sb", size="1", weight="bold", color=GOLD),
                                  width="34px", height="34px", border_radius="7px",
                                  background=GOLD_DIM, border=f"1px solid {GOLD}40",
                                  display="flex", align_items="center", justify_content="center"),
                           rx.text("Antimon — typischer Begleiter in hydrothermalen Silbersystemen", size="2", color=TEXT_MID),
                           spacing="3", align="center"),
                spacing="2", margin_y="10px",
            ),

            # 3. Formel
            section_title("3. Scoring-Formel"),
            para("Der Score einer Bergrettighet ergibt sich aus:"),
            formula_box(
                "Score = 100                              (bei Direkttreffer)\n"
                "      + (Pb-Match × Pb-Gew. / Σ Gew.) × 100\n"
                "      + (Zn-Match × Zn-Gew. / Σ Gew.) × 100\n"
                "      + (Sb-Match × Sb-Gew. / Σ Gew.) × 100"
            ),
            para("Die Gewichte werden normiert — die relative Verteilung zwischen den Proxies zählt, nicht die absolute Summe."),
            score_table(),

            # 4. Slider
            section_title("4. Gewichtung der Proxy-Slider"),
            para("Die Slider steuern ausschließlich das Verhältnis der Proxy-Mineralien untereinander — nicht ob nach Keywords gesucht wird."),
            rx.vstack(
                rx.hstack(
                    rx.text("Pb–Zn–Ag-System (z. B. Kongsberg-Typ):", size="1", weight="bold", color=TEXT_MID, width="280px"),
                    rx.text("Pb hoch · Zn mittel · Sb niedrig", size="1", color=MUTED),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.text("Epithermales Ag–Sb-System:", size="1", weight="bold", color=TEXT_MID, width="280px"),
                    rx.text("Sb hoch · Pb mittel · Zn niedrig", size="1", color=MUTED),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.text("Allgemeiner Überblick:", size="1", weight="bold", color=TEXT_MID, width="280px"),
                    rx.text("gleichmäßig 33 / 33 / 33", size="1", color=MUTED),
                    spacing="2", align="center",
                ),
                spacing="2",
                background=BG_CARD,
                border=f"1px solid {BORDER}",
                border_radius="8px",
                padding="14px 18px",
                margin_y="12px",
            ),

            # 5. Ergebnis & Karte
            section_title("5. Ergebnis & Claim-Karte"),
            para("Nach dem Scoring erscheint eine sortierte Tabelle aller Bergrettigheter mit Score > 0. Der Button «N Treffer auf Karte» überträgt die Ergebnisse direkt in den Choropleth-Layer der Claim-Karte."),
            rx.hstack(
                rx.box(width="12px", height="12px", border_radius="2px", background=MUTED, flex_shrink="0"),
                rx.text("Kein Treffer → unsichtbar", size="1", color=MUTED),
                spacing="2", align="center",
            ),
            rx.hstack(
                rx.box(width="12px", height="12px", border_radius="2px", background=GOLD, flex_shrink="0"),
                rx.text("Proxy-Treffer → goldene Einfärbung", size="1", color=MUTED),
                spacing="2", align="center", margin_top="4px",
            ),
            rx.hstack(
                rx.box(width="12px", height="12px", border_radius="2px", background=GREEN, flex_shrink="0"),
                rx.text("Direkttreffer + alle Proxies → grüne Einfärbung (höchste Priorität)", size="1", color=MUTED),
                spacing="2", align="center", margin_top="4px",
            ),

            # 6. Felder
            section_title("6. Durchsuchte Datenbankfelder"),
            para("Folgende Spalten des Bergrettigheter-Datensatzes (NGU/DMF) werden für den Text-Match verwendet:"),
            rx.grid(
                *[rx.box(rx.text(f, size="1", color=TEXT_MID, font_family="'IBM Plex Mono', monospace"),
                          padding="6px 12px", background=BG_CARD,
                          border=f"1px solid {BORDER}", border_radius="6px")
                  for f in ["Bergverkstype", "Søker", "Hjemmelshaver", "Merknad", "Malm", "Mineral"]],
                columns="3", spacing="2", margin_y="12px",
            ),

            rx.divider(color=BORDER, margin_top="40px", margin_bottom="16px"),
            rx.hstack(
                rx.text("© EMIAG · NGU · DMF · Element29 AS", size="1", color="#3A3530"),
                rx.spacer(),
                rx.text("EMI ExploreIQ™ Interne Dokumentation", size="1", color="#3A3530"),
                width="100%",
            ),

            max_width="860px",
            margin="0 auto",
            padding="32px 24px",
        ),
        background=BG_DEEP,
        min_height="100vh",
        color=TEXT_MAIN,
    )
