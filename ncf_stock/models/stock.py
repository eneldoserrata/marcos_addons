# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_id = fields.Many2one("purchase.order", string="Pedido de compra", readonly=True, copy=False)
    refund_action = fields.Selection(
        [('invoice_refund', u"Con nota de crédito solicitada"),
         ("change", "Para realizar cambio")],
        string=u"Tipo de devolución", readonly=True, required=False, copy=False)

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        if self.refund_action == "invoice_refund":
            origin_picking = self.search([('name', '=', self.origin)])

            if origin_picking.purchase_id:
                refund_action = "in_refund"
            elif origin_picking.sale_id:
                refund_action = "out_refund"

            invoice_id = False
            if refund_action == "in_refund":
                invoice_lines = self.env["account.invoice.line"].search(
                    [('purchase_id', '=', origin_picking.purchase_id.id)])
                if invoice_lines:
                    invoice_id = invoice_lines.mapped("invoice_id")
            elif refund_action == "out_refund":
                invoice_lines = self.env["account.invoice.line"].search([('sale_id', '=', origin_picking.sale_id.id)])
                if invoice_lines:
                    invoice_id = invoice_lines.mapped("invoice_id")

            refund_invoice = invoice_id.refund()
            refund_invoice.ncf_required = invoice_id.ncf_required
            refund_invoice.invoice_line_ids.unlink()

            for line in self.move_lines:
                purchase_line_id = line.origin_returned_move_id.purchase_line_id.id
                origin_invoice_line = self.env["account.invoice.line"].search([("purchase_line_id","=",purchase_line_id)])
                new_invoice_line = origin_invoice_line.copy({"invoice_id": refund_invoice.id, "quantity": line.product_qty})
                new_invoice_line._compute_price()

            refund_invoice._compute_amount()


        return res


picking = [{'origin': u'WH/IN/00051', 'message_follower_ids': [745], 'carrier_tracking_ref': False,
            'pack_operation_product_ids': [162], 'number_of_packages': 0, 'date_done': '2016-02-08 04:22:34',
            'message_needaction': False, 'message_channel_ids': [], 'message_partner_ids': [3], 'carrier_id': False,
            'write_uid': (1, u'Administrator'), 'move_lines_related': [194], 'templ_id': (748, u'Classic Template'),
            'package_ids': [], 'launch_pack_operations': False, 'create_date': '2016-02-08 03:24:26',
            'location_id': (12, u'WH/Existencias'), 'message_ids': [1407, 1406, 1405, 1404], 'backorder_id': False,
            'even': u'#FFFFFF', 'create_uid': (1, u'Administrator'), 'display_name': u'WH/OUT/00027', 'weight': 0.0,
            'message_is_follower': True, 'picking_type_id': (2, u'My Company: \xd3rdenes de entrega'),
            'odd': u'#F2F2F2', 'move_type': u'direct', 'message_last_post': False,
            'company_id': (1, u'EYM Importadores SRL'), 'id': 130, 'note': False, 'state': u'done',
            'name_color': u'#F07C4D', 'picking_type_code': u'outgoing', 'picking_type_entire_packs': False,
            'templ_pk_id': (757, u'Classic Template'), 'message_unread_counter': 0, 'weight_bulk': 0.0,
            'weight_uom_id': (3, u'kg'), 'owner_id': False, 'purchase_id': False, 'delivery_type': False,
            '_barcode_scanned': False, 'move_lines': [194], 'name': u'WH/OUT/00027', 'claim_count_out': 0,
            'min_date': '2016-02-08 03:15:35', 'volume': 0.0, 'pk_logo': False, 'refund_action': u'invoice_refund',
            'cust_color': u'#F07C4D', 'printed': False, 'write_date': '2016-02-08 04:22:34', 'message_unread': False,
            'date': '2016-02-08 03:15:35', 'text_color': u'#6B6C6C', 'pack_operation_ids': [162],
            'pack_operation_exist': True, 'theme_color': u'#F07C4D', 'partner_id': (12, u'NEOTECNOLOGY CYBER CITY SRL'),
            'pack_operation_pack_ids': [], 'recompute_pack_op': False, 'carrier_price': 0.0,
            '__last_update': '2016-02-08 04:22:34', 'theme_txt_color': u'#FFFFFF', 'sale_id': False, 'dn_logo': False,
            'location_dest_id': (8, u'Ubicaciones de empresas/Vendedores'), 'max_date': '2016-02-08 03:15:35',
            'quant_reserved_exist': False, 'group_id': (22, u'PO00033'),
            'product_id': (2, u'[1234] Zapatos nuevos para redir la casa'), 'message_needaction_counter': 0,
            'priority': u'1'}]

