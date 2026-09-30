"""
Modulo de extraccion de datos del portal CLIENT_NAME
"""

import logging
from typing import Dict, Optional, Any
import re
import time

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import settings

logger = logging.getLogger(__name__)


class CLIENT_NAMEExtractor:
    """Extractor de datos del portal CLIENT_NAME"""

    def __init__(self, scraper):
        self.scraper = scraper
        logger.debug("[EXTRACTOR] Inicializado")

    def extraer_campo_autocomplete(self, label_texto: str) -> Optional[str]:
        """
        Extrae valor de campo autocomplete (emisor, tipo)
        Abre dropdown y lee item seleccionado
        """
        try:
            # Buscar label
            label = self.scraper.page.locator(f"label:has-text('{label_texto}')").first
            parent = label.locator("xpath=..")

            # Buscar input
            input_elem = parent.locator("input[type='text']").first

            # Abrir dropdown
            input_elem.click()
            time.sleep(0.3)

            # Buscar item activo
            item_activo = self.scraper.page.locator(
                "div.v-list-item--active div.v-list-item__title"
            ).first
            item_activo.wait_for(state="visible", timeout=3000)
            valor = item_activo.inner_text()

            # Cerrar dropdown
            self.scraper.page.keyboard.press("Escape")
            time.sleep(0.2)

            return valor.strip() if valor else None

        except Exception as e:
            logger.debug(f"[EXTRACTOR] Error en autocomplete '{label_texto}': {e}")
            try:
                self.scraper.page.keyboard.press("Escape")
            except:
                pass
            return None

    def extraer_cabecera(self) -> Dict[str, Any]:
        """Extrae datos de CABECERA"""
        logger.info("[CABECERA] Iniciando extraccion...")
        datos = {}

        try:
            self.scraper.cambiar_pestana("CABECERA")
            time.sleep(0.5)  # Esperar carga completa

            # ID
            id_valor = self.scraper.extraer_texto("input[disabled]", timeout=3000)
            datos["id"] = int(id_valor) if id_valor else None
            logger.debug(f"  [+] ID: {datos['id']}")

            # EMISOR
            try:
                # Buscar input readonly que contenga CUIT (formato XX-XXXXXXXX-X)
                emisor_valor = self.scraper.page.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input[readonly], input[type="text"]');
                        for (const input of inputs) {
                            if (input.value && /^\d{2}-\d{8}-\d/.test(input.value)) {
                                return input.value;
                            }
                        }
                        return null;
                    }
                """)

                if emisor_valor and " - " in emisor_valor:
                    # Formato: "30-52913594-3 - EMBOTELLADORA DEL ATLANTICO"
                    partes = emisor_valor.split(" - ", 1)
                    datos["emisor"] = (
                        partes[1].strip() if len(partes) > 1 else emisor_valor
                    )
                else:
                    # Fallback: intentar autocomplete
                    try:
                        emisor_completo = self.extraer_campo_autocomplete("Emisor")
                        if emisor_completo and " - " in emisor_completo:
                            partes = emisor_completo.split(" - ", 1)
                            datos["emisor"] = partes[1].strip()
                        else:
                            datos["emisor"] = emisor_completo
                    except:
                        datos["emisor"] = None

            except Exception as e:
                logger.warning(f"  [!] Error extrayendo emisor: {e}")
                datos["emisor"] = None

            logger.debug(
                f"  [+] Emisor: {datos['emisor'][:50] if datos['emisor'] else 'None'}..."
            )

            # TIPO
            try:
                time.sleep(2)

                tipo_valor = self.scraper.page.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input[type="text"]');
                        for (const input of inputs) {
                            if (input.value && /^\\d{3}\\s*-\\s*[A-Z]{2}/.test(input.value)) {
                                return input.value;
                            }
                        }
                        return null;
                    }
                """)

                if tipo_valor:
                    match = re.match(r"^(\d{3})", tipo_valor)
                    datos["tipo"] = match.group(1) if match else tipo_valor
                else:
                    datos["tipo"] = None

            except Exception as e:
                logger.warning(f"  [!] Error extrayendo tipo: {e}")
                datos["tipo"] = None

            logger.debug(f"  [+] Tipo: {datos['tipo']}")

            # NRO COMPROBANTE (regex corregido)
            try:
                nro_inputs = self.scraper.page.locator("input[type='text']").all()
                for inp in nro_inputs:
                    valor = inp.input_value()
                    # Formato flexible: 0XXXX-XXXXXXX o XXXXX-XXXXXXXX
                    if valor and re.match(r"^\d{4,5}-\d{7,8}$", valor):
                        datos["nro_comprobante"] = valor
                        break
                else:
                    datos["nro_comprobante"] = None
            except:
                datos["nro_comprobante"] = None

            logger.debug(f"  [+] Nro Comprobante: {datos['nro_comprobante']}")

            # FECHAS (buscar por label especifico)
            try:
                # Fecha de emision
                fecha_emision_input = (
                    self.scraper.page.locator("label:has-text('Fecha de emisión')")
                    .locator("..")
                    .locator("input")
                    .first
                )
                fecha_emision_val = fecha_emision_input.input_value()
                datos["fecha_emision"] = (
                    self._formatear_fecha(fecha_emision_val)
                    if fecha_emision_val
                    else None
                )

                # Vencimiento CAE
                venc_cae_input = (
                    self.scraper.page.locator("label:has-text('Vencimiento CAE')")
                    .locator("..")
                    .locator("input")
                    .first
                )
                venc_cae_val = venc_cae_input.input_value()
                datos["vencimiento_cae"] = (
                    self._formatear_fecha(venc_cae_val) if venc_cae_val else None
                )
            except:
                datos["fecha_emision"] = None
                datos["vencimiento_cae"] = None

            logger.debug(f"  [+] Fecha emision: {datos['fecha_emision']}")
            logger.debug(f"  [+] Venc CAE: {datos['vencimiento_cae']}")

            # CAE
            try:
                cae_inputs = self.scraper.page.locator("input[type='text']").all()
                for inp in cae_inputs:
                    valor = inp.input_value()
                    if valor and valor.isdigit() and len(valor) >= 12:
                        datos["cae"] = valor
                        break
                else:
                    datos["cae"] = None
            except:
                datos["cae"] = None

            logger.debug(f"  [+] CAE: {datos['cae']}")

            # TIPO CONTENIDO
            try:
                # 1. Intentar leer del dropdown primero
                tipo_contenido_dropdown = self._extraer_tipo_contenido_dropdown()

                if tipo_contenido_dropdown:
                    # Tiene valor en dropdown → usarlo
                    datos["tipo_contenido"] = tipo_contenido_dropdown
                    logger.debug(
                        f"  [+] Tipo contenido (dropdown): {tipo_contenido_dropdown}"
                    )
                else:
                    # 2. No hay dropdown o está vacío → mapear por emisor
                    if datos.get("emisor"):
                        tipo_mapeado = self._mapear_tipo_contenido_por_emisor(
                            datos["emisor"]
                        )
                        datos["tipo_contenido"] = (
                            tipo_mapeado or settings.DEFAULT_TIPO_CONTENIDO
                        )
                        logger.debug(
                            f"  [+] Tipo contenido (por emisor): {datos['tipo_contenido']}"
                        )
                    else:
                        datos["tipo_contenido"] = settings.DEFAULT_TIPO_CONTENIDO

            except Exception as e:
                logger.warning(f"  [!] Error tipo contenido: {e}")
                datos["tipo_contenido"] = settings.DEFAULT_TIPO_CONTENIDO

            logger.debug(f"  [+] Tipo contenido: {datos['tipo_contenido']}")

            logger.info(
                f"[CABECERA] Extraida: {datos['id']} - {datos.get('emisor', 'N/A')[:30]}"
            )
            return datos

        except Exception as e:
            logger.error(f"[ERROR] Extrayendo CABECERA: {e}")
            import traceback

            traceback.print_exc()
            return {
                "id": None,
                "emisor": None,
                "tipo": None,
                "nro_comprobante": None,
                "fecha_emision": None,
                "cae": None,
                "vencimiento_cae": None,
                "tipo_contenido": settings.DEFAULT_TIPO_CONTENIDO,
            }

    def extraer_importes(self) -> Dict[str, Any]:
        """Extrae datos de IMPORTES"""
        logger.info("[IMPORTES] Iniciando extraccion...")
        datos = {
            "neto_gravado": 0.0,
            "no_gravado": 0.0,
            "importe_total": 0.0,
            "impuestos": {},
        }

        try:
            self.scraper.cambiar_pestana("IMPORTES")
            time.sleep(0.5)

            # Buscar inputs por label especifico
            try:
                # Neto Gravado
                neto_input = (
                    self.scraper.page.locator("label:has-text('Neto Gravado')")
                    .locator("..")
                    .locator("..")
                    .locator("input[type='tel']")
                    .first
                )
                neto_val = neto_input.input_value()
                datos["neto_gravado"] = self.scraper._limpiar_monto(neto_val) or 0.0

                # No Gravado
                no_grav_input = (
                    self.scraper.page.locator("label:has-text('No Gravado')")
                    .locator("..")
                    .locator("..")
                    .locator("input[type='tel']")
                    .first
                )
                no_grav_val = no_grav_input.input_value()
                datos["no_gravado"] = self.scraper._limpiar_monto(no_grav_val) or 0.0

                # Importe Total
                total_input = (
                    self.scraper.page.locator("label:has-text('Importe Total')")
                    .locator("..")
                    .locator("..")
                    .locator("input[type='tel']")
                    .first
                )
                total_val = total_input.input_value()
                datos["importe_total"] = self.scraper._limpiar_monto(total_val) or 0.0

            except Exception as e:
                logger.warning(f"  [!] Error extrayendo montos principales: {e}")

            logger.debug(f"  [+] Neto Gravado: ${datos['neto_gravado']:,.2f}")
            logger.debug(f"  [+] No Gravado: ${datos['no_gravado']:,.2f}")
            logger.debug(f"  [+] Importe Total: ${datos['importe_total']:,.2f}")

            # Tabla de impuestos
            datos["impuestos"] = self.scraper.extraer_tabla_impuestos()

            logger.info(
                f"[IMPORTES] Extraidos: Total ${datos['importe_total']:,.2f}, {len(datos['impuestos'])} impuestos"
            )
            return datos

        except Exception as e:
            logger.error(f"[ERROR] Extrayendo IMPORTES: {e}")
            return datos

    def extraer_recepciones(self) -> Dict[str, Any]:
        """
        Extrae Nro Recepcion y Nro OC.
        Intenta lado DERECHO (inputs) primero, luego IZQUIERDO (texto plano).
        """
        logger.info("[RECEPCIONES] Iniciando extraccion...")
        datos = {"nro_recepcion": None, "nro_oc": None}

        try:
            self.scraper.cambiar_pestana("RECEPCIONES")
            time.sleep(1)

            # ===== MÉTODO 1: LADO DERECHO (inputs type='text') =====
            try:
                tabla_inputs = self.scraper.page.locator(
                    "table tbody td input[type='text']"
                ).all()

                valores = []
                for inp in tabla_inputs:
                    valor = inp.input_value()
                    if valor and valor.strip():
                        valores.append(valor.strip())

                if len(valores) >= 2:
                    datos["nro_recepcion"] = valores[0]
                    datos["nro_oc"] = valores[1]
                    logger.debug(
                        f"  [+] (DERECHA) Nro Recepcion: {datos['nro_recepcion']}"
                    )
                    logger.debug(f"  [+] (DERECHA) Nro OC: {datos['nro_oc']}")
                elif len(valores) == 1:
                    datos["nro_recepcion"] = valores[0]
            except Exception as e:
                logger.debug(f"  [!] Error método derecha: {e}")

            # ===== MÉTODO 2: LADO IZQUIERDO (texto plano en td) =====
            # Solo si no encontramos datos en el lado derecho
            if not datos["nro_oc"]:
                try:
                    tablas = self.scraper.page.locator("table").all()

                    for tabla in tablas:
                        filas = tabla.locator("tbody tr").all()

                        for fila in filas:
                            celdas = fila.locator("td").all()

                            if len(celdas) < 2:
                                continue

                            texto_c0 = celdas[0].inner_text().strip()
                            texto_c1 = celdas[1].inner_text().strip()

                            # Saltar tabla de impuestos (tiene "_" o texto tipo "IVA")
                            primer_valor_c0 = texto_c0.split("\n")[0].strip()
                            if not primer_valor_c0.isdigit():
                                continue

                            # Saltar tabla vacía
                            if "no hay datos" in texto_c0.lower():
                                continue

                            # Validar: recepción y OC deben ser numéricos
                            if primer_valor_c0.isdigit() and texto_c1.isdigit():
                                datos["nro_recepcion"] = primer_valor_c0
                                datos["nro_oc"] = texto_c1
                                logger.debug(
                                    f"  [+] (IZQUIERDA) Nro Recepcion: {datos['nro_recepcion']}"
                                )
                                logger.debug(
                                    f"  [+] (IZQUIERDA) Nro OC: {datos['nro_oc']}"
                                )
                                break

                        if datos["nro_oc"]:
                            break
                except Exception as e:
                    logger.debug(f"  [!] Error método izquierda: {e}")

            logger.debug(f"  [FINAL] Nro Recepcion: {datos['nro_recepcion']}")
            logger.debug(f"  [FINAL] Nro OC: {datos['nro_oc']}")

            logger.info("[RECEPCIONES] Extraidas correctamente")
            return datos

        except Exception as e:
            logger.error(f"[ERROR] Extrayendo RECEPCIONES: {e}")
            return datos


    def extraer_todo(self, id_comprobante: int) -> Dict[str, Any]:
        """Extrae todos los datos del comprobante"""
        logger.info(f"[EXTRACTOR] Iniciando extraccion de comprobante {id_comprobante}")

        resultado = {"estado_extraccion": settings.ESTADO_OK, "motivo_error": ""}

        try:
            # Navegar
            if not self.scraper.navegar_a_comprobante(id_comprobante):
                resultado["estado_extraccion"] = settings.ESTADO_ERROR_CABECERA
                resultado["motivo_error"] = "No se pudo cargar el comprobante"
                return resultado

            # CABECERA
            try:
                cabecera = self.extraer_cabecera()
                resultado.update(cabecera)
            except Exception as e:
                logger.error(f"[ERROR] En CABECERA: {e}")
                resultado["estado_extraccion"] = settings.ESTADO_ERROR_CABECERA
                resultado["motivo_error"] = f"Error CABECERA: {str(e)[:100]}"
                return resultado

            # IMPORTES
            try:
                importes = self.extraer_importes()
                resultado["neto_gravado"] = importes["neto_gravado"]
                resultado["no_gravado"] = importes["no_gravado"]
                resultado["importe_total"] = importes["importe_total"]
                resultado["impuestos_raw"] = importes["impuestos"]
            except Exception as e:
                logger.error(f"[ERROR] En IMPORTES: {e}")
                resultado["estado_extraccion"] = settings.ESTADO_ERROR_IMPORTES
                resultado["motivo_error"] = f"Error IMPORTES: {str(e)[:100]}"

            # RECEPCIONES
            try:
                recepciones = self.extraer_recepciones()
                resultado["nro_recepcion"] = recepciones["nro_recepcion"]
                resultado["nro_oc"] = recepciones["nro_oc"]
            except Exception as e:
                logger.error(f"[ERROR] En RECEPCIONES: {e}")
                if resultado["estado_extraccion"] == settings.ESTADO_OK:
                    resultado["estado_extraccion"] = settings.ESTADO_ERROR_RECEPCIONES
                resultado["motivo_error"] += f" | Error RECEPCIONES: {str(e)[:100]}"

            logger.info(f"[EXTRACTOR] Completado: {resultado['estado_extraccion']}")
            return resultado

        except Exception as e:
            logger.error(f"[ERROR] General: {e}")
            resultado["estado_extraccion"] = "ERROR_GENERAL"
            resultado["motivo_error"] = str(e)[:200]
            return resultado

    def _formatear_fecha(self, fecha_input: str) -> Optional[str]:
        """Convierte fecha a formato DD-MM-YYYY"""
        if not fecha_input:
            return None

        try:
            if "-" in fecha_input and len(fecha_input) == 10:
                partes = fecha_input.split("-")
                if len(partes[0]) == 4:
                    return f"{partes[2]}-{partes[1]}-{partes[0]}"
            return fecha_input
        except:
            return fecha_input

    def _mapear_tipo_contenido_por_emisor(self, emisor: str) -> Optional[str]:
        """
        Mapea tipo de contenido según proveedor

        Args:
            emisor: Nombre del proveedor

        Returns:
            "Liquido" o None (usar default)
        """
        emisor_upper = emisor.upper()

        # Proveedores de LÍQUIDO (6 proveedores específicos)
        # En producción, esta lista se alimenta de una variable de entorno o base de dato
        proveedores_liquido = [
            "VENDOR LIQUIDO A",
            "VENDOR LIQUIDO B",
            "VENDOR LIQUIDO C",
            "VENDOR LIQUIDO D",
            "VENDOR LIQUIDO E",
            "VENDOR LIQUIDO F",
            "VENDOR LIQUIDO G",
            "VENDOR LIQUIDO H",
            "VENDOR LIQUIDO I",
        ]

        for keyword in proveedores_liquido:
            if keyword in emisor_upper:
                logger.debug(f"  [MAPEO] '{emisor}' → Liquido (match: {keyword})")
                return "Liquido"

        # Si no matchea ninguno, retornar None (usar default)
        return None

    def _extraer_tipo_contenido_dropdown(self) -> Optional[str]:
        """
        Extrae tipo contenido del dropdown si existe y tiene valor específico

        Returns:
            "Liquido", "Envase" o None (usar mapeo por emisor)
        """
        try:
            contenido_elem = self.scraper.page.locator("div.v-select__selection").first
            contenido_texto = contenido_elem.inner_text(timeout=2000).strip().lower()

            if not contenido_texto or contenido_texto == "":
                return None

            # SOLO retornar valor si es Líquido o Envase (específicos)
            if "liquido" in contenido_texto or "líquido" in contenido_texto:
                logger.debug(f"  [DROPDOWN] Líquido detectado")
                return "Liquido"
            elif "envase" in contenido_texto:
                logger.debug(f"  [DROPDOWN] Envase detectado")
                return "Envase"
            else:
                # "Otros/Mercadería" o cualquier otro valor → tratar como vacío
                logger.debug(
                    f"  [DROPDOWN] Valor genérico '{contenido_texto}' → usar mapeo"
                )
                return None

        except Exception as e:
            logger.debug(f"  [DROPDOWN] No encontrado: {e}")
            return None


