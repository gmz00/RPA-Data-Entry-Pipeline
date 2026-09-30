# Extractor  - Módulo 1: Comprobantes a CSV

Automatización para la extracción de datos de comprobantes desde el portal del cliente y generación de un CSV estructurado, como paso previo a la carga en Oracle REIM (Módulo 2).

**Proyecto:** IBMer watsonx Challenge 2026    
**Autor:** Lautaro Gomez (Estudiante Ing. en Sistemas )

---

## Descripción

Script de web scraping con Playwright que automatiza la extracción de datos desde el portal del cliente.

**Funcionalidades principales:**

- Login automático al portal
- Extracción de datos de comprobantes por ID
- Procesamiento de 3 pestañas: CABECERA, IMPORTES, RECEPCIONES
- Mapeo de 39 tipos de impuestos a columnas individuales
- Generación de CSV con 54 columnas
- Escritura incremental (permite reintentos sin perder datos)

**Estado actual:** MVP funcional — Listo para uso en producción

---

## Contexto del Flujo de Trabajo

Este módulo es el primero de dos en el pipeline de automatización:

```
Portal del cliente
    |
    v
[Módulo 1 - Este script]
Extracción de comprobantes --> output/comprobantes.csv
    |
    v
[Módulo 2 - En desarrollo]
Carga en Oracle REIM (entry data automatizado)
    |
    v
Confrontación manual de documentos (tarea residual)
```

El objetivo final es eliminar la carga manual de datos en Oracle REIM, dejando como única tarea manual la confrontación de documentos.

---

## Características Técnicas

### Datos extraídos (54 columnas)

**CABECERA (8 columnas)**

| Columna | Descripción |
|---|---|
| `id` | ID del comprobante en el portal del cliente |
| `emisor` | Nombre del proveedor |
| `tipo` | Tipo de comprobante (001, 201, etc.) |
| `nro_comprobante` | Número de comprobante (formato: XXXXX-XXXXXXXX) |
| `fecha_emision` | Fecha de emisión (formato: DD-MM-YYYY) |
| `cae` | Código de Autorización Electrónica |
| `vencimiento_cae` | Fecha de vencimiento del CAE |
| `tipo_contenido` | Clasificación del contenido (Liquido / Envase / Otros/Mercadería) |

**IMPORTES (3 columnas)**

| Columna | Descripción |
|---|---|
| `neto_gravado` | Monto neto gravado |
| `no_gravado` | Monto no gravado |
| `importe_total` | Importe total del comprobante |

**IMPUESTOS (39 columnas)**

*IVA (2)*

| Columna | Descripción |
|---|---|
| `imp_IVA_21` | IVA 21% |
| `imp_IVA_10_5` | IVA 10.5% |

*Percepciones IIBB — Ingresos Brutos (25)*

| Columna | Columna | Columna |
|---|---|---|
| `imp_PERC_IIBB_CABA` | `imp_PERC_IIBB_BA` | `imp_PERC_IIBB_CATAMARCA` |
| `imp_PERC_IIBB_CHACO` | `imp_PERC_IIBB_CHUBUT` | `imp_PERC_IIBB_CORDOBA` |
| `imp_PERC_IIBB_CORRIENTES` | `imp_PERC_IIBB_ENTRE_RIOS` | `imp_PERC_IIBB_FORMOSA` |
| `imp_PERC_IIBB_JUJUY` | `imp_PERC_IIBB_LA_PAMPA` | `imp_PERC_IIBB_LA_RIOJA` |
| `imp_PERC_IIBB_MENDOZA` | `imp_PERC_IIBB_MISIONES` | `imp_PERC_IIBB_NEUQUEN` |
| `imp_PERC_IIBB_RIO_NEGRO` | `imp_PERC_IIBB_SALTA` | `imp_PERC_IIBB_SAN_JUAN` |
| `imp_PERC_IIBB_SAN_LUIS` | `imp_PERC_IIBB_SANTA_CRUZ` | `imp_PERC_IIBB_SANTA_FE` |
| `imp_PERC_IIBB_SGO_ESTERO` | `imp_PERC_IIBB_TDF` | `imp_PERC_IIBB_TUCUMAN` |
| `imp_PERC_IVA_RG5329` | | |

*Tasas de Seguridad e Higiene — TSH (10)*

| Columna | Columna |
|---|---|
| `imp_TSH_SALTA` | `imp_TSH_TUCUMAN_TEM` |
| `imp_TSH_TUCUMAN_TPP` | `imp_TSH_CORRIENTES` |
| `imp_TSH_COMODORO` | `imp_TSH_CATAMARCA` |
| `imp_TSH_CORDOBA` | `imp_TSH_LA_PLATA` |
| `imp_TSH_POSADAS` | `imp_TSH_GENERICA` |

