class BasePageCoordinates:
    """
    Base class for page coordinates.
    Defines X/ Y axis based coordinates of the main operations.

    Inject the following JS into the devtools.console to discover coordinates per click:
        ```
        document.addEventListener("click", function(event) {
            console.log("Coordinates (viewport): (", event.clientX, ",", event.clientY, ")");
        });
        ```
    """

    coord_initial_ticker_selection = (72, 384)
    coord_user_insertion = (366, 365)
    coord_password_insertion = (390, 421)
    coord_log_in = (365, 583)
    coord_fiscal_tab = (511, 30)
    coord_empty_space = (30, 10)
    coord_close_unwanted_popup = (782, 441)
    coord_close_unwanted_popup_alt = (713, 444)


class EntryInvoicePageCoordinates(BasePageCoordinates):
    """Entry Invoices specific page operational coordinates."""

    coord_invoice_control = (534, 55)
    coord_register = (30, 627)
    coord_locate_provider = (1122, 138)
    coord_provider_search_bar = (417, 533)
    coord_provider_selection = (414, 236)
    coord_include_provider = (199, 478)
    coord_insert_mat_code = (248, 63)
    coord_quantity_selection = (322, 212)
    coord_confirm_mat = (1011, 600)
    coord_close_mat_confirmation = (950, 415)
    coord_price = (463, 210)
    coord_discount = (666, 212)
    coord_store_progress = (618, 703)
    coord_charging = (517, 174)
    coord_exclude = (961, 476)
    coord_confirm_exclusion = (671, 440)
    coord_payments = (904, 236)
    coord_no_payments = (791, 496)
    coord_see_invoice = (822, 662)
    coord_confirm_storage = (709, 445)
    coord_adapt_visibility = (351, 38)
    coord_see_fullscreen = (500, 37)
    coord_close_visualization = (761, 42)
    coord_save_job = (913, 615)
    coord_transmit_invoice = (712, 413)
    coord_dont_see = (763, 414)
    coord_dont_send_email = (791, 415)
