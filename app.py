# app.py

#LIBRERIAS
from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

# Importamos los recursos creados
from recursos.CorreoVerificacion import EnviarVerificacion
from recursos.CorreoRecuperacion import EnviarRecuperacion
from recursos.registro import Registro, Login

app = Flask(__name__)
# Permitir peticiones desde cualquier origen ***IMPORTANTE para funcionar desde PLESK
CORS(app)
api = Api(app)

#Se mantiene este endpoint para no modificar la web
@app.route('/activar_render')
def activar():
    """
    Endpoint simple para despertar API.
    """
    return jsonify({'status': 'ok', 'message': 'Application is running.'})

@app.route('/', methods=['GET'])
def status_check():
    """
    Endpoint simple para mantener el servicio activo en Render
    y verificar que la API está en línea.

    GET https://api-envio-correos.onrender.com/
    """
    return jsonify({
        'status': 'online', 
        'message': 'Breathe Tracking API is running.'
    }), 200

# --- Mapeo de Recursos a Endpoints ---
# Endpoint: POST /email/verificacion
# Body esperado: { "email": "...", "token": "..." }
api.add_resource(EnviarVerificacion, '/email/verificacion')

# Endpoint: POST /email/recuperacion
# Body esperado: { "email": "...", "token": "..." }
api.add_resource(EnviarRecuperacion, '/email/recuperacion')

api.add_resource(Login, '/login')
api.add_resource(Registro, '/register')

if __name__ == '__main__':
    # debug=True solo para desarrollo local
    app.run(debug=False)