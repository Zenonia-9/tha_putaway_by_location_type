from odoo import api, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    @api.model_create_multi
    def create(self, vals_list):
        warehouses = super().create(vals_list)
        self._tha_sync_all_typed_products()
        return warehouses

    def write(self, vals):
        result = super().write(vals)
        if {"lot_stock_id", "company_id"}.intersection(vals):
            self._tha_sync_all_typed_products()
        return result

    @api.model
    def _tha_sync_all_typed_products(self):
        templates = self.env["product.template"].sudo().search(
            [("tha_putaway_location_type_id", "!=", False)]
        )
        if templates:
            templates._tha_sync_putaway_rules()
