import time
from typing import Any

from invoices_automation.models import BaseInvoiceModel
from invoices_automation.services import CANCEL_FLAGS
from invoices_automation.services.entry_invoices_service import EntryInvoiceService
from invoices_automation.services.exit_invoices_service import ExitInvoiceService
from invoices_automation.services.lock_manager import automation_lock

ServiceType = EntryInvoiceService | ExitInvoiceService


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
    if service_class is EntryInvoiceService:
        return service_class(
            provider=invoice.provider,
            materials=build_material_payload(invoice),
            job_id=job_id,
            current_iter=current_iter,
            close_popup_confirmation=invoice.close_popup,
        )
    elif service_class is ExitInvoiceService:
        return service_class(
            provider=invoice.provider,
            materials=build_material_payload(invoice),
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
    service_class: ServiceType,
    invoices: list[BaseInvoiceModel],
    job_id: str,
) -> None:
    with automation_lock:
        for idx, invoice in enumerate(invoices):
            if CANCEL_FLAGS.get(job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
                invoice.status = "cancelled"
                invoice.save()
                break

            current_iter = f"{idx + 1}/{len(invoices)}"
            process_single_invoice(service_class, invoice, job_id, current_iter)

            time.sleep(2)

        CANCEL_FLAGS.pop(job_id, None)
        CANCEL_FLAGS.pop("__GLOBAL_CANCEL__", None)
