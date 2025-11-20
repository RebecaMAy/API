#LIBRERIAS
import base64
import resend
from flask import render_template

#LLAMADA A BBDDD
from recursos.lib.ConexionBBDD import db

from Globales import URL_PHP_BASE, LOGO_URL
from Mensajes import asunto_verificacion, remitente

"""
-----------------------------------------
str -> obtener_usuario() -> dict OR None
-----------------------------------------
Recibe: Correo (ID del documento)
-----------------------------------------
Devuelve: JSON del usuario
-----------------------------------------
"""
def obtener_usuario(correo):
    doc_ref = db.collection('usuarios').document(correo)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None

"""
-----------------------------------------
dict, str -> validacion_token() -> True OR False
-----------------------------------------
Recibe: JSON del usuario y token
-----------------------------------------
Devuelve: True OR False
-----------------------------------------
"""
def validacion_token(datos_usuario, token):
    return datos_usuario.get('token') == token

"""
-----------------------------------------
str -> validacion_token() -> str
-----------------------------------------
Recibe: Dato sin hashear
-----------------------------------------
Devuelve: Dato hasheado
-----------------------------------------
"""
def codificar_parametro(valor):
    return base64.urlsafe_b64encode(valor.encode()).decode()

"""
-----------------------------------------
str, str -> validacion_token() -> str OR Exception
-----------------------------------------
Recibe: Email y token
-----------------------------------------
Devuelve: Respuesta del envio
-----------------------------------------
"""
def enviar_correo_verificacion(email_destino, token):
   
    # 1. Generar Link
    p1_hash = codificar_parametro(email_destino)
    p2_hash = codificar_parametro(token)
    link_final = f"{URL_PHP_BASE}/verificar_usuario.php?p1={p1_hash}&p2={p2_hash}"
    
    #COMPLETAR HTML
    html_content = render_template(
        'verificacion.html', #RUTA NEWLETTERS: templates/...
        link_verificacion=link_final,
        logo_url=LOGO_URL
    )

    # 3. Enviar con Resend
    params = {
        "from": remitente,
        "to": email_destino,
        "subject": asunto_verificacion,
        "html": html_content,
    }

    r = resend.Emails.send(params)
    return r