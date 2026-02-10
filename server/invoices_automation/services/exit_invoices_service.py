from typing import Optional
from playwright.sync_api._generated import Page

from . import BaseServiceManager
from core.settings import COMPANY_CNPJ, COMPANY_USERNAME
from invoices_automation.utils.page_coordinates import ExitInvoicePageCoordinates

# Tipos de Notas de Saídas
# 1. Transferencia de estoque
# 2. Venda comum (dentro do Estado)
# 3. Venda comum (fora do Estado)
# 4. Venda triangular  -  ANA NÃO SABE


class ExitInvoiceService(BaseServiceManager, ExitInvoicePageCoordinates):
    """Service class for automating exit invoice processing.

    Handles the automation of exit invoices (Notas Fiscais de Saída) in the system.
    """

    name = "SAÍDA - Venda comum (dentro do Estado)"

    def __init__(
        self,
        provider: str,
        materials: list[dict],
        job_id: str,
        current_iter: str = "",
        **kwargs,
    ) -> None:
        """Initialize Exit Invoices Automation.

        Args:
            provider (str): Provider name.
            materials (list[dict]): List of materials with their details.
            job_id (str): Unique job identifier.
            current_iter (str, optional): Current iteration in batch processing. Defaults to "".
        """
        super().__init__(job_id=job_id, current_iter=current_iter)
        self.provider = provider
        self.materials = materials

    # TODO: REMOVE HEADFUL
    def run(self, headless: bool = False, devtools: bool = True) -> Optional[str]:
        """Run the exit invoice automation process (Common Sale - Within State).

        Args:
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
            devtools (bool, optional): Whether to open devtools. Defaults to True.

        Returns:
            Optional[str]: Path to the generated invoice PDF if successful, None otherwise.
        """
        try:
            self.logger.info(
                f"Iniciando {self.name} '{self.current_iter}'. NF: {self.provider}\n\t" f"- CONTA: {COMPANY_USERNAME}\n"
            )
            with self.start_navigation(headless=headless, devtools=devtools) as _page:
                self.check_cancelled()
                page: Page = _page
                ticker_sel = page.locator("input[name='Password']")
                ticker_sel.fill(COMPANY_CNPJ)
                self.check_cancelled()
                self._sleep_between_actions()
                with page.context.expect_page() as logged_page_event:
                    self.logger.info(f"Inicializando CNPJ {self.company_name}.")
                    page.locator("#buttonLogOn").click()
                    self.check_cancelled()
                    self._sleep_between_actions(seconds=15)

                # Capturing new tab
                logged_page = logged_page_event.value
                logged_page.wait_for_load_state("load", timeout=60000)
                self.check_cancelled()
                self._sleep_between_actions()
                ...
        except RuntimeError as e:
            self.logger.warning(str(e))
        except Exception as e:
            self.check_cancelled()
            self.logger.warning(str(e))

        finally:
            ...
