import nodemailer from 'nodemailer';
import { google } from 'googleapis';
import { envConfig } from '../config/env.js';
import dns from 'dns';
import { promisify } from 'util';

// Configuración inicial
const { OAuth2 } = google.auth;
const config = envConfig();
const resolveMx = promisify(dns.resolveMx);

// Utilidades
const validateEmail = async (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regex.test(email)) return false;

    try {
        const domain = email.split('@')[1];
        const mxRecords = await resolveMx(domain);
        return mxRecords.length > 0;
    } catch (error) {
        console.error('Error validando email:', error);
        return false;
    }
};

const generateMessageId = () => {
    return `${Date.now()}.${Math.random().toString(36).substring(2)}@swingtails.com`;
};

// Configuración OAuth2
const oauth2Client = new OAuth2(
    config.mailer.clientID,
    config.mailer.clientSecret,
    config.mailer.redirectionURL
);

oauth2Client.setCredentials({
    refresh_token: config.mailer.mailerRefreshToken,
});

// Crear transportador
const createTransporter = async () => {
    try {
        const { token } = await oauth2Client.getAccessToken();

        const transporter = nodemailer.createTransport({
            service: 'gmail',
            auth: {
                type: 'OAuth2',
                user: config.mailer.email,
                clientId: config.mailer.clientID,
                clientSecret: config.mailer.clientSecret,
                refreshToken: config.mailer.mailerRefreshToken,
                accessToken: token,
            },
            pool: true,
            maxConnections: 3,
            maxMessages: 100,
            rateDelta: 1000,
            rateLimit: 3,
            secure: true,
            tls: {
                rejectUnauthorized: true,
                minVersion: 'TLSv1.2'
            },
            debug: process.env.NODE_ENV === 'development'
        });

        await transporter.verify();
        return transporter;
    } catch (error) {
        console.error('Error creando transportador:', error);
        throw new Error('Error en la configuración del servicio de correo');
    }
};

// Sistema de reintentos
const retryOperation = async (operation, maxRetries = 3, delay = 1000) => {
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;
            if (attempt === maxRetries) break;
            await new Promise(resolve => setTimeout(resolve, delay * attempt));
        }
    }

    throw lastError;
};

