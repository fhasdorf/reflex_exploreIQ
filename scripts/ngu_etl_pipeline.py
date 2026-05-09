"""
NGU ETL Pipeline – exploreIQ
==============================
Verarbeitet alle NGU MINS-Datensätze und bereitet sie für die App auf.

Unterstützte Formate (mit exakter Struktur):
  NordTrondelagFosen MINERAL .xlsx  → Sheet HalfPDL, Header Zeile 13, UTM32
  NordTrondelagFosen ORGANIC .xlsx  → Sheet HalfPDL, Header Zeile 16, UTM32
  Hattfjelldal       .xlsx          → Sheet HalfPDL, Header Zeile 13, UTM33 (!)
  SorTrondelag       .ods           → Sheet 2dbf,    Header Zeile 0,  UTM32
  Kongsberg          .XYZ           → Geophysik EM/Mag/Rad

Ausgabe in geodaten/:
  geochemie.parquet
  geophysik_em.parquet / _mag.parquet / _rad.parquet
  anomalien_geochemie.geojson  (Leaflet-ready)
  anomalien_em.geojson / _mag.geojson / _rad.geojson

Verwendung:
  python scripts/ngu_etl_pipeline.py --input rohdaten --output geodaten
  python scripts/ngu_etl_pipeline.py --input rohdaten --output geodaten --verbose
"""

import argparse
import json
import logging
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ngu_etl")

# ── Explorations-Elemente (Prioritätsreihenfolge) ─────────────────────────────
EXPLORATION_ELEMENTS = [
    "Au", "Ag",
    "Cu", "Ni", "Co", "Zn", "Pb",
    "Mo", "W", "Sn", "Bi",
    "Cr", "V", "Ti",
    "As", "Sb", "Te",
    "Fe", "Mn", "S",
    "K", "Th", "U",
]

ELEMENT_WEIGHTS = {
    "Au": 3.0, "Ag": 3.0,
    "Cu": 2.0, "Ni": 2.0, "Co": 2.0,
    "Zn": 1.5, "Pb": 1.5, "Mo": 1.5,
}

META_COLS = [
    "SampleID", "LocalityID", "FieldProject", "FieldYear",
    "Easting", "Northing", "DDE", "DDN", "Medium", "_quelle", "_utm_zone",
]


# ══════════════════════════════════════════════════════════════════════════════
# GEOCHEMIE LOADER – je Dateiformat exakt konfiguriert
# ══════════════════════════════════════════════════════════════════════════════

def _check_openpyxl():
    try:
        import openpyxl  # noqa
        return True
    except ImportError:
        log.error("openpyxl fehlt! → pip install openpyxl")
        return False


def _check_odfpy():
    try:
        import odf  # noqa
        return True
    except ImportError:
        log.error("odfpy fehlt! → pip install odfpy")
        return False


def _flag_pdl(df: pd.DataFrame) -> pd.DataFrame:
    """Ersetzt <PDL-Werte (z.B. '<0.005') durch HalfPDL."""
    for col in df.select_dtypes(include=["object", "string"]).columns:
        mask = df[col].astype(str).str.startswith("<")
        if mask.any():
            numeric = df[col].astype(str).str.replace("<", "", regex=False).str.strip()
            df[col] = pd.to_numeric(numeric, errors="coerce")
            df.loc[mask, col] = df.loc[mask, col] / 2
    return df


def load_xlsx_nordtrondelag_mineral(filepath: Path) -> pd.DataFrame:
    """NordTrondelagFosen MINERAL soil – Sheet HalfPDL, Header Zeile 13."""
    if not _check_openpyxl():
        return pd.DataFrame()
    log.info(f"  XLSX Mineral: {filepath.name}")
    df = pd.read_excel(filepath, sheet_name="HalfPDL", header=13,
                       engine="openpyxl", na_values=[-9999, 999999, -99999])
    df = df.rename(columns={"E32wgs": "Easting", "N32wgs": "Northing"})
    df["Medium"] = "Mineralboden"
    df["_quelle"] = filepath.stem
    df["_utm_zone"] = 32
    log.info(f"    → {len(df):,} Proben")
    return df


