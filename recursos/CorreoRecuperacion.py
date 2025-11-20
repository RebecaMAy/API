"""
RECURSO - RECUPERACION DE ACCESO A PERFIL
"""

# LIBRERIAS
from flask import render_template
from flask_restful import Resource, reqparse, abort

# --- CAMBIO 1: IMPORTAMOS LIBRERIAS SMTP NATIVAS ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# LLAMADA A GLOBALES, MENSAJES Y FUNCIONES
# --- CAMBIO 2: AÑADIMOS LAS VARIABLES SMTP ---
from recursos.lib.Globales import LOGO_URL, URL_PHP_BASE
from recursos.lib.Globales import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD 

from recursos.lib.Mensajes import mensaje_campo_email, mensaje_campo_token
from recursos.lib.Mensajes import mensaje_error_correo, mensaje_error_token
from recursos.lib.Mensajes import remitente, asunto_recuperacion
from recursos.lib.Funciones import obtener_usuario, validacion_token, codificar_parametro

# (Ya no necesitamos configurar resend.api_key)

# CAMPOS REQUERIDOS PARA LLAMAR ENDPOINT
parser_recuperacion = reqparse.RequestParser()
parser_recuperacion.add_argument('email', type=str, required=True, help=mensaje_campo_email)
parser_recuperacion.add_argument('token', type=str, required=True, help=mensaje_campo_token)

class EnviarRecuperacion(Resource):
    def post(self):
        """
        RECURSO QUE RECIBE EMAIL Y TOKEN
        SEGUN SI EXISTEN DE BBDD 
        ENVIA CORREO DE RECUPERACION
        USANDO SMTP (Estándar)

        URL ENDPOINT: POST https://api-envio-correos.onrender.com/email/recuperacion
        """
        # COMPROBACION PARAMETROS
        data = parser_recuperacion.parse_args()
        email_destino = data['email']
        token = data['token']

        try:
            datos_usuario = obtener_usuario(email_destino)
        
            if not datos_usuario:
                # CORREO NO EXISTE
                abort(404, message=mensaje_error_correo)
            
            if not validacion_token(datos_usuario, token):
                # TOKEN NO COINCIDE
                abort(401, message=mensaje_error_token)

        except Exception as e:
            abort(500, message=f"Error al conectar con base de datos: {str(e)}")

        # HASHEAR PARAMETROS
        """
        PARAMETRO 1 (p1) = CORREO
        PARAMETRO 2 (p2) = TOKEN
        """
        p1_hash = codificar_parametro(email_destino)
        p2_hash = codificar_parametro(token)
        
        # LINK DE PHP QUE REALIZA LA COMPROBACION DEL USUARIO 
        link_final = f"{URL_PHP_BASE}/recuperar_acceso.php?p1={p1_hash}&p2={p2_hash}"

        # COMPLETAR HTML
        try:
            html_content = render_template(
                'recuperacion.html', # RUTA NEWLETTERS: templates/...
                link_verificacion=link_final,
                logo_url=LOGO_URL
            )
        except Exception as e:
            abort(500, message=f"Error al renderizar la plantilla: {str(e)}")

        # --- CAMBIO 3: CONSTRUCCIÓN Y ENVÍO SMTP ---
        try:
            # 1. Crear objeto del mensaje
            msg = MIMEMultipart()
            msg['From'] = remitente # Nombre visible (ej: "Breathe <no-reply@...>")
            msg['To'] = email_destino
            msg['Subject'] = asunto_recuperacion

            # 2. Adjuntar el HTML
            msg.attach(MIMEText(html_content, 'html'))

            # 3. Conexión al servidor
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls() # Inicia encriptación segura
            
            # 4. Login y Envío
            # Nota: Usamos SMTP_USER para autenticar y como remitente técnico
            server.login(SMTP_USER, SMTP_PASSWORD) 
            server.sendmail(SMTP_USER, email_destino, msg.as_string())
            
            # 5. Cerrar conexión
            server.quit()

            return {"message": "Correo enviado correctamente", "id": "smtp_sent"}, 200

        except Exception as e:
            # Capturamos errores de conexión o autenticación
            abort(500, message=f"Error al enviar correo SMTP: {str(e)}")