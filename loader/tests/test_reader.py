import os
import tempfile
from reader.csv_reader import leer_comprobantes
from mappings.impuestos import MAPEO_IMPUESTOS


# ---------- Construccion del CSV de prueba ----------

def _build_header():
    cabecera = ["id", "emisor", "tipo", "nro_comprobante", "fecha_emision",
                "cae", "vencimiento_cae", "tipo_contenido"]
    importes = ["neto_gravado", "no_gravado", "importe_total"]
    impuestos = list(MAPEO_IMPUESTOS.keys()) + ["imp_OTROS"]
    control = ["nro_recepcion", "nro_oc", "estado_extraccion", "motivo_error"]
    return cabecera + importes + impuestos + control


COLUMNAS = _build_header()
HEADER = ",".join(COLUMNAS)


def _fila_ok():
    """Genera la fila del comprobante 2094025 alineada al header dinamico."""
    d = {c: "0" for c in COLUMNAS}
    d.update({
        "id": "2094025",
        "emisor": "EMBOTELLADORA DEL ATLANTICO",
        "tipo": "001",
        "nro_comprobante": "4104-00106331",
        "fecha_emision": "17-07-2026",
        "cae": "86294222971151",
        "vencimiento_cae": "27-07-2026",
        "tipo_contenido": "Liquido",
        "neto_gravado": "14570688.89",
        "no_gravado": "0.0",
        "importe_total": "19358580.57",
        "imp_IVA_21": "3059844.69",
        "imp_PERC_IIBB_BA": "277135.3",
        "imp_PERC_IIBB_CORDOBA": "39590.76",
        "imp_PERC_IIBB_MENDOZA": "145706.89",
        "imp_INTERNO_LOCAL": "1265614.04",
        "imp_OTROS": "0",
        "nro_recepcion": "650156",
        "nro_oc": "39530000869",
        "estado_extraccion": "OK",
        "motivo_error": "",
    })
    return ",".join(d[c] for c in COLUMNAS)


FILA_OK = _fila_ok()


def _fila(**overrides):
    """Genera una fila basada en FILA_OK con los campos indicados sobreescritos."""
    d = dict(zip(COLUMNAS, FILA_OK.split(",")))
    d.update(overrides)
    return ",".join(d[c] for c in COLUMNAS)


def _crear_csv_temporal(filas):
    fd, ruta = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(HEADER + "\n")
        for fila in filas:
            f.write(fila + "\n")
    return ruta


# ---------- Guardarrail de consistencia ----------

def test_fila_ok_tiene_columnas_correctas():
    """HEADER y FILA_OK deben tener la misma cantidad de columnas."""
    assert len(HEADER.split(",")) == len(FILA_OK.split(",")), (
        f"Header tiene {len(HEADER.split(','))} cols, "
        f"FILA_OK tiene {len(FILA_OK.split(','))}"
    )


# ---------- CASO FELIZ ----------

def test_lee_comprobante_ok():
    ruta = _crear_csv_temporal([FILA_OK])
    comps = leer_comprobantes(ruta)
    os.remove(ruta)

    assert len(comps) == 1
    c = comps[0]
    assert c.estado == "pendiente"
    assert c.motivo_error == ""
    assert c.id_bpm == "2094025"
    assert c.nombre_proveedor == "EMBOTELLADORA DEL ATLANTICO"
    assert c.nro_oc == "39530000869"
    assert c.cod_doc_fiscal == "001_FACTURAS_A"
    assert c.contenido_factura == "Factura para liquidos"
    assert c.nro_factura == "4104-00106331"
    assert c.letra == "a"
    assert c.importe_total == 19358580.57
    assert c.neto_gravado == 14570688.89
    assert c.neto_no_gravado == 0.0


def test_lineas_impuesto_ok():
    ruta = _crear_csv_temporal([FILA_OK])
    c = leer_comprobantes(ruta)[0]
    os.remove(ruta)

    # Debe haber exactamente 5 lineas: IVA21, BA, Cordoba, Mendoza, Interno
    assert len(c.lineas_impuesto) == 5

    codigos = {l.codigo_reim for l in c.lineas_impuesto}
    assert codigos == {
        "IVA_21.00_BIENES",
        "PERC_IIBB_BUENOS_AIRES",
        "PERC_IIBB_CORDOBA",
        "PERC_IIBB_MENDOZA",
        "IMPUESTO_INTERNO_LOCAL",
    }

    # El IVA debe tener base imponible = neto gravado
    iva = next(l for l in c.lineas_impuesto if l.tipo == "IVA")
    assert iva.base_imponible == 14570688.89
    assert iva.importe == 3059844.69

    # Las percepciones NO tienen base imponible
    perc = [l for l in c.lineas_impuesto if l.tipo == "PERCEPCION"]
    assert all(l.base_imponible == 0.0 for l in perc)


def test_cuadratura_ok():
    ruta = _crear_csv_temporal([FILA_OK])
    c = leer_comprobantes(ruta)[0]
    os.remove(ruta)
    # El comprobante 2094025 cuadra exacto
    assert c.diferencia_total() == 0.0


# ---------- CASOS FALLIDOS ----------

def test_imp_otros_va_a_fallido():
    fila = _fila(imp_OTROS="150.00")
    ruta = _crear_csv_temporal([fila])
    c = leer_comprobantes(ruta)[0]
    os.remove(ruta)

    assert c.estado == "fallido"
    assert "imp_OTROS" in c.motivo_error


def test_tipo_documento_invalido_va_a_fallido():
    fila = _fila(tipo="999")
    ruta = _crear_csv_temporal([fila])
    c = leer_comprobantes(ruta)[0]
    os.remove(ruta)

    assert c.estado == "fallido"
    assert "Tipo de documento no soportado" in c.motivo_error


def test_contenido_invalido_va_a_fallido():
    fila = _fila(tipo_contenido="Gaseoso")
    ruta = _crear_csv_temporal([fila])
    c = leer_comprobantes(ruta)[0]
    os.remove(ruta)

    assert c.estado == "fallido"
    assert "Contenido de factura no soportado" in c.motivo_error


# ---------- MULTIPLES FILAS ----------

def test_multiples_comprobantes():
    fila2 = _fila(id="2094026", nro_comprobante="4104-00106332")
    ruta = _crear_csv_temporal([FILA_OK, fila2])
    comps = leer_comprobantes(ruta)
    os.remove(ruta)

    assert len(comps) == 2
    assert comps[0].id_bpm == "2094025"
    assert comps[1].id_bpm == "2094026"
