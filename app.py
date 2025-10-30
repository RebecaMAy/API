# app.py

from flask import Flask, jsonify
from flask_restful import Api
from recursos.registro import Registro, Login


app = Flask(__name__)
api = Api(app)

@app.route('/activar_render')
def activar():
    """
    Endpoint simple para despertar API.
    """
    return jsonify({'status': 'ok', 'message': 'Application is running.'})

# Ruta para la lista de mediciones (GET, POST)
api.add_resource(Login, '/login')

# Rutas para obtener la última o las 'n' últimas mediciones
api.add_resource(Registro, '/register')

if __name__ == "__main__":
    app.run(debug=True)