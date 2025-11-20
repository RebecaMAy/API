from flask import request
from flask_restful import Resource
from datetime import datetime

from recursos.lib.ConexionBBDD import db


class Usuario(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")

        if not email:
            return {"status": "error", "message": "Email requerido"}, 400
        """Devuelve los datos del usuario sin procesar"""
        doc_ref = db.collection('usuarios').document(email)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {'status': 'error', 'message': 'Usuario no encontrado'}, 404
            
        data = doc.to_dict()
        
        # Convertir la fecha de Firestore a String para que PHP la entienda
        validez = data.get('validez')
        if validez:
            try:
                # Convertir a ISO string
                data['validez'] = validez.isoformat() 
            except:
                data['validez'] = str(validez)

        return {'status': 'success', 'data': data}, 200

    def put(self):
        """Actualiza campos específicos del usuario"""
        data = request.get_json()
        email = data.get("email")

        if not email:
            return {"status": "error", "message": "Email requerido"}, 400
            
        doc_ref = db.collection('usuarios').document(email)
        
        update_data = {}
        
        # Solo actualizamos lo que nos llegue
        if 'token' in data:
            update_data['token'] = data['token']
            
        if 'estado_token' in data:
            update_data['estado_token'] = int(data['estado_token'])
            
        if 'validez' in data:
            # PHP nos enviará la fecha como string, hay que convertirla para Firestore
            # O guardarla como datetime nativo de Python
            fecha_str = data['validez']
            try:
                # Asumiendo formato ISO que envía PHP
                update_data['validez'] = datetime.fromisoformat(fecha_str)
            except ValueError:
                update_data['validez'] = datetime.now()

        if update_data:
            doc_ref.update(update_data)
            return {'status': 'success', 'message': 'Datos actualizados'}, 200
        
        return {'status': 'error', 'message': 'Nada que actualizar'}, 400



