{
    "name": "Putaway by Location Type",
    "version": "17.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Synchronize product putaway rules with typed warehouse locations",
    "author": "Thein Htoo Aung",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/putaway_location_type_views.xml",
        "views/stock_location_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
}