def load_xlsx_nordtrondelag_organic(filepath: Path) -> pd.DataFrame:
    """NordTrondelagFosen ORGANIC soil (Humus) – Sheet HalfPDL, Header Zeile 16."""
    if not _check_openpyxl():
        return pd.DataFrame()
    log.info(f"  XLSX Organic: {filepath.name}")
    df = pd.read_excel(filepath, sheet_name="HalfPDL", header=16,
                       engine="openpyxl", na_values=[-9999, 999999, -99999])
    df = df.rename(columns={"E32wgs": "Easting", "N32wgs": "Northing"})
    df["Medium"] = "Humus"
    df["_quelle"] = filepath.stem
    df["_utm_zone"] = 32
    log.info(f"    → {len(df):,} Proben")
    return df


def load_xlsx_hattfjelldal(filepath: Path) -> pd.DataFrame:
    """Hattfjelldal – Sheet HalfPDL, Header Zeile 13, UTM Zone 33!"""
    if not _check_openpyxl():
        return pd.DataFrame()
    log.info(f"  XLSX Hattfjelldal: {filepath.name}")
    df = pd.read_excel(filepath, sheet_name="HalfPDL", header=13,
                       engine="openpyxl", na_values=[-9999, 999999, -99999])
    # Hattfjelldal: yproj/xproj sind UTM33 Koordinaten
    df = df.rename(columns={"yproj": "Northing", "xproj": "Easting"})
    df["Medium"] = df.get("Medium", pd.Series(["Mineralboden"] * len(df)))
    df["_quelle"] = filepath.stem
    df["_utm_zone"] = 33  # Wichtig! Nordnorwegen
    log.info(f"    → {len(df):,} Proben (UTM Zone 33)")
    return df


def load_ods_sortrondelag(filepath: Path) -> pd.DataFrame:
    """SorTrondelag mineral/humus – Sheet 2dbf, Header Zeile 0."""
    if not _check_odfpy():
        return pd.DataFrame()
    log.info(f"  ODS: {filepath.name}")
    df = pd.read_excel(filepath, sheet_name="2dbf", header=0,
                       engine="odf", na_values=[-9999, 999999, -99999])
    # Elemente haben Suffix 'ppm' → entfernen (Agppm → Ag)
    elem_rename = {c: c.replace("ppm", "") for c in df.columns if c.endswith("ppm")}
    df = df.rename(columns=elem_rename)
    # Koordinaten: Xcoordinate/Ycoordinate sind UTM, DDE/DDN sind WGS84 Grad
    df = df.rename(columns={"Xcoordinate": "Easting", "Ycoordinate": "Northing",
                             "Field Year": "FieldYear",
                             "Project": "FieldProject",
                             "Locality": "LocalityID"})
    # Medium normalisieren (Mineraljord → Mineralboden)
    if "Medium" in df.columns:
        df["Medium"] = df["Medium"].str.replace("Mineraljord", "Mineralboden", regex=False)
        df["Medium"] = df["Medium"].str.replace("Humusjord", "Humus", regex=False)
    else:
        medium = "Humus" if "humus" in filepath.stem.lower() else "Mineralboden"
        df["Medium"] = medium
    df["_quelle"] = filepath.stem
    df["_utm_zone"] = 32
    log.info(f"    → {len(df):,} Proben")
    return df


def _route_xlsx(filepath: Path) -> pd.DataFrame:
    """Wählt den richtigen XLSX-Loader anhand des Dateinamens."""
    stem = filepath.stem.lower()
    if "organic" in stem or "humus" in stem:
        return load_xlsx_nordtrondelag_organic(filepath)
    elif "hattfjelldal" in stem or "minn" in stem:
        return load_xlsx_hattfjelldal(filepath)
    else:
        # Standard: NordTrondelag Mineral oder ähnliche Struktur
        return load_xlsx_nordtrondelag_mineral(filepath)


def _route_ods(filepath: Path) -> pd.DataFrame:
    """Wählt den richtigen ODS-Loader."""
    return load_ods_sortrondelag(filepath)


# ══════════════════════════════════════════════════════════════════════════════
# GEOCHEMIE MERGE & SCORING
# ══════════════════════════════════════════════════════════════════════════════

