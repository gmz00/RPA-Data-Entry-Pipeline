import csv
import sys

import orquestador as orq


# ============================================================================
# contar_ids_validos
# ============================================================================
def test_contar_ids_validos_vacio(tmp_path):
    ids_path = tmp_path / "ids.txt"
    ids_path.write_text("")
    assert orq.contar_ids_validos(ids_path) == 0


def test_contar_ids_validos_solo_comentarios(tmp_path):
    ids_path = tmp_path / "ids.txt"
    ids_path.write_text("# comentario\n# otro\n\n")
    assert orq.contar_ids_validos(ids_path) == 0


def test_contar_ids_validos_mezcla(tmp_path):
    ids_path = tmp_path / "ids.txt"
    ids_path.write_text("2089578\n# comentario\nno_es_un_id\n2089409\n\n2092130\n")
    assert orq.contar_ids_validos(ids_path) == 3


def test_contar_ids_validos_archivo_inexistente(tmp_path):
    assert orq.contar_ids_validos(tmp_path / "no_existe.txt") == 0


# ============================================================================
# contar_fallidos_pendientes / _ids_unicos_desde_csv
# ============================================================================
COLUMNAS_PROC = [
    "timestamp", "id_bpm", "nombre_proveedor", "nro_factura",
    "nro_oc", "nro_recepcion", "subtotal", "importe_total", "estado",
]
COLUMNAS_FALL = COLUMNAS_PROC + ["etapa_fallo", "motivo_error"]


def _escribir_csv(path, columnas, filas):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in filas:
            writer.writerow(fila)


def _fila_proc(id_bpm):
    return {c: "" for c in COLUMNAS_PROC} | {"id_bpm": id_bpm, "estado": "procesado"}


def _fila_fall(id_bpm, etapa="Desconocido"):
    return {c: "" for c in COLUMNAS_FALL} | {
        "id_bpm": id_bpm, "estado": "fallido", "etapa_fallo": etapa,
    }


def test_contar_fallidos_pendientes_sin_archivos(tmp_path):
    assert orq.contar_fallidos_pendientes(tmp_path) == 0


def test_contar_fallidos_pendientes_dedup_y_procesados_manda(tmp_path):
    _escribir_csv(tmp_path / "procesados.csv", COLUMNAS_PROC, [_fila_proc("1"), _fila_proc("2")])
    _escribir_csv(
        tmp_path / "fallidos.csv",
        COLUMNAS_FALL,
        [_fila_fall("2"), _fila_fall("3"), _fila_fall("3"), _fila_fall("4")],
    )
    # "2" fallo pero luego se proceso con exito -> no cuenta.
    # "3" duplicado -> cuenta una sola vez. "4" cuenta.
    assert orq.contar_fallidos_pendientes(tmp_path) == 2


def test_contar_fallidos_pendientes_todos_resueltos(tmp_path):
    _escribir_csv(tmp_path / "procesados.csv", COLUMNAS_PROC, [_fila_proc("1")])
    _escribir_csv(tmp_path / "fallidos.csv", COLUMNAS_FALL, [_fila_fall("1")])
    assert orq.contar_fallidos_pendientes(tmp_path) == 0


# ============================================================================
# venv_python
# ============================================================================
def test_venv_python_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert orq.venv_python(tmp_path) == tmp_path / "venv" / "Scripts" / "python.exe"


