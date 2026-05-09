# EMI ExploreIQ™ — Feature-Ideen
## Bergrettigheter-Tabelle, Statistik & Charts & Flurkarten-Analyse

---

## ☰ Bergrettigheter-Tabelle

Der "Excel-Ersatz" für Analysten — alle 1.847 Bergrettigheter tabellarisch, durchsuchbar und exportierbar.

### Filter & Suche
- Filter nach Fylke, Mineraltyp, Bergverkstype
- Freitextsuche über alle Felder (Søker, Hjemmelshaver, Merknad)
- Datumsbereich (Antragsdatum, Gültigkeitsdauer)
- Score-Filter aus der Prospektivitäts-Suche (z. B. nur Claims mit Score > 50)

### Sortierung
- Nach Fläche, Alter, Score, Mineraltyp
- Mehrfach-Sortierung (z. B. erst nach Fylke, dann nach Score)

### Tabellen-Spalten (Vorschlag)
| Spalte | Quelle |
|---|---|
| Score | Prospektivitäts-Suche |
| Hjemmelshaver / Søker | DMF |
| Bergverkstype | DMF |
| Mineral / Malm | DMF |
| Fylke | DMF |
| Fläche (km²) | GeoJSON |
| Antragsdatum | DMF |
| Merknad | DMF |

### Interaktion
- Klick auf Zeile → Claim-Karte zentriert und hebt den Claim hervor
- Mehrfachauswahl → Gruppe auf Karte anzeigen
- EU Critical Minerals farblich hervorheben

### Export
- CSV-Export (gefilterte Ansicht)
- Excel-Export mit Score-Spalte (für Investoren-Reports)

---

## ◫ Statistik & Charts

Das Management-Dashboard — Überblick über das gesamte norwegische Claim-Universum.

### Zeitreihen
- Claims pro Jahr (Neuanmeldungen) — Zeitreihe als Liniendiagramm
- Flächenentwicklung über Zeit — wächst das beanspruchte Gebiet?
- Aktivitätsphasen: wann wurden historisch viele Claims angemeldet? (Rohstoffpreis-Korrelation)

### Mineralverteilung
- Balkendiagramm: welche Erze dominieren die Bergrettigheter?
- EU Critical Mineral Anteil — wie viele Claims betreffen die 6 priorisierten Mineraltypen?
- Proxy-Mineral-Häufigkeit (Pb, Zn, Sb) im Gesamtdatensatz

### Geografische Verteilung
- Claims nach Fylke (Balken oder Choropleth)
- Claim-Dichte-Karte — wo ist Norwegen am stärksten beansprucht?
- Top-Fylker nach Gesamtfläche vs. Anzahl Claims

### Explorer-Analyse
- Top-Firmen nach Anzahl Claims
- Top-Firmen nach Gesamtfläche
- Neue Marktteilnehmer (wer hat in den letzten 12 Monaten Claims angemeldet?)
- Konkurrenzanalyse: Überschneidung von Claims mehrerer Explorer in einem Gebiet

### Score-Verteilung (Verknüpfung mit Prospektivitäts-Suche)
- Histogramm: Wie verteilen sich die Scores über alle Bergrettigheter?
- Anteil Direkttreffer vs. reine Proxy-Treffer
- Top-10-Claims nach Score als Rangliste

---

## ⬡ Flurkarten-Analyse (Matrikkel-Integration)

Grundlage: `Basisdata_MatrikkelenEiendomskartTeig_FGDB.gdb` (Geonorge)

Geologisch und rechtlich kritisch: Welche Grundstücke (Teige) werden von einem Claim berührt — und zu welchem Prozentsatz? Das vereinfacht die Kontaktaufnahme zu Landbesitzern erheblich.

### Verfügbare Layer
| Layer | Geometrie | Verwendung |
|---|---|---|
| `teig` | MultiPolygon | Flurstücke — Basis für Überschneidungsberechnung |
| `matrikkelenhet` | — | Kataster-Metadaten (Eigner, Matrikkel-Nr.) |
| `eiendomsgrense` | MultiLineString | Grundstücksgrenzen zur Visualisierung |
| `teiggrensepunkt` | Point | Grenzpunkte |
| `teig_arealmerknad` | — | Flächenanmerkungen |

### Überschneidungsberechnung (Spatial Join)
- Für jeden Claim: welche Teige (Flurstücke) werden berührt?
- Berechnung der prozentualen Vereinnahmung je Flurstück:
  ```
  Vereinnahmung [%] = (Schnittfläche Claim ∩ Teig) / Gesamtfläche Teig × 100
  ```
- Klassifizierung: < 10% (randberührt) · 10–50% (teilweise) · > 50% (überwiegend) · 100% (vollständig)

### Darstellung in der Claim-Karte
- Flurstücksgrenzen als einblendbarer Layer (on/off)
- Einfärbung nach Vereinnahmungsgrad (Choropleth)
- Klick auf Flurstück → Infofenster mit Matrikkel-Nr., Fläche, Vereinnahmung %
- Katasternummern einblendbar für direkte Eigentümer-Kontaktaufnahme

### Tabellen-Ansicht je Claim
Beim Klick auf einen Claim in der Karte oder Tabelle:

| Matrikkel-Nr. | Teig-Fläche (m²) | Schnittfläche (m²) | Vereinnahmung |
|---|---|---|---|
| 1234/5 | 45.000 | 12.300 | 27,3 % |
| 1234/6 | 8.200 | 8.200 | 100 % |
| 1235/1 | 120.000 | 3.400 | 2,8 % |

### Export
- CSV je Claim: alle betroffenen Flurstücke mit Vereinnahmungsprozent
- Nutzbar für rechtliche Due Diligence und Eigentümerkontakt

### Technische Umsetzung
- GDB → GeoJSON Konvertierung via `ogr2ogr` (bereits im Projekt etabliert)
- Spatial Join via `geopandas` (overlay intersection)
- Ergebnis in S3 als vorberechnetes GeoJSON ablegen (Performance)
- Nur Teige im Bereich aktiver Claims vorhalten (Datenmenge reduzieren)

---

## Strategische Priorität

Die wertvollste Kombination wäre:

> **Prospektivitäts-Suche → Tabelle → Export**
>
> Score berechnen → gefilterte Tabelle (Score > X) → CSV/Excel für Investoren-Report

> **Claim-Karte → Flurkarten-Analyse → Eigentümerkontakt**
>
> Claim anklicken → betroffene Flurstücke mit % Vereinnahmung → CSV für Rechtsabteilung / Landbesitzer-Kontakt

Das schließt den Analyse-Kreislauf und macht das Tool direkt in der Due-Diligence und im Feldgeschäft nutzbar.

---

*EMI ExploreIQ™ · EMIAG · NGU · DMF · Element29 AS*
