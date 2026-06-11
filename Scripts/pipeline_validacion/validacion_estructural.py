import sys
import pandas as pd
sys.path.append('C:/Users/JeanC/Parcial2_GDIA_Pipeline')

import Scripts.logging_utils.logging_utils as lgu




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
    columnas_obligatorias = ["columna"]
    posiciones_nulas = []
    for k in range(len(columnas_obligatorias)):
        posiciones_nulas.append(df[columnas_obligatorias[k]].isna())

    posiciones_nulas_serie = pd.Series(posiciones_nulas)

    resultado = comparar_series_booleanas(posiciones_nulas_serie)

    return df[resultado]

def fechas_en_formato_erroneo():
