from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    tha_putaway_location_type_id = fields.Many2one(
        "tha.putaway.location.type", string="Putaway Location Type", ondelete="restrict"
    )
    tha_putaway_sync_summary = fields.Text(
        string="Last Putaway Synchronization", readonly=True, copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if any(vals.get("tha_putaway_location_type_id") for vals in vals_list):
            records._tha_sync_putaway_rules()
        return records

    def write(self, vals):
        result = super().write(vals)
        relevant = {"tha_putaway_location_type_id", "active", "company_id"}
        if relevant.intersection(vals) and not self.env.context.get("tha_skip_putaway_sync"):
            self._tha_sync_putaway_rules()
        return result

    def _tha_sync_putaway_rules(self):
        Rule = self.env["stock.putaway.rule"].sudo()
        Warehouse = self.env["stock.warehouse"].sudo()
        summaries = []
        for template in self.sudo():
            managed = Rule.search(
                [("tha_location_type_managed", "=", True), ("product_id.product_tmpl_id", "=", template.id)]
            )
            desired = {}
            notes = []
            location_type = template.tha_putaway_location_type_id
            if location_type and template.active and template.type != "service":
                variants = template.product_variant_ids.filtered("active")
                warehouse_domain = []
                if template.company_id:
                    warehouse_domain = [
                        "|",
                        ("company_id", "=", template.company_id.id),
                        ("company_id", "=", False),
                    ]
                warehouses = Warehouse.search(warehouse_domain)
                for warehouse in warehouses:
                    stock = warehouse.lot_stock_id
                    matches = self.env["stock.location"].sudo().search(
                        [
                            ("location_id", "=", stock.id),
                            ("usage", "=", "internal"),
                            ("active", "=", True),
                            ("tha_putaway_location_type_id", "=", location_type.id),
                            "|",
                            ("company_id", "=", warehouse.company_id.id),
                            ("company_id", "=", False),
                        ]
                    )
                    if len(matches) != 1:
                        notes.append(
                            _("%(warehouse)s: expected one %(type)s location, found %(count)s.")
                            % {"warehouse": warehouse.display_name, "type": location_type.display_name, "count": len(matches)}
                        )
                        continue
                    destination = matches
                    for variant in variants:
                        key = (variant.id, stock.id)
                        manual = Rule.search(
                            [
                                ("product_id", "=", variant.id),
                                ("location_in_id", "=", stock.id),
                                ("tha_location_type_managed", "=", False),
                            ],
                            limit=1,
                        )
                        if manual:
                            notes.append(
                                _("%(warehouse)s / %(product)s: manual rule %(rule)s conflicts; skipped.")
                                % {"warehouse": warehouse.display_name, "product": variant.display_name, "rule": manual.display_name}
                            )
                            continue
                        desired[key] = {
                            "product_id": variant.id,
                            "location_in_id": stock.id,
                            "location_out_id": destination.id,
                            "company_id": warehouse.company_id.id,
                            "tha_location_type_managed": True,
                        }

            created = updated = removed = 0
            for key, values in desired.items():
                existing = managed.filtered(
                    lambda rule, k=key: (rule.product_id.id, rule.location_in_id.id) == k
                )[:1]
                if existing:
                    managed -= existing
                    changes = {}
                    for field, value in values.items():
                        current = getattr(existing, field)
                        current_value = current.id if hasattr(current, "id") else current
                        if current_value != value:
                            changes[field] = value
                    if changes:
                        existing.with_company(existing.company_id).write(changes)
                        updated += 1
                else:
                    company = self.env["res.company"].browse(values["company_id"])
                    Rule.with_company(company).create(values)
                    created += 1
            if managed:
                removed = len(managed)
                managed.unlink()

            summary = _("Created: %(created)s; updated: %(updated)s; removed: %(removed)s; skipped: %(skipped)s.") % {
                "created": created,
                "updated": updated,
                "removed": removed,
                "skipped": len(notes),
            }
            if notes:
                summary += "\n" + "\n".join(notes)
            template.with_context(tha_skip_putaway_sync=True).write({"tha_putaway_sync_summary": summary})
            summaries.append("%s: %s" % (template.display_name, summary))
        return "\n".join(summaries)

    def action_tha_sync_putaway_rules(self):
        summary = self._tha_sync_putaway_rules()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Putaway Rules Synchronized"),
                "message": summary or _("No products were synchronized."),
                "type": "warning" if "skipped: 0" not in summary else "success",
                "sticky": True,
            },
        }
