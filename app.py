import datetime
import os

from src.extensions import db
import sentry_sdk
import werkzeug
from flask import Flask, json, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, JWTManager, current_user
from flask_smorest import Api, Blueprint
from numpy import datetime64
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException

from src.database.database import Supabase
from src.database.locations_table import LocationTable
from src.schemas.location import LocationSchema, Location
from src.legacy.graph import show
from src.legacy.ride import RideSchema


class Config:
    API_TITLE = 'Activity Recognition Engine API'
    API_VERSION = 'v0.1'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"
    JWT_HEADER_NAME = 'Authorization'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('POSTGRES_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def create_app(config_object=Config):
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)

    return app


def register_extensions(app):
    db.init_app(app)


app = create_app()

jwt = JWTManager(app)

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_URI"),
    integrations=[FlaskIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    request_bodies='always'
)

api = Api(app)

blp = Blueprint(
    'locations', 'locations',
    description='Operations on locations',
)

supabase = Supabase()


# @app.before_request
# def log_request_info():
#     app.logger.info('Headers: %s', request.headers)
#     app.logger.info('Body: %s', request.get_data())


@app.errorhandler(werkzeug.exceptions.UnprocessableEntity)
def handle_bad_request(e: werkzeug.exceptions.UnprocessableEntity):
    sentry_sdk.capture_exception(e)
    return e.response


# Register a callback function that loades a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data) -> str:
    return jwt_data["sub"]


@blp.route('/locations')
class Locations(MethodView):

    @blp.arguments(LocationSchema)
    @blp.response(201)
    @jwt_required(locations='headers')
    def post(self, new_data):
        """Ping a new location"""
        item = Location(**new_data)

        response = supabase.client.table('locations').insert(
            {
                'timestamp': item.properties['location_properties']['timestamp'].isoformat(),
                'geojson': json.loads(json.dumps(item.serialize())),
                'user_id': "" + current_user
            }).execute()

        print(response)

        return True

    @blp.response(200, LocationSchema)
    @jwt_required(locations='headers')
    def get(self):
        """Fetch locations"""

        def to_date(date_string):
            try:
                return datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S").date()
            except ValueError:
                raise ValueError('{} is not valid date in the format YYYY-MM-DDTH:M:S'.format(date_string))

        start = to_date(request.args.get('start', default=datetime.date.today().isoformat()))
        end = to_date(request.args.get('end', default=datetime.date.today().isoformat()))

        query = LocationTable.query.filter(
            LocationTable.timestamp >= start,
            LocationTable.timestamp <= end
        ).all()

        def format_timestamp(geojson: dict):
            geojson['properties']['location_properties']['timestamp'] = datetime.datetime.strptime(
                geojson['properties']['location_properties']['timestamp'], '%a, %d %b %Y %H:%M:%S %Z'
            ).strftime("%Y-%m-%dT%H:%M:%S")
            return geojson

        return jsonify(list(map(lambda x: format_timestamp(x.geojson), query)))


@blp.route('/legacy/filter')
class Legacy(MethodView):

    @blp.arguments(RideSchema)
    @blp.response(201)
    def post(self, ride_data):
        """Process ride data"""

        import pandas as pd
        from src.legacy.simplification import simplification

        input_df = pd.json_normalize(ride_data['locations'])

        output_df = simplification(input_df)
        app.logger.debug('-- performing second simplification pass --')
        output_df = simplification(output_df)

        def timestamp_to_string(timestamp: datetime64):
            return pd.Timestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        output = {
            'startedAt': timestamp_to_string(output_df.index[0]),
            'endedAt': timestamp_to_string(output_df.index[len(output_df.index) - 1]),
            'locations': []
        }

        for i in output_df.index:
            _raw = output_df.loc[i].to_json(orient='columns', default_handler=str)
            _data = json.loads(_raw)

            output['locations'].append({
                "timestamp": timestamp_to_string(i),
                "activity": {
                    "type": _data['activity.type'],
                    "confidence": _data['activity.confidence']
                },
                "coordinates": {
                    "coordinateAccuracy": _data['coordinates.coordinateAccuracy'],
                    "speedAccuracy": _data['coordinates.speedAccuracy'],
                    "heading": _data['coordinates.heading'],
                    "altitude": _data['coordinates.altitude'],
                    "latitude": _data['coordinates.latitude'],
                    "longitude": _data['coordinates.longitude'],
                    "headingAccuracy": _data['coordinates.headingAccuracy'],
                    "speed": _data['coordinates.speed']
                }
            })

        database_response = supabase.client.table('filter_results').insert({
            'legacy_ride_id': ride_data['ride_id'],
            'image_base64': show(input_df, output_df),
            'json_before': request.get_json(),
            'json_after': output
        }).execute()

        if database_response['status_code'] > 299:
            sentry_sdk.capture_exception(
                HTTPException(description=database_response['data']['message']))

        return output


api.register_blueprint(blp)

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')
