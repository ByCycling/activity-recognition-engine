from datetime import datetime

from marshmallow import Schema, fields

from typing import List

### Geometry
from marshmallow.validate import OneOf, Equal


class Geometry:
    type: str
    coordinates: List[float]

    def __init__(self, type: str, coordinates: List[float]) -> None:
        self.type = type
        self.coordinates = coordinates


class GeometrySchema(Schema):
    type = fields.Str(validate=Equal('Point'), default='Point')
    coordinates = fields.List(fields.Float())


### App details

class AppDetails:
    version: str
    environment: str

    def __init__(self, version: str, environment: str) -> None:
        self.version = version
        self.environment = environment


class AppDetailsSchema(Schema):
    version = fields.Str()
    environment = fields.Str(validate=OneOf(['PRODUCTION', 'DEVELOPMENT']), default='PRODUCTION')


### Battery

class Battery:
    is_charging: bool
    level: float

    def __init__(self, is_charging: bool, level: float) -> None:
        self.is_charging = is_charging
        self.level = level


class BatterySchema(Schema):
    is_charging = fields.Bool()
    level = fields.Float()


### Location properties

class Activity:
    type: str
    confidence: float


class ActivitySchema(Schema):
    type = fields.Str()
    confidence = fields.Float()


class LocationProperties:
    timestamp: str
    speed: float
    speed_accuracy: float
    heading: float
    heading_accuracy: int
    coordinate_accuracy: int
    altitude_accuracy: float
    is_mock: bool
    is_sample: bool
    is_moving: bool
    activity: Activity

    def __init__(self, timestamp: str, speed: float, speed_accuracy: int, heading: float, heading_accuracy: int,
                 coordinate_accuracy: int, altitude_accuracy: float, is_mock: bool, is_sample: bool, is_moving: bool,
                 activity: Activity) -> None:
        self.timestamp = timestamp
        self.speed = speed
        self.speed_accuracy = speed_accuracy
        self.heading = heading
        self.heading_accuracy = heading_accuracy
        self.coordinate_accuracy = coordinate_accuracy
        self.altitude_accuracy = altitude_accuracy
        self.is_mock = is_mock
        self.is_sample = is_sample
        self.is_moving = is_moving
        self.activity = activity


class LocationPropertiesSchema(Schema):
    class Meta:
        ordered = True

    timestamp = fields.DateTime('iso')
    speed = fields.Float()
    speed_accuracy = fields.Float()
    heading = fields.Float()
    heading_accuracy = fields.Int()
    coordinate_accuracy = fields.Int()
    altitude_accuracy = fields.Float()
    is_mock = fields.Bool()
    is_sample = fields.Bool()
    is_moving = fields.Bool()
    activity = fields.Nested(ActivitySchema)


### Properties

class Properties:
    location_properties: LocationProperties
    battery: Battery
    app_details: AppDetails

    def __init__(self, location_properties: LocationProperties, battery: Battery, app_details: AppDetails) -> None:
        self.location_properties = location_properties
        self.battery = battery
        self.app_details = app_details


class PropertiesSchema(Schema):
    location_properties = fields.Nested(LocationPropertiesSchema)
    battery = fields.Nested(BatterySchema)
    app_details = fields.Nested(AppDetailsSchema)


# Provider
class Provider():
    accuracyAuthorization: str
    enabled: bool
    gps: bool
    network: bool
    status: int


class ProviderSchema(Schema):
    accuracyAuthorization = fields.Str(allow_none=True)
    enabled = fields.Bool()
    gps = fields.Bool()
    network = fields.Bool()
    status = fields.Int()


### Location

class Location:
    type: str
    geometry: Geometry
    properties: Properties
    provider: Provider

    def __init__(self, type: str, geometry: Geometry, properties: Properties, provider: Provider = None) -> None:
        self.type = type
        self.geometry = geometry
        self.properties = properties
        self.provider = provider

    def serialize(self):
        return self.__dict__


class LocationSchema(Schema):
    class Meta:
        ordered = True

    type = fields.Str(validate=Equal('Feature'), default='Feature')
    geometry = fields.Nested(GeometrySchema)
    properties = fields.Nested(PropertiesSchema)
    provider = fields.Nested(ProviderSchema)
