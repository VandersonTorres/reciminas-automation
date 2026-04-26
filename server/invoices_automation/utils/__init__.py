from invoices_automation.services.entry_invoices_service import EntryInvoiceService
from invoices_automation.services.exit_invoices_service.exit_in_state_sale import InStateInvoiceService
from invoices_automation.services.exit_invoices_service.exit_out_state_sale import OutStateInvoiceService
from invoices_automation.services.exit_invoices_service.exit_stock_transfer import StockTransferInvoiceService


service_class_modality_map = {
    "entry": EntryInvoiceService,
    "exit_instate": InStateInvoiceService,
    "exit_outstate": OutStateInvoiceService,
    "exit_stock_transfer": StockTransferInvoiceService,
}
