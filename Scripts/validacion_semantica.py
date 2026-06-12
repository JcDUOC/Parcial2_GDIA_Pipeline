import pandas as pd
import os 
from pathlib import Path
import sys
from pathlib import Path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
import ingesta as ingesta
import logging_utils.logging_utils as lgu


BASE_DIR = Path(__file__).resolve().parent.parent

errors_dir = BASE_DIR / "data" / "errors"
validated_dir = BASE_DIR / "data" / "validated"

errors_dir.mkdir(parents=True, exist_ok=True)
validated_dir.mkdir(parents=True, exist_ok=True)



def hora_salida_presente_hora_entrada_no(df : pd.DataFrame):
    columna_momento_salida = "fecha_hora_salida"

    columna_momento_entrada = "fecha_hora_entrada"

    return df[
        (df[columna_momento_salida].notna() & df[columna_momento_entrada].isna())
    ]


def lineas_no_correctas(df: pd.DataFrame):
    lineas_en_chile = ["L1", "L2", "L3", "L4", "L4A", "L4a", "L5", "L6"]

    columna_linea = ["linea"]
    return df[~(
                df[columna_linea].isin(lineas_en_chile)
            )]


def exportar_archivos(df_errores, df_validos, archivo_path_origen)  -> list[str, str]:
    os.makedirs("../../data/validated", exist_ok=True)
    os.makedirs("../../data/errors", exist_ok=True)
    nombre_archivo_origen = Path(archivo_path_origen).stem
    
    
    ruta_errors = errors_dir / f"{nombre_archivo_origen}_errors_structural.csv"
    ruta_validos = validated_dir / f"{nombre_archivo_origen}_validated_structural.csv"
    
    
    
    #ruta_errors = "../../data/errors/" + nombre_archivo_origen + "_errores_semantica" + ".csv"
    #ruta_validos = "../../data/validated/" + nombre_archivo_origen + "_validated_semantica"+".csv"
    
    df_errores.to_csv(ruta_errors)
    lgu.logging_validacion_semantica.info(f"errores semanticos encontrados en el archivo {nombre_archivo_origen} exportados al archivo {nombre_archivo_origen +"_errores_semantica" + ".csv"}")


    df_validos.to_csv(ruta_validos)
    lgu.logging_validacion_semantica.info(f"datos validados semanticamente del archivo {nombre_archivo_origen} exportados al archivo {nombre_archivo_origen +"_validated_semantica" + ".csv"}")
    return [ruta_validos, ruta_validos]




#funcion del componente          

def validar_semantica(ruta : str) -> list[str, str]:
    df = ingesta.leer_archivo(ruta)

    nombre_archivo_origen = Path(ruta).stem
    
    errores_1 = hora_salida_presente_hora_entrada_no(df)

    errores_2 = lineas_no_correctas(df)
    
    

    df_errores_extraidos = pd.concat([errores_1, errores_2]).drop_duplicates(["viaje_id"], keep="first")
    indices_errores = df_errores_extraidos.index
    
    df_datos_validos = df.drop(indices_errores, errors = "ignore")

    lgu.logging_validacion_estructural.info("errores semanticos del archivo {nombre_archivo_origen} extraidos")

    return exportar_archivos(df_errores_extraidos, df_datos_validos, ruta)