def merge_geochem(dfs: list) -> pd.DataFrame:
    """Vereint alle Geochemiedatensätze zu einem einheitlichen DataFrame."""
    if not dfs:
        return pd.DataFrame()
    log.info(f"Vereinige {len(dfs)} Geochemiedatensätze...")
    merged = pd.concat(dfs, ignore_index=True, sort=False)

    # Koordinaten sicherstellen
    if "Easting" not in merged.columns:
        for alias in ("DDE", "xproj", "Xcoordinate", "X_UTM"):
            if alias in merged.columns:
                merged["Easting"] = merged[alias]
                break
    if "Northing" not in merged.columns:
        for alias in ("DDN", "yproj", "Ycoordinate", "Y_UTM"):
            if alias in merged.columns:
                merged["Northing"] = merged[alias]
                break

    if "Easting" not in merged.columns or "Northing" not in merged.columns:
        log.error("Keine Koordinatenspalten gefunden!")
        log.error(f"Verfügbare Spalten: {list(merged.columns[:20])}")
        return pd.DataFrame()

    before = len(merged)
    merged = merged.dropna(subset=["Easting", "Northing"])
    if before - len(merged) > 0:
        log.warning(f"  {before - len(merged)} Zeilen ohne Koordinaten entfernt")

    available_elements = [e for e in EXPLORATION_ELEMENTS if e in merged.columns]
    meta_available = [c for c in META_COLS if c in merged.columns]
    keep = list(dict.fromkeys(meta_available + available_elements))
    merged = merged[[c for c in keep if c in merged.columns]]

    log.info(f"  Gesamt: {len(merged):,} Proben | {len(available_elements)} Elemente")
    if "Medium" in merged.columns:
        log.info(f"  Medien: {merged['Medium'].value_counts().to_dict()}")
    if "_quelle" in merged.columns:
        log.info(f"  Quellen: {merged['_quelle'].unique().tolist()}")
    return merged


def compute_anomaly_score(df: pd.DataFrame) -> pd.DataFrame:
    """Berechnet gewichteten Anomalie-Score (0–100) pro Probe."""
    available = [e for e in EXPLORATION_ELEMENTS
                 if e in df.columns and df[e].notna().sum() > 10]
    if not available:
        df["anomaly_score"] = 0.0
        return df

    scores = pd.DataFrame(index=df.index)
    for el in available:
        series = df[el].copy()
        mean, std = series.mean(), series.std()
        if std == 0:
            continue
        z = ((series - mean) / std).clip(lower=0)
        scores[el] = z * ELEMENT_WEIGHTS.get(el, 1.0)

    raw = scores.sum(axis=1)
    max_val = raw.quantile(0.99)
    df["anomaly_score"] = (raw / max_val * 100).clip(0, 100).round(1) if max_val > 0 else 0.0
    high = (df["anomaly_score"] > 70).sum()
    log.info(f"  Anomalie-Score berechnet | High (>70): {high:,} Punkte")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# UTM → WGS84
# ══════════════════════════════════════════════════════════════════════════════

def utm_to_wgs84(df: pd.DataFrame, default_zone: int = 32) -> pd.DataFrame:
    """
    Konvertiert UTM → WGS84.
    Unterstützt gemischte UTM-Zonen (32 + 33) im selben DataFrame.
    DDE/DDN (WGS84 Grad) werden bevorzugt wenn vorhanden.
    """
    # Wenn DDE/DDN vorhanden: direkt nutzen (bereits WGS84)
    if "DDE" in df.columns and "DDN" in df.columns:
        valid_dde = df["DDE"].notna() & (df["DDE"].abs() < 180)
        if valid_dde.sum() > len(df) * 0.5:
            df["lon"] = df["DDE"].where(valid_dde)
            df["lat"] = df["DDN"].where(df["DDN"].notna())
            log.info("  Koordinaten: DDE/DDN (bereits WGS84) verwendet")
            # Fehlende Werte über UTM berechnen
            missing = df["lon"].isna()
            if missing.any() and "Easting" in df.columns:
                df = _fill_utm(df, missing, default_zone)
            return df

    return _fill_utm(df, pd.Series([True] * len(df), index=df.index), default_zone)


