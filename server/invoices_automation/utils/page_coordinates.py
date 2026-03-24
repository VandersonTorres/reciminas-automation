class BasePageCoordinates:
    """
    Base class for page coordinates.
    Defines X/ Y axis based coordinates of the main operations.

    Inject the following JS into the devtools.console to discover coordinates per click:
        .. code-block:: javascript
            document.addEventListener("click", function(event) {
                console.log("Coordinates (viewport): (", event.clientX, ",", event.clientY, ")");
            });
    """

    # Initial login process
    coord_initial_ticker_selection = (72, 384)
    coord_user_insertion = (366, 365)
    coord_password_insertion = (430, 430)
    coord_log_in = (365, 583)

    # Main page operations
    coord_fiscal_tab = (511, 30)
    coord_invoice_control = (534, 55)
    coord_register = (30, 627)

    # Provider selection process
    coord_locate_provider = (1122, 138)
    coord_provider_search_bar = (417, 533)
    coord_provider_selection = (414, 236)

    # Material inclusion process
    coord_include_provider = (199, 478)
    coord_insert_mat_code = (248, 63)
    coord_quantity_selection = (322, 212)
    coord_confirm_mat = (1011, 600)
    coord_close_mat_confirmation = (950, 415)
    coord_price = (463, 210)
    coord_discount = (666, 212)
    coord_store_progress = (618, 703)

    # Charging and payment process
    coord_charging = (517, 174)
    coord_exclude = (961, 476)
    coord_confirm_exclusion = (709, 483)  # Before: (671, 440)
    coord_payments = (904, 236)
    coord_no_payments = (791, 496)

    # Invoice visualization process
    coord_see_invoice = (822, 662)
    coord_confirm_storage = (709, 445)
    coord_adapt_visibility = (351, 38)
    coord_see_fullscreen = (500, 37)

    # Invoice saving and transmission process
    coord_save_job = (943, 662)
    coord_transmit_invoice = (712, 430)
    coord_dont_see = (763, 430)
    coord_dont_send_email = (791, 430)

    # Utils coordinates
    coord_empty_space = (30, 10)
    coord_close_unwanted_popup = (782, 441)
    coord_close_unwanted_popup_alt = (713, 444)


class EntryInvoicePageCoordinates(BasePageCoordinates):
    """Entry Invoices specific page operational coordinates."""

    pass


class ExitInvoicePageCoordinates(BasePageCoordinates):
    """Exit Invoices specific page operational coordinates.

    In State Sale (Venda comum) process.
    """

    # Initial login process

    # Main page operations

    # Set operation type
    coord_operation = (450, 79)
    coord_select_exit = (409, 119)

    # Provider selection process
    coord_provider_search_bar = (417, 498)
    coord_provider_selection = (414, 270)
    # Material inclusion process

    # Set freight information
    coord_transport_and_volumes = (412, 176)
    coord_freight_by = (319, 252)

    # Set carrier information
    coord_select_carrier = (1114, 254)
    coord_search_by_code = (328, 259)
    coord_search_by_name = (520, 260)
    coord_search_carrier = (417, 487)
    coord_confirm_carrier = (443, 279)

    # Charging and payment process

    # Observation inclusion process
    coord_observation = (674, 175)
    coord_expand_observation = (1116, 224)
    coord_search_observation_by_name = (184, 157)
    coord_search_observation = (214, 560)
    coord_close_observation_tab = (1214, 104)

    # Invoice visualization process

    # Invoice saving and transmission process


class StockTransferInvoicePageCoordinates(ExitInvoicePageCoordinates):
    """(Exit) Stock Transfer Invoices specific page operational coordinates.

    Stock Transfer process (Transferência de Estoque).
    """

    # Initial login process

    # Main page operations

    # Set operation type

    # Provider selection process
    coord_select_provider_by_code = (595, 255)

    # Select product transfer
    coord_operation_nature = (1025, 80)
    coord_operation_nature_search_bar = (429, 517)
    coord_close_selection = (1022, 556)

    # Material inclusion process
    # No discount to this invoice
    # Click on "código de situação tributária CST"
    coord_tax_situation_code = (777, 406)
    # Select 41 (No taxation)
    coord_no_taxation = (703, 537)
    coord_pis = (288, 344)
    coord_tsc_pis = (317, 409)
    # Select 08 (No incidence)
    coord_no_incidence_pis = (318, 514)
    coord_cofins = (343, 344)
    coord_tsc_cofins = (398, 408)
    # Select 08 (No incidence)
    coord_no_incidence_cofins = (403, 514)
    coord_tsc_store_progress = (625, 697)

    # Set Transport and Volumes

    # Set carrier information by code ("18 - RECIMINAS" || "25 - SUCATRANS")

    # Charging and payment process

    # Observation inclusion process
    coord_search_observation_by_code = (83, 155)
    # Enter with the code "4" (referring to the transfer between establishments of the same owner)

    # Invoice visualization process

    # Invoice saving and transmission process
