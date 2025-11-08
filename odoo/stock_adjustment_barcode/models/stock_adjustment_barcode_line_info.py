# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import groupby


class StockAdjustmentBarcodeLineInfo(models.Model):
    _name = 'stock.adjustment.barcode.line.info'
    _description = 'Stock Adjustment Barcode Line Information'

    inv_adjustment_id = fields.Many2one(
        comodel_name='stock.adjustment.barcode',
        required=True,
        ondelete='cascade'
    )

    inv_adjustment_line_id = fields.Many2one(
        comodel_name='stock.adjustment.barcode.line',
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        domain="[('type', '=', 'product'), ('id', 'not in', disallowed_product_ids)]",
        required=True,
        check_company=True
    )

    disallowed_product_ids = fields.Many2many(
        comodel_name='product.product',
        compute='_compute_disallowed_product_ids',
        store=False,
        help='Products that are not allowed to be scanned directly (parent products from BOM transfers)'
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    )

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product UoM',
        compute='_compute_product_uom_id',
        readonly=False,
        store=True
    )

    scanned_qty = fields.Float(
        string="Counted Quantity",
        default=1
    )

    scanned_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Scanned By",
        copy=False,
    )

    @api.constrains('scanned_qty')
    def _check_scanned_qty(self):
        """
        Ensures the scanned quantity is greater than or equal to 0.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if self.filtered(lambda l: l.scanned_qty < 0):
            raise ValidationError(_("The counted quantity should be 0 or greater."))



    # @api.constrains('product_id')
    # def _check_disallowed_product(self):
    #     """
    #     Validates that the selected product is not in the disallowed products list.
    #     Prevents manual selection of parent products from BOM transfers.
    #     """
    #     for record in self:
    #         if record.inv_adjustment_id and record.inv_adjustment_id.disallowed_products_json:
    #             disallowed_ids = record.inv_adjustment_id.disallowed_products_json
    #             if record.product_id.id in disallowed_ids:
    #                 raise ValidationError(_(
    #                     f"Product '{record.product_id.name}' is not allowed to be added directly. "
    #                     f"It should appear as a parent product when scanning its child products."))

    @api.constrains('product_id', 'lot_id')
    def _check_existing_lot_product(self):
        """
        Validates that a lot is set for a product if it has already been scanned by another user.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        new_product = self.product_id
        existing_lot_product = self.inv_adjustment_id.inv_adjustment_line_info_ids.filtered(
            lambda p: p.product_id == new_product and p.lot_id)

        if not self.lot_id and existing_lot_product:
            raise ValidationError(_(
                f"Please set a lot number for {new_product.name}, "
                f"as it has already been scanned by a different user with a lot."))

    @api.depends('inv_adjustment_id', 'inv_adjustment_id.disallowed_products_json')
    def _compute_disallowed_product_ids(self):
        """
        Computes the list of disallowed products from the parent adjustment.
        These are parent products that should not be manually selected.
        """
        for record in self:
            if record.inv_adjustment_id and record.inv_adjustment_id.disallowed_products_json:
                disallowed_ids = record.inv_adjustment_id.disallowed_products_json
                record.disallowed_product_ids = [(6, 0, disallowed_ids)]
            else:
                record.disallowed_product_ids = [(6, 0, [])]

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        """
        Computes the default unit of measure (UoM) based on the product.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        for record in self:
            record.product_uom_id = record.product_id.uom_id.id

    @api.onchange('product_uom_id')
    def _onchange_product_uom_id(self):
        """
        Adjusts the scanned quantity based on the selected unit of measure (UoM).
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        self.scanned_qty = self.product_id.uom_id._compute_quantity(
            self.scanned_qty, self.product_uom_id, rounding_method='HALF-UP')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Creates multiple stock adjustment records and triggers the creation of adjustment lines.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        result = super().create(vals_list)
        # Only create adjustment lines if inv_adjustment_line_id is not already set
        # This prevents overriding the line_id when copying from child to parent
        records_without_line = result.filtered(lambda r: not r.inv_adjustment_line_id)
        if records_without_line:
            records_without_line.create_adjustment_lines()
        if not result.scanned_user_id:
            result.scanned_user_id = self.env.user.id
        return result

    def create_adjustment_lines(self):
        """
        Creates stock adjustment lines for products with or without a lot number.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        line_lst = list()
        inv_adjustment_id = self.inv_adjustment_id.id
        lot_adjustment_lines = self.filtered(lambda l: l.lot_id)
        without_lot_lines = self - lot_adjustment_lines
        adjustment_line_obj = self.env['stock.adjustment.barcode.line']

        for lot, record_ids in groupby(lot_adjustment_lines, key=lambda l: l.lot_id):
            existing_line = adjustment_line_obj.search([
                ('product_id', '=', lot.product_id.id), ('inv_adjustment_id', '=', inv_adjustment_id),
                ('lot_id', '=', lot.id)])
            if existing_line:
                existing_line.write({'adjustment_line_info_ids': [(4, r.id) for r in record_ids]})
            else:
                line_lst.append({
                    'lot_id': lot.id,
                    'product_id': lot.product_id.id,
                    'inv_adjustment_id': inv_adjustment_id,
                    'adjustment_line_info_ids': [(4, r.id) for r in record_ids],
                })

        for product, record_ids in groupby(without_lot_lines, key=lambda l: l.product_id):
            existing_line = adjustment_line_obj.search([
                ('product_id', '=', product.id), ('inv_adjustment_id', '=', inv_adjustment_id), ('lot_id', '=', False)])
            if existing_line:
                existing_line.write({'adjustment_line_info_ids': [(4, r.id) for r in record_ids]})
            else:
                line_lst.append({
                    'product_id': product.id,
                    'inv_adjustment_id': inv_adjustment_id,
                    'adjustment_line_info_ids': [(4, r.id) for r in record_ids],
                })

        self.env['stock.adjustment.barcode.line'].create(line_lst)

    def unlink(self):
        """
        Unlinks the record and adjusts related adjustment lines if necessary.
        TASK: https://app.asana.com/0/1208684301479826/1208633382193060/f
        """
        if len(self.inv_adjustment_line_id.adjustment_line_info_ids) == 1:
            self.inv_adjustment_line_id.sudo().unlink()
        return super().unlink()
