from typing import Any, Optional
from playwright.sync_api._generated import Page

from . import BaseServiceManager
from core.settings import COMPANY_CNPJ, COMPANY_USERNAME, COMPANY_PASSWORD
from invoices_automation.utils.page_coordinates import EntryInvoicePageCoordinates


class EntryInvoiceService(BaseServiceManager, EntryInvoicePageCoordinates):
    """Service class for automating entry invoice processing.

    Handles the automation of entry invoices (Notas Fiscais de Entrada) in the system.
    """

    name: str = "ENTRADA"

    def __init__(
        self,
        provider: str,
        materials: list[dict[str, Any]],
        job_id: str,
        current_iter: str = "",
        close_popup_confirmation: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Initialize Entry Invoices Automation.

        Args:
            provider (str): Provider name.
            materials (list[dict]): List of materials with their details.
            job_id (str): Unique job identifier.
            current_iter (str, optional): Current iteration in batch processing. Defaults to "".
        """
        super().__init__(job_id=job_id, current_iter=current_iter)
        self.provider = provider
        self.materials = materials
        self.close_popup_confirmation = close_popup_confirmation

    def run(self, headless: bool = True, devtools: bool = False) -> Optional[str]:
        """Run the Entry Invoices Automation"""
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
                    self._sleep_between_actions(seconds=18)

                # Capturing new tab and going to certified page
                logged_page = logged_page_event.value
                self._navigate_to_certified_area(logged_page, self.coord_home_auth, COMPANY_CNPJ)

                # Set Account
                self.set_account(
                    page_to_use=logged_page,
                    initial_ticker_selection=self.coord_initial_ticker_selection,
                    user_insertion=self.coord_user_insertion,
                    password_insertion=self.coord_password_insertion,
                    log_in_button=self.coord_log_in,
                    username=COMPANY_USERNAME,
                    password=COMPANY_PASSWORD,
                )

                self.logger.info(f"PREPARAÇÃO DA NF {self.name}:")

                self.prepare_options(
                    page_to_use=logged_page,
                    fiscal_tab=self.coord_fiscal_tab,
                    invoice_control=self.coord_invoice_control,
                    register=self.coord_register,
                )

                self.set_provider(
                    page_to_use=logged_page,
                    provider=self.provider,
                    locate_provider=self.coord_locate_provider,
                    provider_search_bar=self.coord_provider_search_bar,
                    provider_selection=self.coord_provider_selection,
                    close_popup_confirmation=True,
                    close_unwanted_popup=self.coord_close_unwanted_popup,
                )

                # Material inclusion process
                self.include_materials(
                    page_to_use=logged_page,
                    materials=self.materials,
                    include_provider=self.coord_include_provider,
                    insert_mat_code=self.coord_insert_mat_code,
                    quantity_selection=self.coord_quantity_selection,
                    empty_space=self.coord_empty_space,
                    confirm_mat=self.coord_confirm_mat,
                    close_mat_confirmation=self.coord_close_mat_confirmation,
                    price=self.coord_price,
                    discount=self.coord_discount,
                    store_progress=self.coord_store_progress,
                )

                self.logger.info(f"FINALIZAÇÃO DE NF {self.name}:")

                # Charging and payment process
                self.set_charging_and_payment(
                    page_to_use=logged_page,
                    coord_charging=self.coord_charging,
                    coord_exclude=self.coord_exclude,
                    coord_confirm_exclusion=self.coord_confirm_exclusion,
                    coord_payments=self.coord_payments,
                    coord_no_payments=self.coord_no_payments,
                )

                # Invoice visualization process
                # Cancelling is no longer supported here
                invoice_path = self.preview_invoice(
                    page_to_use=logged_page,
                    see_invoice=self.coord_see_invoice,
                    confirm_storage=self.coord_confirm_storage,
                    adapt_visibility=self.coord_adapt_visibility,
                    see_fullscreen=self.coord_see_fullscreen,
                    provider=self.provider,
                    close_popup_confirmation=self.close_popup_confirmation,
                    close_unwanted_popup_alt=self.coord_close_unwanted_popup_alt,
                )

                # Invoice saving and transmission process
                self.transmit_invoice(
                    page_to_use=logged_page,
                    save_job=self.coord_save_job,
                    transmit_invoice=self.coord_transmit_invoice,
                    dont_see=self.coord_dont_see,
                    dont_send_email=self.coord_dont_send_email,
                )
        except RuntimeError as e:
            # Controlled Cancelling Action
            self.logger.warning(str(e))
        except Exception as e:
            self.check_cancelled()
            self.logger.error(str(e))

        finally:
            self.gracefully_terminate_process(self.provider)

            if self.approval_status == "cancelled" or self.approval_status == "inactive":
                return

        return invoice_path
