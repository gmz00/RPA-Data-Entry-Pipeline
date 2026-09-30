import csv
from models.comprobante import Comprobante, LineaImpuesto
from mappings.impuestos import mapear_impuesto, COLUMNAS_SIN_MAPEO
from mappings.tipo_documento import mapear_tipo_documento
from mappings.contenido import mapear_contenido


def _parse_float(valor: str) -> float:
    """Convierte string del CSV a float. Vacio o invalido -> 0.0"""
    if valor is None:
        return 0.0
    valor = str(valor).strip()
    if valor == "":
        return 0.0
    try:
        return float(valor)
    except ValueError:
        return 0.0


def _construir_lineas_impuesto(fila: dict) -> tuple[list[LineaImpuesto], str]:
    """
    Recorre las columnas de impuesto de la fila.
    Devuelve (lista_lineas, motivo_error).
    motivo_error != "" si hay algo que manda el comprobante a fallidos.
    """
    lineas = []
    motivo_error = ""
    neto_gravado = _parse_float(fila.get("neto_gravado"))

    for columna, valor in fila.items():
        if not columna.startswith("imp_"):
            continue

        monto = _parse_float(valor)
        if monto <= 0:
            continue  # impuesto no presente en esta factura

        # Columna sin mapeo (ej. imp_OTROS con monto > 0) -> fallido
        if columna in COLUMNAS_SIN_MAPEO:
            motivo_error = (
                f"'{columna}' con monto {monto}: impuesto no mapeado, "
                f"revisar manualmente"
            )
            continue

        mapeo = mapear_impuesto(columna)
        if mapeo is None:
            motivo_error = f"Columna de impuesto desconocida: '{columna}'"
            continue

        codigo_reim, tipo = mapeo
        base = neto_gravado if tipo == "IVA" else 0.0
        lineas.append(
            LineaImpuesto(
                codigo_reim=codigo_reim,
                tipo=tipo,
                importe=monto,
                base_imponible=base,
            )
        )

    return lineas, motivo_error


def _construir_comprobante(fila: dict) -> Comprobante:
    """Arma un objeto Comprobante desde una fila del CSV."""
    motivo_error = ""
    estado = "pendiente"

    # --- Mapeos de cabecera (pueden fallar) ---
    try:
        cod_doc_fiscal = mapear_tipo_documento(fila.get("tipo", ""))
    except ValueError as e:
        cod_doc_fiscal = ""
        motivo_error = str(e)

    try:
        contenido = mapear_contenido(fila.get("tipo_contenido", ""))
    except ValueError as e:
        contenido = ""
        if not motivo_error:
            motivo_error = str(e)

    # --- Lineas de impuesto ---
    lineas, motivo_imp = _construir_lineas_impuesto(fila)
    if motivo_imp and not motivo_error:
        motivo_error = motivo_imp

    if motivo_error:
        estado = "fallido"

    comp = Comprobante(
        id_bpm=str(fila.get("id", "")).strip(),
        nombre_proveedor=str(fila.get("emisor", "")).strip(),
        nro_oc=str(fila.get("nro_oc", "")).strip(),
        cod_doc_fiscal=cod_doc_fiscal,
        fecha_documento=str(fila.get("fecha_emision", "")).strip(),
        nro_factura=str(fila.get("nro_comprobante", "")).strip(),
        nro_cae=str(fila.get("cae", "")).strip(),
        venc_cae=str(fila.get("vencimiento_cae", "")).strip(),
        contenido_factura=contenido,
        letra="a",
        importe_total=_parse_float(fila.get("importe_total")),
        neto_gravado=_parse_float(fila.get("neto_gravado")),
        neto_no_gravado=_parse_float(fila.get("no_gravado")),  # CSV: no_gravado
        lineas_impuesto=lineas,
        nro_recepcion=str(fila.get("nro_recepcion", "")).strip(),
        estado=estado,
        motivo_error=motivo_error,
    )
    return comp


def leer_comprobantes(ruta_csv: str) -> list[Comprobante]:
    """Lee el CSV y devuelve una lista de Comprobante."""
    comprobantes = []
    with open(ruta_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            comprobantes.append(_construir_comprobante(fila))
    return comprobantes