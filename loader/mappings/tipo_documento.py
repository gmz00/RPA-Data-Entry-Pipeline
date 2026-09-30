# Mapea el campo 'tipo' del CSV al string exacto del desplegable
# "Código de documento fiscal" en REIM.
# Solo interesan 001 y 201 [1].

TIPO_DOCUMENTO = {
    "001": "001_FACTURAS_A",
    "201": "201_FACTURA_DE_CREDITO_ELECTRONICA_MIPYMES_(FCE)_A",
}


def mapear_tipo_documento(tipo_csv: str) -> str:
    tipo = str(tipo_csv).strip()
    if tipo not in TIPO_DOCUMENTO:
        raise ValueError(f"Tipo de documento no soportado: '{tipo_csv}'")
    return TIPO_DOCUMENTO[tipo]