def test_venv_python_linux(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert orq.venv_python(tmp_path) == tmp_path / "venv" / "bin" / "python"


def test_verificar_venv_inexistente(tmp_path, capsys):
    resultado = orq.verificar_venv(tmp_path, "modulo-x")
    assert resultado is None
    assert "modulo-x" in capsys.readouterr().out


# ============================================================================
# _destino_corrida / mover_outputs
# ============================================================================
def test_destino_corrida_primera_corrida_del_dia(tmp_path):
    fecha_dir = tmp_path / "2026_08_22"
    assert orq._destino_corrida(fecha_dir) == fecha_dir


def test_destino_corrida_segunda_corrida_del_dia(tmp_path):
    fecha_dir = tmp_path / "2026_08_22"
    fecha_dir.mkdir()
    assert orq._destino_corrida(fecha_dir) == fecha_dir / "corrida_2"


def test_destino_corrida_tercera_corrida_del_dia(tmp_path):
    fecha_dir = tmp_path / "2026_08_22"
    fecha_dir.mkdir()
    (fecha_dir / "corrida_2").mkdir()
    assert orq._destino_corrida(fecha_dir) == fecha_dir / "corrida_3"


def _armar_modulos_con_output(tmp_path):
    extractor_dir = tmp_path / "extractor-CLIENT_NAME"
    loader_dir = tmp_path / "loader-CLIENT_NAME"
    (extractor_dir / "output").mkdir(parents=True)
    (extractor_dir / "logs").mkdir(parents=True)
    (loader_dir / "output").mkdir(parents=True)

    (extractor_dir / "output" / "comprobantes.csv").write_text("id\n1\n")
    (extractor_dir / "logs" / "extractor.log").write_text("log extractor\n")
    (loader_dir / "output" / "procesados.csv").write_text("id_bpm\n1\n")
    (loader_dir / "output" / "fallidos.csv").write_text("id_bpm\n2\n")
    (loader_dir / "output" / "ejecucion_20260822_120000.log").write_text("log loader\n")

    return extractor_dir, loader_dir


def test_mover_outputs_mueve_todo(tmp_path):
    extractor_dir, loader_dir = _armar_modulos_con_output(tmp_path)

    destino = orq.mover_outputs(tmp_path, extractor_dir, loader_dir, fecha="2026_08_22")

    assert destino == tmp_path / "outputs_diarios" / "2026_08_22"
    assert (destino / "extractor-CLIENT_NAME" / "comprobantes.csv").exists()
    assert (destino / "extractor-CLIENT_NAME" / "extractor.log").exists()
    assert (destino / "loader-CLIENT_NAME" / "procesados.csv").exists()
    assert (destino / "loader-CLIENT_NAME" / "fallidos.csv").exists()
    assert (destino / "loader-CLIENT_NAME" / "ejecucion_20260822_120000.log").exists()
    # los originales ya no estan (se movieron, no copiaron)
    assert not (extractor_dir / "output" / "comprobantes.csv").exists()


def test_mover_outputs_archivo_faltante_no_rompe(tmp_path, capsys):
    extractor_dir = tmp_path / "extractor-CLIENT_NAME"
    loader_dir = tmp_path / "loader-CLIENT_NAME"
    (extractor_dir / "output").mkdir(parents=True)
    (loader_dir / "output").mkdir(parents=True)
    # no se crea ningun archivo de output

    destino = orq.mover_outputs(tmp_path, extractor_dir, loader_dir, fecha="2026_08_22")
    assert destino.exists()
    assert "se omite" in capsys.readouterr().out


def test_mover_outputs_segunda_corrida_del_mismo_dia(tmp_path):
    extractor_dir, loader_dir = _armar_modulos_con_output(tmp_path)
    # Simula que ya hubo una corrida ese dia (carpeta de fecha ya existe).
    (tmp_path / "outputs_diarios" / "2026_08_22").mkdir(parents=True)

    destino = orq.mover_outputs(tmp_path, extractor_dir, loader_dir, fecha="2026_08_22")
    assert destino == tmp_path / "outputs_diarios" / "2026_08_22" / "corrida_2"
    assert (destino / "extractor-CLIENT_NAME" / "comprobantes.csv").exists()


# ============================================================================
# ejecutar_modulo / ejecutar_con_reintentos (subprocess real contra dummy)
# ============================================================================
def test_ejecutar_modulo_exito(dummy_module, monkeypatch):
    monkeypatch.setenv("DUMMY_EXIT_CODE", "0")
    codigo = orq.ejecutar_modulo("dummy", dummy_module, sys.executable)
    assert codigo == 0


def test_ejecutar_modulo_fallo(dummy_module, monkeypatch):
    monkeypatch.setenv("DUMMY_EXIT_CODE", "1")
    codigo = orq.ejecutar_modulo("dummy", dummy_module, sys.executable)
    assert codigo == 1


def test_ejecutar_modulo_extra_env_override(dummy_module):
    codigo = orq.ejecutar_modulo(
        "dummy", dummy_module, sys.executable, extra_env={"DUMMY_EXIT_CODE": "7"}
    )
    assert codigo == 7


def test_ejecutar_con_reintentos_reintenta_y_abandona(dummy_module, monkeypatch):
    respuestas = iter([False])  # el usuario no quiere reintentar tras el primer fallo
    monkeypatch.setattr(orq, "preguntar_si_no", lambda *a, **k: next(respuestas))

    resultado = orq.ejecutar_con_reintentos(
        "dummy", dummy_module, sys.executable, extra_env={"DUMMY_EXIT_CODE": "1"}
    )
    assert resultado is False


def test_ejecutar_con_reintentos_exito_en_segundo_intento(dummy_module, monkeypatch, tmp_path):
    llamadas = {"n": 0}
    codigos = iter([1, 0])

    def fake_ejecutar_modulo(nombre, module_dir, python_exe, extra_env=None):
        llamadas["n"] += 1
        return next(codigos)

    monkeypatch.setattr(orq, "ejecutar_modulo", fake_ejecutar_modulo)
    monkeypatch.setattr(orq, "preguntar_si_no", lambda *a, **k: True)

    resultado = orq.ejecutar_con_reintentos("dummy", dummy_module, sys.executable)
    assert resultado is True
    assert llamadas["n"] == 2


# ============================================================================
# abrir_ids_txt: no debe propagar excepciones si no hay editor disponible
# ============================================================================
def test_abrir_ids_txt_sin_editor_no_rompe(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "platform", "linux")

    def fake_popen(*a, **k):
        raise FileNotFoundError("xdg-open no encontrado")

    monkeypatch.setattr(orq.subprocess, "Popen", fake_popen)

    ids_path = tmp_path / "ids.txt"
    orq.abrir_ids_txt(ids_path)  # no debe lanzar excepcion

    assert ids_path.exists()
    assert "No se pudo abrir" in capsys.readouterr().out


def test_abrir_ids_txt_crea_archivo_si_no_existe(tmp_path, monkeypatch):
    monkeypatch.setattr(orq.subprocess, "Popen", lambda *a, **k: None)
    monkeypatch.setattr(sys, "platform", "linux")

    ids_path = tmp_path / "ids.txt"
    orq.abrir_ids_txt(ids_path)
    assert ids_path.exists()


# ============================================================================
# preguntar_si_no
# ============================================================================
def test_preguntar_si_no_default_con_enter(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert orq.preguntar_si_no("¿Continuar?", default=True) is True
    assert orq.preguntar_si_no("¿Continuar?", default=False) is False


def test_preguntar_si_no_reintenta_ante_respuesta_invalida(monkeypatch):
    respuestas = iter(["tal_vez", "s"])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))
    assert orq.preguntar_si_no("¿Continuar?") is True


