from flask import request, jsonify
from flask_restful import Resource, abort
from werkzeug.security import generate_password_hash, check_password_hash
from firebase_admin import firestore
import datetime
import secrets
import string

from recursos.lib.ConexionBBDD import db
from recursos.lib.Funciones import enviar_correo_verificacion

# Asumimos que importas 'db' desde tu configuración de conexión
# from app import db 
# Si no lo tienes separado, db = firestore.client()

class Registro(Resource):
    def post(self):
        """Registra un nuevo usuario usando una transacción de Firestore."""
        payload = request.get_json()

        if not payload:
            return {"ok": False, "error": "No se proporcionaron datos JSON."}, 400

        # Extracción de datos
        correo = payload.get('email')
        nombre = payload.get('nombre')
        password_plano = payload.get('password')
        codigo_postal = payload.get('codigo_postal') # Necesario para la colección usuarios_suscriptores

        # Validación básica
        if not all([correo, nombre, password_plano, codigo_postal]):
            return {"ok": False, "error": "Faltan campos obligatorios (email, nombre, password, codigo_postal)"}, 400

        # Referencias a los documentos (El ID es el correo)
        # NOTA: Asume que 'db' es tu cliente de firestore inicializado
        # db = firestore.client() 
        
        user_ref = db.collection('usuarios').document(correo)
        sub_ref = db.collection('usuarios_suscriptores').document(correo)

        # Preparar datos
        password_hash = generate_password_hash(password_plano)
        token_aleatorio = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        validez_token = datetime.datetime.now() + datetime.timedelta(days=1)

        # Datos para colección 'usuarios'
        user_data = {
            "contraseña": password_hash,
            "estado_token": 0,     # 0: No verificado
            "rol": 1,              # 1: Suscriptor por defecto
            "token": token_aleatorio,
            "validez": validez_token
        }

        #mas adelante tiene mas sentido que se cree esta referencia una vez ha iniciado sesion por primera vez, es decir cuando verifica correo
        # Datos para colección 'usuarios_suscriptores'
        sub_data = {
            "nombre": nombre,
            "codigo_postal": codigo_postal
        }

        # --- TRANSACCIÓN ---
        try:
            transaction = db.transaction()
            # Llamamos a la función transaccional
            resultado = crear_usuario_transactional(transaction, user_ref, sub_ref, user_data, sub_data)
            
            if resultado:
                try:
                    
                    enviar_correo_verificacion(correo, token_aleatorio)
                    
                    return {
                        "ok": True, 
                        "message": "Usuario registrado y correo de verificación enviado."
                    }, 201
                    
                except Exception as e:
                    # IMPORTANTE: El usuario ya se creó en la BD, pero falló el correo.
                    # No devolvemos error 500, sino un 201 con advertencia.
                    print(f"Error crítico enviando email: {e}")
                    return {
                        "ok": True, 
                        "message": "Usuario registrado, pero hubo un error enviando el correo de verificación. Por favor solicite uno nuevo."
                    }, 201
                
            else:
                return {"ok": False, "error": "El correo electrónico ya está en uso."}, 409

        except Exception as e:
            return {"ok": False, "error": f"Error interno del servidor: {str(e)}"}, 500


# Definición de la función transaccional fuera de la clase (o como método estático)
@firestore.transactional
def crear_usuario_transactional(transaction, user_ref, sub_ref, user_data, sub_data):
    """
    Verifica si el usuario existe y, si no, crea los documentos en ambas colecciones.
    """
    snapshot = user_ref.get(transaction=transaction)
    
    if snapshot.exists:
        return False  # El usuario ya existe, abortamos
    
    # Si no existe, procedemos a escribir en ambas colecciones atómicamente
    transaction.set(user_ref, user_data)
    transaction.set(sub_ref, sub_data)
    return True


class Login(Resource):
    def post(self):
        """Valida credenciales contra la colección 'usuarios' de Firestore."""
        data = request.get_json()
        
        if not data:
            return {"ok": False, "error": "No se proporcionaron datos JSON."}, 400
        
        correo = data.get('email')
        contraseña = data.get('password')

        if not correo or not contraseña:
            return {"ok": False, "error": "Faltan email o password."}, 400

        try:
            # Buscar el documento por ID (email)
            user_ref = db.collection('usuarios').document(correo)
            doc = user_ref.get()

            if not doc.exists:
                return {"ok": False, "error": "Correo no registrado"}, 401
            
            user_data = doc.to_dict()
            stored_hash = user_data.get('contraseña')
            rol = user_data.get('rol')

            # Verificar contraseña
            if check_password_hash(stored_hash, contraseña):
                # Verificar si la cuenta está activa/verificada si es un requisito
                if user_data.get('estado_token') == 0:
                    return {"ok": False, "error": "Cuenta no verificada"}, 403

                return {
                    "ok": True, 
                    "rol": rol, 
                    "email": correo,
                    # "token": ... aquí podrías generar un JWT si usas eso para la sesión
                }, 200
            else:
                return {"ok": False, "error": "Contraseña incorrecta"}, 401

        except Exception as e:
            return {"ok": False, "error": f"Error al intentar iniciar sesión: {str(e)}"}, 500

    