def _fill_utm(df: pd.DataFrame, mask: pd.Series, default_zone: int) -> pd.DataFrame:
    """Konvertiert UTM-Koordinaten für alle Zeilen in mask."""
    try:
        from pyproj import Transformer
    except ImportError:
        log.warning("pyproj nicht installiert → pip install pyproj")
        log.warning("UTM-Koordinaten werden direkt als lon/lat gesetzt (ungenau!)")
        df["lon"] = df.get("Easting", np.nan)
        df["lat"] = df.get("Northing", np.nan)
        return df

    if "lon" not in df.columns:
        df["lon"] = np.nan
    if "lat" not in df.columns:
        df["lat"] = np.nan

    # Zonen-aware Konvertierung
    zone_col = "_utm_zone" if "_utm_zone" in df.columns else None
    zones = df[zone_col].unique() if zone_col else [default_zone]

    for zone in zones:
        if zone_col:
            row_mask = mask & (df[zone_col] == zone)
        else:
            row_mask = mask
        if not row_mask.any():
            continue
        sub = df.loc[row_mask]
        t = Transformer.from_crs(f"EPSG:326{int(zone):02d}", "EPSG:4326", always_xy=True)
        lons, lats = t.transform(sub["Easting"].values, sub["Northing"].values)
        df.loc[row_mask, "lon"] = np.round(lons, 6)
        df.loc[row_mask, "lat"] = np.round(lats, 6)
        log.info(f"  UTM Zone {zone} → WGS84: {row_mask.sum():,} Punkte konvertiert")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# GEOPHYSIK (XYZ)
# ══════════════════════════════════════════════════════════════════════════════

def _detect_xyz_type(filepath: Path) -> str:
    name = filepath.stem.lower()
    if "_em_" in name:  return "em"
    if "_mag_" in name: return "mag"
    if "_rad_" in name: return "rad"
    return "em"


def load_geophys_xyz(filepath: Path) -> pd.DataFrame:
    log.info(f"  XYZ: {filepath.name}")
    dtype = _detect_xyz_type(filepath)
    comments, header_line, data_start = [], None, 0
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if not s: continue
        if s[0] in ("/", "#", "!"):
            comments.append(s); data_start = i + 1
        elif header_line is None:
            try:    float(s.split()[0]); data_start = i
            except: header_line = s; data_start = i + 1
            break
    col_names = header_line.replace(",", " ").split() if header_line else None
    df = pd.read_csv(filepath, skiprows=data_start, sep=r"\s+", header=None,
                     names=col_names, na_values=[-9999, -9999.0, 99999, 999999],
                     engine="python", on_bad_lines="skip")
    rename = {}
    for col in df.columns:
        cl = str(col).lower()
        if cl in ("x","east","easting","utme","e32wgs"): rename[col] = "Easting"
        elif cl in ("y","north","northing","utmn","n32wgs"): rename[col] = "Northing"
        elif cl in ("z","elev","elevation","alt"): rename[col] = "Elevation"
    df = df.rename(columns=rename)
    df["_typ"] = dtype
    df["_quelle"] = filepath.stem
    df["_area"] = next((a for a in ("Area1","Area2","Area3")
                        if a.lower() in filepath.stem.lower()), "Unknown")
    log.info(f"    → {len(df):,} Punkte | {dtype.upper()}")
    return df, dtype


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def save_parquet(df: pd.DataFrame, path: Path):
    if df.empty:
        log.warning(f"  Leer – {path.name} nicht gespeichert"); return
    path.parent.mkdir(parents=True, exist_ok=True)
    # Gemischte Typen (z.B. SampleID mit Buchstaben) zu str normalisieren
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).replace("nan", pd.NA)
    df.to_parquet(path, index=False, compression="snappy")
    log.info(f"  ✓ {path.name} ({path.stat().st_size/1e6:.1f} MB, {len(df):,} Zeilen)")


