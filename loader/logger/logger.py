import csv
import logging
import os
from datetime import datetime
import config


class ResultadoLogger:
    """
    Centraliza la salida del loader:
      - Log tecnico (.log nuevo por corrida + consola)
      - Escribe procesados.csv / fallidos.csv en modo APPEND (permite reanudar)
      - Provee IDs ya procesados para saltearlos en reejecuciones
      - Al finalizar: imprime concatenaciones de IDs (formato "id1|id2|id3")
        UNICAS y con procesados con prioridad (un ID aprobado no figura en fallidos)
    """

    COLUMNAS_PROCESADOS = [
        "timestamp", "id_bpm", "nombre_proveedor", "nro_factura",
        "nro_oc", "nro_recepcion", "subtotal", "importe_total", "estado",
    ]
    COLUMNAS_FALLIDOS = COLUMNAS_PROCESADOS + ["etapa_fallo", "motivo_error"]

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.proc_path = os.path.join(self.output_dir, "procesados.csv")
        self.fall_path = os.path.join(self.output_dir, "fallidos.csv")

        # Acumuladores en memoria (para el resumen/concatenacion final)
        self.procesados_sesion = []
        self.fallidos_sesion = []

        self._configurar_log_tecnico()
        self._asegurar_headers()

    # ---------- Log tecnico ----------
    def _configurar_log_tecnico(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(self.output_dir, f"ejecucion_{ts}.log")

        self.logger = logging.getLogger("reim_loader")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        self.logger.addHandler(ch)

        self.logger.info(f"Log tecnico: {log_path}")

    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)

    # ---------- Headers (crear CSV si no existen) ----------
    def _asegurar_headers(self):
        if not os.path.exists(self.proc_path):
            with open(self.proc_path, "w", encoding="utf-8-sig", newline="") as f:
                csv.DictWriter(f, fieldnames=self.COLUMNAS_PROCESADOS).writeheader()
        if not os.path.exists(self.fall_path):
            with open(self.fall_path, "w", encoding="utf-8-sig", newline="") as f:
                csv.DictWriter(f, fieldnames=self.COLUMNAS_FALLIDOS).writeheader()

    # ---------- Reanudacion: IDs ya procesados ----------
    def ids_ya_procesados(self) -> set:
        """Lee procesados.csv y devuelve el set de id_bpm ya cargados con exito."""
        ids = set()
        if os.path.exists(self.proc_path):
            with open(self.proc_path, "r", encoding="utf-8-sig", newline="") as f:
                for fila in csv.DictReader(f):
                    ids.add(str(fila["id_bpm"]).strip())
        return ids

    # ---------- Helpers ----------
    def _subtotal(self, comp) -> float:
        return comp.neto_gravado if comp.neto_gravado > 0 else comp.neto_no_gravado

    def _fila_base(self, comp) -> dict:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "id_bpm": comp.id_bpm,
            "nombre_proveedor": comp.nombre_proveedor,
            "nro_factura": comp.nro_factura,
            "nro_oc": comp.nro_oc,
            "nro_recepcion": comp.nro_recepcion,
            "subtotal": self._subtotal(comp),
            "importe_total": comp.importe_total,
        }

    def _append_csv(self, ruta, columnas, fila):
        with open(ruta, "a", encoding="utf-8-sig", newline="") as f:
            csv.DictWriter(f, fieldnames=columnas).writerow(fila)

    # ---------- Registro (escribe YA en el CSV) ----------
    def registrar_procesado(self, comp):
        fila = self._fila_base(comp)
        fila["estado"] = "procesado"
        self._append_csv(self.proc_path, self.COLUMNAS_PROCESADOS, fila)
        self.procesados_sesion.append(fila)
        self.info(f"PROCESADO: id={comp.id_bpm} factura={comp.nro_factura}")

    def registrar_fallido(self, comp, motivo: str, etapa: str = ""):
        fila = self._fila_base(comp)
        fila["estado"] = "fallido"
        fila["etapa_fallo"] = etapa
        fila["motivo_error"] = motivo
        self._append_csv(self.fall_path, self.COLUMNAS_FALLIDOS, fila)
        self.fallidos_sesion.append(fila)
        self.error(f"FALLIDO: id={comp.id_bpm} etapa={etapa} motivo={motivo}")

    # ---------- Resumen final ----------
    def _ids_unicos_desde_csv(self, ruta) -> list:
        """
        Lee el CSV y devuelve la lista de id_bpm SIN duplicados,
        en orden de aparicion.
        """
        ids = []
        vistos = set()
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
                for fila in csv.DictReader(f):
                    idb = str(fila["id_bpm"]).strip()
                    if idb and idb not in vistos:
                        vistos.add(idb)
                        ids.append(idb)
        return ids

    def resumen(self):
        """
        Imprime resumen de la sesion + concatenacion ACUMULADA de IDs.
        Reglas:
          - Sin duplicados.
          - Un ID que esta en procesados NO aparece en fallidos (procesados manda).
        """
        # Procesados: unicos
        ids_proc = self._ids_unicos_desde_csv(self.proc_path)
        set_proc = set(ids_proc)

        # Fallidos: unicos Y que NO esten en procesados
        ids_fall = [i for i in self._ids_unicos_desde_csv(self.fall_path)
                    if i not in set_proc]

        str_proc = "|".join(ids_proc)
        str_fall = "|".join(ids_fall)

        self.info("=" * 60)
        self.info(f"RESUMEN SESION: {len(self.procesados_sesion)} procesados, "
                  f"{len(self.fallidos_sesion)} fallidos")
        self.info("-" * 60)
        self.info(f"IDs PROCESADOS acumulados (pegar en CLIENT_NAME):\n{str_proc}")
        self.info("-" * 60)
        self.info(f"IDs FALLIDOS acumulados (pegar en CLIENT_NAME):\n{str_fall}")
        self.info("=" * 60)