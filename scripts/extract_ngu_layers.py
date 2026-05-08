"""
extract_ngu_layers.py
=====================
Extrahiert 8 NGU-Layer aus Mineralressurser.gdb und exportiert
sie als farbkodierte GeoJSON-Dateien in den assets/ngu/ Ordner.

Ausführen aus dem Apps_Reflex-Ordner:
    python extract_ngu_layers.py
"""

import os
import json
import geopandas as gpd

# ── Pfade ─────────────────────────────────────────────────────────────────────
GDB_PATH  = r"E:\EMIAG\Data_Geonorge\Mineralressurser.gdb"
OUT_DIR   = r"E:\EMIAG\Apps_Reflex\mineral_app\assets\ngu"

# ── Farbkodierung nach ressursType_tekst ──────────────────────────────────────
COLORS = {
    "Edelmetaller (Au, Ag, PGE)":                                        "#FFD700",
    "Basemetaller (Cu, Zn, Pbinkl. Fe-sulfider, As, Sb, Bi, Sn)":       "#CD7F32",
    "Jernlegeringsmetaller (Cr, Ni, Co, V, Mo, W)":                      "#4A90D9",
    "Jernmetaller (Fe, Mn, Ti)":                                         "#8B6914",
    "Energimetaller (U, Th)":                                            "#90EE90",
    "Spesialmetaller (Nb, Ta, Be, Li, Sc, REE)":                        "#DA70D6",
    "Karbonatmineraler":                                                 "#F0E68C",
    "Silika":                                                            "#E8E8D0",
    "Olivin":                                                            "#6B8E23",
    "Feltspat":                                                          "#DEB887",
    "Grafitt":                                                           "#808080",
    "Magnesiummineraler":                                                "#20B2AA",
    "Nefelinsyenitt":                                                    "#9370DB",
    "Talk":                                                              "#98FB98",
    "Glimmermineraler":                                                  "#DAA520",
    "Andre industrimineraler":                                           "#A9A9A9",
}

# ── Layer-Mapping: Ausgabename → GDB-Layername ────────────────────────────────
LAYERS = {
    "malm_forekomst_flate":        "MalmForekomst_flate",
    "malm_registrering_flate":     "MalmRegistrering_flate",
    "malm_forekomst_punkt":        "MalmForekomst",
    "malm_registrering_punkt":     "MalmRegistrering",
    "industri_forekomst_flate":    "IndustrimineralForekomst_flate",
    "industri_registrering_flate": "IndustrimineralRegistrering_flate",
    "industri_forekomst_punkt":    "IndustrimineralForekomst",
    "industri_registrering_punkt": "IndustrimineralRegistrering",
}

# ── Ausgabeordner anlegen ─────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)

# ── Verfügbare Layer in der GDB prüfen ───────────────────────────────────────
print("Verfügbare Layer in der GDB:")
try:
    import fiona
    layers_in_gdb = fiona.listlayers(GDB_PATH)
    for l in layers_in_gdb:
        print(f"  {l}")
except Exception as e:
    print(f"  Fehler beim Lesen der GDB: {e}")
    print("  Bitte sicherstellen dass fiona/geopandas installiert sind:")
    print("  pip install geopandas fiona")
    exit(1)

print()

# ── Extraktion ────────────────────────────────────────────────────────────────
for out_name, layer_name in LAYERS.items():

    # Prüfen ob Layer existiert (Groß/Kleinschreibung)
    matched = None
    for l in layers_in_gdb:
        if l.lower() == layer_name.lower():
            matched = l
            break

    if not matched:
        print(f"⚠  Layer nicht gefunden: {layer_name}")
        print(f"   Verfügbar: {[l for l in layers_in_gdb if 'alm' in l or 'ndustri' in l]}")
        continue

    print(f"Lese: {matched} → {out_name}.geojson")

    try:
        gdf = gpd.read_file(GDB_PATH, layer=matched)

        # CRS → WGS84
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")

        # Farbkodierung
        if "ressursType_tekst" in gdf.columns:
            gdf["_fill"] = gdf["ressursType_tekst"].map(COLORS).fillna("#A9A9A9")
        else:
            # Fallback: nach objekttype
            gdf["_fill"] = "#A9A9A9"
            print(f"   ⚠ Spalte 'ressursType_tekst' nicht gefunden")
            print(f"   Spalten: {list(gdf.columns)}")

        # Datetime-Spalten → String
        import pandas as pd
        for col in gdf.columns:
            if col == "geometry":
                continue
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.strftime("%Y-%m-%d").fillna("")
            else:
                gdf[col] = gdf[col].astype(str).replace("nan", "").replace("None", "")

        # Exportieren
        out_path = os.path.join(OUT_DIR, f"{out_name}.geojson")
        gdf.to_file(out_path, driver="GeoJSON")
        size_kb = os.path.getsize(out_path) // 1024
        print(f"   ✓ {len(gdf)} Features → {size_kb} KB")

    except Exception as e:
        print(f"   ✗ Fehler: {e}")

print()
print("Fertig! Dateien in:", OUT_DIR)
print()
print("Nächster Schritt: reflex run")
