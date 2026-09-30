"""
Selectores CSS/XPath para extracción de datos del portal CLIENT_NAME
Organizados por pestaña del comprobante
"""

# ============================================================================
# PESTAÑA: CABECERA
# ============================================================================
CABECERA = {
    # ID del comprobante (URL también lo tiene como parámetro)
    "id": {
        "primary": "input[type='text'][disabled]",  # Primer input deshabilitado
        "fallback": "//label[contains(text(),'ID')]/following::input[1]",  # XPath
    },
    # Emisor (proveedor)
    "emisor": {
        "primary": "input[type='text'][disabled]:nth-of-type(2)",
        "attribute": "value",  # Leer atributo value si es readonly
    },
    # Tipo de comprobante (ej: 001 - FC A)
    "tipo": {
        "primary": "//label[contains(text(),'Tipo')]/following::input[1]",
        "fallback": "input[value*='FC']",
    },
    # Número de comprobante (formato: 00751-00000162)
    "nro_comprobante": {
        "primary": "//label[contains(text(),'Número Comprobante')]/following::input[1]",
    },
    # Fecha de emisión
    "fecha_emision": {
        "primary": "input[type='date'], input[placeholder*='DD-MM-YYYY']",
        "index": 0,  # Primera fecha que aparece
    },
    # CAE
    "cae": {
        "primary": "//label[contains(text(),'CAE')]/following::input[1]",
        "fallback": "input[value*='862']",  # CAE suele empezar con dígitos largos
    },
    # Vencimiento CAE
    "vencimiento_cae": {
        "primary": "//label[contains(text(),'Vencimiento CAE')]/following::input[1]",
        "fallback": "input[type='date']:nth-of-type(2)",
    },
    # Contenido de Factura (Envase/Líquido/Otros)
    "tipo_contenido": {
        "primary": "//label[contains(text(),'Contenido de Factura')]/following::input[1]",
        "fallback": "input[value*='Factura para']",
    },
}

# ============================================================================
# PESTAÑA: IMPORTES
# ============================================================================
IMPORTES = {
    # Montos principales
    "neto_gravado": {
        "primary": "//label[contains(text(),'Neto Gravado')]/following::input[1]",
    },
    "no_gravado": {
        "primary": "//label[contains(text(),'No Gravado')]/following::input[1]",
    },
    "importe_total": {
        "primary": "//label[contains(text(),'Importe Total')]/following::input[1]",
    },
    # Tabla de impuestos
    "tabla_impuestos": {
        "container": "table tbody",  # Contenedor de la tabla
        "filas": "tr",  # Cada fila de impuesto
        "descripcion": "td.text-start",  # Columna descripción (ej: "IVA 21")
        "subtotal": "td:last-child",  # Última columna (monto)
    },
}

# ============================================================================
# PESTAÑA: RECEPCIONES
# ============================================================================
RECEPCIONES = {
    "nro_recepcion": {
        "primary": "//label[contains(text(),'Nro Recepción Prima')]/following::input[1]",
    },
    "nro_oc": {
        "primary": "//label[contains(text(),'Nro OC Prima')]/following::input[1]",
    },
}

# ============================================================================
# NAVEGACIÓN Y PESTAÑAS
# ============================================================================
NAVEGACION = {
    # Tabs del comprobante
    "tab_cabecera": "//div[contains(text(),'CABECERA')]",
    "tab_importes": "//div[contains(text(),'IMPORTES')]",
    "tab_recepciones": "//div[contains(text(),'RECEPCIONES')]",
    # Botón volver
    "btn_volver": "button:has-text('VOLVER')",
}

