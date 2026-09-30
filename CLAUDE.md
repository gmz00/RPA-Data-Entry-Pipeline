# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Two-stage RPA pipeline (Playwright) that replaces manual invoice entry for company's TENANT_NAME account:

1. **`extractor/`** — scrapes invoice ("comprobante") data from the CLIENT_NAME portal and writes `output/comprobantes.csv` (54 columns: cabecera, importes, 39 mapped tax columns, recepciones, control).
2. **`loader/`** — reads that CSV and loads each comprobante into Oracle REIM (built on Oracle ADF) via browser automation, writing `output/procesados.csv` / `output/fallidos.csv` / `output/ejecucion_<timestamp>.log`.
3. **`orquestador.py`** (root) — runs both modules end-to-end: prompts to edit `extractor/ids.txt`, runs the extractor, feeds its CSV to the loader via `CSV_INPUT_PATH` env var, offers retries on failure/nonzero exit, and finally moves all output files into `outputs_diarios/YYYY_MM_DD/`. If the pipeline already ran that day, the new outputs go into a `corrida_2/`, `corrida_3/`, ... subfolder instead of overwriting the first run's files (`_destino_corrida`). `iniciar.bat` is the Windows double-click entry point for this orchestrator.

Each module is a fully independent Python project with its **own venv** and `requirements.txt` — there is no shared root environment.

## Commands

Each module requires its own venv, created inside the module directory:

```bash
cd extractor   # or loader
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
```

Run a module directly (venv activated, from inside the module dir):

```bash
python main.py
```

Run the full pipeline (checks both venvs exist, from repo root):

```bash
python orquestador.py
# or double-click iniciar.bat on Windows
```

Tests (pytest, run from repo root for orchestrator tests, from `loader/` for loader tests — there is no shared root config):

```bash
pytest                              # root: tests/test_orquestador.py (orquestador.py)
cd loader && pytest             # loader/tests/test_reader.py (CSV parsing + tax mapping)
```

`extractor` has no test suite currently wired up (its README references a `tests/test_parser.py` that isn't present).

Single test example: `pytest tests/test_orquestador.py::test_mover_outputs_mueve_todo`

## Configuration

Both modules load credentials/config from a module-local `.env` (never committed; see `.env.example` in each dir). Config is centralized per module:

- `extractor/config/settings.py` — `CLIENT_NAME_USER`/`CLIENT_NAME_PASS` (raises `ValueError` at import time if missing), portal URLs, `HEADLESS`/`TIMEOUT`, and the authoritative `CSV_COLUMNS` list (order matters — it's the CSV schema).
- `extractor/config/selectors.py` — CSS/XPath selectors per portal tab, and `IMPUESTO_MAP` (tax description → CSV column).
- `loader/config.py` — `REIM_URL`/`REIM_USER`/`REIM_PASSWORD`, `TIMEOUT_DEFAULT`/`TIMEOUT_CREAR_FACTURA`, `TOLERANCIA_MAXIMA` (max cents tolerance for total-vs-sum-of-lines reconciliation), `CSV_INPUT_PATH` (defaults to `../extractor/output/comprobantes.csv` if not overridden — the orchestrator always overrides it to the just-run extractor's output).

## Architecture notes

### extractor pipeline (per comprobante ID from `ids.txt`)

`main.py` → `Scraper` (Playwright session/login/navigation) → `Extractor.extraer_todo()` (iterates CABECERA/IMPORTES/RECEPCIONES tabs) → `parser.parsear_a_fila_csv()` (maps raw dict to the 54 fixed CSV columns, sums unmapped taxes into `imp_OTROS`) → `CSVHandler.agregar_fila()` (incremental append, validates column count, dedupes against already-processed IDs on restart).

Each row always gets written, even on failure — `estado_extraccion` (`OK` / `ERROR_CABECERA` / `ERROR_IMPORTES` / `ERROR_RECEPCIONES` / `ERROR_GENERAL`) plus `motivo_error` record the failure for later auditing instead of aborting the batch.

### loader pipeline (per comprobante row from the CSV)

`main.py` reads comprobantes via `reader/csv_reader.py` (CSV row → `Comprobante`/`LineaImpuesto` dataclasses in `models/comprobante.py`, applying `mappings/tipo_documento.py`, `mappings/contenido.py`, `mappings/impuestos.py`; rows with unmappable data are marked `estado="fallido"` here and never touch REIM). For each pending comprobante: `reim/buscador.py` (find provider + validate OC) → `reim/crear_factura.py` (header tab) → `reim/desglose_impuestos.py` (tax breakdown tab) → `reim/aprobar.py` (approve + detect result). `reim/popups.py` handles REIM's intermittent server-error popup. Failures are caught per-stage in `main.py`'s `procesar_comprobante()` and routed to specific `etapa_fallo` values (`OC`, `Proveedor`, `Cabecera`, `Desglose`, `IVA_mal_calculado`, `montos_no_coinciden`, `Aprobacion`, ...) via `logger/logger.py`'s `ResultadoLogger`, which also drives resume-on-restart by reading `procesados.csv` back in.

**Oracle ADF quirks that shape the REIM automation code** (see `loader/README.md` "Notas técnicas" for full detail):
- OC fields must be filled by dispatching JS `input`/`change` events — Playwright's `fill()` doesn't register with ADF.
- Combos/selects can't use `select_option()` — type the visible text (which filters options) then Enter+Tab.
- Grid amount fields must use `fill()` + Tab — JS-event dispatch resets them to 0 in ADF's grid widget.
- Field `name` attributes contain incrementing indices (`tabrgN`); selectors use suffix + `:visible` filtering instead of fixed indices.
- REIM's DOM degrades after ~13 documents created in one session without a refresh — `main.py`'s `REINICIAR_CADA = 10` forces a full browser restart (re-login) every 10 documents to avoid this.
- The "Contenido de la factura" combo's options can render in Spanish or English at runtime; `mappings/contenido.py` matches either.

### Cross-module contract

The extractor's `CSV_COLUMNS` (in `extractor/config/settings.py`) and the loader's expected header (built dynamically in tests from `mappings/impuestos.py`'s `MAPEO_IMPUESTOS` keys) must stay in sync — adding a new tax column requires updating both `extractor/config/selectors.py` (`IMPUESTO_MAP`) + `settings.py` (`CSV_COLUMNS`) and `loader/mappings/impuestos.py`.
