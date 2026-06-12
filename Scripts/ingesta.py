import pandas as pd
from pathlib import Path
import sys
from pathlib import Path
import sys
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
import logging_utils.logging_utils as lgu
import os 


extensiones_excel = [".xls", ".xlsx"]
extensiones_csv = [".csv"]
extensiones_simples = [".txt"]




def leer_datos(path, extension, sheet_excel):
    if extension in extensiones_excel:
        try:
           return  pd.read_excel(path, sheet_name= sheet_excel)
        except Exception as e:
           lgu.logging_ingesta.exception(f"Error de lectura: {e}")
    elif extension in extensiones_csv:
        try:
            return pd.read_csv(path)
        except Exception as e:
            lgu.logging_ingesta.exception(f"Error de lectura: {e}")
    elif extension in extensiones_simples:
        try:
           return pd.read_table(path)
        except Exception as e:
            lgu.logging_ingesta.exception(f"Error de lectura: {e}")
    
    else:
        lgu.logging_ingesta.error(f'el archivo con la extensión "{extension}" '+
                                       'no esta soportada por ahora en el pipeline.')
        
    



#Funcion principal para la lectura de datos, sheet_excel se debe especificar si se trabaja con excel y 
#y se requiere extraer la infromación de una hoja que no es la primera.
#si devuelve none, quiere decir que fallo la lectura.
def leer_archivo(direccion_archivo : str, sheet_excel = 0 ) -> pd.DataFrame:
    f_path = Path(direccion_archivo)
    lgu.logging_ingesta.info("iniciando lectura de datos.")
    if(f_path.exists()):
        extension = f_path.suffix

        datos = leer_datos(direccion_archivo, extension, sheet_excel)
    else:
        print("no existe el archivo")
        lgu.logging_ingesta.warning(f"Se ingreso la ruta de un archivo inexistente: {direccion_archivo}")

    if(datos is not None):
        lgu.logging_ingesta.info("[Finalizado] datos transformados en DataFrame")

    return datos

        

def guardar_archivo_bruto_url(url : str = "https://drive.usercontent.google.com/download?id=1qI7EOHSY-xMH5-05fRIPalH2grxDaYt9&export=download&authuser=0&confirm=t&uuid=2b0118bb-e452-4542-9160-786a02e477c4&at=AAINaIKZ0_qxa-SvTcmRwbhbvWon:1781288030280") -> str:
    

    os.makedirs("data/raw", exist_ok=True)

    response = requests.get(url)

    print(response)

    with open("data/raw/viajes_transporte_raw.csv", "wb") as f:
        f.write(response.content)       

    lgu.logging_ingesta.info("archivo viajes_transporte_raw.csv cargado en bruto en data/raw")

    return "data/raw/viajes_transporte_raw.csv"
