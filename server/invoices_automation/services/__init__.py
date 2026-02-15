import logging
import time
from typing import Any, Literal, Optional

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Page

from .log_buffer import InMemoryLogHandler

# Shared registries for services: base URL, cancellation flags and PDF-approval workflow
RECIMINAS_URL = "https://cloud.gruposygecom.com.br/sgr_reciminas.html"
CANCEL_FLAGS = {}
TO_PDF_APPROVAL = {
    # "<taskID>": {
    #     "path": "downloads/path.pdf",
    #     "status": "inactive",  # ("inactive", "pending", "cancelled" or "approved")
    #     "job_id": "JOB_001",
    # }
}


class AutomationControl:
    """Base class for automation control, helpers and utilities.

    Responsibilities:
    - start_navigation: Context manager to start a Playwright Page with the correct settings.
    - _click_element: Helper to click on a specific coordinate with optional double-click and redundancy.
    - _insert_data: Helper to click and type into a field based on coordinates.
    """

    company_name = "RECIMINAS"

    def __init__(self) -> None:
        # Set logger
        self.logger = logging.getLogger("SYGECOM")

        # Clean old handlers to avoid duplicates
        self.logger.handlers.clear()

        # Connect logger to a memory buffer
        self.log_handler = InMemoryLogHandler()
        self.log_handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(name)s] - %(levelname)s - %(message)s", datefmt="%d/%m/%y %H:%M:%S"),
        )
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

        # Clean logs whenever starts a new execution
        self.log_handler.clear()

    def _sleep_between_actions(self, seconds: int = 3) -> None:
        """Apply a delay between actions to avoid being detected."""
        time.sleep(seconds)

    def start_navigation(self, url: str = RECIMINAS_URL, headless: bool = True, devtools: bool = False) -> object:
        """Context manager to start a Playwright Page.

        Args:
            url (str): URL to be started.
            headless (bool): Do not show the browser.
            devtools (bool): Do not open the Devtools.
        Returns:
            object: Playwright context.
        """

        class PageContext:
            def __enter__(inner_self):
                self._pw = sync_playwright().start()
                self._browser = self._pw.chromium.launch(headless=headless, devtools=devtools)
                self._context = self._browser.new_context()
                self._page = self._context.new_page()
                self.logger.info(f"Navegando para {url}...")
                self._page.goto(url, wait_until="load", timeout=60000)
                return self._page

            def __exit__(inner_self, exc_type, exc_val, exc_tb):
                self.logger.warning("Fechando o contexto do playwright.")
                self._browser.close()
                self._pw.stop()

        return PageContext()

    def _click_element(
        self,
        page: Page,
        element_to_click: tuple[int],
        use_dblclick: bool = False,
        add_redundance: bool = False,
        delay: int = 4,
    ) -> None:
        """Click or double-click on a specific element.

        Args:
            page (Page): Playwright Page object.
            element_to_click (tuple[int]): X and Y axis coordinates to click.
            use_dblclick (bool): Whether to use double-click.
            delay (int): Delay after the click action.
        """
        x_ax, y_ax = element_to_click
        if use_dblclick:
            page.mouse.move(x_ax, y_ax)
            page.mouse.down()
            page.wait_for_timeout(100)
            page.mouse.up()
            page.mouse.dblclick(x_ax, y_ax)
        else:
            page.mouse.click(x_ax, y_ax)

        if add_redundance:
            # Click again to ensure the action
            self._sleep_between_actions(seconds=1)
            page.mouse.click(x_ax, y_ax)

        self._sleep_between_actions(seconds=delay)

    def _insert_data(self, page: Page, element_to_click: tuple[int], data_to_insert: str, delay: int = 4) -> None:
        """Insert data into a field by clicking and typing.

        Args:
            page (Page): Playwright Page object.
            element_to_click (tuple[int]): X and Y axis coordinates to click.
            data_to_insert (str): Data to be typed.
            delay (int): Delay after clicking before typing.
        """
        self._click_element(page=page, element_to_click=element_to_click, delay=delay)
        page.keyboard.type(data_to_insert)


