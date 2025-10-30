# db.py

import os
import psycopg2
from psycopg2 import OperationalError

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos PostgreSQL.
    Lanza una excepción OperationalError si la conexión falla.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('HOST'), # ip google cloud
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('NAME'), # postgres
            user=os.getenv('USER'),
            password=os.getenv('PASS')
        )
        return conn
    except OperationalError as e:
        print(f"ERROR: No se pudo conectar a la base de datos. {e}")
        raise e