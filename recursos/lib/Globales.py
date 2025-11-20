#LIBRERIAS
import os

# URL Imagen Header Newsletters
LOGO_URL = "https://mrmenaya.upv.edu.es/proyecto_biometria/logo-breathe-tracking.png"

"""
Guardado en Render como variable de entorno
"""
# URL PHP Base alojado en Plesk 
URL_PHP_BASE = os.environ.get("URL_PHP_BASE")
# Clave de API Resend 
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
# RUTA JSON con credenciales de Firebase Firestore
NOMBRE_CRED_DOC = 'serviceAccountKey.json'
PATH_CRED_RENDER = f"/etc/secrets/{NOMBRE_CRED_DOC}"