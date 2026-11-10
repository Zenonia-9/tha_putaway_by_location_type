from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    tha_putaway_location_type_id = fields.Many2one(
        "tha.putaway.location.type",
        string="Putaway Location Type",
        ondelete="restrict",
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if any(vals.get("tha_putaway_location_type_id") for vals in vals_list):
            self._tha_sync_affected_products(records.mapped("tha_putaway_location_type_id").ids)
        return records

    def write(self, vals):
        relevant = {"tha_putaway_location_type_id", "location_id", "usage", "active", "company_id"}
        old_types = self.mapped("tha_putaway_location_type_id").ids if relevant.intersection(vals) else []
        result = super().write(vals)
        if relevant.intersection(vals):
            type_ids = list(set(old_types + self.mapped("tha_putaway_location_type_id").ids))
            if "location_id" in vals:
                type_ids += self.env["tha.putaway.location.type"].sudo().search([]).ids
            self._tha_sync_affected_products(type_ids)
        return result

    @api.model
    def _tha_sync_affected_products(self, type_ids):
        if not type_ids:
            return
        templates = self.env["product.template"].sudo().search(
            [("tha_putaway_location_type_id", "in", type_ids)]
        )
        if templates:
            templates._tha_sync_putaway_rules()
