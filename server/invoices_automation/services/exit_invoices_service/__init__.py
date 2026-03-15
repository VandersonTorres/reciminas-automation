from typing import Any, Literal
from playwright.sync_api._generated import Page

from invoices_automation.services import BaseServiceManager
from invoices_automation.utils.page_coordinates import ExitInvoicePageCoordinates


class ExitInvoiceService(BaseServiceManager, ExitInvoicePageCoordinates):
    """Service class for Base Exit Invoices processing."""

    name: str

    def __init__(
        self,
        provider: str,
        materials: list[dict[str, Any]],
        freight: str | int,
        search_carrier_by: Literal["code", "name"],
        carrier_target: str | int,
        observation: str,
        job_id: str,
        current_iter: str = "",
        *args,
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

    def include_observation(
        self,
        page_to_use: Page,
        coord_observation: tuple[int],
        coord_expand_observation: tuple[int],
        coord_search_observation_by: tuple[int],
        coord_search_observation: tuple[int],
        coord_close_observation_tab: tuple[int],
        observation_to_insert: str,
    ) -> None:
        """Isolate actions for including observation fields."""
        self.logger.info("Incluindo observação.")
        self._click_element(page=page_to_use, element_to_click=coord_observation, delay=2)
        self._click_element(page=page_to_use, element_to_click=coord_expand_observation, delay=2)
        self._click_element(page=page_to_use, element_to_click=coord_search_observation_by, delay=2)
        self._insert_data(
            page=page_to_use,
            element_to_click=coord_search_observation,
            data_to_insert=observation_to_insert,
            delay=2,
        )
        self._click_element(page=page_to_use, element_to_click=coord_close_observation_tab, delay=2)
        self.check_cancelled()

    def set_carrier_info(
        self,
        page_to_use: Page,
        coord_select_carrier: tuple[int],
        coord_search_by_code: tuple[int],
        coord_search_by_name: tuple[int],
        carrier_target: str,
    ) -> None:
        """Isolate actions for setting carrier information."""
        self.logger.info("Definindo informações de transportadora.")
        self._click_element(page=page_to_use, element_to_click=coord_select_carrier, delay=1)
        if self.search_carrier_by == "code":
            self.logger.info(f"Buscando transportadora por código: {carrier_target}.")
            self._click_element(page=page_to_use, element_to_click=coord_search_by_code, delay=1)
        else:
            self.logger.info(f"Buscando transportadora por nome: {carrier_target}.")
            self._click_element(page=page_to_use, element_to_click=coord_search_by_name, delay=1)
