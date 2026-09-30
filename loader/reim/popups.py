from playwright.sync_api import Page


def cerrar_popup_error_si_existe(page: Page) -> bool:
    """
    Detecta el popup 'Error / Se ha producido un error' (bug intermitente
    de REIM) y lo cierra. Intenta Aceptar, luego Esc. Factura intacta.
    """
    try:
        popup = page.get_by_text("Se ha producido un error", exact=False)
        if popup.count() > 0 and popup.first.is_visible():
            # Intento 1: boton Aceptar del popup
            try:
                page.get_by_role("button", name="Aceptar").first.click(timeout=2000)
                page.wait_for_timeout(500)
                return True
            except Exception:
                pass
            # Intento 2: Escape
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return True
    except Exception:
        pass
    return False