*Otros impuestos (2)*

| Columna | Descripción |
|---|---|
| `imp_INTERNO_LOCAL` | Impuesto Interno Local |
| `imp_OTROS` | Acumulador de impuestos sin mapeo definido |

**RECEPCIONES (2 columnas)**

| Columna | Descripción |
|---|---|
| `nro_recepcion` | Número de recepción |
| `nro_oc` | Número de orden de compra |

**CONTROL (2 columnas)**

| Columna | Descripción |
|---|---|
| `estado_extraccion` | Resultado de la extracción: OK, ERROR_CABECERA, ERROR_IMPORTES, ERROR_RECEPCIONES, ERROR_GENERAL |
| `motivo_error` | Descripción del error (solo se completa si hay error) |

---

### Funcionalidades implementadas

**Extracción robusta:**

- Manejo de campos autocomplete (Emisor, Tipo)
- Detección de valores ocultos en DOM (CAE, recepciones)
- Extracción de tabla de impuestos dinámica
- Retry automático para campos de carga lenta

**Lógica de negocio:**

- Mapeo automático de tipo de contenido por proveedor (6 proveedores de líquido predefinidos)
- Prioridad al valor del dropdown si existe; fallback a mapeo por emisor si no hay dropdown

**Control de proceso:**

- Logging detallado con niveles DEBUG / INFO / WARNING / ERROR
- Filtrado de IDs ya procesados (evita duplicados al reiniciar)
- Manejo de interrupciones con Ctrl+C
- Validación de estructura del CSV antes de cada escritura
- Escritura incremental: cada fila se guarda inmediatamente, sin perder datos ante interrupciones

---

## Requisitos del Sistema

### Software necesario

- Python 3.11 o superior
- Chromium (se instala automáticamente con Playwright)

### Dependencias Python

```
playwright==1.48.0
pandas==2.2.3
python-dotenv==1.0.1
```

---

## Instalación

### Paso 1: Crear entorno virtual

Abrir una terminal en la carpeta del proyecto y ejecutar:

```bash
python -m venv venv
```

### Paso 2: Activar el entorno virtual

**Windows (PowerShell):**

```powershell
venv\Scripts\activate
```

**Windows (CMD):**

```cmd
venv\Scripts\activate.bat
```

**Linux / Mac:**

```bash
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Instalar el navegador Chromium

```bash
playwright install chromium
```

### Paso 5: Configurar credenciales

Crear un archivo `.env` en la raíz del proyecto copiando el template:

```bash
copy .env.example .env
```

Luego editar `.env` con los datos reales:

```env
CLIENT_NAME_USER=tu_email@CLIENT_NAMEargentina.com
CLIENT_NAME_PASS=tu_password
HEADLESS=False
TIMEOUT=30000
```

> **IMPORTANTE:** El archivo `.env` contiene credenciales sensibles. Nunca compartirlo ni subirlo a un repositorio. Ya está incluido en `.gitignore`.

---

## Uso

### Paso 1: Preparar los IDs

Editar el archivo `ids.txt` con los IDs de los comprobantes a procesar, uno por línea:

```
2089578
2089409
2092130
# Este es un comentario, se ignora
```

Las líneas que comienzan con `#` se ignoran.

### Paso 2: Ejecutar

```bash
python main.py
```

### Resultados

- **CSV generado:** `output/comprobantes.csv`
- **Log de ejecución:** `logs/extractor.log`

### Ejemplo de salida en consola

```
======================================================================
  EXTRACTOR CLIENT_NAME - Modulo 1: Comprobantes a CSV
======================================================================

======================================================================
  [1/3] Procesando ID: 2089578
======================================================================
[OK] [1/3] OK: 2089578

======================================================================
  [2/3] Procesando ID: 2089409
======================================================================
[OK] [2/3] OK: 2089409

======================================================================
  [3/3] Procesando ID: 2092130
======================================================================
[OK] [3/3] OK: 2092130

======================================================================
  RESUMEN FINAL
======================================================================
  Total procesados: 3
  [OK]  Exitosos:      3
  [!!]  Con errores:   0
  [>>]  Tasa exito:    100.0%

  [>>]  CSV generado: output/comprobantes.csv

  [>>]  Estadisticas CSV:
     Total filas:        3
     OK:                 3
     Error CABECERA:     0
     Error IMPORTES:     0
     Error RECEPCIONES:  0
======================================================================
```

---

## Estructura del Proyecto

