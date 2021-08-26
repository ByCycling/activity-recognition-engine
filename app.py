import os

import jwt
import sentry_sdk
import werkzeug
from flask import Flask, json, request
from flask.views import MethodView
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
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = True


app = Flask(__name__)
app.config.from_object(Config)

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
    app.logger.error('UnprocessableEntity: caught an exception!')
    return e


@blp.route('/locations')
class Locations(MethodView):

    @blp.arguments(LocationSchema)
    @blp.response(201)
    def post(self, new_data):
        """Ping a new location"""
        token = request.headers.get('Authorization').replace("Bearer ", "")
        decoded = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
        print(decoded)

        item = Location(**new_data)

        response = supabase.client.table('locations').insert(
            {'timestamp': item.properties['location_properties']['timestamp'].isoformat(),
             'geojson': json.dumps(item.serialize())}).execute()

        print(response)

        return True


api.register_blueprint(blp)

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')
