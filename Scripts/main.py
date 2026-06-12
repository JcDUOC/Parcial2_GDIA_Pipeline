import sys
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))



import logging_utils.logging_utils as lgu
import limpieza as lim
import validacion_estructural as val_est
import validacion_semantica as val_sem
import carga

logging_main = lgu.configurar_logger("Main")

RUTA_RAW     = "data/raw/viajes_transporte_raw.csv"
RUTA_CLEAN   = "data/clean/datos_limpios.csv"


def ejecutar_pipeline():

    logging_main.info("=" * 60)
    logging_main.info("INICIO — Pipeline de Datos: Transporte Urbano")
    logging_main.info("=" * 60)

    logging_main.info("Iniciando Etapa 2: Limpieza y Transformación.")

    df_limpio = lim.limpiar_datos(RUTA_RAW)

    if df_limpio is None:
        logging_main.error("Etapa 2 falló. Pipeline detenido.")
        return

    logging_main.info(f"Etapa 2 completada. {df_limpio.shape[0]} filas limpias.")

    
    logging_main.info("Iniciando Etapa 3a: Validación Estructural.")

    rutas_estructural = val_est.validar_estructuralmente(RUTA_CLEAN)

    if rutas_estructural is None:
        logging_main.error("Etapa 3a falló. Pipeline detenido.")
        return

    ruta_validos_estructural = rutas_estructural[0]

    logging_main.info(f"Etapa 3a completada. Válidos en: {ruta_validos_estructural}")

    
    logging_main.info("Iniciando Etapa 3b: Validación Semántica.")

    rutas_semantica = val_sem.validar_semantica(ruta_validos_estructural)

    if rutas_semantica is None:
        logging_main.error("Etapa 3b falló. Pipeline detenido.")
        return

    logging_main.info(f"Etapa 3b completada. Válidos en: {rutas_semantica[0]}")


    logging_main.info("Iniciando Etapa 4: Carga a Base de Datos.")

    carga.cargar_datos_bd()

    logging_main.info("Etapa 4 completada.")

    logging_main.info("=" * 60)
    logging_main.info("FIN — Pipeline completado exitosamente.")
    logging_main.info("=" * 60)


if __name__ == "__main__":
    ejecutar_pipeline()