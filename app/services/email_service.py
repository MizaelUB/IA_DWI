import re
import asyncio
import base64
import time
import uuid
from typing import Optional
from email.message import EmailMessage

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

    pass

try:
    import aiosmtplib
    HAS_AIOSMTPLIB = True
except ImportError:
    HAS_AIOSMTPLIB = False

try:
    from aiolimiter import AsyncLimiter
    email_rate_limiter = AsyncLimiter(3, 1.0)
except ImportError:
    class DummyLimiter:
        async def __aenter__(self): pass
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    email_rate_limiter = DummyLimiter()

from app.core.config import (
    MAILER_EMAIL,
    APP_PASSWORD
)

def validate_email_format(email: str) -> bool:
    regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return re.match(regex, email) is not None

async def validate_email_domain(email: str) -> bool:
    if not validate_email_format(email):
        return False
    if not HAS_DNS:
        return True
    try:
        domain = email.split('@')[1]
        loop = asyncio.get_event_loop()
        answers = await loop.run_in_executor(None, dns.resolver.resolve, domain, 'MX')
        return len(answers) > 0
    except Exception as e:
        print(f"Error validando email DNS: {e}")
        return True

def generate_message_id() -> str:
    timestamp = int(time.time() * 1000)
    random_str = uuid.uuid4().hex[:8]
    return f"{timestamp}.{random_str}@swingtails.com"



