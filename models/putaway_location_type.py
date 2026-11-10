from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PutawayLocationType(models.Model):
    _name = "tha.putaway.location.type"
    _description = "Putaway Location Type"
    _order = "name, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    color = fields.Integer()

    _sql_constraints = [
        ("name_unique", "unique(name)", "Location type names must be unique."),
    ]

    def unlink(self):
        used_locations = self.env["stock.location"].sudo().search_count(
            [("tha_putaway_location_type_id", "in", self.ids)]
        )
        used_products = self.env["product.template"].sudo().search_count(
            [("tha_putaway_location_type_id", "in", self.ids)]
        )
        if used_locations or used_products:
            raise UserError(
                _("Reassign or clear this type on all locations and products before deleting it.")
            )
        return super().unlink()