```
modulo1_extractor/
│
├── config/
│   ├── settings.py          # Configuracion global (URLs, timeouts, estructura CSV)
│   ├── selectors.py         # Selectores CSS/XPath y mapeo de impuestos a columnas
│   └── __init__.py
│
├── src/
│   ├── scraper.py           # Manejo de Playwright (navegacion, login, clics)
│   ├── extractor.py         # Logica de extraccion de datos del DOM
│   ├── parser.py            # Transformacion de datos crudos a formato CSV
│   ├── csv_handler.py       # Escritura incremental del CSV con pandas
│   └── __init__.py
│
├── tests/
│   └── test_parser.py       # Pruebas unitarias del parser
│
├── logs/
│   └── extractor.log        # Log de ejecucion (se genera automaticamente)
│
├── output/
│   └── comprobantes.csv     # CSV generado (se crea automaticamente)
│
├── .env                     # Credenciales (NO SUBIR A GIT)
├── .env.example             # Template de configuracion
├── ids.txt                  # Lista de IDs a procesar
├── ids.example.txt          # Ejemplo de formato del archivo de IDs
├── main.py                  # Punto de entrada principal
├── requirements.txt         # Dependencias Python
├── .gitignore               # Archivos excluidos de Git
└── README.md                # Esta documentacion
```

---

## Configuracion Avanzada

### Variables de entorno disponibles

Editar `.env` para modificar el comportamiento:

```env
# Credenciales del portal CLIENT_NAME
CLIENT_NAME_USER=usuario@CLIENT_NAMEargentina.com
CLIENT_NAME_PASS=contraseña

# Modo de ejecucion
HEADLESS=False        # True = sin ventana visible | False = ver el navegador en pantalla

# Timeouts
TIMEOUT=30000         # Timeout en milisegundos (30 segundos por defecto)
MAX_RETRIES=3         # Numero de reintentos (reservado para version futura)

# Nivel de logging
LOG_LEVEL=INFO        # Opciones: DEBUG, INFO, WARNING, ERROR
```

---

## Personalizacion

### Modificar proveedores de liquido

Si necesitas agregar o quitar proveedores que se clasifican automaticamente como `Liquido`, editar la lista en `src/extractor.py`:

```python
proveedores_liquido = [
    "VENDOR LIQUIDOS A",
    "VENDOR LIQUIDOS B",
    "VENDOR LIQUIDOS C",
    "VENDOR LIQUIDOS D",
    "VENDOR LIQUIDOS F",
    "VENDOR LIQUIDOS G",
    "VENDOR LIQUIDOS H",
    # Agregar mas proveedores aca si es necesario
]
```

### Agregar un nuevo impuesto al mapeo

Si aparece un impuesto nuevo en el portal y cae en la columna `imp_OTROS`, seguir estos pasos:

**Paso 1 — Identificar la descripcion exacta en el log:**

```
[WARN] Impuesto no mapeado: 'NUEVA DESCRIPCION' ($1000.00) -> imp_OTROS
```

**Paso 2 — Agregar la entrada al diccionario en `config/selectors.py`:**

```python
IMPUESTO_MAP = {
    # ... entradas existentes ...
    "NUEVA DESCRIPCION": "imp_NUEVO_IMPUESTO",
}
```

**Paso 3 — Agregar la columna en `config/settings.py`:**

```python
CSV_COLUMNS = [
    # ... columnas existentes ...
    "imp_NUEVO_IMPUESTO",  # Agregar en el grupo que corresponda
]
```

> Nota: Despues de agregar una columna nueva, el CSV existente no la tendra. Procesarlo de nuevo o agregar la columna manualmente en Excel antes de usar el archivo.

---

## Resolucion de Problemas

### Error: "Faltan las credenciales en .env"

**Causa:** El archivo `.env` no existe o esta mal configurado.

**Solucion:**

1. Verificar que existe el archivo `.env` en la raiz del proyecto
2. Verificar que contenga las lineas `CLIENT_NAME_USER` y `CLIENT_NAME_PASS`
3. No debe haber espacios alrededor del `=`

Ejemplo correcto:

```env
CLIENT_NAME_USER=usuario@ejemplo.com
CLIENT_NAME_PASS=contraseña123
```

---

### Error: "Archivo ids.txt no existe"

**Causa:** No se encuentra el archivo con los IDs a procesar.

**Solucion:** Crear `ids.txt` en la raiz del proyecto con al menos un ID:

```
2089578
```

---

### Login falla

**Sintomas:**

- El script muestra `[ERROR] Login fallo`
- Se genera un screenshot en `logs/login_error.png`

**Causas posibles:**

