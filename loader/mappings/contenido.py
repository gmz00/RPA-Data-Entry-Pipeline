# Mapea 'tipo_contenido' del CSV al texto del desplegable
# "Contenido de la factura" en REIM.
# Valores reales que emite el Modulo 1 (portal CLIENT_NAME).

# 1. CSV -> texto REIM en espanol (lo usa el reader via mapear_contenido)
CONTENIDO_FACTURA = {
    "Liquido": "Factura para liquidos",
    "Envase": "Factura para envases",
    "Otros/Mercadería": "Otros (Por defecto)",
}

# 2. Equivalencias ES <-> EN del combo (REIM a veces muestra el combo en ingles).
#    Lo usa crear_factura._seleccionar_combo para elegir el texto correcto.
CONTENIDO_ES_EN = {
    "Otros (Por defecto)": "Others (Default)",
    "Factura para envases": "Invoice for containers",
    "Factura para liquidos": "Invoice for liquids",
}


def mapear_contenido(contenido_csv: str) -> str:
    valor = str(contenido_csv).strip()
    if valor not in CONTENIDO_FACTURA:
        raise ValueError(f"Contenido de factura no soportado: '{contenido_csv}'")
    return CONTENIDO_FACTURA[valor]