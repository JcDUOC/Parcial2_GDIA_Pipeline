"""
Etapa 2 — Limpieza y Transformación
Pipeline de Datos: Transporte Urbano (Viajes en Metro/Bus)
Asignatura: Gestión de Datos para IA — DuocUC
"""

import pandas as pd
import numpy as np
import logging
import os
from sklearn.preprocessing import MinMaxScaler

# ──────────────────────────────────────────
#  Configuración de logging
# ──────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log = logging.getLogger("limpieza")
log.setLevel(logging.INFO)
if not log.handlers:
    _fmt = logging.Formatter("%(asctime)s | LIMPIEZA | %(levelname)s | %(message)s")
    _fh = logging.FileHandler(os.path.join(LOG_DIR, "limpieza.log"), encoding="utf-8")
    _fh.setFormatter(_fmt)
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    log.addHandler(_fh)
    log.addHandler(_sh)
    log.propagate = False

BASE_DIR  = os.path.join(os.path.dirname(__file__), "..")
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
os.makedirs(CLEAN_DIR, exist_ok=True)


# ──────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────
def _log_shape(df: pd.DataFrame, etapa: str):
    log.info(f"[{etapa}] Shape actual: {df.shape[0]} filas × {df.shape[1]} columnas")


# ──────────────────────────────────────────
#  Función principal
# ──────────────────────────────────────────
def limpiar(df: pd.DataFrame = None) -> pd.DataFrame:
    log.info("=" * 60)
    log.info("INICIO — Etapa 2: Limpieza y Transformación")
    log.info("=" * 60)

    # Cargar desde disco si no se pasa DataFrame
    if df is None:
        raw_path = os.path.join(RAW_DIR, "viajes_transporte_raw.csv")
        df = pd.read_csv(raw_path, encoding="utf-8")
        log.info(f"Dataset cargado desde {raw_path}")

    _log_shape(df, "Inicio")

    # ── 1. Eliminar duplicados ───────────────────────────────────
    antes = len(df)
    df = df.drop_duplicates()
    eliminados = antes - len(df)
    log.info(f"Duplicados eliminados: {eliminados} filas.")
    _log_shape(df, "Tras deduplicación")

    # ── 2. Tratar fechas con formato inválido ────────────────────
    for col in ["fecha_hora_entrada", "fecha_hora_salida"]:
        invalidos_mask = pd.to_datetime(df[col], errors="coerce").isna()
        n_invalidos = invalidos_mask.sum()
        if n_invalidos > 0:
            log.warning(f"Fechas inválidas en '{col}': {n_invalidos} registros → se eliminan.")
            df = df[~invalidos_mask].copy()
        df[col] = pd.to_datetime(df[col], errors="coerce")
    _log_shape(df, "Tras limpieza de fechas")

    # ── 3. Corregir duraciones imposibles ───────────────────────
    antes = len(df)
    df = df[(df["duracion_minutos"] >= 1) & (df["duracion_minutos"] <= 300)]
    log.info(f"Duraciones fuera de rango [1, 300] min eliminadas: {antes - len(df)} filas.")
    _log_shape(df, "Tras corrección de duraciones")

    # ── 4. Corregir tarifas negativas ────────────────────────────
    n_neg = (df["tarifa_pagada"] < 0).sum()
    df.loc[df["tarifa_pagada"] < 0, "tarifa_pagada"] = np.nan
    log.info(f"Tarifas negativas convertidas a NaN: {n_neg} registros.")

    # ── 5. Corregir número de pasajeros = 0 ─────────────────────
    n_cero = (df["numero_pasajeros"] == 0).sum()
    df = df[df["numero_pasajeros"] > 0]
    log.info(f"Registros con numero_pasajeros = 0 eliminados: {n_cero}.")
    _log_shape(df, "Tras corrección de pasajeros")

    # ── 6. Normalizar categorías inconsistentes ──────────────────
    TIPO_MAPPING = {
        "bip":                    "BIP!",
        "bip!":                   "BIP!",
        "bip! adulto mayor":      "BIP! Adulto Mayor",
        "bip adulto mayor":       "BIP! Adulto Mayor",
        "bip! estudiante":        "BIP! Estudiante",
        "bip estudiante":         "BIP! Estudiante",
        "bip! tne":               "BIP! TNE",
        "bip tne":                "BIP! TNE",
        "efectivo":               "Efectivo",
    }
    df["tipo_tarjeta"] = (
        df["tipo_tarjeta"]
        .str.strip()
        .str.lower()
        .map(lambda x: TIPO_MAPPING.get(x, x) if isinstance(x, str) else x)
    )
    log.info("Categorías de tipo_tarjeta normalizadas.")

    # ── 7. Imputar nulos en tarifa_pagada con la mediana ────────
    mediana_tarifa = df["tarifa_pagada"].median()
    n_nulos = df["tarifa_pagada"].isna().sum()
    df["tarifa_pagada"] = df["tarifa_pagada"].fillna(mediana_tarifa)
    log.info(f"Nulos en 'tarifa_pagada' imputados con mediana ({mediana_tarifa:.0f}): {n_nulos} registros.")

    # ── 8. Eliminar nulos restantes en columnas críticas ─────────
    cols_criticas = ["estacion_entrada", "estacion_salida", "linea", "tipo_tarjeta"]
    antes = len(df)
    df = df.dropna(subset=cols_criticas)
    log.info(f"Filas con nulos en columnas críticas eliminadas: {antes - len(df)}.")
    _log_shape(df, "Tras eliminación de nulos críticos")

    # ════════════════════════════════════════
    #  TRANSFORMACIONES
    # ════════════════════════════════════════

    # T1 — Nueva columna derivada: franja horaria
    def franja_horaria(dt):
        h = dt.hour
        if   6 <= h < 9:  return "Mañana_punta"
        elif 9 <= h < 12: return "Mañana_baja"
        elif 12 <= h < 14: return "Mediodía"
        elif 14 <= h < 18: return "Tarde_baja"
        elif 18 <= h < 21: return "Tarde_punta"
        else:              return "Nocturno"

    df["franja_horaria"] = df["fecha_hora_entrada"].apply(franja_horaria)
    log.info("T1: Columna derivada 'franja_horaria' creada.")

    # T2 — Nueva columna derivada: día de la semana
    df["dia_semana"] = df["fecha_hora_entrada"].dt.day_name()
    log.info("T2: Columna derivada 'dia_semana' creada.")

    # T3 — Normalización Min-Max de tarifa_pagada → tarifa_normalizada
    scaler = MinMaxScaler()
    df["tarifa_normalizada"] = scaler.fit_transform(df[["tarifa_pagada"]])
    log.info("T3: Normalización Min-Max aplicada → columna 'tarifa_normalizada'.")

    # T4 — Encoding ordinal de franja_horaria
    orden_franja = {
        "Mañana_punta": 0, "Mañana_baja": 1, "Mediodía": 2,
        "Tarde_baja": 3,   "Tarde_punta": 4, "Nocturno": 5,
    }
    df["franja_codigo"] = df["franja_horaria"].map(orden_franja)
    log.info("T4: Encoding ordinal de 'franja_horaria' → columna 'franja_codigo'.")

    # T5 — Flag evasión de tarifa (tarifa = 0)
    df["evasion"] = (df["tarifa_pagada"] == 0).astype(int)
    log.info("T5: Columna binaria 'evasion' creada (1 = evasión de tarifa).")

    # ── Guardar dataset limpio ──────────────────────────────────
    clean_path = os.path.join(CLEAN_DIR, "viajes_transporte_clean.csv")
    df.to_csv(clean_path, index=False, encoding="utf-8")
    log.info(f"Dataset limpio guardado en: {clean_path}")
    log.info(f"Shape final: {df.shape[0]} filas × {df.shape[1]} columnas")
    log.info("FIN — Etapa 2: Limpieza y Transformación completada exitosamente.")
    return df


if __name__ == "__main__":
    df = limpiar()
    print("\n── Primeras 5 filas del dataset limpio ──")
    print(df.head().to_string())
    print(f"\n── Distribución de franja_horaria ──\n{df['franja_horaria'].value_counts()}")
