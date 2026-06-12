from ingesta import leer_archivo
from limpieza import limpiar_datos
from validacion_estructural import validar_estructuralmente
from validacion_semantica import validar_semantica
from carga import cargar_datos_bd
from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))



def main():

    ruta_archivo = "data/raw/viajes_transporte_raw.csv"

    print("=" * 60)
    print("PIPELINE DE DATOS")
    print("=" * 60)

    print("\n[1] INGESTA")
    df = leer_archivo(ruta_archivo)

    if df is None:
        print("Error al leer el archivo.")
        return

    print(f"Registros leídos: {len(df)}")

    print("\n[2] LIMPIEZA Y TRANSFORMACIÓN")

    df_limpio = limpiar_datos(ruta_archivo)

    if df_limpio is None:
        print("Error durante la limpieza.")
        return

    archivo_limpio = "data/clean/datos_limpios.csv"


    print("\n[3] VALIDACIÓN ESTRUCTURAL")

    rutas_estructural = validar_estructuralmente(archivo_limpio)

    archivo_validado_estructural = rutas_estructural[0]

    print("\n[4] VALIDACIÓN SEMÁNTICA")

    rutas_semantica = validar_semantica(
        archivo_validado_estructural
    )

    print("\n[5] CARGA A BASE DE DATOS")

    cargar_datos_bd()

    print("\nPIPELINE FINALIZADO")


if __name__ == "__main__":
    main()