# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""Seed roles, admin, and a multi-industry starter catalog for TracePass."""
import os
from app import create_app
from app.extensions import db
from app.models.role import Role, ALL_ROLES, ROLE_ADMIN
from app.models.user import User
from app.models.industry import Industry
from app.models.product_category import ProductCategory
from app.models.product_template import ProductTemplate, TemplateField

app = create_app()

STARTER = {
    "Apparel": {
        "description": "Garments, textiles and footwear products.",
        "categories": [("Shirt", "Finished shirts and tops"), ("Trousers", "Formal and casual trousers"), ("Footwear", "Shoes and footwear products")],
        "template": ("Apparel Product", [("material_composition","Material Composition","text",True,"e.g. 100% cotton"),("country_of_origin","Country of Origin","text",True,None),("recycled_content","Recycled Content (%)","number",False,None)])
    },
    "Batteries": {
        "description": "Portable, industrial and electric-vehicle batteries.",
        "categories": [("EV Battery", "Electric vehicle battery packs"), ("Portable Battery", "Portable rechargeable batteries")],
        "template": ("Battery Product", [("chemistry","Battery Chemistry","text",True,"e.g. LFP"),("capacity_kwh","Capacity (kWh)","number",True,None),("voltage","Nominal Voltage","number",False,"Volts")])
    },
    "Electronics": {
        "description": "Electrical and electronic equipment and components.",
        "categories": [("Smart Device", "Connected consumer electronics"), ("Electronic Component", "Electronic components and modules")],
        "template": ("Electronics Product", [("model_number","Model Number","text",True,None),("energy_rating","Energy Rating","text",False,None),("repairability","Repairability Information","textarea",False,None)])
    },
    "Furniture": {
        "description": "Furniture and interior products.",
        "categories": [("Office Furniture", "Office desks, chairs and furniture"), ("Home Furniture", "Residential furniture")],
        "template": ("Furniture Product", [("primary_material","Primary Material","text",True,None),("country_of_origin","Country of Origin","text",True,None),("recyclability","Recyclability","text",False,None)])
    },
    "Automotive": {
        "description": "Vehicles, parts and components.",
        "categories": [("Automotive Component", "Vehicle parts and components"), ("EV Component", "Electric vehicle components")],
        "template": ("Automotive Component", [("part_number","Part Number","text",True,None),("material","Primary Material","text",False,None),("production_country","Production Country","text",True,None)])
    },
    "Packaging": {
        "description": "Packaging and packaging components.",
        "categories": [("Consumer Packaging", "Packaging for consumer products"), ("Industrial Packaging", "Industrial and transport packaging")],
        "template": ("Packaging Product", [("material","Packaging Material","text",True,None),("recycled_content","Recycled Content (%)","number",False,None),("recyclability","Recyclability","text",True,None)])
    },
}

# Bundled placeholder images (app/static/images/industries/) used only to seed demo
# industries with a card image out of the box. Real admin-created industries store
# their uploaded image under UPLOAD_FOLDER/industry_images instead — see app/admin/routes.py.
STARTER_IMAGES = {
    "Apparel": "/static/images/industries/apparel.jpg",
    "Batteries": "/static/images/industries/batteries.jpg",
    "Electronics": "/static/images/industries/electronics.jpg",
    "Furniture": "/static/images/industries/furniture.jpg",
    "Automotive": "/static/images/industries/automotive.jpg",
    "Packaging": "/static/images/industries/packaging.jpg",
}

with app.app_context():
    for role_name in ALL_ROLES:
        if not Role.query.filter_by(name=role_name).first(): db.session.add(Role(name=role_name, permissions=""))
    db.session.commit()

    for industry_name, spec in STARTER.items():
        industry = Industry.query.filter_by(name=industry_name).first()
        if not industry:
            industry = Industry(name=industry_name, description=spec["description"], image_url=STARTER_IMAGES.get(industry_name))
            db.session.add(industry); db.session.flush()
        elif not industry.image_url and industry_name in STARTER_IMAGES:
            industry.image_url = STARTER_IMAGES[industry_name]
        template_name, fields = spec["template"]
        template = ProductTemplate.query.filter_by(name=template_name).first()
        if not template:
            template = ProductTemplate(name=template_name, industry_id=industry.id, description=f"Generic {industry_name} passport template")
            db.session.add(template); db.session.flush()
            for idx, (key,label,ftype,required,help_text) in enumerate(fields):
                db.session.add(TemplateField(template_id=template.id,key=key,label=label,field_type=ftype,required=required,help_text=help_text,sort_order=idx))
        for cat_name, desc in spec["categories"]:
            category = ProductCategory.query.filter_by(name=cat_name).first()
            if not category:
                category = ProductCategory(name=cat_name, description=desc, industry_id=industry.id, template_id=template.id)
                db.session.add(category)
            else:
                category.industry_id = industry.id
                category.template_id = template.id
    db.session.commit()

    admin_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@tracepass.example")
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe123!")
    if not User.query.filter_by(email=admin_email).first():
        admin_role = Role.query.filter_by(name=ROLE_ADMIN).first()
        admin = User(name="System Administrator", email=admin_email, role_id=admin_role.id)
        admin.set_password(admin_password); db.session.add(admin); db.session.commit()
        print(f"Default admin created: {admin_email} / {admin_password}")
    else: print("Default admin already exists — skipped.")
    print("Multi-industry starter catalog ensured.")
