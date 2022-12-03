from http import HTTPStatus

from app.apis import api_blueprint as api
from flask_restful import Resource

from app.exambank.models import Specification


class SpecificationResource(Resource):
    def get(self):
        data = []
        for spec in Specification.query:
            data.append(spec.to_dict())

        return data, HTTPStatus.OK
