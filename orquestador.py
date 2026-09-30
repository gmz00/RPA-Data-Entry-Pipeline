"""
Orquestador del pipeline CLIENT_NAME.

Ejecuta en orden:
  1. extractor-CLIENT_NAME/main.py  (Portal CLIENT_NAME -> comprobantes.csv)
  2. loader-CLIENT_NAME/main.py     (comprobantes.csv -> carga en Oracle REIM)

y mueve todo el output generado a una carpeta con la fecha de ejecucion.
"""

import csv
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent
EXTRACTOR_DIR = ROOT_DIR / "extractor-CLIENT_NAME"
LOADER_DIR = ROOT_DIR / "loader-CLIENT_NAME"
IDS_FILE = EXTRACTOR_DIR / "ids.txt"


# ============================================================================
# Utilidades de entorno / venv
# ============================================================================
def venv_python(module_dir: Path) -> Path:
    """Ruta al python del venv propio del modulo, segun el SO actual."""
    if sys.platform == "win32":
        return module_dir / "venv" / "Scripts" / "python.exe"
    return module_dir / "venv" / "bin" / "python"


def verificar_venv(module_dir: Path, nombre: str):
    """Devuelve la ruta al python del venv, o None si no existe (con mensaje)."""
    python_exe = venv_python(module_dir)
    if not python_exe.exists():
        print(f"[ERROR] No se encontro el entorno virtual de {nombre} en: {python_exe}")
        print(f"        Cree el venv dentro de {module_dir} (ver su README.md):")
        print(f"          python -m venv venv")
        print(f"          (activar el venv) && pip install -r requirements.txt")
        print(f"          playwright install chromium")
        return None
    return python_exe


# ============================================================================
# Interaccion con el usuario
# ============================================================================
def preguntar_si_no(mensaje: str, default: bool = False) -> bool:
    sufijo = " [S/n]: " if default else " [s/N]: "
    while True:
        resp = input(mensaje + sufijo).strip().lower()
        if resp == "":
            return default
        if resp in ("s", "si", "y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
        print("Respuesta no reconocida. Ingrese 's' o 'n'.")


def abrir_ids_txt(ids_path: Path) -> None:
    """Abre ids.txt con el programa por defecto del SO (crea el archivo si no existe)."""
    if not ids_path.exists():
        ids_path.write_text(
            "# Pegue aca los IDs de comprobantes, uno por linea.\n"
            "# Las lineas que empiecen con # son ignoradas.\n",
            encoding="utf-8",
        )
    try:
        if sys.platform == "win32":
            os.startfile(str(ids_path))  # noqa: S606 - accion intencional del usuario
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(ids_path)])
        else:
            subprocess.Popen(["xdg-open", str(ids_path)])
    except OSError as e:
        print(f"[WARN] No se pudo abrir el editor automaticamente ({e}).")
        print(f"       Abra manualmente el archivo: {ids_path}")


def contar_ids_validos(ids_path: Path) -> int:
    """Cuenta lineas validas (enteros, ignorando vacias y comentarios) en ids.txt."""
    if not ids_path.exists():
        return 0
    count = 0
    with ids_path.open("r", encoding="utf-8-sig") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            try:
                int(linea)
                count += 1
            except ValueError:
                pass
    return count


def lineas_rechazadas(ids_path: Path, limite: int = 5) -> list:
    """Lineas no vacias/no comentario que no se pudieron interpretar como ID (para diagnostico)."""
    if not ids_path.exists():
        return []
    rechazadas = []
    with ids_path.open("r", encoding="utf-8-sig") as f:
        for linea in f:
            cruda = linea.strip()
            if not cruda or cruda.startswith("#"):
                continue
            try:
                int(cruda)
            except ValueError:
                rechazadas.append(linea.rstrip("\n"))
                if len(rechazadas) >= limite:
                    break
    return rechazadas