# PRUEBA
if __name__ == "__main__":
    import logging
    from scraper import CLIENT_NAMEScraper

    logging.basicConfig(
        level=logging.DEBUG,
        format=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
    )

    scraper = CLIENT_NAMEScraper(headless=False)

    try:
        scraper.iniciar_navegador()

        if not scraper.login():
            print("[ERROR] Login fallo")
            exit(1)

        print("[OK] Login exitoso\n")

        extractor = CLIENT_NAMEExtractor(scraper)

        id_prueba = 9999999  # ID en estado Sup BPO
        datos = extractor.extraer_todo(id_prueba)

        print("\n" + "=" * 60)
        print("RESULTADOS DE LA EXTRACCION")
        print("=" * 60)
        print(f"\n[+] ID: {datos.get('id')}")
        print(f"[+] Emisor: {datos.get('emisor')}")
        print(f"[+] Tipo: {datos.get('tipo')}")
        print(f"[+] Nro: {datos.get('nro_comprobante')}")
        print(f"[+] Emision: {datos.get('fecha_emision')}")
        print(f"[+] CAE: {datos.get('cae')}")
        print(f"[+] Contenido: {datos.get('tipo_contenido')}")

        print(f"\n[+] Neto Gravado: ${datos.get('neto_gravado', 0):,.2f}")
        print(f"[+] No Gravado: ${datos.get('no_gravado', 0):,.2f}")
        print(f"[+] TOTAL: ${datos.get('importe_total', 0):,.2f}")

        print(f"\n[+] Impuestos ({len(datos.get('impuestos_raw', {}))}):")
        for desc, monto in list(datos.get("impuestos_raw", {}).items())[:5]:
            print(f"    - {desc}: ${monto:,.2f}")

        print(f"\n[+] Nro Recepcion: {datos.get('nro_recepcion')}")
        print(f"[+] Nro OC: {datos.get('nro_oc')}")

        print(f"\n[+] Estado: {datos.get('estado_extraccion')}")
        if datos.get("motivo_error"):
            print(f"[!] Error: {datos.get('motivo_error')}")

        print("\n" + "=" * 60)
        print("\n[OK] Prueba completada - Enter para cerrar...")
        input()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback

        traceback.print_exc()

    finally:
        scraper.cerrar()