# ============================================================================
# smoke test de main() con modulos dummy
# ============================================================================
def test_main_smoke_end_to_end(tmp_path, monkeypatch):
    extractor_dir = tmp_path / "extractor-CLIENT_NAME"
    loader_dir = tmp_path / "loader-CLIENT_NAME"
    (extractor_dir / "output").mkdir(parents=True)
    (extractor_dir / "logs").mkdir(parents=True)
    (loader_dir / "output").mkdir(parents=True)
    (extractor_dir / "main.py").write_text("import sys; sys.exit(0)")
    (loader_dir / "main.py").write_text("import sys; sys.exit(0)")
    # comprobantes.csv generado por el "extractor" dummy
    (extractor_dir / "output" / "comprobantes.csv").write_text("id\n1\n")
    (loader_dir / "output" / "procesados.csv").write_text("id_bpm\n1\n")

    monkeypatch.setattr(orq, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(orq, "EXTRACTOR_DIR", extractor_dir)
    monkeypatch.setattr(orq, "LOADER_DIR", loader_dir)
    monkeypatch.setattr(orq, "IDS_FILE", extractor_dir / "ids.txt")
    monkeypatch.setattr(orq, "verificar_venv", lambda module_dir, nombre: sys.executable)
    monkeypatch.setattr(orq, "abrir_ids_txt", lambda ids_path: ids_path.write_text("111\n"))
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")  # todo default (S)

    codigo = orq.main()

    assert codigo == 0
    fecha = orq.datetime.now().strftime("%Y_%m_%d")
    destino = tmp_path / "outputs_diarios" / fecha
    assert destino.exists()
    assert (destino / "extractor-CLIENT_NAME" / "comprobantes.csv").exists()
    assert (destino / "loader-CLIENT_NAME" / "procesados.csv").exists()
