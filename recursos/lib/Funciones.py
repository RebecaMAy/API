# LIBRERIAS
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template

# LLAMADA A BBDDD
from recursos.lib.ConexionBBDD import db

# LLAMADA A GLOBALES (Sustituimos RESEND_API_KEY por las variables SMTP)
from recursos.lib.Globales import URL_PHP_BASE, LOGO_URL
from recursos.lib.Globales import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

from recursos.lib.Mensajes import asunto_verificacion, remitente

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
str -> codificar_parametro() -> str
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
str, str -> enviar_correo_verificacion() -> dict OR Exception
-----------------------------------------
Recibe: Email y token
-----------------------------------------
Devuelve: Respuesta del envio (Simulada como objeto dict)
-----------------------------------------
"""
def enviar_correo_verificacion(email_destino, token):
    
    # 1. Generar Link
    p1_hash = codificar_parametro(email_destino)
    p2_hash = codificar_parametro(token)
    link_final = f"{URL_PHP_BASE}/verificar_usuario.php?p1={p1_hash}&p2={p2_hash}"
    
    # 2. COMPLETAR HTML
    try:
        html_content = render_template(
            'verificacion.html', # RUTA NEWLETTERS: templates/...
            link_verificacion=link_final,
            logo_url=LOGO_URL
        )
    except Exception as e:
        print(f"Error renderizando template: {e}")
        raise e

    # 3. Enviar con SMTP ROBUSTO (Sustituye a Resend)
    
    # Crear el objeto del mensaje
    msg = MIMEMultipart()
    msg['From'] = remitente     # Nombre visible (ej: "Tu App <no-reply@...>")
    msg['To'] = email_destino
    msg['Subject'] = asunto_verificacion

    # Adjuntar el cuerpo HTML
    msg.attach(MIMEText(html_content, 'html'))

    try:
        print(f"Iniciando conexión SMTP a {SMTP_HOST}:{SMTP_PORT}...")

        # --- CORRECCIÓN CRÍTICA PARA RENDER ---
        # 1. Convertimos el puerto a entero (SMTP_PORT viene como string de variables de entorno)
        # 2. Añadimos timeout=15 para evitar que el worker se congele infinitamente
        server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT), timeout=15)
        
        # 3. Protocolo EHLO/STARTTLS para Brevo/Outlook
        server.ehlo()       # Saludo inicial
        server.starttls()   # Encriptar conexión
        server.ehlo()       # Saludo de nuevo tras encriptar
        
        # Login con las credenciales reales
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        # Enviar correo
        server.sendmail(SMTP_USER, email_destino, msg.as_string())
        
        server.quit()
        
        print(f"✅ Correo enviado correctamente a {email_destino}")
        # Retornamos un diccionario similar a lo que devolvía Resend para mantener coherencia
        return {"id": "smtp_sent", "message": "Enviado correctamente"}

    except Exception as e:
        print(f"❌ ERROR CRÍTICO SMTP: {str(e)}")
        # Si falla, lanzamos la excepción para que el recurso principal (Resource) la capture con su try/except
        raise e