import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append('C:/Users/JeanC/Parcial2_GDIA_Pipeline')
import Scripts.logging_utils.logging_utils as lgu
import os

from ingesta import leer_archivo

logging_limpieza = lgu.configurar_logger("Limpieza")


# ─────────────────────────────────────────
#  Valores válidos por columna categórica
# ─────────────────────────────────────────
LINEAS_VALIDAS      = ["L1", "L2", "L4", "L4A", "L5", "L6"]
TIPOS_TARJETA_VALID = ["BIP!", "BIP! Adulto Mayor", "BIP! Estudiante", "BIP! TNE", "Efectivo"]


TIPO_MAPPING = {
    "bip":               "BIP!",
    "bip!":              "BIP!",
    "bip! adulto mayor": "BIP! Adulto Mayor",
    "bip adulto mayor":  "BIP! Adulto Mayor",
    "bip! estudiante":   "BIP! Estudiante",
    "bip estudiante":    "BIP! Estudiante",
    "bip! tne":          "BIP! TNE",
    "bip tne":           "BIP! TNE",
    "efectivo":          "Efectivo",
}


def eliminar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    antes = len(df)
    df = df.drop_duplicates()
    eliminados = antes - len(df)
    logging_limpieza.info(f"Duplicados eliminados: {eliminados} filas.")
    return df


