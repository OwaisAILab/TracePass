from app.extensions import db


class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    origin_country = db.Column(db.String(100), nullable=True)
    sustainability_notes = db.Column(db.Text, nullable=True)

    product_links = db.relationship("ProductMaterial", back_populates="material", lazy="dynamic")

    def __repr__(self):
        return f"<Material {self.name}>"