// Función principal de envío de email
export const sendVerificationEmail = async (email, token) => {
    try {
        // Validación de email
        const isValid = await validateEmail(email);
        if (!isValid) {
            throw new Error('Dirección de email inválida');
        }

        // URLs
        const appUrl = `https://swingtails-api-yz02.onrender.com/app/reset-password?token=${token}`;
        const playStoreUrl = 'https://play.google.com/store/apps/details?id=com.swingtails.app';
        const appStoreUrl = 'https://apps.apple.com/app/swingtails/id123456789';
        const unsubscribeUrl = `https://swingtails-api-yz02.onrender.com/unsubscribe?email=${encodeURIComponent(email)}`;

        const messageId = generateMessageId();

        const mailOptions = {
            from: {
                name: "Swingtails",
                address: config.mailer.email
            },
            to: email,
            subject: 'Restablecimiento de Contraseña - Swingtails',
            messageId,
            priority: 'high',
            headers: {
                'List-Unsubscribe': `<mailto:unsubscribe@swingtails.com?subject=unsubscribe>, <${unsubscribeUrl}>`,
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
                'Precedence': 'bulk',
                'X-Auto-Response-Suppress': 'OOF, AutoReply',
                'X-Priority': '1',
                'X-MSMail-Priority': 'High',
                'Importance': 'high',
                'X-GM-THRID': messageId,
                'Category': 'Account Security',
                'X-Entity-Ref-ID': messageId
            },
            text: `
      Restablecimiento de Contraseña - Swingtails

      Hola,

      Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Swingtails.

      Para restablecer tu contraseña, visita el siguiente enlace:
      ${appUrl}

      Este enlace expirará en 15 minutos por razones de seguridad.

      Si no solicitaste este restablecimiento, puedes ignorar este correo.

      Descarga nuestra app:
      Google Play Store: ${playStoreUrl}
      Apple App Store: ${appStoreUrl}

      © 2024 Swingtails
      Todos los derechos reservados.

      Para cancelar la suscripción: ${unsubscribeUrl}
      
      Este es un correo automático, por favor no respondas a este mensaje.
    `,
            html: `
      <!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <title>Restablecer Contraseña - Swingtails</title>
    <style>
        :root {
            color-scheme: light dark;
        }
        
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #1a1a1a !important;
                color: #ffffff !important;
            }
            .container {
                background-color: #2d2d2d !important;
            }
            .header {
                background: linear-gradient(135deg, #a06830 0%, #c98f57 100%) !important;
            }
            .content {
                color: #ffffff !important;
            }
            .primary-button {
                background-color: #e3a665 !important;
            }
            .warning {
                background-color: #3d3223 !important;
                color: #ffd7a8 !important;
            }
            .footer {
                background-color: #222222 !important;
                color: #888888 !important;
            }
            .store-button {
                background-color: #444444 !important;
                border: 1px solid #666666 !important;
            }
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .header {
            background: linear-gradient(135deg, #c9863c 0%, #e3a665 100%);
            padding: 30px 20px;
            text-align: center;
        }

        .header h1 {
            color: white;
            margin: 10px 0;
            font-size: 32px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }

        .content {
            padding: 40px 30px;
            text-align: center;
            color: #444444;
        }

        .content h2 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #333333;
        }

        .content p {
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 15px;
        }

        .button-container {
            margin: 30px 0;
            text-align: center;
        }

        .primary-button {
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
        }

        .primary-button:hover {
            background-color: #b67732;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }

        .store-buttons-container {
            width: 100%;
            max-width: 400px;
            margin: 20px auto;
            text-align: center;
        }

        .store-buttons {
            display: inline-flex;
            justify-content: center;
            gap: 15px;
            margin: 10px 0;
        }

        .store-button {
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
        }

        .store-button:hover {
            background-color: #444444;
            transform: translateY(-1px);
        }

        .warning {
            font-size: 14px;
            color: #666666;
            margin: 30px auto;
            padding: 20px;
            background-color: #fff3e0;
            border-radius: 12px;
            max-width: 80%;
        }

        .warning p {
            margin: 5px 0;
        }

        .footer {
            background-color: #f8f9fa;
            padding: 25px 20px;
            text-align: center;
            font-size: 13px;
            color: #666666;
            border-top: 1px solid #eeeeee;
        }

        .footer p {
            margin: 5px 0;
        }

        .footer a {
            color: #666666;
            text-decoration: underline;
            transition: color 0.3s ease;
        }

        .footer a:hover {
            color: #333333;
        }

        @media only screen and (max-width: 600px) {
            .container {
                margin: 10px;
                width: auto;
            }
            .content {
                padding: 20px 15px;
            }
            .store-buttons {
                flex-direction: column;
                gap: 10px;
            }
            .warning {
                max-width: 90%;
                margin: 20px auto;
            }
            .header h1 {
                font-size: 28px;
            }
            .content h2 {
                font-size: 22px;
            }
            .primary-button {
                padding: 12px 30px;
                font-size: 15px;
            }
        }
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
                <a href="${appUrl}" class="primary-button">
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
                    <a href="${playStoreUrl}" class="store-button">
                        Google Play Store
                    </a>
                    <a href="${appStoreUrl}" class="store-button">
                        Apple App Store
                    </a>
                </div>
            </div>
        </div>
        <div class="footer" role="contentinfo">
            <p>© 2024 Swingtails. Todos los derechos reservados.</p>
            <p>Dirección: Av. Principal #123, Ciudad, País</p>
            <p>
                <a href="${unsubscribeUrl}" 
                   target="_blank"
                   rel="noopener noreferrer">
                    Cancelar suscripción
                </a>
            </p>
        </div>
    </div>
</body>
</html>
    `,
            dsn: {
                id: messageId,
                return: 'headers',
                notify: ['failure', 'delay'],
                recipient: config.mailer.email
            }
        };

        // Enviar email con reintentos
        const result = await retryOperation(async () => {
            const transporter = await createTransporter();
            return await transporter.sendMail(mailOptions);
        });

        // Logging y monitoreo
        // console.log('Email enviado exitosamente:', {
        //     messageId: result.messageId,
        //     recipient: email,
        //     timestamp: new Date().toISOString()
        // });

        return result;

    } catch (error) {
        // console.error('Error en el envío de email:', {
        //     error: error.message,
        //     stack: error.stack,
        //     recipient: email,
        //     timestamp: new Date().toISOString()
        // });
        throw new Error('Error al enviar el correo de verificación');
    }
};

// Funciones auxiliares para manejo de errores y monitoreo
export const handleBounce = async (bounceInfo) => {
    try {
        // console.log('Rebote detectado:', bounceInfo);
        // Implementar lógica de manejo de rebotes
    } catch (error) {
        // console.error('Error manejando rebote:', error);
    }
};

export const trackEmailMetrics = async (messageId, status) => {
    try {
        // console.log('Métricas de email:', { messageId, status, timestamp: new Date() });
        // Implementar tracking de métricas
    } catch (error) {
        // console.error('Error tracking métricas:', error);
    }
};