picking_line = [{'origin': u'PO00033', 'create_date': '2016-02-08 03:24:26', 'move_dest_id': False, 'weight': 0.0,
                 'move_orig_ids': [], 'price_unit': 100.0, 'product_uom_qty': 10.0, 'linked_move_operation_ids': [377],
                 'date': '2016-02-08 03:24:32', 'product_qty': 10.0, 'location_id': (12, u'WH/Existencias'),
                 'availability': 10.0, 'remaining_qty': 0.0, 'priority': u'1',
                 'display_name': u'WH/IN/00051/ 1234: Existencias > Vendedores', 'product_uom': (1, u'Unidad(es)'),
                 'picking_type_id': (2, u'My Company: \xd3rdenes de entrega'),
                 'picking_partner_id': (12, u'NEOTECNOLOGY CYBER CITY SRL'), 'sequence': 10,
                 'company_id': (1, u'EYM Importadores SRL'), 'id': 194, 'note': False, 'state': u'done',
                 'quant_ids': [210],
                 'origin_returned_move_id': (193, u'PO00033/ 1234: Vendedores > Existencias'),
                 'product_packaging': False,
                 'purchase_line_id': False, 'product_tmpl_id': (2, u'Zapatos nuevos para redir la casa'),
                 'weight_uom_id': (3, u'kg'), 'returned_move_ids': [], 'date_expected': '2016-02-08 03:15:35',
                 'procurement_id': False, 'backorder_id': False, 'name': u'[1234] Zapatos nuevos para redir la casa',
                 'create_uid': (1, u'Administrator'), 'string_availability_info': u'',
                 'warehouse_id': (1, u'My Company'),
                 'inventory_id': False, 'partially_available': False, 'propagate': True, 'restrict_partner_id': False,
                 'procure_method': u'make_to_stock', 'scrapped': False, 'write_uid': (1, u'Administrator'),
                 'restrict_lot_id': False, 'partner_id': False, 'group_id': (22, u'PO00033'),
                 'product_id': (2, u'[1234] Zapatos nuevos para redir la casa'), 'route_ids': [3, 2], 'lot_ids': [],
                 '__last_update': '2016-02-08 03:24:32', 'split_from': False, 'picking_id': (130, u'WH/OUT/00027'),
                 'reserved_quant_ids': [], 'reserved_availability': 0.0,
                 'location_dest_id': (8, u'Ubicaciones de empresas/Vendedores'), 'write_date': '2016-02-08 03:24:32',
                 'push_rule_id': False, 'rule_id': False}]

