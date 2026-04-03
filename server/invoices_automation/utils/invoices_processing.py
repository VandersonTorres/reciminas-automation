import time
from typing import Any

from invoices_automation.models import BaseInvoiceModel
from invoices_automation.services import CANCEL_FLAGS
from invoices_automation.services.entry_invoices_service import EntryInvoiceService
from invoices_automation.services.exit_invoices_service.exit_in_state_sale import InStateInvoiceService
from invoices_automation.services.exit_invoices_service.exit_out_state_sale import OutStateInvoiceService
from invoices_automation.services.exit_invoices_service.exit_stock_transfer import StockTransferInvoiceService
from invoices_automation.services.lock_manager import automation_lock
from . import service_class_modality_map

ServiceType = EntryInvoiceService | InStateInvoiceService | OutStateInvoiceService | StockTransferInvoiceService


def build_material_payload(invoice: BaseInvoiceModel) -> list[dict[str, Any]]:
    return [
        {
            "material_code": item.material.code,
            "material_quantity": item.material_quantity,
            "material_price": item.material_price,
            "discount": item.discount,
        }
        for item in invoice.items.all()
    ]


def build_service(service_class: ServiceType, invoice: BaseInvoiceModel, job_id: str, current_iter: str) -> ServiceType:
    serialized_materials = build_material_payload(invoice)

    if service_class is EntryInvoiceService:
        return service_class(
            provider=invoice.provider,
            materials=serialized_materials,
            job_id=job_id,
            current_iter=current_iter,
            close_popup_confirmation=invoice.close_popup,
        )
    elif service_class in (InStateInvoiceService, OutStateInvoiceService, StockTransferInvoiceService):
        return service_class(
            provider=invoice.provider,
            materials=serialized_materials,
            job_id=job_id,
            current_iter=current_iter,
            freight=invoice.freight,
            search_carrier_by=invoice.search_carrier_by,
            carrier_target=invoice.carrier_name or invoice.carrier_code,
            observation=invoice.observation,
        )

    raise ValueError("Invalid service class")


def process_single_invoice(
    service_class: ServiceType,
    invoice: BaseInvoiceModel,
    job_id: str,
    current_iter: str,
) -> None:
    try:
        invoice.status = "processing"
        invoice.save()

        automation = build_service(service_class, invoice, job_id, current_iter)
        invoice_path = automation.run()

        if invoice_path:
            invoice.status = "done"
            invoice.invoice_path = invoice_path.replace("downloads/", "")
        else:
            invoice.status = "cancelled"

    except Exception:
        invoice.status = "cancelled"
    finally:
        invoice.save()


def process_invoice_batch(
    invoices: list[BaseInvoiceModel],
    job_id: str,
) -> None:
    with automation_lock:
        for idx, invoice in enumerate(invoices):
            service_class: ServiceType = service_class_modality_map[invoice.modality]
            if CANCEL_FLAGS.get(job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
                invoice.status = "cancelled"
                invoice.save()
                break

            current_iter = f"{idx + 1}/{len(invoices)}"
            process_single_invoice(service_class, invoice, job_id, current_iter)

            time.sleep(2)

        CANCEL_FLAGS.pop(job_id, None)
        CANCEL_FLAGS.pop("__GLOBAL_CANCEL__", None)
