import flask
import pydantic as pydantic
from flask import Flask, request, jsonify
from flask.views import MethodView

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker

app = Flask('app')

BaseModel = declarative_base()
PG_DSN = 'postgresql://admin:1111@127.0.0.1:5433/flask_hw'
engine = create_engine(PG_DSN)
Session = sessionmaker(bind=engine)


class Advertisement(BaseModel):
    __tablename__ = 'Advertisements'

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    user = Column(Integer, default=1, nullable=False)

    def json_resp(self):
        return {'id': self.id,
                'created_at': self.created_at,
                'created_by': self.user,
                'title': self.title,
                'description': self.description,
                }


BaseModel.metadata.create_all(engine)


class HttpError(Exception):
    def __init__(self, status_code, error_message):
        self.status_code = status_code
        self.error_message = error_message


@app.errorhandler(HttpError)
def error_handler(error):
    response = jsonify({
        'error': error.error_message
    })
    response.status_code = error.status_code
    return response


class AdvertisementValidator(pydantic.BaseModel):
    title: str
    description: str
    user: int


class AdvertisementView(MethodView):

    def post(self):
        try:
            validated_data = AdvertisementValidator(**request.json).dict()
        except pydantic.ValidationError as er:
            raise HttpError(400, er.errors())

        with Session() as session:
            new_adv = Advertisement(**validated_data)
            session.add(new_adv)
            session.commit()
            return flask.jsonify({'new_adv_id': new_adv.id})

    def get(self, adv_id):
        with Session() as session:
            adv = session.query(Advertisement).get(adv_id)
            if adv is None:
                raise HttpError(404, 'Advertisement not found')
            response = adv.json_resp()
            return flask.jsonify(response)

    def delete(self, adv_id):
        with Session() as session:
            adv = session.query(Advertisement).get(adv_id)
            if adv is None:
                raise HttpError(404, 'Advertisement not found')
            session.delete(adv)
            session.commit()
            return flask.jsonify({'deleted?': 'yes'})


app.add_url_rule('/adv/', view_func=AdvertisementView.as_view('adv_post'), methods=['POST'])
app.add_url_rule('/adv/<int:adv_id>', view_func=AdvertisementView.as_view('adv_get'), methods=['GET'])
app.add_url_rule('/adv/<int:adv_id>', view_func=AdvertisementView.as_view('adv_delete'), methods=['DELETE'])


app.run()
