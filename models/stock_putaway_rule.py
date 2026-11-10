from odoo import fields, models


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    tha_location_type_managed = fields.Boolean(
        string="Managed by Location Type", default=False, copy=False, index=True, readonly=True
    )
