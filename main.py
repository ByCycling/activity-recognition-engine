import datetime
import os

import sentry_sdk
import werkzeug
from flask import Flask, json, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, JWTManager, current_user
from flask_smorest import Api, Blueprint
from numpy import datetime64
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException

from src.legacy.graph import show
from src.legacy.ride import RideSchema


class Config:
    API_TITLE = "Activity Recognition Engine API"
    API_VERSION = "v0.1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"
    JWT_HEADER_NAME = "Authorization"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")


def create_app(config_object=Config):
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_object)

    return app


app = create_app()

jwt = JWTManager(app)

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_URI"),
    integrations=[FlaskIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    request_bodies="always",
)

api = Api(app)

blp = Blueprint(
    "locations",
    "locations",
    description="Operations on locations",
)


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


@blp.route("/legacy/filter")
class Legacy(MethodView):
    @blp.arguments(RideSchema)
    @blp.response(201)
    def post(self, ride_data):
        """Process ride data"""

        import pandas as pd
        from src.legacy.simplification import simplification

        input_df = pd.json_normalize(ride_data["locations"])

        output_df = simplification(input_df)
        app.logger.debug("-- performing second simplification pass --")
        output_df = simplification(output_df)

        def timestamp_to_string(timestamp: datetime64):
            return pd.Timestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        output = {
            "startedAt": timestamp_to_string(output_df.index[0]),
            "endedAt": timestamp_to_string(output_df.index[len(output_df.index) - 1]),
            "locations": [],
        }

        for i in output_df.index:
            _raw = output_df.loc[i].to_json(orient="columns", default_handler=str)
            _data = json.loads(_raw)

            output["locations"].append(
                {
                    "timestamp": timestamp_to_string(i),
                    "activity": {
                        "type": _data["activity.type"],
                        "confidence": _data["activity.confidence"],
                    },
                    "coordinates": {
                        "coordinateAccuracy": _data["coordinates.coordinateAccuracy"],
                        "speedAccuracy": _data["coordinates.speedAccuracy"],
                        "heading": _data["coordinates.heading"],
                        "altitude": _data["coordinates.altitude"],
                        "latitude": _data["coordinates.latitude"],
                        "longitude": _data["coordinates.longitude"],
                        "headingAccuracy": _data["coordinates.headingAccuracy"],
                        "speed": _data["coordinates.speed"],
                    },
                }
            )

        return output


api.register_blueprint(blp)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
