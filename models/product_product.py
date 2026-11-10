from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        templates = products.mapped("product_tmpl_id").filtered("tha_putaway_location_type_id")
        if templates:
            templates._tha_sync_putaway_rules()
        return products

    def write(self, vals):
        old_templates = self.mapped("product_tmpl_id") if "product_tmpl_id" in vals else self.env["product.template"]
        result = super().write(vals)
        if {"product_tmpl_id", "active"}.intersection(vals):
            templates = (old_templates | self.mapped("product_tmpl_id")).filtered("tha_putaway_location_type_id")
            if templates:
                templates._tha_sync_putaway_rules()
        return result
