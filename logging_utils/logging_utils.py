import logging as lg
import os 

from pathlib import Path
import sys

#esto permite crear un logger para registro de acciones en un archivo externo. Esto para cumplir con el principio 
#de trazabilidad
def configurar_logger(componente: str):
    logger = lg.getLogger(f"Logger de {componente}")
    logger.setLevel(lg.INFO)
    logger.propagate = False

    formato = lg.Formatter("| %(asctime)s --- %(levelname)s --- %(message)s |")
    conshandler = lg.StreamHandler()

    conshandler.setFormatter(formato)

    os.makedirs("logs"  , exist_ok=True)

    handler_archivo = lg.FileHandler(f"logs/logs de {componente}.log", encoding = "UTF-8", errors = "ignore", delay=True)
    handler_archivo.setFormatter(formato)
    logger.addHandler(handler_archivo)

    return logger


### asi se crea el logger, debes pasarle el nombre del componente que lo usa. para hacer uso, 
# se puede hacer con los metodos .info, .error, .warning, .exception, .critical, a los cuales se les debe pasar el mensaje en string.
logging_ingesta = configurar_logger("Ingesta")
logging_validacion_estructural = configurar_logger("Validacion_Estructural")
logging_validacion_semantica   = configurar_logger("Validacion_Semantica")