def limpiar_fechas(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["fecha_hora_entrada", "fecha_hora_salida"]:
        if col not in df.columns:
            logging_limpieza.warning(f"Columna '{col}' no encontrada, se omite.")
            continue
        invalidos = pd.to_datetime(df[col], errors="coerce").isna()
        n = invalidos.sum()
        if n > 0:
            logging_limpieza.warning(f"Fechas inválidas en '{col}': {n} filas eliminadas.")
            df = df[~invalidos].copy()
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def limpiar_duraciones(df: pd.DataFrame) -> pd.DataFrame:
    if "duracion_minutos" not in df.columns:
        logging_limpieza.warning("Columna 'duracion_minutos' no encontrada, se omite.")
        return df
    antes = len(df)
    df = df[(df["duracion_minutos"] >= 1) & (df["duracion_minutos"] <= 300)]
    logging_limpieza.info(f"Duraciones fuera de rango eliminadas: {antes - len(df)} filas.")
    return df


def limpiar_tarifas(df: pd.DataFrame) -> pd.DataFrame:
    if "tarifa_pagada" not in df.columns:
        logging_limpieza.warning("Columna 'tarifa_pagada' no encontrada, se omite.")
        return df
    n_neg = (df["tarifa_pagada"] < 0).sum()
    df.loc[df["tarifa_pagada"] < 0, "tarifa_pagada"] = np.nan
    logging_limpieza.info(f"Tarifas negativas convertidas a NaN: {n_neg} registros.")

    mediana = df["tarifa_pagada"].median()
    n_nulos = df["tarifa_pagada"].isna().sum()
    df["tarifa_pagada"] = df["tarifa_pagada"].fillna(mediana)
    logging_limpieza.info(f"Nulos en 'tarifa_pagada' imputados con mediana ({mediana:.0f} CLP): {n_nulos} registros.")
    return df


def limpiar_pasajeros(df: pd.DataFrame) -> pd.DataFrame:
    if "numero_pasajeros" not in df.columns:
        logging_limpieza.warning("Columna 'numero_pasajeros' no encontrada, se omite.")
        return df
    antes = len(df)
    df = df[df["numero_pasajeros"] > 0]
    logging_limpieza.info(f"Registros con numero_pasajeros <= 0 eliminados: {antes - len(df)} filas.")
    return df


def normalizar_tipo_tarjeta(df: pd.DataFrame) -> pd.DataFrame:
    if "tipo_tarjeta" not in df.columns:
        logging_limpieza.warning("Columna 'tipo_tarjeta' no encontrada, se omite.")
        return df
    df["tipo_tarjeta"] = (
        df["tipo_tarjeta"]
        .str.strip()
        .str.lower()
        .map(lambda x: TIPO_MAPPING.get(x, x) if isinstance(x, str) else x)
    )
    logging_limpieza.info("Categorías de 'tipo_tarjeta' normalizadas al catálogo oficial.")
    return df


def eliminar_nulos_criticos(df: pd.DataFrame) -> pd.DataFrame:
    cols_criticas = [c for c in ["estacion_entrada", "estacion_salida", "linea", "tipo_tarjeta"] if c in df.columns]
    antes = len(df)
    df = df.dropna(subset=cols_criticas)
    logging_limpieza.info(f"Filas con nulos en columnas críticas eliminadas: {antes - len(df)} filas.")
    return df


# ─────────────────────────────────────────
#  Transformaciones
# ─────────────────────────────────────────

def agregar_franja_horaria(df: pd.DataFrame) -> pd.DataFrame:
    if "fecha_hora_entrada" not in df.columns:
        logging_limpieza.warning("No se puede calcular franja_horaria: falta 'fecha_hora_entrada'.")
        return df

    def franja(dt):
        h = dt.hour
        if   6 <= h < 9:   return "Mañana_punta"
        elif 9 <= h < 12:  return "Mañana_baja"
        elif 12 <= h < 14: return "Mediodía"
        elif 14 <= h < 18: return "Tarde_baja"
        elif 18 <= h < 21: return "Tarde_punta"
        else:              return "Nocturno"

    df["franja_horaria"] = df["fecha_hora_entrada"].apply(franja)
    logging_limpieza.info("T1: Columna 'franja_horaria' creada.")
    return df


def agregar_dia_semana(df: pd.DataFrame) -> pd.DataFrame:
    if "fecha_hora_entrada" not in df.columns:
        logging_limpieza.warning("No se puede calcular dia_semana: falta 'fecha_hora_entrada'.")
        return df
    df["dia_semana"] = df["fecha_hora_entrada"].dt.day_name()
    logging_limpieza.info("T2: Columna 'dia_semana' creada.")
    return df


def agregar_flag_evasion(df: pd.DataFrame) -> pd.DataFrame:
    if "tarifa_pagada" not in df.columns:
        logging_limpieza.warning("No se puede calcular evasion: falta 'tarifa_pagada'.")
        return df
    df["evasion"] = (df["tarifa_pagada"] == 0).astype(int)
    logging_limpieza.info("T3: Columna 'evasion' creada (1 = evasión de tarifa).")
    return df


# ─────────────────────────────────────────
#  Función principal
# ─────────────────────────────────────────

def limpiar_datos(direccion_archivo: str, sheet_excel=0) -> pd.DataFrame:

    logging_limpieza.info("=" * 60)
    logging_limpieza.info("INICIO — Etapa 2: Limpieza y Transformación")
    logging_limpieza.info("=" * 60)

    df = leer_archivo(direccion_archivo, sheet_excel)

    if df is None:
        logging_limpieza.error("No se pudo cargar el archivo. Limpieza abortada.")
        return None

    logging_limpieza.info(f"Dataset recibido: {df.shape[0]} filas × {df.shape[1]} columnas.")

    # ── Limpieza ──────────────────────────────────────────────
    df = eliminar_duplicados(df)
    df = limpiar_fechas(df)
    df = limpiar_duraciones(df)
    df = limpiar_tarifas(df)
    df = limpiar_pasajeros(df)
    df = normalizar_tipo_tarjeta(df)
    df = eliminar_nulos_criticos(df)

    # ── Transformaciones ──────────────────────────────────────
    df = agregar_franja_horaria(df)
    df = agregar_dia_semana(df)
    df = agregar_flag_evasion(df)

    # ── Guardar resultado ─────────────────────────────────────
    os.makedirs("data/clean", exist_ok=True)
    output_path = "data/clean/datos_limpios.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logging_limpieza.info(f"Dataset limpio guardado en: {output_path}")
    logging_limpieza.info(f"Shape final: {df.shape[0]} filas × {df.shape[1]} columnas.")
    logging_limpieza.info("FIN — Etapa 2: Limpieza y Transformación completada.")

    return df


if __name__ == "__main__":
    df_limpio = limpiar_datos("data/raw/viajes_transporte_raw.csv")
    if df_limpio is not None:
        print(df_limpio.head().to_string())