# Putaway by Location Type

This Odoo 17 addon creates and maintains product putaway rules from a configurable type shared by product templates and warehouse storage locations.

## Configuration

1. Open **Inventory → Configuration → Putaway Location Types** and create types such as Chiller, Cold Storage, and Dry.
2. Assign a type to each applicable internal sublocation directly under a warehouse's stock location.
3. Assign a type to a product template on its **Inventory** tab. The type applies to all active variants.
4. Use **Synchronize Putaway Rules** on the product form to see the created, updated, removed, and skipped rule summary.

The addon creates one rule per active variant and warehouse, from the warehouse stock location to the single active direct child location assigned the selected type. Warehouses with zero or multiple matches are skipped and included in the summary. A manual rule for the same product and incoming stock location is preserved and treated as a conflict; it prevents creation of a competing managed rule.

Managed rules are synchronized when the product type, active state, or company changes; variants are created, moved, or archived; matching locations are assigned/reassigned, archived, or reparented; and a warehouse is created or its stock location/company changes. Clearing a product type removes its managed rules. Manual rules are never modified or deleted by this addon.

Location types cannot be deleted while assigned to a product or location. Reassign or clear those fields first. Archiving a type does not remove existing assignments or managed rules.

## Access

Inventory users can read and assign existing location types. Inventory managers can create, edit, archive, and delete types, subject to the in-use restriction.

## Validation

The addon was installed and tested in the local `THA17` database. The focused tests cover rule creation for variants, duplicate location matches, manual-rule conflicts, and clearing a product type.
