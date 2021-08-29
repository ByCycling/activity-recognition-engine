import os

import jwt
import sentry_sdk
import werkzeug
from flask import Flask, json, request
from flask.views import MethodView
from flask_jwt_extended import jwt_required, JWTManager, current_user
from flask_smorest import Api, Blueprint
from sentry_sdk.integrations.flask import FlaskIntegration

from src.database import Supabase
from src.geometry import LocationSchema, Location


class Config:
    API_TITLE = 'Activity Recognition Engine API'
    API_VERSION = 'v0.1'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"
    JWT_HEADER_NAME = 'Authorization'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')


app = Flask(__name__)
app.config.from_object(Config)

jwt = JWTManager(app)

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_URI"),
    integrations=[FlaskIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

api = Api(app)

blp = Blueprint(
    'locations', 'locations',
    description='Operations on locations',
)

supabase = Supabase()


@app.before_request
def log_request_info():
    app.logger.info('Headers: %s', request.headers)
    app.logger.info('Body: %s', request.get_data())


@app.errorhandler(werkzeug.exceptions.UnprocessableEntity)
def handle_bad_request(e):
    sentry_sdk.capture_exception(e)
    return e


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


api.register_blueprint(blp)

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')
