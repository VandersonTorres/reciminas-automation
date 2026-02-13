from typing import Literal, Optional
from playwright.sync_api._generated import Page

from . import BaseServiceManager
from core.settings import COMPANY_CNPJ, COMPANY_USERNAME, COMPANY_PASSWORD
from invoices_automation.utils.page_coordinates import ExitInvoicePageCoordinates

# Tipos de Notas de Saídas
# 1. Transferencia de estoque
# 2. Venda comum (dentro do Estado)  In Progress
# 3. Venda comum (fora do Estado)
# 4. Venda triangular  -  ANA NÃO SABE


class ExitInvoiceService(BaseServiceManager, ExitInvoicePageCoordinates):
    """Service class for automating exit invoice processing.

    Handles the automation of exit invoices (Notas Fiscais de Saída) in the system.
    """

    name = "SAIDA - Venda comum (dentro do Estado)"

    def __init__(
        self,
        provider: str,
        materials: list[dict],
        freight: str | int,
        search_carrier_by: Literal["code", "name"],
        carrier_target: str | int,
        observation: str,
        job_id: str,
        current_iter: str = "",
        **kwargs,
    ) -> None:
        """Initialize Exit Invoices Automation.

        Args:
            provider (str): Provider name.
            materials (list[dict]): List of materials with their details.
            freight (str | int): Freight by who.
            search_carrier_by (Literal["code", "name"]): Method to search carrier.
            carrier_target (str | int): Target value for carrier search (code or name).
            observation (str): Additional observations for the invoice.
            job_id (str): Unique job identifier.
            current_iter (str, optional): Current iteration in batch processing. Defaults to "".
        """
        super().__init__(job_id=job_id, current_iter=current_iter)
        self.provider = provider
        self.materials = materials
        self.freight = freight
        self.search_carrier_by = search_carrier_by
        self.carrier_target = carrier_target
        self.observation = observation

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

                # Go to Reciminas ticker content
                self.logger.info(f"Selecionando ticker {self.company_name}.\n")
                self._click_element(
                    page=logged_page,
                    element_to_click=self.coord_initial_ticker_selection,
                    use_dblclick=True,
                    add_redundance=True,
                    delay=10,
                )
                self.check_cancelled()

                self.logger.info("LOGIN:")

                # Insert Username
                self.logger.info("Inserindo usuário.")
                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_user_insertion,
                    data_to_insert=COMPANY_USERNAME,
                    delay=2,
                )
                self.check_cancelled()

                self._click_element(
                    page=logged_page,
                    element_to_click=self.coord_password_insertion,
                    use_dblclick=True,
                    add_redundance=True,
                    delay=2,
                )
                self.logger.info("Inserindo Senha.")
                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_password_insertion,
                    data_to_insert=COMPANY_PASSWORD,
                    delay=2,
                )
                self.check_cancelled()

                # Enter the account
                self.logger.info("Acessando conta.\n")
                self._click_element(
                    page=logged_page,
                    element_to_click=self.coord_log_in,
                    use_dblclick=True,
                    add_redundance=True,
                    delay=10,
                )
                self.check_cancelled()

                self.logger.info(f"PREPARAÇÃO DA NF {self.name}:")

                # Open Fiscal Tab
                self.logger.info("Abrindo guia 'Opções | Fiscal'.")
                self._click_element(page=logged_page, element_to_click=self.coord_fiscal_tab, delay=1)
                self.check_cancelled()

                # Open Invoice Control
                self.logger.info("Abrindo guia 'Controle de Nota Fiscal'.")
                self._click_element(page=logged_page, element_to_click=self.coord_invoice_control, delay=1)
                self.check_cancelled()

                # Open Registry
                self.logger.info("Abrindo 'Cadastro'.")
                self._click_element(page=logged_page, element_to_click=self.coord_register, use_dblclick=True, delay=1)
                self.check_cancelled()

                # Set Operation Type
                self.logger.info("Definindo tipo de operação para SAÍDA.")
                self._click_element(page=logged_page, element_to_click=self.coord_operation, delay=1)
                self._click_element(page=logged_page, element_to_click=self.coord_select_exit, delay=1)

                # Locate provider
                self.logger.info("Expandindo lista de fornecedores.")
                self._click_element(page=logged_page, element_to_click=self.coord_locate_provider, delay=1)
                self.check_cancelled()

                # Fill the search bar with the provider name
                self.logger.info(f"Procurando pelo fornecedor {self.provider}.")
                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_provider_search_bar,
                    data_to_insert=self.provider,
                    delay=1,
                )
                self.check_cancelled()

                # Provider selection process
                self.logger.info(f"Selecionando {self.provider}.\n")
                self._click_element(
                    page=logged_page, element_to_click=self.coord_provider_selection, use_dblclick=True, delay=3
                )
                self.check_cancelled()

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
                    self._click_element(page=logged_page, element_to_click=self.coord_close_mat_confirmation)
                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_quantity_selection,
                        data_to_insert=str(mat["material_quantity"]),
                        delay=2,
                    )
                    self.check_cancelled()
                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_price,
                        data_to_insert=str(mat["material_price"]),
                        delay=2,
                    )
                    self.check_cancelled()
                    self._insert_data(
                        page=logged_page,
                        element_to_click=self.coord_discount,
                        data_to_insert=str(mat["discount"]),
                        delay=2,
                    )

                    self._click_element(page=logged_page, element_to_click=self.coord_store_progress, delay=3)
                    self.check_cancelled()

                # Set freight information
                self.logger.info("Definindo informações de frete.")
                self._click_element(page=logged_page, element_to_click=self.coord_transport_and_volumes, delay=1)
                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_freight_by,
                    data_to_insert=str(self.freight),
                    delay=1,
                )
                self._click_element(page=logged_page, element_to_click=self.coord_freight_by, delay=1)
                self.check_cancelled()

                # Set carrier information
                self.logger.info("Definindo informações de transportadora.")
                self._click_element(page=logged_page, element_to_click=self.coord_select_carrier, delay=1)
                if self.search_carrier_by == "code":
                    self.logger.info(f"Buscando transportadora por código: {self.carrier_target}.")
                    self._click_element(page=logged_page, element_to_click=self.coord_search_by_code, delay=1)
                else:
                    self.logger.info(f"Buscando transportadora por nome: {self.carrier_target}.")
                    self._click_element(page=logged_page, element_to_click=self.coord_search_by_name, delay=1)

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
                self.logger.info("Excluindo cobrança e selecionando 'Sem Pagamentos'.")
                self._click_element(page=logged_page, element_to_click=self.coord_charging, delay=2)
                self._click_element(page=logged_page, element_to_click=self.coord_exclude, delay=2)
                self._click_element(page=logged_page, element_to_click=self.coord_confirm_exclusion, delay=2)
                self._click_element(page=logged_page, element_to_click=self.coord_payments, delay=2)
                self._click_element(page=logged_page, element_to_click=self.coord_no_payments, delay=2)
                self.check_cancelled()

                # Observation inclusion process
                self.logger.info("Incluindo observação.")
                self._click_element(page=logged_page, element_to_click=self.coord_observation, delay=2)
                self._click_element(page=logged_page, element_to_click=self.coord_expand_observation, delay=2)
                self._click_element(page=logged_page, element_to_click=self.coord_search_observation_by_name, delay=2)
                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_search_observation,
                    data_to_insert=self.observation,
                    delay=2,
                )
                self._click_element(page=logged_page, element_to_click=self.coord_close_observation_tab, delay=2)
                self.check_cancelled()

                self.logger.info(f"FINALIZAÇÃO DE NF {self.name}:")

                # Invoice visualization process
                # Cancelling is no longer supported here
                self.logger.info("Preparando PDF para confirmação.")
                self._click_element(page=logged_page, element_to_click=self.coord_see_invoice)
                self._click_element(page=logged_page, element_to_click=self.coord_confirm_storage, delay=25)
                self._insert_data(page=logged_page, element_to_click=self.coord_adapt_visibility, data_to_insert="105")
                self._click_element(page=logged_page, element_to_click=self.coord_see_fullscreen, delay=10)
                invoice_path = f"downloads/NF-{self.name}-{self.provider}-{self.task_id}.pdf".replace(" ", "-")
                logged_page.pdf(
                    path=invoice_path,
                    format="A4",
                    margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"},
                    scale=0.9,
                    print_background=False,
                )

                # Allow pre visualization of the NF emitted
                self.register_pdf_pending(invoice_path=invoice_path)
                self.logger.info(f"Pré visualização da NF salva em '{invoice_path}'. Aguardando aprovação.\n")

                # Wait for the User decision
                self.approval_status = self.wait_for_transmit_decision()
                if self.approval_status == "cancelled":
                    # Interrupt the flow
                    self.logger.warning("Transmissão abortada pelo usuário.")
                    raise RuntimeError("Automação cancelada.")

                # Invoice saving and transmission process
                self.logger.info("Aprovado. Prosseguindo com transmissão.")
                logged_page.keyboard.press("Escape")
                self._sleep_between_actions(seconds=10)
                self._click_element(page=logged_page, element_to_click=self.coord_save_job, delay=10)
                self._click_element(page=logged_page, element_to_click=self.coord_transmit_invoice)
                self._click_element(page=logged_page, element_to_click=self.coord_dont_see)
                self._click_element(page=logged_page, element_to_click=self.coord_dont_send_email)
                self.logger.info(f"NF '{self.name}' para '{self.provider}' Transmitida com sucesso.")
        except RuntimeError as e:
            self.logger.warning(str(e))
        except Exception as e:
            self.check_cancelled()
            self.logger.warning(str(e))

        finally:
            terminate_process = False
            if (n_of_nn := self.current_iter.split("/")) and len(n_of_nn) == 2:
                if n_of_nn[0] == n_of_nn[1]:
                    # Example: '2/2' -> It means the service is finished
                    terminate_process = True
            else:
                # This means an unique finished execution
                terminate_process = True

            if terminate_process:
                # This logger trigger an action on the caller view function
                self.logger.info(f"Término do processo '{self.job_id}'. NF-{self.provider}")

            if self.approval_status == "cancelled" or self.approval_status == "inactive":
                return

        return invoice_path
