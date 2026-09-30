from dataclasses import dataclass, field


@dataclass
class LineaImpuesto:
    """Una línea del desglose de impuestos en REIM."""
    codigo_reim: str          # string exacto del popup REIM (ej. "PERC_IIBB_BUENOS_AIRES")
    tipo: str                 # "IVA" | "PERCEPCION" | "IMP_INTERNO"
    importe: float
    base_imponible: float = 0.0   # solo aplica a IVA (= neto_gravado)


@dataclass
class Comprobante:
    # --- Cabecera ---
    id_bpm: str
    nombre_proveedor: str
    nro_oc: str
    cod_doc_fiscal: str       # ya mapeado a "001_FACTURAS_A" / "201_..."
    fecha_documento: str      # dd-mm-aaaa
    nro_factura: str
    nro_cae: str
    venc_cae: str             # dd-mm-aaaa
    contenido_factura: str    # ya mapeado al texto del desplegable REIM
    letra: str = "a"

    # --- Importes ---
    importe_total: float = 0.0
    neto_gravado: float = 0.0
    neto_no_gravado: float = 0.0

    # --- Impuestos ---
    lineas_impuesto: list[LineaImpuesto] = field(default_factory=list)

    # --- Recepción (informativo; la confrontación es manual) ---
    nro_recepcion: str = ""

    # --- Control ---
    estado: str = "pendiente"     # pendiente | procesado | fallido
    motivo_error: str = ""

    def suma_impuestos(self) -> float:
        return sum(l.importe for l in self.lineas_impuesto)

    def total_calculado(self) -> float:
        return round(self.neto_gravado + self.neto_no_gravado + self.suma_impuestos(), 2)

    def diferencia_total(self) -> float:
        return round(self.total_calculado() - self.importe_total, 2)