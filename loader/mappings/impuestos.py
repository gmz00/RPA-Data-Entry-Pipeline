# Traduce la DESCRIPCION del portal CLIENT_NAME (columnas del CSV)
# al texto EXACTO que aparece en los popups de Oracle REIM.
#
# Formato: "columna_csv": ("codigo_reim_exacto", "categoria")
#
# categoria indica en que popup de REIM se agrega el impuesto:
#   "IVA"         -> popup "Agregar codigo de impuestos"
#   "PERCEPCION"  -> popup "Agregar codigo de percepcion"
#   "IMP_INTERNO" -> popup "Agregar codigo de impuestos internos"
#
# El codigo_reim DEBE coincidir EXACTO con la columna "Descripcion"
# del popup de REIM (la seleccion se hace por texto).

MAPEO_IMPUESTOS = {
    # ---------- IVA ----------
    "imp_IVA_21":   ("IVA_21.00_BIENES", "IVA"),
    "imp_IVA_10_5": ("IVA_10.50_BIENES", "IVA"),

    # ---------- Percepciones IIBB (IIB001-IIB024) ----------
    "imp_PERC_IIBB_CABA":        ("PERC_IIBB_CABA", "PERCEPCION"),              # IIB002
    "imp_PERC_IIBB_BA":          ("PERC_IIBB_BUENOS_AIRES", "PERCEPCION"),      # IIB001
    "imp_PERC_IIBB_CATAMARCA":   ("PERC_IIBB_CATAMARCA", "PERCEPCION"),         # IIB003
    "imp_PERC_IIBB_CHACO":       ("PERC_IIBB_CHACO", "PERCEPCION"),             # IIB005
    "imp_PERC_IIBB_CHUBUT":      ("PERC_IIBB_CHUBUT", "PERCEPCION"),            # IIB006
    "imp_PERC_IIBB_CORDOBA":     ("PERC_IIBB_CORDOBA", "PERCEPCION"),           # IIB004
    "imp_PERC_IIBB_CORRIENTES":  ("PERC_IIBB_CORRIENTES", "PERCEPCION"),        # IIB007
    "imp_PERC_IIBB_ENTRE_RIOS":  ("PERC_IIBB_ENTRE_RIOS", "PERCEPCION"),        # IIB008
    "imp_PERC_IIBB_FORMOSA":     ("PERC_IIBB_FORMOSA", "PERCEPCION"),           # IIB009
    "imp_PERC_IIBB_JUJUY":       ("PERC_IIBB_JUJUY", "PERCEPCION"),             # IIB010
    "imp_PERC_IIBB_LA_PAMPA":    ("PERC_IIBB_LA_PAMPA", "PERCEPCION"),          # IIB011
    "imp_PERC_IIBB_LA_RIOJA":    ("PERC_IIBB_LA_RIOJA", "PERCEPCION"),          # IIB012
    "imp_PERC_IIBB_MENDOZA":     ("PERC_IIBB_MENDOZA", "PERCEPCION"),           # IIB013
    "imp_PERC_IIBB_MISIONES":    ("PERC_IIBB_MISIONES", "PERCEPCION"),          # IIB014
    "imp_PERC_IIBB_NEUQUEN":     ("PERC_IIBB_NEUQUEN", "PERCEPCION"),           # IIB015
    "imp_PERC_IIBB_RIO_NEGRO":   ("PERC_IIBB_RIO_NEGRO", "PERCEPCION"),         # IIB016
    "imp_PERC_IIBB_SALTA":       ("PERC_IIBB_SALTA", "PERCEPCION"),             # IIB017
    "imp_PERC_IIBB_SAN_JUAN":    ("PERC_IIBB_SAN_JUAN", "PERCEPCION"),          # IIB018
    "imp_PERC_IIBB_SAN_LUIS":    ("PERC_IIBB_SAN_LUIS", "PERCEPCION"),          # IIB019
    "imp_PERC_IIBB_SANTA_CRUZ":  ("PERC_IIBB_SANTA_CRUZ", "PERCEPCION"),        # IIB020
    "imp_PERC_IIBB_SANTA_FE":    ("PERC_IIBB_SANTA_FE", "PERCEPCION"),          # IIB021
    "imp_PERC_IIBB_SGO_ESTERO":  ("PERC_IIBB_SANTIAGO_ESTERO", "PERCEPCION"),   # IIB022
    "imp_PERC_IIBB_TDF":         ("PERC_IIBB_TIERRA_DEL_FUEGO", "PERCEPCION"),  # IIB023
    "imp_PERC_IIBB_TUCUMAN":     ("PERC_IIBB_TUCUMAN", "PERCEPCION"),           # IIB024

    # ---------- Percepcion IVA (IVA001) ----------
    "imp_PERC_IVA_RG5329":       ("PERC_IVA_GENERAL", "PERCEPCION"),            # RG5329 = PERC_IVA_GENERAL

    # ---------- Percepciones TSH (TSH001-TSH010) ----------
    "imp_TSH_SALTA":             ("PERC_TSH_SALTA", "PERCEPCION"),              # TSH001
    "imp_TSH_TUCUMAN_TEM":       ("PERC_TSH_TUCUMAN_TEM", "PERCEPCION"),        # TSH002
    "imp_TSH_TUCUMAN_TPP":       ("PERC_TSH_TUCUMAN_TPP", "PERCEPCION"),        # TSH003
    "imp_TSH_CORRIENTES":        ("PERC_TSH_CORRIENTES", "PERCEPCION"),         # TSH004
    "imp_TSH_COMODORO":          ("PERC_TSH_COMODORO", "PERCEPCION"),           # TSH005
    "imp_TSH_CATAMARCA":         ("PERC_TSH_CATAMARCA", "PERCEPCION"),          # TSH006
    "imp_TSH_CORDOBA":           ("PERC_TSH_CORDOBA", "PERCEPCION"),            # TSH007
    "imp_TSH_LA_PLATA":          ("PERC_TSH_LA_PLATA", "PERCEPCION"),           # TSH008
    "imp_TSH_POSADAS":           ("PERC_TSH_POSADAS", "PERCEPCION"),            # TSH009
    "imp_TSH_GENERICA":          ("PERC_TSH_GENERICA", "PERCEPCION"),           # TSH010

    # ---------- Impuesto Interno (IIL000) ----------
    "imp_INTERNO_LOCAL":         ("IMPUESTO_INTERNO_LOCAL", "IMP_INTERNO"),
}

# Columnas del CSV que NO se mapean a un impuesto de REIM.
# Si 'imp_OTROS' viene con monto > 0, el comprobante va a fallidos.csv.
COLUMNAS_SIN_MAPEO = ["imp_OTROS"]


def mapear_impuesto(columna_csv: str):
    """Devuelve (codigo_reim, categoria) o None si la columna no mapea."""
    return MAPEO_IMPUESTOS.get(columna_csv)