# Módulo 2 — Oracle REIM Loader

Automatización de la carga de comprobantes de compra en **Oracle REIM**
(pantalla *Confrontación de facturas de venta*) a partir de un archivo CSV.

Desarrollado con **Python + Playwright**, reemplaza la carga manual —factura por
factura— por un proceso automático por lotes, con registro de resultados y
reanudación ante interrupciones.

---

## Tabla de contenidos

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Salidas](#salidas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Funcionamiento interno](#funcionamiento-interno)
- [Manejo de errores](#manejo-de-errores)
- [Notas técnicas](#notas-técnicas)
- [Tests](#tests)

---

## Descripción

Este proyecto es el **segundo módulo** de un flujo de dos etapas:

1. **Módulo 1 — Extractor:** extrae los datos de los comprobantes desde el
   portal del cliente y genera un CSV.
2. **Módulo 2 — Oracle REIM Loader (este repositorio):** lee ese CSV y carga
   cada comprobante en Oracle REIM de forma automática.

Por cada comprobante, el loader:

1. Busca el proveedor por Razón Social e ingresa el número de Orden de Compra (OC).
2. Completa la cabecera (fechas, CAE, importes, netos, tipo de documento, contenido).
3. Carga el desglose de impuestos (IVA, percepciones, impuesto interno).
4. Aprueba el comprobante.
5. Registra el resultado (procesado o fallido, con el motivo).

---

## Arquitectura

```
Portal del cliente ──> [Módulo 1] ──> comprobantes.csv ──> [Módulo 2] ──> 
──> Oracle REIM
    │
    ├─> procesados.csv
    ├─> fallidos.csv
    └─> ejecucion_*.log
```

---

## Requisitos

- **Python 3.11+**
- **Windows** (probado en Windows 11 / PowerShell)
- Acceso a Oracle REIM con credenciales válidas
- Navegador Chromium (lo instala Playwright)

### Dependencias

| Librería | Versión | Uso |
|----------|---------|-----|
| playwright | 1.48.0 | Automatización del navegador |
| python-dotenv | 1.0.1 | Carga de configuración desde `.env` |
| pytest | 8.3.3 | Tests unitarios |

---

## Instalación

```powershell
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar el navegador de Playwright
playwright install chromium
```

---

## Configuración

Crear un archivo `.env` en la raíz del proyecto (basado en `.env.example`):

```env
REIM_URL=https://<host>:<puerto>/ReimViewController/faces/Home
REIM_USER=usuario@dominio.com
REIM_PASSWORD=tu_password
TIMEOUT_DEFAULT=20000
TIMEOUT_CREAR_FACTURA=25000
TOLERANCIA_MAXIMA=100
```

> **Importante:**
> - El archivo `.env` no se versiona (está en `.gitignore`).
> - No definir `CSV_INPUT_PATH` en el `.env`: la ruta al CSV del Módulo 1 se
>   resuelve automáticamente en `config.py`.

### Ubicación del CSV de entrada

El loader espera el CSV generado por el Módulo 1 en:

```
<directorio_padre>/modulo1_extractor/output/comprobantes.csv
```

Para verificar que la ruta se resuelve correctamente:

```powershell
python -c "import config; print(config.CSV_INPUT_PATH)"
```

---

## Uso

```powershell
python main.py
```

El script:

1. Lee el CSV de comprobantes.
2. Saltea los que ya fueron procesados con éxito en corridas anteriores (reanudación).
3. Procesa cada comprobante pendiente en Oracle REIM.
4. Genera las salidas y muestra un resumen final con los IDs concatenados.

> El navegador se ejecuta en modo visible (`headless=False`) para poder supervisar el proceso.

### Reanudación

Si el proceso se interrumpe, basta con volver a ejecutar `python main.py`.
El loader detecta los comprobantes ya cargados (leyendo `procesados.csv`) y
continúa desde donde quedó, sin duplicar cargas.

---

## Salidas

Todas las salidas se generan en la carpeta `output/`:

| Archivo | Contenido |
|---------|-----------|
| `procesados.csv` | Comprobantes cargados y aprobados con éxito |
| `fallidos.csv` | Comprobantes que fallaron, con etapa y motivo del error |
| `ejecucion_<timestamp>.log` | Log técnico completo de cada corrida |

### Concatenación de IDs

Al finalizar, el resumen imprime los IDs procesados y fallidos concatenados con
el formato:

```
2100136|2100135|2100134|...
```

Este formato permite pegar los IDs directamente en el portal del cliente para filtrar y
confrontar los comprobantes correspondientes.

### Columnas de los CSV de salida

- **`procesados.csv`:** `timestamp`, `id_bpm`, `nombre_proveedor`, `nro_factura`, `nro_oc`, `nro_recepcion`, `subtotal`, `importe_total`, `estado`
- **`fallidos.csv`:** las mismas columnas + `etapa_fallo`, `motivo_error`

---

## Estructura del proyecto

```
modulo2_oracle_loader/
├── logger/
│   └── logger.py             # Salida centralizada: log + CSVs + IDs
├── mappings/
│   ├── contenido.py          # Mapeo tipo_contenido CSV -> REIM (ES/EN)
│   ├── impuestos.py          # Mapeo de impuestos CSV -> códigos REIM
│   └── tipo_documento.py     # Mapeo tipo de documento fiscal
├── models/
│   └── comprobante.py        # Dataclasses Comprobante y LineaImpuesto
├── reader/
│   └── csv_reader.py         # Lectura y parseo del CSV -> Comprobante
├── reim/
│   ├── session.py            # Login y navegación en REIM
│   ├── buscador.py           # Búsqueda de proveedor + OC
│   ├── crear_factura.py      # Carga del tab "Ingreso de Factura"
│   ├── desglose_impuestos.py # Carga del tab "Desglose de Impuesto"
│   ├── aprobar.py            # Aprobación y detección de resultados
│   └── popups.py             # Manejo de popups de error de REIM
├── validators/
│   └── rules.py              # Validaciones (reservado)
├── tests/
│   └── test_reader.py        # Tests unitarios del reader
├── output/                   # Salidas generadas (no versionadas)
├── config.py                 # Configuración y rutas
├── main.py                   # Orquestador principal
├── requirements.txt
├── .env.example
└── README.md
```

---

## Funcionamiento interno

### Flujo del orquestador (`main.py`)

1. Carga los comprobantes desde el CSV.
2. Inicia sesión en REIM (login + navegación a *Búsqueda de documento*).
3. Por cada comprobante pendiente:
   - Crea un nuevo documento.
   - Carga cabecera, desglose de impuestos y aprueba.
   - Registra el resultado.
   - Vuelve a *Búsqueda de documento* para el siguiente.
4. **Reinicio preventivo:** cada 10 documentos, reinicia el navegador
   (re-login) para evitar la degradación del DOM de REIM (ver [Notas técnicas](#notas-técnicas)).
5. Al finalizar, imprime el resumen con las concatenaciones de IDs.

### Mapeos

Los datos del CSV (portal) se traducen a los valores exactos que espera REIM:

- **Tipo de documento:** `001` → `001_FACTURAS_A`, `201` → `201_FACTURA_DE_CREDITO_ELECTRONICA_MIPYMES_(FCE)_A`
- **Contenido de factura:** `Liquido` → `Factura para liquidos`, etc. (con soporte ES/EN)
- **Impuestos:** cada columna `imp_*` del CSV se mapea a su código REIM y categoría (IVA / Percepción / Impuesto Interno)

---

## Manejo de errores

Cada comprobante que falla se registra en `fallidos.csv` con la etapa en la
que ocurrió el error, sin interrumpir el procesamiento de los demás:

| Etapa | Descripción |
|-------|-------------|
| `Reader` | Datos inválidos en el CSV (ej. impuesto no mapeado) |
| `sin_OC` | Comprobante sin número de Orden de Compra |
| `OC` | La OC no es válida o no coincide con el proveedor |
| `Proveedor` | Proveedor no encontrado por Razón Social |
| `Cabecera` | Error al completar el tab de ingreso |
| `Desglose` | Error al cargar impuestos |
| `IVA_mal_calculado` | REIM rechaza el importe de IVA (diferencia de centavos) |
| `montos_no_coinciden` | La suma de impuestos + netos no iguala el total |
| `Aprobacion` | No se confirmó la aprobación |
| `Desconocido` | Error inesperado |

> Los comprobantes fallidos se revisan y cargan manualmente. Suelen ser una
> minoría (proveedores sin OC, diferencias de IVA, etc.).

---

## Notas técnicas

Oracle REIM está construido sobre Oracle ADF, lo que impone técnicas
específicas de automatización descubiertas durante el desarrollo:

- **Campos de OC:** se completan disparando eventos `input`/`change` vía
  JavaScript; `fill()` de Playwright no compromete el valor en ADF.
- **Combos (selects):** no se pueden operar con `select_option()`; se completan
  escribiendo el texto (que filtra las opciones) seguido de Enter + Tab.
- **Montos de la grilla:** se escriben con `fill()` + Tab (gesto humano);
  la técnica de eventos JS provoca que ADF los reinicialice a 0.
- **Índices dinámicos:** los atributos `name` de los campos incluyen índices
  (`tabrgN`) que incrementan con cada documento creado. Los selectores usan
  sufijos + filtro de visibilidad (`:visible`) en lugar de índices fijos.
- **Degradación del DOM:** REIM acumula los documentos creados en el DOM sin
  limpiarlos, lo que degrada los selectores tras ~13 documentos. Se resuelve con
  un **reinicio automático del navegador cada 10 documentos** (constante
  `REINICIAR_CADA` en `main.py`), que limpia el estado sin intervención manual.
- **Popup de error intermitente:** REIM muestra ocasionalmente un popup
  *"Se ha producido un error en la aplicación"* (bug del servidor). Se detecta y
  cierra automáticamente sin afectar la carga.
- **Idioma variable:** el combo *Contenido de la factura* aparece a veces en
  español y a veces en inglés. El loader detecta las opciones disponibles y
  selecciona el texto correcto en cualquiera de los dos idiomas.

---

## Tests

Los tests unitarios cubren el parseo del CSV y los mapeos (no requieren conexión
a REIM):

```powershell
pytest
```
