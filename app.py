from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint

from src.database import Database
from src.geometry import LocationSchema, Location


class Config:
    API_TITLE = 'Activity Recognition Engine API'
    API_VERSION = 'v0.1'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"


app = Flask(__name__)
app.config.from_object(Config)
api = Api(app)

blp = Blueprint(
    'locations', 'locations',
    description='Operations on locations'
)

db = Database()


@blp.route('/locations')
class Locations(MethodView):

    @blp.arguments(LocationSchema)
    @blp.response(201, LocationSchema)
    def post(self, new_data):
        """Ping a new location"""
        item = Location(**new_data)
        return item


api.register_blueprint(blp)

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')