async def send_verification_email(email: str, token: str) -> Optional[dict]:
    # Limitar el rate de envío de correos
    async with email_rate_limiter:
        is_valid = await validate_email_domain(email)
        if not is_valid:
            raise ValueError("Dirección de email inválida")

        app_url = f"https://swingtails-api-yz02.onrender.com/app/reset-password?token={token}"
        play_store_url = "https://play.google.com/store/apps/details?id=com.swingtails.app"
        app_store_url = "https://apps.apple.com/app/swingtails/id123456789"
        
        import urllib.parse
        encoded_email = urllib.parse.quote(email)
        unsubscribe_url = f"https://swingtails-api-yz02.onrender.com/unsubscribe?email={encoded_email}"

        message_id = generate_message_id()

        msg = EmailMessage()
        msg["From"] = f"Swingtails <{MAILER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = "Restablecimiento de Contraseña - Swingtails"
        msg["Message-ID"] = f"<{message_id}>"
        
        msg["List-Unsubscribe"] = f"<mailto:unsubscribe@swingtails.com?subject=unsubscribe>, <{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        msg["Precedence"] = "bulk"
        msg["X-Auto-Response-Suppress"] = "OOF, AutoReply"
        msg["X-Priority"] = "1"
        msg["X-MSMail-Priority"] = "High"
        msg["Importance"] = "high"
        msg["X-GM-THRID"] = message_id
        msg["Category"] = "Account Security"
        msg["X-Entity-Ref-ID"] = message_id

        text_content = f"""
Restablecimiento de Contraseña - Swingtails

Hola,

Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Swingtails.

Para restablecer tu contraseña, visita el siguiente enlace:
{app_url}

Este enlace expirará en 15 minutos por razones de seguridad.

Si no solicitaste este restablecimiento, puedes ignorar este correo.

Descarga nuestra app:
Google Play Store: {play_store_url}
Apple App Store: {app_store_url}

© 2024 Swingtails
Todos los derechos reservados.

Para cancelar la suscripción: {unsubscribe_url}

Este es un correo automático, por favor no respondas a este mensaje.
"""
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <title>Restablecer Contraseña - Swingtails</title>
    <style>
        :root {{
            color-scheme: light dark;
        }}
        
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #1a1a1a !important;
                color: #ffffff !important;
            }}
            .container {{
                background-color: #2d2d2d !important;
            }}
            .header {{
                background: linear-gradient(135deg, #a06830 0%, #c98f57 100%) !important;
            }}
            .content {{
                color: #ffffff !important;
            }}
            .primary-button {{
                background-color: #e3a665 !important;
            }}
            .warning {{
                background-color: #3d3223 !important;
                color: #ffd7a8 !important;
            }}
            .footer {{
                background-color: #222222 !important;
                color: #888888 !important;
            }}
            .store-button {{
                background-color: #444444 !important;
                border: 1px solid #666666 !important;
            }}
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .header {{
            background: linear-gradient(135deg, #c9863c 0%, #e3a665 100%);
            padding: 30px 20px;
            text-align: center;
        }}

        .header h1 {{
            color: white;
            margin: 10px 0;
            font-size: 32px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }}

        .content {{
            padding: 40px 30px;
            text-align: center;
            color: #444444;
        }}

        .content h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #333333;
        }}

        .content p {{
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 15px;
        }}

        .button-container {{
            margin: 30px 0;
            text-align: center;
        }}

        .primary-button {{
            display: inline-block;
            padding: 15px 40px;
            background-color: #c9863c;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            margin: 10px 0;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .primary-button:hover {{
            background-color: #b67732;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }}

        .store-buttons-container {{
            width: 100%;
            max-width: 400px;
            margin: 20px auto;
            text-align: center;
        }}

        .store-buttons {{
            display: inline-flex;
            justify-content: center;
            gap: 15px;
            margin: 10px 0;
        }}

        .store-button {{
            display: inline-block;
            padding: 12px 25px;
            background-color: #333333;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }}

        .store-button:hover {{
            background-color: #444444;
            transform: translateY(-1px);
        }}

        .warning {{
            font-size: 14px;
            color: #666666;
            margin: 30px auto;
            padding: 20px;
            background-color: #fff3e0;
            border-radius: 12px;
            max-width: 80%;
        }}

        .warning p {{
            margin: 5px 0;
        }}

        .footer {{
            background-color: #f8f9fa;
            padding: 25px 20px;
            text-align: center;
            font-size: 13px;
            color: #666666;
            border-top: 1px solid #eeeeee;
        }}

        .footer p {{
            margin: 5px 0;
        }}

        .footer a {{
            color: #666666;
            text-decoration: underline;
            transition: color 0.3s ease;
        }}

        .footer a:hover {{
            color: #333333;
        }}

        @media only screen and (max-width: 600px) {{
            .container {{
                margin: 10px;
                width: auto;
            }}
            .content {{
                padding: 20px 15px;
            }}
            .store-buttons {{
                flex-direction: column;
                gap: 10px;
            }}
            .warning {{
                max-width: 90%;
                margin: 20px auto;
            }}
            .header h1 {{
                font-size: 28px;
            }}
            .content h2 {{
                font-size: 22px;
            }}
            .primary-button {{
                padding: 12px 30px;
                font-size: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container" role="article" aria-label="Restablecimiento de contraseña">
        <div class="header" role="banner">
            <h1>Swingtails</h1>
        </div>
        <div class="content" role="main">
            <h2>Restablecimiento de Contraseña</h2>
            <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Swingtails.</p>
            
            <div class="button-container">
                <a href="{app_url}" class="primary-button">
                    Restablecer Contraseña
                </a>
            </div>

            <div class="warning">
                <p>⚠️ Este enlace expirará en 15 minutos por razones de seguridad.</p>
                <p>Si no solicitaste este restablecimiento, por favor ignora este correo.</p>
            </div>

            <p>¿No tienes nuestra app? Descárgala aquí:</p>
            <div class="store-buttons-container">
                <div class="store-buttons">
                    <a href="{play_store_url}" class="store-button">
                        Google Play Store
                    </a>
                    <a href="{app_store_url}" class="store-button">
                        Apple App Store
                    </a>
                </div>
            </div>
        </div>
        <div class="footer" role="contentinfo">
            <p>© 2024 Swingtails. Todos los derechos reservados.</p>
            <p>Dirección: Av. Principal #123, Ciudad, País</p>
            <p>
                <a href="{unsubscribe_url}" 
                   target="_blank"
                   rel="noopener noreferrer">
                    Cancelar suscripción
                </a>
            </p>
        </div>
    </div>
</body>
</html>
"""
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")

        client = aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587, start_tls=False)
        await client.connect()
        await client.starttls()
        await client.login(MAILER_EMAIL, APP_PASSWORD)
        
        response = await client.send_message(msg)
        await client.quit()
        
        return {
            "messageId": message_id,
            "recipient": email,
            "status": "success",
            "response": response
        }


async def send_code_email(email: str, code: str, purpose: str = "registro") -> Optional[dict]:
    """
    Envía un código de 6 dígitos por correo electrónico para validación de registro o recuperación.
    """
    async with email_rate_limiter:
        is_valid = await validate_email_domain(email)
        if not is_valid:
            raise ValueError("Dirección de email inválida")

        titulo = "Código de Verificación - Swingtails" if purpose == "registro" else "Restablecimiento de Contraseña - Swingtails"
        subtitulo = "Código de Verificación de Cuenta" if purpose == "registro" else "Código de Restablecimiento de Contraseña"
        mensaje_intro = (
            "Tu código de verificación para completar el registro en Swingtails es:"
            if purpose == "registro"
            else "Hemos recibido una solicitud para restablecer tu contraseña. Tu código de verificación es:"
        )

        message_id = generate_message_id()

        msg = EmailMessage()
        msg["From"] = f"Swingtails <{MAILER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = titulo
        msg["Message-ID"] = f"<{message_id}>"
        msg["Precedence"] = "bulk"
        msg["X-Priority"] = "1"
        msg["X-MSMail-Priority"] = "High"
        msg["Importance"] = "high"

        text_content = f"""
{titulo}

Hola,

{mensaje_intro}

CÓDIGO: {code}

Este código expirará en 15 minutos por razones de seguridad.

Si no solicitaste este código, por favor ignora este correo.

© 2024 Swingtails. Todos los derechos reservados.
"""
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #c9863c 0%, #e3a665 100%);
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            color: white;
            margin: 0;
            font-size: 32px;
            font-weight: 700;
        }}
        .content {{
            padding: 40px 30px;
            text-align: center;
            color: #444444;
        }}
        .code-box {{
            display: inline-block;
            background-color: #fff3e0;
            border: 2px dashed #c9863c;
            color: #c9863c;
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 8px;
            padding: 15px 35px;
            margin: 25px 0;
            border-radius: 10px;
        }}
        .warning {{
            font-size: 14px;
            color: #666666;
            margin: 20px auto;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 13px;
            color: #666666;
            border-top: 1px solid #eeeeee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Swingtails</h1>
        </div>
        <div class="content">
            <h2>{subtitulo}</h2>
            <p>{mensaje_intro}</p>
            
            <div class="code-box">
                {code}
            </div>

            <div class="warning">
                <p>⚠️ Este código expirará en 15 minutos por razones de seguridad.</p>
                <p>Si no solicitaste este código, puedes ignorar este mensaje.</p>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 Swingtails. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>
"""
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")

        client = aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587, start_tls=False)
        await client.connect()
        await client.starttls()
        await client.login(MAILER_EMAIL, APP_PASSWORD)
        
        response = await client.send_message(msg)
        await client.quit()
        
        return {
            "messageId": message_id,
            "recipient": email,
            "status": "success",
            "response": response
        }