def save_geojson(df: pd.DataFrame, path: Path, value_cols: list, max_points: int = 50_000):
    if df.empty or "lon" not in df.columns:
        log.warning(f"  Kein GeoJSON für {path.name}"); return
    export = df.dropna(subset=["lon", "lat"]).copy()
    if len(export) > max_points:
        export = export.iloc[::len(export)//max_points]
    features = []
    for _, row in export.iterrows():
        props = {}
        for col in value_cols + ["SampleID","Medium","_quelle","FieldYear","anomaly_score"]:
            if col in row.index:
                v = row[col]
                props[col] = None if (isinstance(v, float) and np.isnan(v)) else (
                    str(v) if isinstance(v, str) else
                    round(float(v), 4) if isinstance(v, (int, float, np.integer, np.floating)) else str(v)
                )
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row["lon"]), float(row["lat"])]},
            "properties": props,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f,
                  separators=(",", ":"), ensure_ascii=False)
    log.info(f"  ✓ {path.name} ({path.stat().st_size/1e6:.1f} MB, {len(features):,} Features)")


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(input_dir: Path, output_dir: Path, utm_zone: int = 32):
    output_dir.mkdir(parents=True, exist_ok=True)
    log.info("=" * 60)
    log.info("NGU ETL Pipeline – exploreIQ")
    log.info(f"Input:  {input_dir}")
    log.info(f"Output: {output_dir}")
    log.info("=" * 60)

    xlsx_files = sorted(input_dir.rglob("*.xlsx")) + sorted(input_dir.rglob("*.XLSX"))
    ods_files  = sorted(input_dir.rglob("*.ods"))  + sorted(input_dir.rglob("*.ODS"))
    xyz_files  = sorted(input_dir.rglob("*.XYZ"))  + sorted(input_dir.rglob("*.xyz"))
    log.info(f"Gefunden: {len(xlsx_files)} XLSX | {len(ods_files)} ODS | {len(xyz_files)} XYZ")

    # ── Geochemie ────────────────────────────────────────────────────────────
    geochem_dfs = []

    if xlsx_files:
        log.info("\n── Geochemie XLSX ──────────────────────────────────")
        for f in xlsx_files:
            try:
                df = _route_xlsx(f)
                if not df.empty:
                    df = _flag_pdl(df)
                    geochem_dfs.append(df)
            except Exception as e:
                log.error(f"  Fehler {f.name}: {e}")

    if ods_files:
        log.info("\n── Geochemie ODS ───────────────────────────────────")
        for f in ods_files:
            try:
                df = _route_ods(f)
                if not df.empty:
                    df = _flag_pdl(df)
                    geochem_dfs.append(df)
            except Exception as e:
                log.error(f"  Fehler {f.name}: {e}")

    if geochem_dfs:
        log.info("\n── Merge & Scoring ─────────────────────────────────")
        geochem = merge_geochem(geochem_dfs)
        if not geochem.empty:
            geochem = compute_anomaly_score(geochem)
            geochem = utm_to_wgs84(geochem, utm_zone)
            log.info("\n── Export Geochemie ────────────────────────────────")
            save_parquet(geochem, output_dir / "geochemie.parquet")
            exp_els = [e for e in EXPLORATION_ELEMENTS[:8] if e in geochem.columns]
            save_geojson(geochem, output_dir / "anomalien_geochemie.geojson", exp_els)

    # ── Geophysik ────────────────────────────────────────────────────────────
    if xyz_files:
        log.info("\n── Geophysik XYZ ───────────────────────────────────")
        em_dfs, mag_dfs, rad_dfs = [], [], []
        for f in xyz_files:
            try:
                df, dtype = load_geophys_xyz(f)
                if   dtype == "em":  em_dfs.append(df)
                elif dtype == "mag": mag_dfs.append(df)
                elif dtype == "rad": rad_dfs.append(df)
            except Exception as e:
                log.error(f"  Fehler {f.name}: {e}")

        log.info("\n── Export Geophysik ────────────────────────────────")
        for label, dfs, fname in [
            ("EM",  em_dfs,  "geophysik_em.parquet"),
            ("Mag", mag_dfs, "geophysik_mag.parquet"),
            ("Rad", rad_dfs, "geophysik_rad.parquet"),
        ]:
            if not dfs: continue
            merged = pd.concat(dfs, ignore_index=True, sort=False)
            merged = utm_to_wgs84(merged, utm_zone)
            save_parquet(merged, output_dir / fname)
            meta = {"Easting","Northing","lon","lat","Line","Fiducial","_typ","_quelle","_area"}
            val_cols = [c for c in merged.columns if c not in meta][:6]
            save_geojson(merged, output_dir / f"anomalien_{label.lower()}.geojson",
                         val_cols, max_points=30_000)

    # ── Zusammenfassung ──────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("PIPELINE ABGESCHLOSSEN")
    log.info("=" * 60)
    for f in sorted(output_dir.glob("*.*")):
        log.info(f"  {f.name:<48} {f.stat().st_size/1e6:6.1f} MB")
    log.info("\nNächster Schritt: reflex run")


def main():
    parser = argparse.ArgumentParser(description="NGU ETL Pipeline für exploreIQ")
    parser.add_argument("--input",    "-i", default="rohdaten")
    parser.add_argument("--output",   "-o", default="geodaten")
    parser.add_argument("--utm-zone", "-u", type=int, default=32)
    parser.add_argument("--verbose",  "-v", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    input_dir = Path(args.input)
    if not input_dir.exists():
        log.error(f"Eingabeordner nicht gefunden: {input_dir}")
        sys.exit(1)
    run_pipeline(input_dir, Path(args.output), args.utm_zone)


if __name__ == "__main__":
    main()