| Causa | Solucion |
|---|---|
| Credenciales incorrectas | Verificar usuario y contraseña en `.env`. Probar login manual en el portal. |
| Captcha activado | Ejecutar con `HEADLESS=False`. Resolver el captcha manualmente cuando aparezca. |
| Red lenta o timeout | Aumentar `TIMEOUT=60000` en `.env` (60 segundos). |
| Portal caido | Verificar acceso manual a `portal-operativo.example.com` |

---

### Campo "Tipo" extrae None

**Sintoma:**

```
[+] Tipo: None
```

**Causa:** El campo "Tipo" tarda en renderizarse en el DOM.

**Solucion:** El script aplica un wait automatico. Si el problema persiste, aumentar el `time.sleep` en la seccion de extraccion de tipo en `src/extractor.py` (linea ~122).

---

### Impuesto cae en columna imp_OTROS

**Sintoma:**

```
[WARN] Impuesto no mapeado: 'ALGUNA DESCRIPCION' ($28.00) -> imp_OTROS
```

**Causa:** La descripcion del impuesto no esta registrada en el diccionario `IMPUESTO_MAP`.

**Acciones:**

- Si el monto es pequeño (menos de $100): ignorar, no afecta el total.
- Si el monto es significativo: agregar al mapeo (ver seccion [Agregar un nuevo impuesto al mapeo](#agregar-un-nuevo-impuesto-al-mapeo)).
- Para auditar todos los impuestos no mapeados: abrir `output/comprobantes.csv` y filtrar las filas donde `imp_OTROS > 0`.

---

### Warning de pandas sobre pyarrow

**Mensaje:**

```
DeprecationWarning: Pyarrow will become a required dependency of pandas...
```

**Causa:** Pandas 3.0 requerira pyarrow como dependencia.

**Solucion (opcional):**

```bash
pip install pyarrow
```

No afecta la funcionalidad actual del script.

---

### El script se cuelga o tarda mucho

**Causas posibles:**

| Causa | Solucion |
|---|---|
| Comprobante con muchos impuestos | La extraccion de la tabla puede tardar 30-40 segundos. Es comportamiento normal. |
| Red lenta | Aumentar `TIMEOUT` en `.env`. Ejecutar en horarios de menor trafico. |
| Comprobante inexistente | El script esperara el timeout completo antes de fallar. Verificar que el ID existe en el portal. |

---

### Estados de extraccion

Cada fila del CSV incluye la columna `estado_extraccion` con los siguientes valores posibles:

| Estado | Descripcion | Accion recomendada |
|---|---|---|
| `OK` | Extraccion completa y exitosa | Ninguna |
| `ERROR_CABECERA` | Fallo la extraccion de cabecera (ID, Emisor, etc.) | Verificar que el comprobante existe y esta cargado en el portal |
| `ERROR_IMPORTES` | Fallo la extraccion de importes o tabla de impuestos | Verificar la pestana IMPORTES en el portal |
| `ERROR_RECEPCIONES` | Fallo la extraccion de recepciones | Verificar la pestana RECEPCIONES (puede estar vacia en algunos comprobantes) |
| `ERROR_GENERAL` | Error no categorizado | Revisar la columna `motivo_error` y el archivo `logs/extractor.log` |

> Los comprobantes con error se escriben igualmente en el CSV con los datos parciales disponibles, para facilitar la auditoria.

---

## Flujo de Ejecucion Tecnico

```
main.py
  |-- Lee configuracion desde .env y config/settings.py
  |-- Valida existencia de ids.txt y credenciales
  |-- Inicializa CSVHandler (crea comprobantes.csv si no existe)
  |-- Lee IDs ya procesados del CSV (para evitar duplicados)
  |-- Inicializa Scraper (Playwright + Chromium)
  |-- Realiza login en el portal del cliente
  |
  Para cada ID en ids.txt:
  |   |-- Navega a la URL del comprobante
  |   |
  |   |-- Extractor.extraer_cabecera()
  |   |     Extrae: ID, Emisor, Tipo, Nro Comprobante, Fechas, CAE
  |   |     Mapea tipo de contenido por proveedor
  |   |
  |   |-- Extractor.extraer_importes()
  |   |     Extrae: Neto Gravado, No Gravado, Importe Total
  |   |     Extrae la tabla de impuestos (itera filas <tr>)
  |   |
  |   |-- Extractor.extraer_recepciones()
  |   |     Extrae: Nro Recepcion, Nro OC
  |   |
  |   |-- parser.parsear_a_fila_csv()
  |   |     Mapea impuestos a sus 39 columnas especificas
  |   |     Suma impuestos sin mapeo a imp_OTROS
  |   |
  |   |-- CSVHandler.agregar_fila()
  |         Valida estructura (54 columnas)
  |         Escribe fila en modo append
  |
  |-- Muestra resumen estadistico
  |-- Cierra el navegador
```

---

## Arquitectura del Codigo

### Separacion de responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `config/settings.py` | URLs del portal, timeouts, estructura de las 54 columnas del CSV, estados de extraccion |
| `config/selectors.py` | Selectores CSS/XPath por pestana, diccionario de mapeo impuesto → columna CSV |
| `src/scraper.py` | Inicializacion de Playwright, login, navegacion, cambio de pestanas, extraccion de texto y tabla de impuestos |
| `src/extractor.py` | Orquestacion de extraccion por pestana, logica de retry, mapeo de tipo de contenido por proveedor |
| `src/parser.py` | Transformacion del dict crudo a 54 columnas, aplicacion del mapeo de impuestos, validacion |
| `src/csv_handler.py` | Creacion del CSV con encabezados, escritura incremental (append), lectura de IDs procesados, estadisticas |
| `main.py` | Punto de entrada, lectura de ids.txt, orquestacion del flujo, manejo de interrupciones, reporte final |

---

## Decisiones Tecnicas

**Por que Playwright en vez de Selenium:**
- API mas moderna y activamente mantenida
- Mejor manejo de elementos dinamicos y SPAs
- Instalacion del navegador integrada (`playwright install`)
- Menor overhead de recursos

**Por que usar la API sincrona de Playwright:**
- Codigo mas legible (sin async/await)
- Suficiente para procesamiento secuencial
- Menor complejidad para mantenimiento futuro

**Por que mapeo por proveedor para tipo de contenido:**
- El dropdown del portal no siempre esta presente o cargado
- Es mas robusto que depender del estado del DOM
- Permite ajustar el comportamiento sin tocar la logica de scraping

**Por que extraccion con JavaScript (evaluate):**
- Algunos campos dinamicos no son detectables con selectores CSS
- Evita esperas innecesarias por visibilidad del elemento
- Acceso directo al valor del input sin interaccion de usuario

**Por que CSV incremental (append):**
- Permite interrumpir y reanudar sin perder datos previos
- Facilita el procesamiento por lotes
- Reduce el riesgo de perdida de datos ante fallos inesperados

---

## Limitaciones Conocidas

- **Captchas:** No se manejan automaticamente. Requiere intervencion manual con `HEADLESS=False`.
- **Timeout fijo:** 30 segundos por defecto. En redes lentas puede ser insuficiente.
- **Sin paralelizacion:** Procesa un comprobante a la vez (mejora planificada).
- **Sin reintentos automaticos:** Si un comprobante falla, no se reintenta en la misma ejecucion. Debe ejecutarse de nuevo manualmente.
- **Impuestos no mapeados:** Si aparece un impuesto nuevo en el portal, cae en `imp_OTROS` hasta agregar el mapeo manualmente.
- **Dependencia de la estructura del portal:** Si CLIENT_NAME modifica su HTML/CSS, puede romper los selectores.

---

## Mantenimiento

### Actualizar dependencias

```bash
pip install --upgrade playwright pandas python-dotenv
playwright install chromium
```

### Backup del CSV

Antes de procesar lotes grandes, hacer un backup del CSV existente:

```powershell
copy output\comprobantes.csv output\comprobantes_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.csv
```

### Limpieza de logs

Los logs pueden crecer con el tiempo. Limpiar periodicamente:

```powershell
del logs\extractor.log
```

---

## Roadmap - Mejoras Futuras

### Prioridad Alta

- [ ] Deteccion de cambios en la estructura del portal (alertas)

### Prioridad Media

- [ ] Barra de progreso visual (tqdm)
- [ ] Modo de validacion (compara CSV vs portal)

### Prioridad Baja

- [ ] Paralelizacion (multiples navegadores)
- [ ] Exportacion a Excel con formato
- [ ] Dashboard web para monitoreo

---

## Contacto y Soporte

- **Desarrollador:** Lautaro Gomez
- **Email:** lautarogmz0@gmail.com
- **Proyecto:** IBMer watsonx Challenge 2026 - Modulo 1

Para reportar problemas o sugerir mejoras, contactar por email.

---

## Informacion del Proyecto

| Campo | Valor |
|---|---|
| Version | 1.0.0 |
| Ultima actualizacion | 21/07/2026 |
| Estado | Produccion |
| Columnas CSV | 54 |
| Impuestos mapeados | 37 descripciones → 39 columnas |
| Modulo siguiente | Modulo 2 — Carga en Oracle REIM (en desarrollo) |
