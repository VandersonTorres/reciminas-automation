from typing import Optional
from playwright.sync_api._generated import Page

from core.settings import COMPANY_CNPJ, COMPANY_USERNAME, COMPANY_PASSWORD
from invoices_automation.services.exit_invoices_service import ExitInvoiceService
from invoices_automation.utils.page_coordinates import OutstateSaleInvoicePageCoordinates


# Out State (common sale) - Venda comum fora do Estado


class OutStateInvoiceService(ExitInvoiceService, OutstateSaleInvoicePageCoordinates):
    """Service class for automating Out State Sale invoice processing."""

    name = "SAIDA - Venda comum (fora do Estado)"
    icms_aliq_percentual = "12"  # 12% for out of state sales, as tax regulations

    def run(self, headless: bool = True, devtools: bool = False) -> Optional[str]:
        """Run the exit invoice automation process (Common Sale - Out of State)"""
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

                # Set Operation Type
                self.logger.info("Definindo tipo de operação para SAÍDA.")
                self._click_element(page=logged_page, element_to_click=self.coord_operation, delay=1)
                self._click_element(page=logged_page, element_to_click=self.coord_select_exit, delay=1)

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
                for mat in self.materials:
                    self.logger.info("INCLUSÃO DE MATERIAL:")
                    self._click_element(page=logged_page, element_to_click=self.coord_include_provider)
                    self.logger.info(
                        "Registrando:\n\t"
                        f"Código {mat['material_code']}\n\t"
                        f"Quantidade {mat['material_quantity']}\n\t"
                        f"Preço {mat['material_price']}\n\t"
                        f"Desconto {mat['discount']}.\n"
                    )

                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_insert_mat_code,
                        data_to_insert=mat["material_code"],
                    )
                    self._click_element(page=logged_page, element_to_click=self.coord_quantity_selection)
                    self._click_element(page=logged_page, element_to_click=self.coord_empty_space)
                    self._click_element(page=logged_page, element_to_click=self.coord_confirm_mat, use_dblclick=True)
                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_quantity_selection,
                        data_to_insert=str(mat["material_quantity"]),
                        delay=2,
                    )
                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_price,
                        data_to_insert=str(mat["material_price"]),
                        delay=2,
                    )
                    self.check_cancelled()

                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_icms_aliq,
                        data_to_insert=self.icms_aliq_percentual,
                        delay=2,
                        press_enter=True,
                    )

                    self._click_element(page=logged_page, element_to_click=self.coord_store_progress)
                    self.check_cancelled()

                # Set carrier information
                self.logger.info("Definindo Transportadora.")
                self._click_element(page=logged_page, element_to_click=self.coord_transport_and_volumes, delay=1)
                self.set_carrier_info(
                    page_to_use=logged_page,
                    coord_select_carrier=self.coord_select_carrier,
                    coord_search_by_code=self.coord_search_by_code,
                    coord_search_by_name=self.coord_search_by_name,
                    carrier_target=self.carrier_target,
                )

                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_search_carrier,
                    data_to_insert=self.carrier_target,
                    delay=1,
                )
                self._click_element(
                    page=logged_page, element_to_click=self.coord_confirm_carrier, use_dblclick=True, delay=1
                )
                self.check_cancelled()

                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_search_carrier,
                    data_to_insert=self.carrier_target,
                    delay=1,
                )
                self._click_element(
                    page=logged_page, element_to_click=self.coord_confirm_carrier, use_dblclick=True, delay=1
                )
                self.check_cancelled()

                # Charging and payment process
                self.set_charging_and_payment(
                    page_to_use=logged_page,
                    coord_charging=self.coord_charging,
                    coord_exclude=self.coord_exclude,
                    coord_confirm_exclusion=self.coord_confirm_exclusion,
                    coord_payments=self.coord_payments,
                    coord_no_payments=self.coord_no_payments,
                )

                # Observation inclusion process
                self.include_observation(
                    page_to_use=logged_page,
                    coord_observation=self.coord_observation,
                    coord_expand_observation=self.coord_expand_observation,
                    coord_search_observation_by=self.coord_search_observation_by_name,
                    coord_search_observation=self.coord_search_observation,
                    coord_close_observation_tab=self.coord_close_observation_tab,
                    observation_to_insert=self.observation,
                )

                self.logger.info(f"FINALIZAÇÃO DE NF {self.name}:")
                import pdb

                pdb.set_trace()

                # Invoice visualization process
                # Cancelling is no longer supported here
                invoice_path = self.preview_invoice(
                    page_to_use=logged_page,
                    see_invoice=self.coord_see_invoice,
                    confirm_storage=self.coord_confirm_storage,
                    adapt_visibility=self.coord_adapt_visibility,
                    see_fullscreen=self.coord_see_fullscreen,
                    provider=self.provider,
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
