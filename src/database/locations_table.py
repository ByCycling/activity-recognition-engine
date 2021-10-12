import uuid
from dataclasses import dataclass

from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.extensions import db


@dataclass
class LocationTable(db.Model):
    id: str
    geojson: str
    timestamp: str
    created_at: str
    user_id: str
    delta: str

    __tablename__ = 'locations'

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    geojson = db.Column(JSONB)
    timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    user_id = db.Column(UUID)
    delta = db.Column(db.Integer)