from marshmallow import Schema, fields
from marshmallow.validate import Equal
from typing import List
import datetime as dt


class Coordinate:
    latitude: float
    longitude: float
    altitude: float
    coordinateAccuracy: float
    heading: float
    headingAccuracy: float
    speed: float
    speedAccuracy: float


class CoordinateSchema(Schema):
    latitude = fields.Float()
    longitude = fields.Float()
    altitude = fields.Float()
    coordinateAccuracy = fields.Float()
    heading = fields.Float()
    headingAccuracy = fields.Float()
    speed = fields.Float()
    speedAccuracy = fields.Float()


class Activity:
    type: str
    confidence: float


class _ActivitySchema(Schema):
    type = fields.Str()
    confidence = fields.Float()


class Location:
    timestamp: dt.date
    coordinates: List[Coordinate]
    activity: Activity


class _LocationSchema(Schema):
    timestamp = fields.DateTime()
    coordinates = fields.Nested(CoordinateSchema)
    activity = fields.Nested(_ActivitySchema)


class Ride:
    ride_id: str
    startedAt: dt.date
    endedAt: dt.date
    locations: List[Location]

    def __init__(self, startedAt: dt.date, endedAt: dt.date, locations: List[Location]) -> None:
        self.startedAt = startedAt
        self.endedAt = endedAt
        self.locations = locations


class RideSchema(Schema):
    ride_id = fields.Str()
    startedAt = fields.DateTime()
    endedAt = fields.DateTime()
    locations = fields.List(fields.Nested(_LocationSchema))
