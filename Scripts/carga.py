import pandas as pd
import sqlite3
import os
import sys
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import logging_utils.logging_utils as lgu

logging_carga = lgu.configurar_logger("Carga")


def crear_tabla(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS viajes (

        viaje_id INTEGER PRIMARY KEY,

        fecha_hora_entrada TEXT,
        fecha_hora_salida TEXT,

        estacion_entrada TEXT,
        estacion_salida TEXT,

        linea TEXT,
        tipo_tarjeta TEXT,

        tarifa_pagada REAL,
        duracion_minutos INTEGER,
        numero_pasajeros INTEGER,

        franja_horaria TEXT,
        dia_semana TEXT,

        evasion INTEGER
    )
    """)


def cargar_datos_bd():

    os.makedirs("database", exist_ok=True)

    ruta_csv = "data/clean/datos_limpios.csv"
    ruta_bd = "database/transporte.db"

    conn = None

    try:

        logging_carga.info("=" * 60)
        logging_carga.info("INICIO — Etapa 4: Carga a Base de Datos")
        logging_carga.info("=" * 60)

        df = pd.read_csv(ruta_csv)

        logging_carga.info(
            f"Dataset recibido: {df.shape[0]} filas x {df.shape[1]} columnas"
        )

        conn = sqlite3.connect(ruta_bd)

        cursor = conn.cursor()

        crear_tabla(cursor)

        logging_carga.info("Tabla 'viajes' creada/verificada.")

        conn.execute("BEGIN")

        registros_insertados = 0

        for _, fila in df.iterrows():

            cursor.execute("""
            INSERT OR REPLACE INTO viajes
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (

                fila["viaje_id"],
                fila["fecha_hora_entrada"],
                fila["fecha_hora_salida"],
                fila["estacion_entrada"],
                fila["estacion_salida"],
                fila["linea"],
                fila["tipo_tarjeta"],
                fila["tarifa_pagada"],
                fila["duracion_minutos"],
                fila["numero_pasajeros"],
                fila["franja_horaria"],
                fila["dia_semana"],
                fila["evasion"]
            ))

            registros_insertados += 1

        conn.commit()

        logging_carga.info(
            f"COMMIT realizado correctamente. Registros cargados: {registros_insertados}"
        )

        total = cursor.execute(
            "SELECT COUNT(*) FROM viajes"
        ).fetchone()[0]

        logging_carga.info(
            f"Verificación SQL: {total} registros almacenados."
        )

        print(f"\nTotal registros en BD: {total}")

        print("\nCantidad de viajes por línea:\n")

        resultado = cursor.execute("""
            SELECT linea, COUNT(*)
            FROM viajes
            GROUP BY linea
            ORDER BY COUNT(*) DESC
        """)

        for fila in resultado:
            print(fila)

        logging_carga.info("Consulta GROUP BY ejecutada correctamente.")

        logging_carga.info(
            "FIN — Etapa 4: Carga a Base de Datos completada."
        )

    except Exception as e:

        if conn:
            conn.rollback()

        logging_carga.exception(
            f"Error durante la carga. ROLLBACK ejecutado: {e}"
        )

    finally:

        if conn:
            conn.close()

        logging_carga.info("Conexión cerrada.")


if __name__ == "__main__":
    cargar_datos_bd()