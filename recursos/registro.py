# recursos/registro.py

import json
from flask import request
from flask_restful import Resource, reqparse, abort
from psycopg2 import OperationalError, Error as Psycopg2Error
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import cross_origin

ROLES = { "Administrador" : 1 , "Suscriptor" : 2 }

class Registro(Resource):
    @cross_origin(origins="https://mrmenaya.upv.edu.es")
    def post(self):
        """Registra un nuevo usuario en la base de datos."""
        payload = request.get_json()

        if not payload:
            return {"ok": False, "error": "No se proporcionaron datos JSON."}, 400

        correo = payload.get('correo')
        nombre = payload.get('nombre')
        password_plano = payload.get('pass')
        id_rol_defecto = ROLES["Suscriptor"] 

        # --- Punto de seguridad crítico ---
        password_hash = generate_password_hash(password_plano)

        query = """
            INSERT INTO usuarios (Id_Rol, nombre, email, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id_usuario;
        """
        
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, (id_rol_defecto, nombre, correo, password_hash))
            new_user_id = cur.fetchone()[0]
            conn.commit()
            return {"ok": True, "message": "Usuario registrado con éxito", "id_usuario": new_user_id}, 201

        except Psycopg2Error as e:
            if conn: conn.rollback()
            # TODO Manejar violación de constraint 'UNIQUE' (email repetido)
            if e.pgcode == '23505': 
                return {"ok": False, "error": "El correo electrónico ya está en uso."}, 409 # 409 Conflict
            # Otro error de base de datos
            abort(500, message=f"Error de base de datos al registrar: {e}")
        except OperationalError:
            abort(503, message="Servicio no disponible: no se pudo conectar a la base de datos.")
        except Exception as e:
            if conn: conn.rollback()
            abort(500, message=f"Error interno del servidor: {e}")
        finally:
            if conn: conn.close()

        
class Login(Resource):

    def get(self):
        """Devuelve código de éxito o error, y si el usuario existe devuelve su rol"""

        data = request.get_json()
        if not data:
            return {"ok": False, "error": "No se proporcionaron datos JSON."}, 400
        
        correo = data.get('email')
        contraseña = data.get('password')

        if not correo:
            return {"ok": False, "error": "Falta 'email' en el cuerpo JSON."}, 400
        if not contraseña:
            return {"ok": False, "error": "Faltan 'password' en el cuerpo JSON."}, 400

        query = """ SELECT u.password_hash, r.nombre AS rol_nombre
            FROM  usuarios u
            JOIN  roles r ON u.Id_Rol = r.id_rol
            WHERE u.email = %s;
        """

        conn = None 
        try: 
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, (correo,))
            user_data = cur.fetchone()

            if user_data is None:
                # Usuario no encontrado
                # Damos un mensaje genérico por seguridad
                return {"ok": False, "error": "Correo no registrado"}, 401
            
            stored_hash = user_data[0]
            rol = user_data[1]

            if check_password_hash(stored_hash, contraseña):
                # Contraseña correcta: Éxito
                # Respondemos como espera el frontend
                return {"ok": True, "rol": rol, "email": correo}, 200
            else:
                # Contraseña incorrecta
                return {"ok": False, "error": "Contraseña incorrecta"}, 401 # 401 Unauthorized

        except OperationalError:
            abort(503, message="Servicio no disponible: no se pudo conectar a la base de datos.")
        except Psycopg2Error as e:
            abort(500, message=f"Error de base de datos al consultar: {e}")
        except Exception as e:
            abort(500, message=f"Error interno del servidor: {e}")
        finally:
            if conn: conn.close()

    