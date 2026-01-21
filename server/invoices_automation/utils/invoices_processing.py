import time

from invoices_automation.services.lock_manager import automation_lock
from invoices_automation.services import CANCEL_FLAGS
from invoices_automation.services.invoices_service import EntryInvoiceService


def build_material_payload(invoice):
    return [
        {
            "material_code": item.material.code,
            "material_quantity": item.material_quantity,
            "material_price": item.material_price,
            "discount": item.discount,
        }
        for item in invoice.items.all()
    ]


def process_single_invoice(
    invoice,
    job_id,
    current_iter=None,
):
    try:
        invoice.status = "processing"
        invoice.save()

        automation = EntryInvoiceService(
            provider=invoice.provider,
            materials=build_material_payload(invoice),
            job_id=job_id,
            current_iter=current_iter,
            close_popup_confirmation=invoice.close_popup,
        )

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


def process_invoice_batch(invoices, job_id):
    with automation_lock:
        for idx, invoice in enumerate(invoices):
            if CANCEL_FLAGS.get(job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
                invoice.status = "cancelled"
                invoice.save()
                break

            current_iter = f"{idx + 1}/{len(invoices)}"
            process_single_invoice(invoice, job_id, current_iter)

            time.sleep(2)

        CANCEL_FLAGS.pop(job_id, None)
        CANCEL_FLAGS.pop("__GLOBAL_CANCEL__", None)