# ============================================================================
# MAPEO DE IMPUESTOS: Descripción CLIENT_NAME → Columna CSV
# ============================================================================
IMPUESTO_MAP = {
    # IVA
    "IVA 21": "imp_IVA_21",
    "IVA 10.5": "imp_IVA_10_5",
    # Percepciones IIBB (sin prefijo "AP")
    "Perc IIBB CABA": "imp_PERC_IIBB_CABA",
    "Perc IIBB Buenos Aires": "imp_PERC_IIBB_BA",
    "Perc IIBB Cordoba": "imp_PERC_IIBB_CORDOBA",
    "Perc IIBB Corrientes": "imp_PERC_IIBB_CORRIENTES",
    # Percepciones IIBB (con prefijo "AP")
    "AP Perc IIBB Catamarca": "imp_PERC_IIBB_CATAMARCA",
    "AP Perc IIBB Chaco": "imp_PERC_IIBB_CHACO",
    "AP Perc IIBB Chubut": "imp_PERC_IIBB_CHUBUT",
    "AP Perc IIBB Entre Rios": "imp_PERC_IIBB_ENTRE_RIOS",
    "AP Perc IIBB Formosa": "imp_PERC_IIBB_FORMOSA",
    "AP Perc IIBB Jujuy": "imp_PERC_IIBB_JUJUY",
    "AP Perc IIBB La Pampa": "imp_PERC_IIBB_LA_PAMPA",
    "AP Perc IIBB La Rioja": "imp_PERC_IIBB_LA_RIOJA",
    "AP Perc IIBB Mendoza": "imp_PERC_IIBB_MENDOZA",
    "AP Perc IIBB Misiones": "imp_PERC_IIBB_MISIONES",
    "AP Perc IIBB Neuquen": "imp_PERC_IIBB_NEUQUEN",
    "AP Perc IIBB Río Negro": "imp_PERC_IIBB_RIO_NEGRO",
    "AP Perc IIBB Salta": "imp_PERC_IIBB_SALTA",
    "AP Perc IIBB San Juan": "imp_PERC_IIBB_SAN_JUAN",
    "AP Perc IIBB San Luis": "imp_PERC_IIBB_SAN_LUIS",
    "AP Perc IIBB Santa Cruz": "imp_PERC_IIBB_SANTA_CRUZ",
    "AP Perc IIBB Santa Fe": "imp_PERC_IIBB_SANTA_FE",
    "AP Perc IIBB Santiago Estero": "imp_PERC_IIBB_SGO_ESTERO",
    "AP Perc IIBB Tierra del Fuego": "imp_PERC_IIBB_TDF",
    "AP Perc IIBB Tucuman": "imp_PERC_IIBB_TUCUMAN",
    # Tasas de Seguridad e Higiene
    "AP Perc TSH Salta": "imp_TSH_SALTA",  # NUEVO - faltaba
    "AP Perc TSH La Plata": "imp_TSH_LA_PLATA",
    "AP Perc TSH Tucuman TEM": "imp_TSH_TUCUMAN_TEM",
    "AP Perc TSH Tucuman TPP": "imp_TSH_TUCUMAN_TPP",
    "AP Perc TSH Corrientes": "imp_TSH_CORRIENTES",
    "AP Perc TSH Comodoro": "imp_TSH_COMODORO",
    "AP Perc TSH Catamarca": "imp_TSH_CATAMARCA",
    "AP Perc TSH Cordoba": "imp_TSH_CORDOBA",
    "AP Perc TSH Posadas": "imp_TSH_POSADAS",
    "PERC_TSH_GENERICA": "imp_TSH_GENERICA",
    # Otros impuestos
    "IMPUESTO INTERNO LOCAL": "imp_INTERNO_LOCAL",
    "PERC IVA RG 5329/2023": "imp_PERC_IVA_RG5329",
    "Perc IVA": "imp_PERC_IVA_RG5329",
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def get_selector(seccion: str, campo: str, tipo: str = "primary") -> str:
    """
    Retorna el selector CSS/XPath de un campo específico

    Args:
        seccion: "CABECERA", "IMPORTES", "RECEPCIONES", "NAVEGACION"
        campo: Nombre del campo (ej: "id", "emisor", "neto_gravado")
        tipo: "primary" o "fallback"

    Returns:
        str: Selector CSS o XPath

    Ejemplo:
        >>> get_selector("CABECERA", "id")
        "input[type='text'][disabled]"
    """
    secciones = {
        "CABECERA": CABECERA,
        "IMPORTES": IMPORTES,
        "RECEPCIONES": RECEPCIONES,
        "NAVEGACION": NAVEGACION,
    }

    if seccion not in secciones:
        raise ValueError(f"Sección inválida: {seccion}")

    campo_config = secciones[seccion].get(campo)
    if not campo_config:
        raise ValueError(f"Campo '{campo}' no existe en {seccion}")

    # Si es string directo, retornar
    if isinstance(campo_config, str):
        return campo_config

    # Si es dict, retornar el tipo solicitado
    return campo_config.get(tipo, campo_config.get("primary"))


def mapear_impuesto(descripcion_CLIENT_NAME: str) -> str:
    """
    Mapea una descripción de impuesto del portal CLIENT_NAME a columna CSV

    Args:
        descripcion_CLIENT_NAME: Texto exacto de la columna "Descripción" (ej: "IVA 21")

    Returns:
        str: Nombre de la columna CSV (ej: "imp_IVA_21") o None si no está mapeado

    Ejemplo:
        >>> mapear_impuesto("IVA 21")
        "imp_IVA_21"
        >>> mapear_impuesto("Impuesto Desconocido")
        None
    """
    return IMPUESTO_MAP.get(descripcion_CLIENT_NAME.strip())
