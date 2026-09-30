"""
Módulo de scraping con Playwright
Maneja login, navegación y extracción de elementos del portal CLIENT_NAME
"""

import logging
from playwright.sync_api import (
    sync_playwright,
    Page,
    Browser,
    TimeoutError as PlaywrightTimeout,
)
from typing import Optional, Dict
import time

# Importar configuración
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from config.selectors import get_selector

# Configurar logger
logger = logging.getLogger(__name__)


class CLIENT_NAMEScraper:
    """
    Clase principal para interactuar con el portal CLIENT_NAME
    Maneja sesión de Playwright, login y navegación
    """

    def __init__(self, headless: bool = None, slow_mo: int = None):
        """
        Inicializa el scraper

        Args:
            headless: Ejecutar sin ventana visible (None = usar config)
            slow_mo: Milisegundos de delay entre acciones (None = usar config)
        """
        self.headless = headless if headless is not None else settings.HEADLESS
        self.slow_mo = slow_mo if slow_mo is not None else settings.SLOW_MO

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        logger.info(
            f"[INFO] Scraper inicializado (headless={self.headless}, slow_mo={self.slow_mo})"
        )

    def iniciar_navegador(self):
        """Inicia Playwright y abre el navegador"""
        try:
            logger.info("[INFO] Iniciando navegador Chromium...")
            self.playwright = sync_playwright().start()

            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=["--start-maximized"] if not self.headless else [],
            )

            # Crear contexto con viewport amplio
            context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080} if self.headless else None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            self.page = context.new_page()
            self.page.set_default_timeout(settings.TIMEOUT)

            logger.info("[OK] Navegador iniciado correctamente")

        except Exception as e:
            logger.error(f"[ERROR] Error al iniciar navegador: {e}")
            raise

    def login(self, usuario: str = None, password: str = None) -> bool:
        """
        Realiza login en el portal CLIENT_NAME

        Args:
            usuario: Email del usuario (None = usar .env)
            password: Contraseña (None = usar .env)

        Returns:
            bool: True si login exitoso, False en caso contrario
        """
        usuario = usuario or settings.CLIENT_NAME_USER
        password = password or settings.CLIENT_NAME_PASS

        try:
            logger.info(f"[INFO] Intentando login para usuario: {usuario}")

            # Navegar a página de login
            self.page.goto(settings.LOGIN_URL)
            logger.debug(f"Navegando a {settings.LOGIN_URL}")

            # Esperar que cargue el formulario
            self.page.wait_for_selector(
                "input[type='text'], input[type='email']", timeout=10000
            )

            # Llenar formulario (selectores genéricos para email + password)
            email_input = self.page.locator(
                "input[type='text'], input[type='email']"
            ).first
            email_input.fill(usuario)
            logger.debug("[+] Usuario ingresado")

            password_input = self.page.locator("input[type='password']").first
            password_input.fill(password)
            logger.debug("[+] Contrasena ingresada")

            # Hacer clic en botón LOGIN
            btn_login = self.page.locator(
                "button:has-text('LOGIN'), button:has-text('Ingresar')"
            ).first
            btn_login.click()
            logger.debug("[+] Clic en boton LOGIN")

            # Esperar redirección al home (verificar URL o elemento característico)
            try:
                # Opción 1: Esperar URL del home
                self.page.wait_for_url("**/home", timeout=15000)
                logger.info(f"[OK] Login exitoso - Redirigido a {self.page.url}")
                return True

            except PlaywrightTimeout:
                # Opción 2: Si no redirige, verificar que desapareció el formulario de login
                if "login" not in self.page.url.lower():
                    logger.info("[OK] Login exitoso - Sesion iniciada")
                    return True
                else:
                    logger.error(
                        "[ERROR] Login fallo - Credenciales incorrectas o timeout"
                    )
                    # Capturar screenshot para debug
                    self.page.screenshot(path="logs/login_error.png")
                    return False

        except Exception as e:
            logger.error(f"[ERROR] Error durante login: {e}")
            self.page.screenshot(path="logs/login_exception.png")
            return False

    def navegar_a_comprobante(self, id_comprobante: int) -> bool:
        """
        Navega directamente a un comprobante por su ID

        Args:
            id_comprobante: ID del comprobante

        Returns:
            bool: True si navegación exitosa
        """
        url = settings.get_comprobante_url(id_comprobante)

        try:
            logger.info(f"[INFO] Navegando a comprobante {id_comprobante}")
            self.page.goto(
                url, wait_until="domcontentloaded", timeout=15000
            )  # Reducir timeout

            # Verificar si existe o da error 404
            try:
                # Buscar mensaje de error o página vacía
                error_msg = self.page.locator(
                    "text=/no encontr|not found|error 404/i"
                ).first
                if error_msg.is_visible(timeout=2000):
                    logger.error(
                        f"[ERROR] Comprobante {id_comprobante} no existe en el sistema"
                    )
                    return False
            except:
                pass

            # Esperar que cargue algún elemento característico
            selectores_verificacion = [
                "text=CABECERA",
                "text=IMPORTES",
                "input[disabled]",
                "button:has-text('VOLVER')",
            ]

            for selector in selectores_verificacion:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"[OK] Comprobante {id_comprobante} cargado")
                    return True
                except:
                    continue

            # Si ningún selector funcionó
            logger.error(f"[ERROR] Comprobante {id_comprobante} no cargo correctamente")
            return False

        except Exception as e:
            logger.error(f"[ERROR] Error navegando a comprobante {id_comprobante}: {e}")
            return False

    def cambiar_pestana(self, pestana: str) -> bool:
        """
        Cambia a una pestaña específica del comprobante

        Args:
            pestana: "CABECERA", "IMPORTES", "RECEPCIONES", "ADJUNTOS", "HISTORIAL"

        Returns:
            bool: True si cambio exitoso
        """
        try:
            # Usar selector simple por texto
            tab_selector = f"text={pestana}"
            tab = self.page.locator(tab_selector).first

            # Verificar si ya está activa
            try:
                if "active" in (tab.get_attribute("class") or ""):
                    logger.debug(f"Pestaña {pestana} ya está activa")
                    return True
            except:
                pass

            tab.click()
            logger.debug(f"[+] Clic en pestana {pestana}")

            # Esperar a que cargue el contenido
            time.sleep(0.5)

            return True

        except Exception as e:
            logger.error(f"[ERROR] Error al cambiar a pestana {pestana}: {e}")
            return False

    def extraer_texto(self, selector: str, timeout: int = 5000) -> Optional[str]:
        """
        Extrae texto de un elemento usando selector CSS o XPath

        Args:
            selector: Selector CSS o XPath del elemento
            timeout: Milisegundos máximos de espera

        Returns:
            str: Texto extraído o None si no se encuentra
        """
        try:
            # Determinar si es XPath (empieza con //) o CSS
            if selector.startswith("//"):
                element = self.page.locator(f"xpath={selector}").first
            else:
                element = self.page.locator(selector).first

            # Esperar a que el elemento sea visible
            element.wait_for(state="visible", timeout=timeout)

            # Intentar diferentes métodos de extracción
            tag = element.evaluate("el => el.tagName").lower()
            if tag in ["input", "textarea"]:
                valor = element.input_value()
            else:
                valor = element.inner_text()

            return valor.strip() if valor else None

        except PlaywrightTimeout:
            logger.warning(f"[WARN] Timeout esperando elemento: {selector}")
            return None
        except Exception as e:
            logger.warning(f"[WARN] Error extrayendo texto ({selector}): {e}")
            return None

    def extraer_tabla_impuestos(self) -> Dict[str, float]:
        """
        Extrae todos los impuestos de la tabla en pestaña IMPORTES

        Returns:
            dict: {descripcion_impuesto: monto}
        """
        impuestos = {}

        try:
            # Hacer scroll en la tabla para cargar todas las filas
            try:
                tabla = self.page.locator("table tbody").first
                tabla.scroll_into_view_if_needed()
                time.sleep(0.3)
            except:
                pass

            # Selector: filas que tienen descripcion
            filas = self.page.locator("table tbody tr:has(td.text-start)").all()

            logger.debug(f"[IMPUESTOS] Encontradas {len(filas)} filas de impuestos")

            for i, fila in enumerate(filas, 1):
                try:
                    columnas = fila.locator("td").all()

                    if len(columnas) < 4:
                        logger.debug(
                            f"  [!] Fila {i} tiene {len(columnas)} columnas, skip"
                        )
                        continue

                    # Columna 1: Descripcion
                    descripcion = columnas[1].inner_text().strip()

                    # Filtro 1: Ignorar descripciones que sean solo números (códigos internos)
                    if descripcion.isdigit():
                        logger.debug(
                            f"  [!] Fila {i}: descripción numérica '{descripcion}' ignorada"
                        )
                        continue

                    # Filtro 2: Descripción debe tener al menos 3 caracteres
                    if len(descripcion) < 3:
                        logger.debug(
                            f"  [!] Fila {i}: descripción muy corta '{descripcion}' ignorada"
                        )
                        continue

                    # Columna 3: Subtotal (input type="tel")
                    try:
                        input_monto = columnas[3].locator("input[type='tel']").first
                        subtotal_texto = input_monto.input_value()

                        if not subtotal_texto:
                            subtotal_texto = input_monto.get_attribute("value")

                        if not subtotal_texto:
                            subtotal_texto = columnas[3].inner_text().strip()

                    except Exception:
                        # Si no hay input, intentar leer texto directo
                        subtotal_texto = columnas[3].inner_text().strip()

                    # Filtro 3: Si no hay monto válido, skip
                    if not subtotal_texto or subtotal_texto in [
                        "N/A",
                        "",
                        "0",
                        "0.00",
                        "0,00",
                    ]:
                        logger.debug(
                            f"  [!] Fila {i}: '{descripcion}' sin monto válido, skip"
                        )
                        continue

                    subtotal = self._limpiar_monto(subtotal_texto)

                    if subtotal is not None and subtotal > 0:
                        impuestos[descripcion] = subtotal
                        logger.debug(f"  [+] {descripcion}: ${subtotal:,.2f}")
                    else:
                        logger.debug(
                            f"  [!] Fila {i}: {descripcion} = $0.00 (ignorado)"
                        )

                except Exception as e:
                    logger.warning(f"  [!] Error en fila {i}: {e}")
                    continue

            logger.info(f"[IMPUESTOS] Extraidos {len(impuestos)} impuestos")
            return impuestos

        except Exception as e:
            logger.error(f"[ERROR] Extrayendo tabla de impuestos: {e}")
            return {}

    def _limpiar_monto(self, texto: str) -> Optional[float]:
        """
        Convierte string de monto a float
        Maneja múltiples formatos:
        - "584452.79" (formato input)
        - "584.452,79" (formato visual)
        - "$ 584.452,79" (con símbolo)
        """
        try:
            if not texto:
                return 0.0

            # Remover espacios, $, y otros caracteres
            texto = texto.replace("$", "").replace(" ", "").strip()

            # Detectar formato (si tiene coma, es formato argentino)
            if "," in texto:
                # Formato: 584.452,79 → 584452.79
                texto = texto.replace(".", "").replace(",", ".")
            # Si no tiene coma pero tiene punto, verificar posición
            elif "." in texto:
                # Si el punto está 3 posiciones desde el final, es separador de miles
                partes = texto.split(".")
                if len(partes) == 2 and len(partes[1]) == 3:
                    # Formato: 584.452 → 584452
                    texto = texto.replace(".", "")

            return float(texto)

        except ValueError:
            logger.warning(f"[WARN] No se pudo convertir: '{texto}'")
            return None

    def tomar_screenshot(self, nombre: str = "screenshot.png"):
        """Captura screenshot"""
        try:
            ruta = settings.LOGS_DIR / nombre
            self.page.screenshot(path=str(ruta))
            logger.info(f"[INFO] Screenshot guardado: {ruta}")
        except Exception as e:
            logger.error(f"[ERROR] Error screenshot: {e}")

    def cerrar(self):
        """Cierra navegador"""
        try:
            if self.browser:
                self.browser.close()
                logger.info("[INFO] Navegador cerrado")
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"[ERROR] Error cerrando: {e}")


# ============================================================================
# PRUEBA
# ============================================================================
if __name__ == "__main__":
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

        print("[OK] Login OK - Enter para continuar...")
        input()

        # CAMBIAR ESTE ID POR UNO VÁLIDO DE TU LISTA
        id_prueba = 9999999

        if scraper.navegar_a_comprobante(id_prueba):
            print(f"[OK] Comprobante cargado")

            # Probar extracción
            id_comp = scraper.extraer_texto("input[disabled]")
            print(f"[>>] ID: {id_comp}")

            scraper.cambiar_pestana("IMPORTES")
            time.sleep(1)
            impuestos = scraper.extraer_tabla_impuestos()
            print(f"[>>] Impuestos: {len(impuestos)}")
        else:
            print("[ERROR] No se pudo cargar el comprobante")
            print("[INFO] Revisa el screenshot en logs/ para ver que paso")

        print("\n[OK] Enter para cerrar...")
        input()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        scraper.tomar_screenshot("error_general.png")

    finally:
        scraper.cerrar()
