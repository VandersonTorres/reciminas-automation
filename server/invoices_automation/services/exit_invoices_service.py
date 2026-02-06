from . import BaseService
from invoices_automation.utils.page_coordinates import ExitInvoicePageCoordinates

# Tipos de Notas de Saídas
# 1. Transferencia de estoque
# 2. Venda comum (dentro do Estado)
# 3. Venda comum (fora do Estado)
# 4. Venda triangular  -  ANA NÃO SABE


class ExitInvoiceService(BaseService, ExitInvoicePageCoordinates):
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
