from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPutawayByLocationType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.assertTrue(cls.warehouse, "A warehouse is required for this test.")
        cls.location_type = cls.env["tha.putaway.location.type"].create(
            {"name": "Test Chiller"}
        )
        cls.destination = cls.env["stock.location"].create(
            {
                "name": "Test Chiller",
                "location_id": cls.warehouse.lot_stock_id.id,
                "usage": "internal",
                "company_id": cls.company.id,
                "tha_putaway_location_type_id": cls.location_type.id,
            }
        )
        cls.template = cls.env["product.template"].create(
            {
                "name": "Putaway Type Test Product",
                "type": "consu",
                "tha_putaway_location_type_id": cls.location_type.id,
            }
        )

    def _managed_rules(self):
        return self.env["stock.putaway.rule"].search(
            [
                ("product_id", "in", self.template.product_variant_ids.ids),
                ("tha_location_type_managed", "=", True),
            ]
        )

    def test_sync_creates_rule_for_each_variant(self):
        summary = self.template._tha_sync_putaway_rules()
        rules = self._managed_rules()
        self.assertEqual(len(rules), len(self.template.product_variant_ids))
        self.assertTrue(all(rule.location_in_id == self.warehouse.lot_stock_id for rule in rules))
        self.assertTrue(all(rule.location_out_id == self.destination for rule in rules))
        self.assertIn("Created:", summary)

    def test_duplicate_matching_locations_are_reported_and_rules_removed(self):
        self.template._tha_sync_putaway_rules()
        self.env["stock.location"].create(
            {
                "name": "Second Test Chiller",
                "location_id": self.warehouse.lot_stock_id.id,
                "usage": "internal",
                "company_id": self.company.id,
                "tha_putaway_location_type_id": self.location_type.id,
            }
        )
        summary = self.template._tha_sync_putaway_rules()
        self.assertFalse(self._managed_rules())
        self.assertIn("found 2", summary)

    def test_conflicting_manual_rule_is_left_untouched(self):
        manual = self.env["stock.putaway.rule"].create(
            {
                "product_id": self.template.product_variant_id.id,
                "location_in_id": self.warehouse.lot_stock_id.id,
                "location_out_id": self.warehouse.lot_stock_id.id,
                "company_id": self.company.id,
            }
        )
        summary = self.template._tha_sync_putaway_rules()
        self.assertEqual(manual.location_out_id, self.warehouse.lot_stock_id)
        self.assertFalse(self._managed_rules().filtered(lambda rule: rule.product_id == manual.product_id))
        self.assertIn("conflicts", summary)

    def test_clearing_product_type_removes_only_managed_rules(self):
        self.template._tha_sync_putaway_rules()
        manual = self.env["stock.putaway.rule"].create(
            {
                "product_id": self.template.product_variant_id.id,
                "location_in_id": self.warehouse.lot_stock_id.id,
                "location_out_id": self.warehouse.lot_stock_id.id,
                "company_id": self.company.id,
            }
        )
        self.template.tha_putaway_location_type_id = False
        self.assertFalse(self._managed_rules())
        self.assertTrue(manual.exists())

    def test_location_type_reassignment_resynchronizes_products(self):
        self.template._tha_sync_putaway_rules()
        other_type = self.env["tha.putaway.location.type"].create(
            {"name": "Test Dry"}
        )
        self.destination.tha_putaway_location_type_id = other_type
        self.template.tha_putaway_location_type_id = other_type
        rules = self._managed_rules()
        self.assertEqual(len(rules), len(self.template.product_variant_ids))
        self.assertTrue(all(rule.location_out_id == self.destination for rule in rules))

    def test_reparenting_location_removes_no_longer_matching_rule(self):
        self.template._tha_sync_putaway_rules()
        inner_parent = self.env["stock.location"].create(
            {
                "name": "Inner Parent",
                "location_id": self.warehouse.lot_stock_id.id,
                "usage": "internal",
                "company_id": self.company.id,
            }
        )
        self.destination.location_id = inner_parent
        self.assertFalse(self._managed_rules())
        self.assertIn("found 0", self.template.tha_putaway_sync_summary)

    def test_type_cannot_be_deleted_while_assigned(self):
        with self.assertRaises(UserError):
            self.location_type.unlink()
