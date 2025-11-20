#LIBRERIAS
import os
import firebase_admin
from firebase_admin import credentials, firestore

from recursos.lib.Globales import PATH_CRED_RENDER

# Evitamos inicializar la app más de una vez si el script se recarga
if not firebase_admin._apps:

    if os.path.exists(PATH_CRED_RENDER):
        # Estamos en Render: Usamos el archivo secreto
        cred = credentials.Certificate(PATH_CRED_RENDER)
    else:
            raise Exception(
                "No se encontraron credenciales de Firebase. "
                "Asegúrate de tener 'serviceAccountKey.json' en los files secretos de Render."
            )
    
    firebase_admin.initialize_app(cred)

db = firestore.client()