from playwright.sync_api._generated import Page

from . import BaseAutomation
from server.core.settings import RECIMINAS_CNPJ, RECIMINAS_USERNAME, RECIMINAS_PASSWORD
from server.invoices_automation.utils.page_coordinates import PageAttributesCoordinates


# python -m server.invoices_automation.services.invoices_generator
class EntryInvoicesAutomation(BaseAutomation, PageAttributesCoordinates):
    company_name = "RECIMINAS"

    def __init__(
        self, provider: str, material_code: str, material_quantity: float, material_price: float, discount: float
    ) -> None:
        super().__init__()
        self.provider = provider
        self.material_code = material_code
        self.material_quantity = material_quantity
        self.material_price = material_price
        self.discount = discount

    def run(self, url: str, headless: bool = True, devtools: bool = False) -> None:
        with self.start_navigation(url=url, headless=headless, devtools=devtools) as _page:
            page: Page = _page
            ticker_sel = page.locator("input[name='Password']")
            ticker_sel.fill(RECIMINAS_CNPJ)
            self._sleep_between_actions()
            with page.context.expect_page() as logged_page_event:
                self.logger.info(f"Starting {self.company_name} CNPJ.")
                page.locator("input[value='Entrar']").click()
                self._sleep_between_actions(seconds=15)

            # Capturing new tab
            logged_page = logged_page_event.value
            logged_page.wait_for_load_state("networkidle")
            self._sleep_between_actions()

            # Go to Reciminas ticker content
            self.logger.info(f"Selecting {self.company_name} ticker...")
            self._click_element(page=logged_page, element_to_click=self.coord_initial_ticker_selection)

            # Insert Username
            self.logger.info("Inserting username...")
            self._insert_data(
                page=logged_page, element_to_click=self.coord_user_insertion, data_to_insert=RECIMINAS_USERNAME
            )

            # Insert Password
            self.logger.info("Inserting password...")
            self._insert_data(
                page=logged_page, element_to_click=self.coord_password_insertion, data_to_insert=RECIMINAS_PASSWORD
            )

            # Log in
            self.logger.info(f"Logging in to {RECIMINAS_USERNAME} account...")
            self._click_element(page=logged_page, element_to_click=self.coord_log_in, delay=10)

            # Open Fiscal Tab
            self.logger.info("Opening fiscal options tab...")
            self._click_element(page=logged_page, element_to_click=self.coord_fiscal_tab)

            # Open Invoice Control
            self.logger.info("Opening invoice control...")
            self._click_element(page=logged_page, element_to_click=self.coord_invoice_control)

            # Open Registry
            self.logger.info("Opening registry...")
            self._click_element(page=logged_page, element_to_click=self.coord_register, use_dblclick=True)

            # Locate provider
            self.logger.info("Opening providers list...")
            self._click_element(page=logged_page, element_to_click=self.coord_locate_provider)

            # Fill the search bar with the provider name
            self.logger.info("Searching for the provider...")
            self._insert_data(
                page=logged_page, element_to_click=self.coord_provider_search_bar, data_to_insert=self.provider
            )

            # Include Provider
            self.logger.info(f"Selecting and including provider {self.provider}...")
            self._click_element(page=logged_page, element_to_click=self.coord_provider_selection, use_dblclick=True)
            self._click_element(page=logged_page, element_to_click=self.coord_include_provider)

            # Inserting Material Specifications
            self.logger.info(
                "Inserting material specifications. "
                f"Product: {self.material_code} - {self.material_quantity} - R${self.material_price}"
            )
            self._insert_data(
                page=logged_page, element_to_click=self.coord_insert_mat_code, data_to_insert=self.material_code
            )
            self._click_element(page=logged_page, element_to_click=self.coord_confirm_mat, use_dblclick=True)
            self._insert_data(
                page=logged_page,
                element_to_click=self.coord_quantity_selection,
                data_to_insert=str(self.material_quantity),
            )
            self._insert_data(
                page=logged_page, element_to_click=self.coord_price, data_to_insert=str(self.material_price)
            )
            self._insert_data(page=logged_page, element_to_click=self.coord_discount, data_to_insert=str(self.discount))
            self._click_element(page=logged_page, element_to_click=self.coord_store_progress)

            # Manage charge and payments
            self.logger.info("Excluding charge and setting 'no payments'...")
            self._click_element(page=logged_page, element_to_click=self.coord_charging)
            self._click_element(page=logged_page, element_to_click=self.coord_exclude)
            self._click_element(page=logged_page, element_to_click=self.coord_confirm_exclusion)
            self._click_element(page=logged_page, element_to_click=self.coord_payments)
            self._click_element(page=logged_page, element_to_click=self.coord_no_payments)

            # Finish process and wait for user confirmation
            self.logger.info("Documento salvo em reciminas_documento.pdf")
            self._click_element(page=logged_page, element_to_click=self.coord_see_invoice)
            self._click_element(page=logged_page, element_to_click=self.coord_confirm_store, delay=30)
            # import pdb; pdb.set_trace()
            self._click_element(page=logged_page, element_to_click=self.coord_page_zoom)
            self._click_element(page=logged_page, element_to_click=self.coord_set_zoom)
            logged_page.screenshot(path=f"NF-ENTRADA-{self.provider}-{str(self.coord_price)}.png", full_page=True)


if __name__ == "__main__":
    # INPUTS
    provider = "SERGIO WANDUARLES"
    material_code = "50"
    material_quantity = 10.2  # Kg
    material_price = 50.10  # R$
    discount = 0  # R$

    entry_invoices_automation = EntryInvoicesAutomation(
        provider=provider,
        material_code=material_code,
        material_quantity=material_quantity,
        material_price=material_price,
        discount=discount,
    )
    reciminas_url = "https://cloud3.sygecom.com.br/sgr_reciminas.html"
    entry_invoices_automation.run(url=reciminas_url, headless=False, devtools=True)
