# app.py

from flask import Flask, jsonify
from flask_restful import Api
from recursos.registro import Registro, Login
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

api = Api(app)

@app.route('/activar_render')
def activar():
    """
    Endpoint simple para despertar API.
    """
    return jsonify({'status': 'ok', 'message': 'Application is running.'})

api.add_resource(Login, '/login')
api.add_resource(Registro, '/register')

if __name__ == "__main__":
    app.run()