class BaseServiceManager(AutomationControl):
    """Base class for automation services that centralizes job/task logic.

    Responsibilities:
    - Initialize and expose self.job_id, self.current_iter and self.task_id
    - Register the job in CANCEL_FLAGS
    - Provide check_cancelled helper
    - Helpers to register a PDF as pending and wait for a user decision
    """

    name: str  # Name of the service
    approval_status: Literal["inactive", "pending", "approved", "cancelled"] = "inactive"

    def __init__(self, job_id: str, current_iter: str = "") -> None:
        super().__init__()

        self.job_id = job_id
        self.current_iter = current_iter or ""
        # Build a stable task id joined by '-' from the iteration (e.g. "JOB_1_1-2")
        self.task_id = (
            f"{self.job_id}_{'-'.join(self.current_iter.split('/'))}" if self.current_iter else f"{self.job_id}_1"
        )

        # Ensure the Job starts with the CANCEL Flag set to False
        CANCEL_FLAGS.setdefault(self.job_id, False)

    def check_cancelled(self) -> None:
        """Interrupt the Playwright automation process, by deliberately raising RuntimeError
        when a single job or the global flag is set to CANCEL.
        """
        if CANCEL_FLAGS.get(self.job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
            raise RuntimeError("Automação cancelada pelo usuário.")

    def register_pdf_pending(self, invoice_path: str) -> None:
        """Register the generated invoice PDF and set it to pending approval."""
        TO_PDF_APPROVAL[self.task_id] = {"path": invoice_path, "status": "pending", "job_id": self.job_id}

    def wait_for_transmit_decision(self, sleep_seconds: int = 2) -> str:
        """Block until the PDF is approved/cancelled by the user. Returns the final status."""
        while TO_PDF_APPROVAL[self.task_id]["status"] == "pending":
            self._sleep_between_actions(sleep_seconds)
            self.check_cancelled()

        return TO_PDF_APPROVAL[self.task_id]["status"]

    # --- Base Page Actions ---

    def set_account(
        self,
        page_to_use: Page,
        initial_ticker_selection: tuple[int],
        user_insertion: tuple[int],
        password_insertion: tuple[int],
        log_in_button: tuple[int],
        username: str,
        password: str,
    ) -> None:
        """Isolate actions for setting account on the ERP Environment"""

        # Go to Reciminas ticker content
        self.logger.info(f"Selecionando ticker {self.company_name}.\n")
        self._click_element(page=page_to_use, element_to_click=initial_ticker_selection, delay=1)
        # Ensure the previous click works
        self._click_element(
            page=page_to_use,
            element_to_click=initial_ticker_selection,
            use_dblclick=True,
            add_redundance=True,
            delay=9,
        )
        self.check_cancelled()

        self.logger.info("LOGIN:")

        # Insert Username
        self.logger.info("Inserindo usuário.")
        self._insert_data(
            page=page_to_use,
            element_to_click=user_insertion,
            data_to_insert=username,
            delay=2,
        )
        self.check_cancelled()

        # It was needed to add redundance on clicking the correct element
        self._click_element(
            page=page_to_use,
            element_to_click=password_insertion,
            use_dblclick=True,
            add_redundance=True,
            delay=2,
        )

        # Insert Password
        self.logger.info("Inserindo Senha.")
        self._insert_data(
            page=page_to_use,
            element_to_click=password_insertion,
            data_to_insert=password,
            delay=2,
        )
        self.check_cancelled()

        # Enter the account
        self.logger.info("Acessando conta.\n")
        self._click_element(
            page=page_to_use,
            element_to_click=log_in_button,
            use_dblclick=True,
            add_redundance=True,
            delay=10,
        )
        self.check_cancelled()

    def prepare_options(
        self,
        page_to_use: Page,
        fiscal_tab: tuple[int],
        invoice_control: tuple[int],
        register: tuple[int],
    ) -> None:
        """Isolate actions for preparing options on the initial ERP Page"""

        # Open Fiscal Tab
        self.logger.info("Abrindo guia 'Opções | Fiscal'.")
        self._click_element(page=page_to_use, element_to_click=fiscal_tab, delay=1)
        self.check_cancelled()

        # Open Invoice Control
        self.logger.info("Abrindo guia 'Controle de Nota Fiscal'.")
        self._click_element(page=page_to_use, element_to_click=invoice_control, delay=1)
        self.check_cancelled()

        # Open Registry
        self.logger.info("Abrindo 'Cadastro'.")
        self._click_element(page=page_to_use, element_to_click=register, use_dblclick=True, delay=1)
        self.check_cancelled()

    def set_provider(
        self,
        page_to_use: Page,
        provider: str,
        locate_provider: tuple[int],
        provider_search_bar: tuple[int],
        provider_selection: tuple[int],
        close_popup_confirmation: bool = False,
        close_unwanted_popup: Optional[tuple[int]] = None,
    ) -> None:
        """Isolate actions for setting the provider"""

        # Locate provider
        self.logger.info("Expandindo lista de fornecedores.")
        self._click_element(page=page_to_use, element_to_click=locate_provider, delay=1)
        self.check_cancelled()

        # Fill the search bar with the provider name
        self.logger.info(f"Procurando pelo fornecedor {provider}.")
        self._insert_data(
            page=page_to_use,
            element_to_click=provider_search_bar,
            data_to_insert=provider,
            delay=1,
        )
        self.check_cancelled()

        # Provider selection process
        self.logger.info(f"Selecionando {provider}.\n")
        self._click_element(page=page_to_use, element_to_click=provider_selection, use_dblclick=True, delay=3)
        if close_popup_confirmation:
            self._click_element(page=page_to_use, element_to_click=close_unwanted_popup, delay=2)

        self.check_cancelled()

    def include_materials(
        self,
        page_to_use: Page,
        materials: list[dict[str, Any]],
        include_provider: tuple[int],
        insert_mat_code: tuple[int],
        quantity_selection: tuple[int],
        empty_space: tuple[int],
        confirm_mat: tuple[int],
        close_mat_confirmation: tuple[int],
        price: tuple[int],
        discount: tuple[int],
        store_progress: tuple[int],
    ) -> None:
        """Isolate actions for including materials on the Invoice"""

        for mat in materials:
            self.logger.info("INCLUSÃO DE MATERIAL:")
            self._click_element(page=page_to_use, element_to_click=include_provider)
            self.logger.info(
                "Registrando:\n\t"
                f"Código {mat['material_code']}\n\t"
                f"Quantidade {mat['material_quantity']}\n\t"
                f"Preço {mat['material_price']}\n\t"
                f"Desconto {mat['discount']}.\n"
            )

            self._insert_data(
                page=page_to_use,
                element_to_click=insert_mat_code,
                data_to_insert=mat["material_code"],
            )
            self._click_element(page=page_to_use, element_to_click=quantity_selection)
            self._click_element(page=page_to_use, element_to_click=empty_space)
            self._click_element(page=page_to_use, element_to_click=confirm_mat, use_dblclick=True)
            self._click_element(page=page_to_use, element_to_click=close_mat_confirmation)
            self._insert_data(
                page=page_to_use,
                element_to_click=quantity_selection,
                data_to_insert=str(mat["material_quantity"]),
                delay=2,
            )
            self.check_cancelled()
            self._insert_data(
                page=page_to_use,
                element_to_click=price,
                data_to_insert=str(mat["material_price"]),
                delay=2,
            )
            self.check_cancelled()
            self._insert_data(
                page=page_to_use,
                element_to_click=discount,
                data_to_insert=str(mat["discount"]),
                delay=2,
            )

            self._click_element(page=page_to_use, element_to_click=store_progress, delay=3)
            self.check_cancelled()

    def preview_invoice(
        self,
        page_to_use: Page,
        see_invoice: tuple[int],
        confirm_storage: tuple[int],
        adapt_visibility: tuple[int],
        see_fullscreen: tuple[int],
        provider: str,
        close_popup_confirmation: bool = False,
        close_unwanted_popup_alt: Optional[tuple[int]] = None,
    ) -> Optional[str]:
        """Isolate actions for preparing Invoice visualization."""

        self.logger.info("Preparando PDF para confirmação.")
        self._click_element(page=page_to_use, element_to_click=see_invoice)
        if close_popup_confirmation:
            self._click_element(page=page_to_use, element_to_click=close_unwanted_popup_alt)

        self._click_element(page=page_to_use, element_to_click=confirm_storage, delay=25)
        self._insert_data(page=page_to_use, element_to_click=adapt_visibility, data_to_insert="105")
        self._click_element(page=page_to_use, element_to_click=see_fullscreen, delay=10)
        invoice_path = f"downloads/NF-{self.name}-{provider}-{self.task_id}.pdf".replace(" ", "-")
        page_to_use.pdf(
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

        return invoice_path

    def transmit_invoice(
        self,
        page_to_use: Page,
        save_job: tuple[int],
        transmit_invoice: tuple[int],
        dont_see: tuple[int],
        dont_send_email: tuple[int],
    ) -> None:
        """Isolate actions for transmiting Invoice"""

        self.logger.info("Aprovado. Prosseguindo com transmissão.")
        page_to_use.keyboard.press("Escape")
        self._sleep_between_actions(seconds=10)
        self._click_element(page=page_to_use, element_to_click=save_job, delay=10)
        self._click_element(page=page_to_use, element_to_click=transmit_invoice)
        self._click_element(page=page_to_use, element_to_click=dont_see)
        self._click_element(page=page_to_use, element_to_click=dont_send_email)
        self.logger.info(f"NF '{self.name}' para '{self.provider}' Transmitida com sucesso.")

    # TODO: This is a poor way to warn client-side to finish the Log Fetcher(Handler) process.
    # Despite we are using sync playwright, when trying to manage the finishing process through django.Models,
    # we get a Django Error pointing to a sync-async operation
    def gracefully_terminate_process(self, provider) -> None:
        """Triggers the finish flag on:
        `server/invoices_automation/static/js/client_side_automation_manager.js L38`
        """
        terminate_process = False
        if (n_of_nn := self.current_iter.split("/")) and len(n_of_nn) == 2:
            if n_of_nn[0] == n_of_nn[1]:
                # Example: '2/2' -> It means the service is finished
                terminate_process = True
        else:
            # This means an unique finished execution
            terminate_process = True

        if terminate_process:
            # THIS LOGGER TRIGGER AN ACTION ON THE CALLER VIEW FUNCTION
            self.logger.info(f"Término do processo '{self.job_id}'. NF-{provider}")
