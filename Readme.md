# Pipeline de Datos — Transporte Urbano (Metro de Santiago)

**Asignatura:** Gestión de Datos para IA  
**Institución:** DuocUC — Escuela de Informática y Telecomunicaciones  
**Evaluación:** Grupal — Unidad 2  
**Entrega:** Viernes 12 de junio de 2026  
**Integrantes:** Arturo Arellano · Javiela Maita · Jean Cament

---

## 1. Dominio elegido

**Transporte Urbano — Viajes en Metro de Santiago**

El dataset simula registros del sistema de transporte público de Santiago. Contiene información de viajes individuales: estaciones de entrada y salida, línea utilizada, tipo de tarjeta BIP!, tarifa pagada, duración del viaje y número de pasajeros.

### Preguntas que busca responder el pipeline

1. ¿Cuántos viajes se realizan por línea ?
2. ¿En qué franja horaria se evade más la tarifa?
3. ¿Cuanto se recauda por tipo de tarjeta?
4. ¿Cuáles son las estaciones mas concurridas?

---

## 2. Estructura del proyecto

```
Parcial2_GDIA_Pipeline/
├── Scripts/
│   ├── logging_utils.py              # Configuración centralizada de loggers
│   ├── ingesta.py                    # Etapa 1: Lectura del archivo raw
│   ├── limpieza.py                   # Etapa 2: Limpieza y transformaciones
│   ├── validacion_estructural.py     # Etapa 3a: Validación de tipos y formatos
│   ├── validacion_semantica.py       # Etapa 3b: Validación de reglas de negocio
│   ├── carga.py                      # Etapa 4: Carga a SQLite
│   └── main.py                       # Orquestador del pipeline completo
├── data/
│   ├── raw/                          # Dataset original sin modificar
│   ├── clean/                        # Dataset limpio y transformado
│   ├── validated/                    # Registros que pasaron validación
│   └── errors/                       # Registros rechazados con motivo
├── database/
│   └── transporte.db                 # Base de datos SQLite
└── logs/
    ├── logs de Main.log
    ├── logs de Ingesta.log
    ├── logs de Limpieza.log
    ├── logs de Validacion_Estructural.log
    ├── logs de Validacion_Semantica.log
    └── logs de Carga.log
```

---

## 3. Requisitos

```bash
pip install pandas numpy pandera pathlib requests
```

Python entre 3.10 y 3.14.

---

## 4. Cómo ejecutar el pipeline

### Ejecución completa (recomendado)

Desde la carpeta `PARCIAL2_GDIA_PIPELINE`:

```bash
python Scripts/main.py
```

Esto ejecuta las 4 etapas en orden: ingesta &rarr; limpieza &rarr; validación estructural &rarr; validación semántica &rarr; carga a BD.

### Ejecución por etapas

```bash
python limpieza.py                  # Genera data/clean/datos_limpios.csv
python validacion_estructural.py    # Genera data/validated/ y data/errors/
python validacion_semantica.py      # Filtra errores semánticos
python carga.py                     # Carga en SQLite y ejecuta queries
```

### Requisito previo

El archivo raw debe estar en:
```
data/raw/viajes_transporte_raw.csv
```

---

## 5. Descripción del dataset

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `viaje_id` | int | Identificador único del viaje |
| `fecha_hora_entrada` | datetime | Timestamp de validación de entrada |
| `fecha_hora_salida` | datetime | Timestamp de salida de estación |
| `estacion_entrada` | str | Estación de origen |
| `estacion_salida` | str | Estación de destino |
| `linea` | str | Línea de metro (L1, L2, L4, L4A, L5, L6) |
| `tipo_tarjeta` | str | Tipo de tarjeta BIP! o Efectivo |
| `tarifa_pagada` | float | Monto pagado en CLP |
| `duracion_minutos` | int | Duración del viaje en minutos |
| `numero_pasajeros` | int | Pasajeros por registro |
| `franja_horaria` | str | Segmento horario (columna derivada) |
| `dia_semana` | str | Día de la semana (columna derivada) |
| `evasion` | int | 1 = evasión de tarifa detectada (columna derivada) |