invoice_line = [{'origin': False, 'sale_line_ids': [], 'qty_allow_refund': 20.0, 'create_date': '2016-02-08 03:29:42',
                 'sequence': 0, 'refund_line_ref': (274, u'[1234] Zapatos nuevos para redir la casa'),
                 'price_subtotal': 2000.0, 'write_uid': (1, u'Administrator'), 'currency_id': (74, u'DOP'),
                 'uom_id': (1, u'Unidad(es)'), 'partner_id': (12, u'NEOTECNOLOGY CYBER CITY SRL'), 'id': 276,
                 'purchase_id': (33, u'PO00033'), 'create_uid': (1, u'Administrator'), 'asset_category_id': False,
                 '__last_update': '2016-02-08 03:29:42', 'company_id': (1, u'EYM Importadores SRL'),
                 'tax_amount': 360.0, 'account_analytic_id': False,
                 'purchase_line_id': (43, u'[1234] Zapatos nuevos para redir la casa'), 'price_unit': 100.0,
                 'account_id': (8, u'10140000 MERCANCIA ENTREGADA NO FACTURADA'), 'asset_end_date': False,
                 'discount': 0.0, 'write_date': '2016-02-08 03:29:42', 'price_subtotal_signed': -2000.0,
                 'display_name': u'[1234] Zapatos nuevos para redir la casa',
                 'product_id': (2, u'[1234] Zapatos nuevos para redir la casa'), 'company_currency_id': (74, u'DOP'),
                 'asset_start_date': False, 'name': u'[1234] Zapatos nuevos para redir la casa',
                 'invoice_id': (130, u'Devoluci\xf3n a proveedor '), 'asset_mrr': 0.0, 'invoice_line_tax_ids': [4],
                 'quantity': 20.0}]

invoice = [{'comment': False, 'message_follower_ids': [749], 'date_due': False, 'create_date': '2016-02-08 03:29:42',
            'invoice_logo': False, 'partner_bank_id': False, 'message_needaction': False, 'reference_type': u'none',
            'message_partner_ids': [3], 'number': False, 'company_id': (1, u'EYM Importadores SRL'),
            'currency_id': (74, u'DOP'), 'amount_total_company_signed': -2000.0, 'payment_move_line_ids': [],
            'shop_id': (1, u'Principal'), 'anulation_type': False, 'type': u'in_refund',
            'display_name': u'Devoluci\xf3n a proveedor ', 'odd': u'#F2F2F2', 'message_ids': [1409], 'even': u'#FFFFFF',
            'create_uid': (1, u'Administrator'), 'amount_untaxed': 2000.0, 'reference': False,
            'message_is_follower': True, 'residual_company_signed': 0.0, 'amount_total_signed': -2000.0,
            'message_last_post': False, 'journal_id': (2, u'Facturas de proveedor (DOP)'), 'id': 130, 'amount_tax': 0.0,
            'state': u'draft', 'name_color': u'#F07C4D', 'move_id': False, 'total_discount': 0.0,
            'message_channel_ids': [], 'message_unread_counter': 0, 'incoterms_id': False, 'sent': False,
            'invoice_line_ids': [276], 'purchase_id': False, 'internal_number': False,
            'outstanding_credits_debits_widget': u'false', 'message_needaction_counter': 0,
            'account_id': (25, u'20110000 CUENTAS POR PAGAR'), 'payment_ids': [], 'client_fiscal_type': False,
            'reconciled': True, 'origin': u'A010010010100000001', 'residual': 0.0, 'move_name': False,
            'text_color': u'#6B6C6C', 'date_invoice': '2016-02-08', 'payment_term_id': False, 'cust_color': u'#F07C4D',
            'write_date': '2016-02-08 03:29:42', 'residual_signed': 0.0, 'date': False,
            'user_id': (1, u'Administrator'), 'fiscal_nif': u'false', 'write_uid': (1, u'Administrator'), 'ncf': False,
            'amount_total': 2000.0, 'theme_color': u'#F07C4D', 'company_currency_id': (74, u'DOP'),
            'partner_id': (12, u'NEOTECNOLOGY CYBER CITY SRL'), 'name': False, 'supplier_fiscal_type': u'09',
            'amount_untaxed_signed': -2000.0, '__last_update': '2016-02-08 03:29:42',
            'team_id': (1, u'Ventas directas'), 'picking_id': False, 'has_outstanding': False, 'tax_line_ids': [],
            'fiscal_position_id': (16, u'09 \u2013 Compras y gastos que formaran parte del costo de venta09'),
            'ncf_required': False, 'message_unread': False, 'payments_widget': u'false',
            'template_id': (794, u'Retro Template'), 'commercial_partner_id': (12, u'NEOTECNOLOGY CYBER CITY SRL'),
            'theme_txt_color': u'#FFFFFF'}]
