from validacion_estructural import validar_estructuralmente
from validacion_semantica import validar_semantica
from limpieza import limpiar_datos
from carga import cargar_datos_bd
from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
def main():

    ruta_archivo = "data/raw/viajes_transporte_raw.csv"

    print("=" * 60)
    print("INICIANDO PIPELINE ETL")
    print("=" * 60)

    
    print("\n[1/4] Validación estructural...")
    rutas_estructural = validar_estructuralmente(ruta_archivo)

    archivo_validado_estructural = rutas_estructural[0]

    print("\n[2/4] Validación semántica...")
    rutas_semantica = validar_semantica(archivo_validado_estructural)

    archivo_validado_semantica = rutas_semantica[0]

   
    print("\n[3/4] Limpieza y transformación...")
    df_limpio = limpiar_datos(archivo_validado_semantica)

    if df_limpio is None:
        print("Error durante la limpieza.")
        return


    print("\n[4/4] Carga a SQLite...")
    cargar_datos_bd()

    print("\n" + "=" * 60)
    print("PIPELINE FINALIZADO CORRECTAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()