def paso_editar_ids(ids_path: Path) -> bool:
    """Abre el editor y espera confirmacion. Reintenta si no detecta IDs validos."""
    while True:
        abrir_ids_txt(ids_path)
        input(
            "\nPegue los IDs en ids.txt, GUARDE el archivo y presione ENTER "
            "aqui para continuar..."
        )
        n = contar_ids_validos(ids_path)
        if n > 0:
            print(f"[OK] Se detectaron {n} IDs validos en {ids_path.name}")
            return True
        print(f"[WARN] No se detectaron IDs validos en {ids_path}")
        tam = ids_path.stat().st_size if ids_path.exists() else 0
        print(f"       Tamano del archivo: {tam} bytes")
        for cruda in lineas_rechazadas(ids_path):
            print(f"       Linea no reconocida como ID: {cruda!r}")
        if preguntar_si_no("¿Desea reabrir el archivo para revisar/pegar los IDs?", default=True):
            continue
        return preguntar_si_no(
            "¿Continuar de todas formas sin IDs validos? (no recomendado)", default=False
        )


# ============================================================================
# Ejecucion de modulos
# ============================================================================
def ejecutar_modulo(nombre: str, module_dir: Path, python_exe: Path, extra_env=None) -> int:
    main_py = module_dir / "main.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if extra_env:
        env.update(extra_env)

    print(f"\n{'=' * 70}")
    print(f"  Ejecutando {nombre}...")
    print(f"{'=' * 70}\n")

    proceso = subprocess.run([str(python_exe), str(main_py)], cwd=str(module_dir), env=env)
    return proceso.returncode


def ejecutar_con_reintentos(nombre: str, module_dir: Path, python_exe: Path, extra_env=None) -> bool:
    """Ejecuta el modulo, ofreciendo reintentar mientras falle. True si termino OK."""
    while True:
        codigo = ejecutar_modulo(nombre, module_dir, python_exe, extra_env)
        if codigo == 0:
            print(f"\n[OK] {nombre} finalizo correctamente (exit code 0)")
            return True
        print(f"\n[ERROR] {nombre} finalizo con exit code {codigo}")
        if not preguntar_si_no(f"¿Desea reintentar la ejecucion de {nombre}?", default=True):
            return False


# ============================================================================
# Conteo de fallidos pendientes (replica ResultadoLogger.resumen())
# ============================================================================
def _ids_unicos_desde_csv(path: Path):
    ids, vistos = [], set()
    if not path.exists():
        return ids
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            idb = str(fila.get("id_bpm") or "").strip()
            if idb and idb not in vistos:
                vistos.add(idb)
                ids.append(idb)
    return ids


def contar_fallidos_pendientes(loader_output_dir: Path) -> int:
    """Fallidos unicos que NO estan en procesados (mismos criterios que logger.py)."""
    ids_proc = set(_ids_unicos_desde_csv(loader_output_dir / "procesados.csv"))
    ids_fall = _ids_unicos_desde_csv(loader_output_dir / "fallidos.csv")
    return len([i for i in ids_fall if i not in ids_proc])


# ============================================================================
# Mover outputs a carpeta con fecha
# ============================================================================
def _destino_corrida(fecha_dir: Path) -> Path:
    """Ruta de destino para esta corrida dentro de la carpeta de la fecha.

    La primera corrida del dia usa fecha_dir directamente. Si ya hubo una
    corrida ese mismo dia (fecha_dir ya existe), se crea una subcarpeta
    corrida_2, corrida_3, etc. para no pisar los outputs anteriores.
    """
    if not fecha_dir.exists():
        return fecha_dir
    contador = 2
    while (fecha_dir / f"corrida_{contador}").exists():
        contador += 1
    return fecha_dir / f"corrida_{contador}"


def _mover_archivo(origen: Path, destino_dir: Path) -> None:
    if not origen.exists():
        print(f"  [WARN] No se encontro (se omite): {origen}")
        return
    while True:
        try:
            shutil.move(str(origen), str(destino_dir / origen.name))
            print(f"  movido: {origen.name}")
            return
        except PermissionError:
            input(
                f"[ERROR] No se pudo mover {origen.name} "
                f"(¿esta abierto en Excel/otro programa?). Cierrelo y presione ENTER "
                f"para reintentar..."
            )


