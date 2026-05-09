# EMI ExploreIQ — UI Design System

## Konzept

Corporate-technisches Dark-Navy-Design für eine Mineral-Intelligence-Plattform.
Klare Hierarchie, datenorientierte Typografie, minimale visuelle Ablenkung.

---

## Farbpalette

### Hintergründe

| Token | Hex | Verwendung |
|---|---|---|
| BG_DEEP | `#0B1222` | Seitenhintergrund, Sidebar, fullscreen Pages |
| BG_CARD | `#0F1A30` | Card-Hintergrund (tief), Icon-Boxen |
| BG_MID | `#132238` | Card-Hintergrund (mittel), Panel-Header |
| BG_HOVER | `#172A48` | Hover-Zustand von Cards & Buttons |

### Borders

| Token | Hex | Verwendung |
|---|---|---|
| BORDER | `#1E3254` | Standard-Border (Cards, Inputs, Divider) |
| BORDER_M | `#284468` | Sekundäre Border (Hover-Übergang, Labels) |

### Text

| Token | Hex | Verwendung |
|---|---|---|
| TEXT_MAIN | `#E0E8F4` | Primärtext, Werte, Titel |
| TEXT_MID | `#8AAAC6` | Sekundärtext, Metadaten, Zoom-Wert |
| MUTED | `#4A6888` | Beschriftungen, Platzhalter, Footer-Text |

### Akzentfarben

| Token | Hex | Verwendung |
|---|---|---|
| GOLD | `#C8A850` | Primärer Akzent — aktive Tabs, Scores, Highlights |
| GOLD_DIM | `#C8A85020` | Badge-Hintergrund (transparent) |
| GOLD_BDR | `#C8A85055` | Badge-Border (transparent) |
| GREEN | `#4D9A7A` | Positiv-Status — AKTIV, Live-Indikator, Score OK |
| WARN | `#D85A30` | Warnung — Gewichtungs-Fehler, falsches Passwort |

---

## Typografie

### Schriften

| Familie | Verwendung |
|---|---|
| **IBM Plex Sans** | UI-Standardschrift — alle Fließtexte, Labels, Buttons, Titeln |
| **IBM Plex Mono** | Technische Elemente — Basemap-Tabs, Daten-Buttons, Koordinaten, Proxy-Symbole |

### Gewichte
- `300` Light — dezente Metadaten
- `400` Regular — Fließtext, Beschreibungen
- `500` Medium — Navigationslabels, Kartentitel
- `600` Semibold — Panel-Header, KPI-Labels
- `700` Bold — KPI-Werte, Logo, Score-Badges

### Größen (Radix `size`-Skala)
- `size="1"` — Beschriftungen, Status-Chips, Footer (≈ 12 px)
- `size="2"` — Card-Titel, Layer-Namen (≈ 14 px)
- `size="3"` — Abschnittstitel (≈ 16 px)
- `size="4"` — Seiten-Haupttitel (≈ 20 px)
- `size="6"` — KPI-Hauptwerte (≈ 28 px)

### Typografische Konventionen
- `letter_spacing: 0.06–0.2em` — für CAPS-Labels und Logo-Text
- `text_transform: uppercase` — Sektion-Labels, Status-Chips
- `weight="bold"` + `letter_spacing` — Logo "EMI", Score-Badges

---

## Komponenten

### Navbar
- Höhe 48 px, sticky, `z-index: 100`
- Hintergrund `#0B1222`, untere Border `#1E3254`
- Logo: "EMI" in Gold + "ExploreIQ" in `#284468`
- Pill-Tabs: aktiv = Gold-Hintergrund + dunkler Text; inaktiv = `#132238` + `#4A6888`
- Live-Indikator rechts: grüner Dot `#4D9A7A` + "NGU · DMF · Live"

### KPI-Cards (Dashboard)
- Hintergrund `#0F1A30`, Border `#1E3254`, `border-radius: 8px`
- Label: CAPS, `#4A6888` — Wert: `size="6"`, bold, `#E0E8F4`
- Subtext in kontextabhängiger Akzentfarbe (Grün / Gold / Muted)