---

## 6. Decisiones técnicas

### Etapa 1 — Ingesta (`ingesta.py`)

- La función `leer_archivo()` soporta tres extensiones: `.csv`, `.xlsx`/`.xls` y `.txt`, usando `pd.read_csv`, `pd.read_excel` y `pd.read_table` respectivamente.
- Si la ruta no existe o la lectura falla, se registra el error en el log y se retorna `None` para detener el pipeline de forma controlada.
- El archivo se guarda sin ninguna modificación en `data/raw/` para preservar el dato original.
- Se creo un logger por componente, para facilitar la trazabilidad.
- Los tipos de validación se separaron en etapas diferentes.
- Se creo un entorno virtual con venv para evitar el conflicto de versiones.


### Etapa 2 — Limpieza (`limpieza.py`)

| Problema | Decisión | Justificación |
|----------|----------|---------------|
| Filas duplicadas | Eliminación completa | No hay forma de saber cuál copia es la correcta |
| Fechas con formato inválido | Eliminación de la fila | Son irrecuperables sin el dato original |
| Tarifas negativas | Conversión a NaN e imputación con mediana | La mediana no distorsiona la distribución como lo haría la media |
| `numero_pasajeros` = 0 | Eliminación | Un viaje sin pasajeros no tiene sentido de negocio |
| Categorías inconsistentes en `tipo_tarjeta` | Diccionario de mapeo (`TIPO_MAPPING`) | Normaliza variantes como "bip", "BIP", "bip!" al catálogo oficial |
| Nulos en columnas críticas | Eliminación | Columnas como `linea` o `estacion_entrada` no tienen imputación razonable |

**Transformaciones aplicadas:**

- **T1 `franja_horaria`** — Segmenta el día en 6 franjas según la hora de entrada (Mañana_punta, Mañana_baja, Mediodía, Tarde_baja, Tarde_punta, Nocturno). Permite analizar patrones de demanda.
- **T2 `dia_semana`** — Nombre del día derivado de `fecha_hora_entrada`. Diferencia días hábiles de fin de semana.
- **T3 `evasion`** — Flag binario (0/1): vale 1 cuando `tarifa_pagada == 0`. Permite cuantificar evasión directamente en SQL.

### Etapa 3 — Validación (`validacion_estructural.py` y `validacion_semantica.py`)

La validación se dividió en dos scripts con responsabilidades separadas:

**Estructural** — verifica que los datos tengan el formato correcto:
- Columnas numéricas (`tarifa_pagada`, `duracion_minutos`, `numero_pasajeros`) contienen valores numéricos.
- No existen nulos en columnas obligatorias.
- Las fechas tienen el formato `%Y-%m-%d %H:%M:%S`.

**Semántica** — verifica que los datos tengan sentido de negocio:
- Si existe `fecha_hora_salida`, debe existir `fecha_hora_entrada`.
- La columna `linea` solo acepta valores del catálogo oficial (L1, L2, L3, L4, L4A, L5, L6).

Los registros inválidos se exportan a `data/errors/` con sufijo `_errors_structural` o `_errores_semantica`. Los válidos pasan a la siguiente etapa.

### Etapa 4 — Carga (`carga.py`)

- Se eligió **SQLite** por su simplicidad de despliegue (no requiere servidor), compatibilidad nativa con Python y suficiencia para el volumen del dataset.
- Se usa `INSERT OR REPLACE` para que el pipeline sea idempotente: ejecutarlo más de una vez no genera duplicados en la BD.
- La carga está envuelta en un bloque `try/except` con `conn.rollback()` en caso de error, garantizando que la base de datos nunca quede en estado inconsistente.
- Se ejecutan 2 queries de verificación post-carga: conteo total y agrupación por línea.

### Trazabilidad — `logging_utils.py`

Cada componente tiene su propio logger con nombre, lo que permite que cada etapa escriba en su propio archivo `.log` de forma independiente. Esto resuelve la limitación de `logging.basicConfig()`, que en Python solo se inicializa una vez por proceso y hace que los módulos posteriores no puedan escribir en sus propios archivos si uno anterior ya configuró el logger raíz.