def mover_outputs(root_dir: Path, extractor_dir: Path, loader_dir: Path, fecha: str = None) -> Path:
    fecha = fecha or datetime.now().strftime("%Y_%m_%d")
    fecha_dir = root_dir / "outputs_diarios" / fecha
    destino = _destino_corrida(fecha_dir)
    (destino / "extractor-CLIENT_NAME").mkdir(parents=True)
    (destino / "loader-CLIENT_NAME").mkdir(parents=True)

    print(f"\nMoviendo outputs a: {destino}")

    for archivo in [
        extractor_dir / "output" / "comprobantes.csv",
        extractor_dir / "logs" / "extractor.log",
    ]:
        _mover_archivo(archivo, destino / "extractor-CLIENT_NAME")

    loader_output = loader_dir / "output"
    archivos_loader = [
        loader_output / "procesados.csv",
        loader_output / "fallidos.csv",
    ]
    if loader_output.exists():
        archivos_loader.extend(sorted(loader_output.glob("ejecucion_*.log")))
    for archivo in archivos_loader:
        _mover_archivo(archivo, destino / "loader-CLIENT_NAME")

    print(f"[OK] Outputs movidos a: {destino}")
    return destino


# ============================================================================
# Flujo principal
# ============================================================================
def main() -> int:
    print("=" * 70)
    print("  ORQUESTADOR CLIENT_NAME - Extraccion + Carga")
    print("=" * 70)

    if not preguntar_si_no("¿Desea comenzar el proceso?", default=True):
        print("Operacion cancelada por el usuario.")
        return 0

    py_extractor = verificar_venv(EXTRACTOR_DIR, "extractor-CLIENT_NAME")
    py_loader = verificar_venv(LOADER_DIR, "loader-CLIENT_NAME")
    if py_extractor is None or py_loader is None:
        return 1

    if not paso_editar_ids(IDS_FILE):
        print("[ERROR] No hay IDs validos para procesar. Abortando.")
        return 1

    ejecutar_con_reintentos("extractor-CLIENT_NAME", EXTRACTOR_DIR, py_extractor)

    comprobantes_csv = EXTRACTOR_DIR / "output" / "comprobantes.csv"
    if not comprobantes_csv.exists():
        print(f"[WARN] No existe {comprobantes_csv}; loader-CLIENT_NAME probablemente falle.")

    env_loader = {"CSV_INPUT_PATH": str(comprobantes_csv.resolve())}
    ejecutar_con_reintentos("loader-CLIENT_NAME", LOADER_DIR, py_loader, extra_env=env_loader)

    while True:
        pendientes = contar_fallidos_pendientes(LOADER_DIR / "output")
        if pendientes == 0:
            break
        if not preguntar_si_no(
            f"Quedaron {pendientes} comprobante(s) fallidos en fallidos.csv. "
            f"¿Reintentar loader-CLIENT_NAME?",
            default=True,
        ):
            break
        ejecutar_con_reintentos("loader-CLIENT_NAME", LOADER_DIR, py_loader, extra_env=env_loader)

    destino = mover_outputs(ROOT_DIR, EXTRACTOR_DIR, LOADER_DIR)
    print(f"\nProceso finalizado. Resultados en: {destino}")
    return 0


if __name__ == "__main__":
    try:
        codigo = main()
    except KeyboardInterrupt:
        print("\n[!!] Proceso interrumpido por el usuario (Ctrl+C).")
        codigo = 130
    except Exception:
        import traceback

        traceback.print_exc()
        input("\n[ERROR] Ocurrio un error inesperado en el orquestador. Presione ENTER para cerrar...")
        codigo = 1
    input("\nPresione ENTER para cerrar esta ventana...")
    sys.exit(codigo)