### App-Cards (Dashboard)
- Hintergrund `#132238`, Border `#1E3254`, `border-radius: 10px`
- Hover: Border wechselt zu Gold `#C8A850`, Hintergrund → `#172A48`
- Icon-Box 40×40 px, `#0F1A30`, eigene Border
- Status-Chip: Hintergrund = `{color}18`, Border = `{color}40`

### Sidebar (Karte & Geochem)
- Breite 220–280 px, `height: 100vh`, `overflow-y: auto`
- Hintergrund `#0B1222`, rechte Border `#1E3254`
- Sektion-Labels: CAPS, `#284468`, `letter-spacing: 0.15em`
- Layer-Toggles: Radix Switch + zweizeiliger Text (Name + Beschreibung)

### Proxy-Zeilen (Suche)
- Symbol-Badge: `#C8A85020` Hintergrund, Gold-Border, 34×34 px, `border-radius: 7px`
- Slider: `color_scheme="amber"`
- Hover: Border-Farbe → `#284468`

### Buttons
- Primär (CTA): Gold-Hintergrund `#C8A850`, dunkler Text `#0B1222`, `border-radius: 20px`
- Sekundär: transparent + Border `#1E3254`, Text `#4A6888`
- Toggle aktiv: Gold oder Grün, Text `#0B1222`
- Toggle inaktiv: `#0F1A30` Hintergrund, Text `#4A6888`

### Inputs
- Hintergrund `#0F1A30`, Border `#284468`, Text `#E0E8F4`
- Focus: Border-Farbe → Gold `#C8A850`, outline: none

### Popup / Modal
- Hintergrund `#0F1A30`, Border `1px solid #C8A850`
- `border-radius: 8px`, `box-shadow: 0 4px 24px rgba(0,0,0,0.6)`

### Back-Button (fullscreen Pages)
- `position: absolute`, `top: 12px`, `left: 12px`, `z-index: 20`
- Border `#1E3254`, Hintergrund `rgba(11,18,34,0.88)` (Glassmorphism-Effekt)
- Hover: Border → `#284468`, Text → `#8AAAC6`

---

## Animationen & Übergänge

- Alle interaktiven Elemente: `transition: all 0.2s`
- Hover-Übergänge ausschließlich über Border-Farbe und Hintergrund — kein Scale oder Transform
- Spinner bei laufenden Operationen: `rx.spinner`, Farbe `#0B1222` (auf Gold-Button)

---

## Barchart (Recharts)
- Bar-Farbe: Gold `#C8A850`
- Grid: `stroke_dasharray="3 3"`, Farbe `#1E3254`
- Achsenbeschriftung: `#4A6888`, `font-size: 10–11px`
- Höhe: 140 px

---

## Legende (Anomalie-Score)
| Score | Farbe |
|---|---|
| > 70 High | `#E74C3C` (Rot) |
| 40–70 Mid | `#C8A850` (Gold) |
| < 40 Low | `#4D9A7A` (Grün) |

---

## Layout-Raster

| Seite | Struktur |
|---|---|
| Dashboard | Zentriert, max-width 1100 px, padding 32 px |
| Suche | Zentriert, max-width 860 px, padding 32 px |
| Karte | Sidebar 280 px + Flex-Karte, 100 vh, kein Scroll |
| Geochem | Sidebar 220 px + Flex-Karte, 100 vh, kein Scroll |

---

## Design-Entscheidungen

- **Gold bleibt:** `#C8A850` ist Markenfarbe (EMIAG / Element29), erzeugt starken Kontrast auf Navy
- **IBM Plex Sans** ersetzt IBM Plex Mono als Standard — technisch aber lesbar; Mono bleibt für Datenwerte
- **Kein Glassmorphism im Content** — nur beim Back-Button-Overlay; sonst opake Flächen für Lesbarkeit auf Kartenhintergrund
- **Keine Schatten auf Cards** — flaches Design, nur Border-Differenzierung durch Hover
