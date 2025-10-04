import logging
import time

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Page

from .log_buffer import InMemoryLogHandler


class BaseAutomation:
    company_name = "RECIMINAS"
    reciminas_url = "https://cloud3.sygecom.com.br/sgr_reciminas.html"

    def __init__(self) -> None:
        # Set logger
        self.logger = logging.getLogger("Reciminas - SYGECOM")

        # Connect logger to a memory buffer
        self.log_handler = InMemoryLogHandler()
        self.log_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] - %(levelname)s - %(message)s"))
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

        # Clean logs whenever starts a new execution
        self.log_handler.clear()

    def _sleep_between_actions(self, seconds: int = 3) -> None:
        """
        Apply a delay between actions to avoid being detected.

        Args:
            seconds (int): Number of seconds to sleep.
        """
        time.sleep(seconds)

    def start_navigation(self, url: str, headless: bool = True, devtools: bool = False) -> object:
        """
        Context manager to start a Playwright Page.
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
                self._context = self._browser.new_context(viewport={"width": 1280, "height": 720})
                self._page = self._context.new_page()
                self.logger.info(f"Navigating to {url}...")
                self._page.goto(url, wait_until="load", timeout=60000)
                return self._page

            def __exit__(inner_self, exc_type, exc_val, exc_tb):
                self.logger.warning("Closing playwright context.")
                self._browser.close()
                self._pw.stop()

        return PageContext()

    def _click_element(
        self, page: Page, element_to_click: tuple[int], use_dblclick: bool = False, delay: int = 5
    ) -> None:
        x_ax, y_ax = element_to_click
        if use_dblclick:
            page.mouse.move(x_ax, y_ax)
            page.mouse.down()
            page.wait_for_timeout(100)
            page.mouse.up()
            page.mouse.dblclick(x_ax, y_ax)
        else:
            page.mouse.click(x_ax, y_ax)

        self._sleep_between_actions(seconds=delay)

    def _insert_data(self, page: Page, element_to_click: tuple[int], data_to_insert: str) -> None:
        self._click_element(page=page, element_to_click=element_to_click)
        page.keyboard.type(data_to_insert)
        self._sleep_between_actions()
