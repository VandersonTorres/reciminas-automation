import logging
import time

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Page

from .log_buffer import InMemoryLogHandler
from core.settings import COMPANY_CNPJ, COMPANY_USERNAME, COMPANY_PASSWORD
from invoices_automation.utils.page_coordinates import BasePageCoordinates

# Shared registries for services: base URL, cancellation flags and PDF-approval workflow
RECIMINAS_URL = "https://cloud.gruposygecom.com.br/sgr_reciminas.html"
CANCEL_FLAGS = {}
TO_PDF_APPROVAL = {
    # "<taskID>": {
    #     "path": "downloads/path.pdf",
    #     "status": "pending",  # ("pending", "cancelled" or "approved")
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


class BaseServiceManager(AutomationControl, BasePageCoordinates):
    """Base class for automation services that centralizes job/task logic.

    Responsibilities:
    - Initialize and expose self.job_id, self.current_iter and self.task_id
    - Register the job in CANCEL_FLAGS
    - Provide check_cancelled helper
    - Helpers to register a PDF as pending and wait for a user decision
    """

    name: str  # Name of the service
    approval_status: str = "inactive"  # ("inactive", "pending", "approved" or "cancelled")

    def __init__(self, job_id: str, current_iter: str = "") -> None:
        super().__init__()

        self.job_id = job_id
        self.current_iter = current_iter or ""
        # Build a stable task id joined by '-' from the iteration (e.g. "JOB_1_1-2")
        self.task_id = (
            f"{self.job_id}_{'-'.join(self.current_iter.split('/'))}" if self.current_iter else f"{self.job_id}_1"
        )
        # Ensure a flag is present for this job
        CANCEL_FLAGS.setdefault(self.job_id, False)

    def check_cancelled(self) -> None:
        """Raise RuntimeError when the job or the global flag was set to cancel."""
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

    def start_service(self, headless=True, devtools=False):
        """Start the service by performing login and navigating to the correct page.

        :Important: This method returns a context manager that must be closed by the caller
        by calling context_manager.__exit__(None, None, None) after finishing the service's tasks,
        or in a try/finally block to ensure proper cleanup.

        Args:
            headless (bool): Whether to run the browser in headless mode. Defaults to True.
            devtools (bool): Whether to open devtools. Defaults to False.
        Returns:
            tuple: (context_manager, page, logged_page) where
            - "context_manager" is the Playwright context manager,
            - "page" is the initial page after login, and
            - "logged_page" is the page after navigating to the ticker content.
        """
        self.logger.info(f"Iniciando {self.name} '{self.current_iter}'.\n\t- CONTA: {COMPANY_USERNAME}\n")
        context_manager = self.start_navigation(headless=headless, devtools=devtools)
        page: Page = context_manager.__enter__()
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

        # It was needed to add redundance on clicking the correct element
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

        return context_manager, page, logged_page
