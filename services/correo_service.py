
import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv


load_dotenv()


class CorreoService:
    """Gestiona el envío de correos mediante Gmail."""

    def __init__(self):
        self.correo = os.getenv("GMAIL_USER")
        self.contrasena = os.getenv("GMAIL_APP_PASSWORD")

        if not self.correo or not self.contrasena:
            raise ValueError(
                "No se configuraron las credenciales de Gmail."
            )

    def enviar_correo(self, destinatario, asunto, contenido):
        """Envía un correo electrónico."""

        mensaje = EmailMessage()
        mensaje["From"] = self.correo
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.set_content(contenido)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(self.correo, self.contrasena)
            servidor.send_message(mensaje)

    def enviar_bienvenida(self, destinatario, nombre):
        """Envía un correo de bienvenida."""

        asunto = "¡Bienvenido a Social UNA!"

        contenido = (
            f"Hola, {nombre}.\n\n"
            "¡Te damos la bienvenida a Social UNA!\n"
            "Tu cuenta se ha creado correctamente.\n\n"
            "Ya puedes iniciar sesión y comenzar a utilizar "
            "nuestra plataforma.\n\n"
            "El equipo de Social UNA."
        )

        self.enviar_correo(destinatario, asunto, contenido)

    def enviar_recuperacion(self, destinatario, enlace):
        """Envía el enlace para restablecer la contraseña."""

        asunto = "Recuperación de contraseña - Social UNA"

        contenido = (
            "Hola.\n\n"
            "Recibimos una solicitud para restablecer tu contraseña.\n\n"
            f"Utiliza el siguiente enlace:\n{enlace}\n\n"
            "Este enlace expirará en 30 minutos y solo puede "
            "utilizarse una vez.\n\n"
            "Si no solicitaste este cambio, puedes ignorar "
            "este correo.\n\n"
            "El equipo de Social UNA."
        )

        self.enviar_correo(destinatario, asunto, contenido)
    