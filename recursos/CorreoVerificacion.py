"""
RECURSO - VERIFICACION DE CORREO TRAS REGISTRO
"""

#LIBRERIAS
from flask import render_template
from flask_restful import Resource, reqparse, abort
import resend

#LLAMADA A GLOBALES, MENSAJES Y FUNCIONES
from recursos.lib.Globales import LOGO_URL, URL_PHP_BASE, RESEND_API_KEY
from recursos.lib.Mensajes import mensaje_campo_email, mensaje_campo_token
from recursos.lib.Mensajes import mensaje_error_correo, mensaje_error_token
from recursos.lib.Mensajes import remitente, asunto_verificacion
from recursos.lib.Funciones import obtener_usuario, validacion_token, codificar_parametro

resend.api_key = RESEND_API_KEY

#CAMPOS REQUERIDOS PARA LLAMAR ENDPOINT
parser_verificacion = reqparse.RequestParser()
parser_verificacion.add_argument('email', type=str, required=True, help=mensaje_campo_email)
parser_verificacion.add_argument('token', type=str, required=True, help=mensaje_campo_token)

class EnviarVerificacion(Resource):
    def post(self):
        """
        RECURSO QUE RECIBE EMAIL Y TOKEN
        SEGUN SI EXISTEN DE BBDD 
        ENVIA CORREO DE VERIFICACION 
        USANDO RESEND

        URL ENDPOINT: POST https://api-envio-correos.onrender.com/email/verificacion
        """
        #COMPROBACION PARAMETROS
        data = parser_verificacion.parse_args()
        email_destino = data['email']
        token = data['token']

        try:
            datos_usuario = obtener_usuario(email_destino)
        
            if not datos_usuario:
                #CORREO NO EXISTE
                abort(404, message=mensaje_error_correo)
            
            if not validacion_token(datos_usuario, token):
                #TOKEN NO COINCIDE
                abort(401, message=mensaje_error_token)

        except Exception as e:
            abort(500, message=f"Error al conectar con base de datos: {str(e)}")

        #HASHEAR PARAMETROS
        """
        PARAMETRO 1 (p1) = CORREO
        PARAMETRO 2 (p2) = TOKEN
        """
        p1_hash = codificar_parametro(email_destino)
        p2_hash = codificar_parametro(token)
        
        #LINK DE PHP QUE REALIZA LA COMPROBACION DEL USUARIO 
        link_final = f"{URL_PHP_BASE}/verificar_usuario.php?p1={p1_hash}&p2={p2_hash}"

        #COMPLETAR HTML
        try:
            html_content = render_template(
                'verificacion.html', #RUTA NEWLETTERS: templates/...
                link_verificacion=link_final,
                logo_url=LOGO_URL
            )
        except Exception as e:
            abort(500, message=f"Error al renderizar la plantilla: {str(e)}")

        params = {
            "from": remitente,
            "to": email_destino,
            "subject": asunto_verificacion,
            "html": html_content,
        }

        #ENVIO DE CORREO
        try:
            r = resend.Emails.send(params)
            return {"message": "Correo enviado", "id": r.get("id")}, 200
        except Exception as e:
            abort(500, message=f"Error API Resend: {str(e)}")