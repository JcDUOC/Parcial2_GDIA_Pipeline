import sys
import pandas as pd
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import logging_utils.logging_utils as lgu
import ingesta as ingesta
import os

from pathlib import Path


#BASE_DIR = Path(__file__).resolve().parent.parent

#errors_dir = BASE_DIR / "data" / "errors"
#validated_dir = BASE_DIR / "data" / "validated"

#errors_dir.mkdir(parents=True, exist_ok=True)
#validated_dir.mkdir(parents=True, exist_ok=True)



def comparar_series_booleanas(lista: pd.Series) -> pd.Series:
    resultado = lista.iloc[0]

    for k in range(1, len(lista)):
        resultado = resultado | lista.iloc[k]
    
    return resultado


def datos_no_numerico(df: pd.DataFrame): 
    return df[
        ~(
            (df["tarifa_pagada"].apply(lambda x: pd.api.types.is_number(x))) &
            (df["duracion_minutos"].apply(lambda x: pd.api.types.is_number(x))) &
            (df["numero_pasajeros"].apply(lambda x: pd.api.types.is_integer(x)))
        )
    ]





def nulos_en_datos_obligatorios(df: pd.DataFrame) -> pd.DataFrame:
    columnas_obligatorias = ["viaje_id", "fecha_hora_entrada", "fecha_hora_salida",
                         "estacion_entrada", "estacion_salida", "linea",
                         "tipo_tarjeta", "tarifa_pagada", "duracion_minutos",
                         "numero_pasajeros"]
    posiciones_nulas = []
    for k in range(len(columnas_obligatorias)):
        posiciones_nulas.append(df[columnas_obligatorias[k]].isna())

    posiciones_nulas_serie = pd.Series(posiciones_nulas)

    resultado = comparar_series_booleanas(posiciones_nulas_serie)

    return df[resultado]



def fechas_en_formato_erroneo(df : pd.DataFrame) -> pd.DataFrame:
    columnas_con_fecha = ["fecha_hora_entrada", "fecha_hora_salida"]

    df_edit = df[columnas_con_fecha]

    formato="%Y-%m-%d %H:%M:%S"

    for s in columnas_con_fecha:
        df_edit[s] = pd.to_datetime(df_edit[s], format=formato, errors="coerce")

    serie_bool = df_edit.isna().any(axis=1)

    return df[serie_bool]


def exportar_archivos(df_errores, df_validos, archivo_path_origen):
    os.makedirs("data/validated", exist_ok=True)
    os.makedirs(".data/errors", exist_ok=True)
    nombre_archivo_origen = Path(archivo_path_origen).stem

    ruta_errors = "data/errors/" + nombre_archivo_origen + "_errors_structural" + ".csv"
    ruta_validos = "data/validated/" + nombre_archivo_origen + "_validated_structural"+".csv"
    
    #ruta_errors = errors_dir / f"{nombre_archivo_origen}_errors_structural.csv"
    #ruta_validos = validated_dir / f"{nombre_archivo_origen}_validated_structural.csv"
    
    df_errores.to_csv(ruta_errors)
    lgu.logging_validacion_estructural.info(f"errores estructurales encontrados en el archivo {nombre_archivo_origen} exportados al archivo {nombre_archivo_origen+"_errors_structural" + ".csv"}")
    df_validos.to_csv(ruta_validos)

    lgu.logging_validacion_estructural.info(f"datos validados estructuralmente en el archivo {nombre_archivo_origen} exportados al archivo {nombre_archivo_origen+"_validated_structural"+".csv"}")

    return [ruta_validos, ruta_validos]





## funcion principal del componente 
def validar_estructuralmente(archivo_path: str) -> list[str, str]:
    df = ingesta.leer_archivo(archivo_path)
    nombre_archivo_origen = Path(archivo_path).stem
    error1 = datos_no_numerico(df)

    error2 = nulos_en_datos_obligatorios(df)

    error3 = fechas_en_formato_erroneo(df)

    df_errores_extraidos = pd.concat([error1, error2, error3]).drop_duplicates(["viaje_id"], keep="first")
    indices_errores = df_errores_extraidos.index

    df_datos_validos = df.drop(indices_errores, errors = "ignore")

    lgu.logging_validacion_estructural.info(f"errores semanticos del archivo {nombre_archivo_origen} extraidos")



    return exportar_archivos(df_errores_extraidos, df_datos_validos, archivo_path)




