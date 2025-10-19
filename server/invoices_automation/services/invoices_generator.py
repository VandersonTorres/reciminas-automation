from playwright.sync_api._generated import Page

from . import BaseAutomation
from core.settings import RECIMINAS_CNPJ, RECIMINAS_USERNAME, RECIMINAS_PASSWORD
from invoices_automation.utils.page_coordinates import PageAttributesCoordinates

CANCEL_FLAGS = {}
TO_PDF_APPROVAL = {}  # Ex.: {"<taskID>": {"path": "downloads/path.pdf", "status": "pending", "job_id": "JOB_001"}}


class EntryInvoicesAutomation(BaseAutomation, PageAttributesCoordinates):
    name = "ENTRADA"

    def __init__(
        self,
        provider: str,
        material_code: str,
        material_quantity: float,
        material_price: float,
        discount: float,
        job_id: str,
        current_iter: str = "",
    ) -> None:
        super().__init__()
        # Automation Inputs
        self.provider = provider
        self.material_code = material_code
        self.material_quantity = material_quantity
        self.material_price = material_price
        self.discount = discount
        self.job_id = job_id
        self.current_iter = current_iter
        self.task_id = f"{self.job_id}_{'-'.join(self.current_iter.split('/'))}"
        CANCEL_FLAGS[self.job_id] = False

    def check_cancelled(self):
        if CANCEL_FLAGS.get(self.job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
            self.logger.warning("Automação cancelada pelo usuário.")
            raise RuntimeError("Automation cancelled")

    # TODO: REMOVE HEADFUL
    def run(self, headless: bool = False, devtools: bool = False) -> str:
        try:
            self.logger.info(f"Iniciando processo '{self.task_id}'. NF-{self.provider}")
            with self.start_navigation(url=self.reciminas_url, headless=headless, devtools=devtools) as _page:
                page: Page = _page
                ticker_sel = page.locator("input[name='Password']")
                ticker_sel.fill(RECIMINAS_CNPJ)
                self._sleep_between_actions()
                self.check_cancelled()
                with page.context.expect_page() as logged_page_event:
                    self.logger.info(f"Inicializando CNPJ {self.company_name}.")
                    page.locator("input[value='Entrar']").click()
                    self.check_cancelled()
                    self._sleep_between_actions(seconds=25)

                # Capturing new tab
                logged_page = logged_page_event.value
                logged_page.wait_for_load_state("networkidle")
                self._sleep_between_actions()
                self.check_cancelled()

                # Go to Reciminas ticker content
                self.logger.info(f"Selecionando ticker {self.company_name}...")
                self._click_element(page=logged_page, element_to_click=self.coord_initial_ticker_selection)
                self.check_cancelled()

                # Insert Username
                self.logger.info(f"Inserindo nome de usuário (conta: {RECIMINAS_USERNAME})...")
                self._insert_data(
                    page=logged_page, element_to_click=self.coord_user_insertion, data_to_insert=RECIMINAS_USERNAME
                )
                self.check_cancelled()

                # Insert Password
                self.logger.info("Inserindo Senha...")
                self._insert_data(
                    page=logged_page, element_to_click=self.coord_password_insertion, data_to_insert=RECIMINAS_PASSWORD
                )
                self.check_cancelled()

                # Log in
                self.logger.info("Logando na conta...")
                self._click_element(page=logged_page, element_to_click=self.coord_log_in, delay=10)
                self.check_cancelled()

                # Open Fiscal Tab
                self.logger.info("Abrindo guia 'Opções Fiscal'...")
                self._click_element(page=logged_page, element_to_click=self.coord_fiscal_tab)
                self.check_cancelled()

                # Open Invoice Control
                self.logger.info("Abrindo guia 'Controle de Nota Fiscal'...")
                self._click_element(page=logged_page, element_to_click=self.coord_invoice_control)
                self.check_cancelled()

                # Open Registry
                self.logger.info("Abrindo 'Cadastro'...")
                self._click_element(page=logged_page, element_to_click=self.coord_register, use_dblclick=True)
                self.check_cancelled()

                # Locate provider
                self.logger.info("Expandindo lista de fornecedores...")
                self._click_element(page=logged_page, element_to_click=self.coord_locate_provider)
                self.check_cancelled()

                # Fill the search bar with the provider name
                self.logger.info(f"Procurando pelo fornecedor {self.provider}...")
                self._insert_data(
                    page=logged_page, element_to_click=self.coord_provider_search_bar, data_to_insert=self.provider
                )
                self.check_cancelled()

                # Include Provider
                self.logger.info(f"Selecionando e incluindo {self.provider}...")
                self._click_element(page=logged_page, element_to_click=self.coord_provider_selection, use_dblclick=True)
                self._click_element(page=logged_page, element_to_click=self.coord_include_provider)
                self.check_cancelled()

                # Inserting Material Specifications
                self.logger.info(
                    "Inserindo especificações de material. "
                    f"Produto: {self.material_code} - {self.material_quantity} - R${self.material_price}"
                )
                self._insert_data(
                    page=logged_page, element_to_click=self.coord_insert_mat_code, data_to_insert=self.material_code
                )
                self._click_element(page=logged_page, element_to_click=self.coord_quantity_selection)
                self._click_element(page=logged_page, element_to_click=self.coord_confirm_mat, use_dblclick=True)
                self._insert_data(
                    page=logged_page,
                    element_to_click=self.coord_quantity_selection,
                    data_to_insert=str(self.material_quantity),
                )
                self._insert_data(
                    page=logged_page, element_to_click=self.coord_price, data_to_insert=str(self.material_price)
                )
                self._insert_data(
                    page=logged_page, element_to_click=self.coord_discount, data_to_insert=str(self.discount)
                )
                self._click_element(page=logged_page, element_to_click=self.coord_store_progress)
                self.check_cancelled()

                # Manage charge and payments
                self.logger.info("Excluindo cobrança e selecionando 'Sem Pagamentos'...")
                self._click_element(page=logged_page, element_to_click=self.coord_charging)
                self._click_element(page=logged_page, element_to_click=self.coord_exclude)
                self._click_element(page=logged_page, element_to_click=self.coord_confirm_exclusion)
                self._click_element(page=logged_page, element_to_click=self.coord_payments)
                self._click_element(page=logged_page, element_to_click=self.coord_no_payments)
                self.check_cancelled()

                # Cancelling is no longer supported here
                self.logger.info("Baixando NF em PDF...")
                self._click_element(page=logged_page, element_to_click=self.coord_see_invoice)
                self._click_element(page=logged_page, element_to_click=self.coord_confirm_storage, delay=25)
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
                TO_PDF_APPROVAL[self.task_id] = {"path": invoice_path, "status": "pending", "job_id": self.job_id}
                self.logger.info(f"Pré visualização da NF salva em '{invoice_path}'. Aguardando aprovação...")
                while TO_PDF_APPROVAL[self.task_id]["status"] == "pending":
                    # Wait for the User decision
                    self._sleep_between_actions(seconds=2)
                    self.check_cancelled()
                if TO_PDF_APPROVAL[self.task_id]["status"] == "cancelled":
                    # Interrupt the flow
                    self.logger.warning("Transmissão abortada pelo usuário.")
                    raise RuntimeError("Automation cancelled")

                self.logger.info("Aprovado. Prosseguindo com transmissão...")
                self._click_element(page=logged_page, element_to_click=self.coord_close_visualization, delay=10)
                self._click_element(page=logged_page, element_to_click=self.coord_save_job, delay=10)
                self._click_element(page=logged_page, element_to_click=self.coord_transmit_invoice, delay=10)
                self._click_element(page=logged_page, element_to_click=self.coord_dont_see, delay=10)
                self._click_element(page=logged_page, element_to_click=self.coord_dont_send_email, delay=10)
                self.logger.info(f"NF 'Entrada' para '{self.provider}' Transmitida com sucesso.")

        except RuntimeError as e:
            self.logger.warning(str(e))

        finally:
            terminate_process = False
            if (n_of_nn := self.current_iter.split("/")) and len(n_of_nn) == 2:
                if n_of_nn[0] == n_of_nn[1]:
                    terminate_process = True
            else:
                terminate_process = True

            if terminate_process:
                # This logger trigger an action on the caller view function
                self.logger.info(f"Término do processo '{self.job_id}'. NF-{self.provider}")

            if TO_PDF_APPROVAL[self.task_id]["status"] == "cancelled":
                return

        return invoice_path


# TODO: Remove this debug snippet
# python -m server.invoices_automation.services.invoices_generator
# if __name__ == "__main__":
#     # INPUTS
#     provider = "Ramon Azevedo"
#     material_code = "52"
#     material_quantity = 3007.6  # Kg
#     material_price = 13.30  # R$
#     discount = 1.08  # R$

#     entry_invoices_automation = EntryInvoicesAutomation(
#         provider=provider,
#         material_code=material_code,
#         material_quantity=material_quantity,
#         material_price=material_price,
#         discount=discount,
#         job_id="DEBUG_JOB_001",
#     )

#     entry_invoices_automation.run(headless=False, devtools=False)
