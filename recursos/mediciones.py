# recursos/mediciones.py

import json
from flask import request
from flask_restful import Resource, reqparse, abort
from psycopg2 import OperationalError, Error as Psycopg2Error
from db import get_db_connection

TIPOS_MEDICIONES_VALIDOS = ['temperatura','ozono']

# --- Parser para las peticiones POST ---
parser_post = reqparse.RequestParser()
parser_post.add_argument('device_id', type=int, required=True, help='El ID del dispositivo es obligatorio (entero)')
parser_post.add_argument('coordenadas', type=dict, required=True, help="Las coordenadas son obligatorias (objeto con 'lat' y 'lon')")
parser_post.add_argument('mediciones', type=dict, required=True, help='El objeto de mediciones es obligatorio')
parser_post.add_argument('fecha', type=str, required=False, help='Fecha en formato ISO 8601 (opcional)')

class MedicionesListas(Resource):
    """
    Recurso para crear nuevas mediciones (POST) y obtener una lista de ellas (GET).
    """
    def post(self):
        """Crea un nuevo registro de medición."""
        payload = parser_post.parse_args()

        # --- VALIDACIONES ---
        coordenadas = payload['coordenadas']
        mediciones = payload['mediciones']

        if not all(k in coordenadas for k in ['lat', 'lon']):
            abort(400, message="El objeto 'coordenadas' debe contener 'lat' y 'lon'.")
        if not mediciones:
            abort(400, message="El objeto 'mediciones' no puede estar vacío.")
        
        for tipo in mediciones.keys():
            if tipo not in TIPOS_MEDICIONES_VALIDOS:
                abort(400, message=f"Tipo de medición '{tipo}' no válido. Válidos: {list(TIPOS_MEDICIONES_VALIDOS)}")

        try:
            lon, lat = float(coordenadas['lon']), float(coordenadas['lat'])
            geom_wkt = f'SRID=4326;POINT({lon} {lat})'
        except (ValueError, TypeError):
            abort(400, message="Las coordenadas 'lat' y 'lon' deben ser números válidos.")

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # --- Iniciar transacción ---
            conn.autocommit = False

            sql_info = """
                INSERT INTO info_mediciones (device_id, coordenadas, mediciones_json, fecha)
                VALUES (%s, ST_GeomFromEWKT(%s), %s, COALESCE(%s::timestamptz, NOW()))
                RETURNING id;
            """
            cur.execute(sql_info, (payload['device_id'], geom_wkt, json.dumps(mediciones), payload.get('fecha')))
            medicion_id = cur.fetchone()[0]

            valores = [(medicion_id, tipo, valor) for tipo, valor in mediciones.items()]
            sql_valores = "INSERT INTO valores_mediciones (medicion_id, tipo, valor) VALUES (%s, %s, %s);"
            # executemany es eficiente para inserciones múltiples
            cur.executemany(sql_valores, valores)
            
            conn.commit()
            return {'message': 'Mediciones registradas con éxito', 'id': medicion_id}, 201

        except OperationalError:
            abort(503, message="Servicio no disponible: no se pudo conectar a la base de datos.")
        except Psycopg2Error as e:
            if conn: conn.rollback()
            # No exponer detalles del error de la BBDD al cliente
            abort(500, message=f"Error de base de datos al guardar los datos.")
        except Exception as e:
            if conn: conn.rollback()
            abort(500, message=f"Error interno del servidor: {e}")
        finally:
            if conn: conn.close()

    def get(self):
        """Devuelve una lista de mediciones, opcionalmente filtradas."""
        
        DEFAULT_LIMIT = 100
        
        query = """
            SELECT
                id,
                device_id,
                fecha,
                ST_AsGeoJSON(coordenadas) as coordenadas,
                mediciones_json
            FROM info_mediciones
            ORDER BY fecha DESC
            LIMIT %s;
        """

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, (DEFAULT_LIMIT,))
            rows = cur.fetchall()
            
            resultados = [{
                "id": row[0],
                "device_id": row[1],
                "fecha": row[2].isoformat(),
                "coordenadas": json.loads(row[3]),
                "mediciones": row[4]
            } for row in rows]
            
            return resultados, 200
        
        except OperationalError:
            abort(503, message="Servicio no disponible: no se pudo conectar a la base de datos.")
        except Exception as e:
            abort(500, message=f"Error al consultar la base de datos: {e}")
        finally:
            if conn: conn.close()


class MedicionesUltimas(Resource):
    """
    Recurso para obtener la última o las N últimas mediciones.
    """
    def get(self, n=None):
        """Devuelve la última o las últimas 'n' mediciones, , con filtro opcional por tipo."""

        limit = n if n is not None else 1
        if n is not None and (n <= 0 or n > 50):
            abort(400, message="El número de mediciones debe ser un entero entre 1 y 50.")
        
        tipo = request.args.get('tipo')
        query = "SELECT id, device_id, fecha, ST_AsGeoJSON(coordenadas) as coordenadas, mediciones_json FROM info_mediciones"
        params = []

        if tipo:
            if tipo not in TIPOS_MEDICIONES_VALIDOS: abort(400, message=f"Tipo '{tipo}' no válido.")
            query += " WHERE mediciones_json ? %s"
            params.append(tipo)
        
        query += " ORDER BY fecha DESC LIMIT %s;"
        params.append(limit)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            resultados = [{
                "id": row[0],
                "device_id": row[1],
                "fecha": row[2].isoformat(),
                "coordenadas": json.loads(row[3]),
                "mediciones": {tipo: row[4][tipo]} if tipo else row[4]
            } for row in rows]
            return resultados, 200

        except OperationalError:
            abort(503, message="Servicio no disponible: no se pudo conectar a la base de datos.")
        except Exception as e:
            abort(500, message=f"Error interno del servidor al consultar la base de datos: {e}")
        finally:
            if conn: conn.close()