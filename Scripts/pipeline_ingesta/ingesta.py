import pandas as pd
from pathlib import Path
import sys
import requests

sys.path.append('C:/Users/JeanC/Parcial2_GDIA_Pipeline')
import Scripts.logging_utils.logging_utils as lgu
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
        lgu.logging_ingesta.info("[Finalizado] datos encontrados en {direccion_archivo} transformados en DataFrame")

    return datos

        
##funcion que obtiene el dataset, lo guarda en bruto y devuelve la ruta del archivo 
def guardar_archivo_bruto_url(url : str = "https://usc-excel.officeapps.live.com/x/_layouts/XlFileHandler.aspx?sheetName=in&downloadAsCsvEnabled=1&WacUserType=WOPI&usid=30e61928-581b-0527-9d70-a6c639959b9a&NoAuth=1&waccluster=PUS8") -> str:
    

    os.makedirs("data/raw", exist_ok=True)

    response = requests.get(url)

    print(response)

    with open("data/raw/viajes_transporte_raw.csv", "w", encoding="utf-8") as f:
        f.write(response.text)       

    lgu.logging_ingesta.info("archivo viajes_transporte_raw.csv cargado en bruto en data/raw")



    



