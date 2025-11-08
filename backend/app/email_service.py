import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app.email_config import EmailConfig


def generate_verification_token():
    return secrets.token_urlsafe(32)


def get_verification_expiry():
    return datetime.utcnow() + timedelta(hours=EmailConfig.VERIFICATION_TOKEN_EXPIRATION_HOURS)


def send_verification_email(recipient_email, username, verification_token):
    try:
        verification_url = f"{EmailConfig.VERIFICATION_URL_BASE}/verify?token={verification_token}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-mail megerősítés</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #2c3e50; padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Damareen</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #2c3e50; margin: 0 0 20px 0;">Üdvözlünk, {username}!</h2>
                            <p style="color: #555555; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Köszönjük, hogy regisztráltál a Damareen platformon. Az e-mail címed megerősítéséhez kattints az alábbi gombra:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{verification_url}" style="display: inline-block; padding: 15px 40px; background-color: #3498db; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">E-mail megerősítése</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #555555; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0;">
                                Ha nem tudod megnyitni a gombot, másold be az alábbi linket a böngésződbe:
                            </p>
                            <p style="color: #3498db; font-size: 14px; word-break: break-all; margin: 10px 0 0 0;">
                                {verification_url}
                            </p>
                            <p style="color: #999999; font-size: 13px; line-height: 1.6; margin: 30px 0 0 0;">
                                Ez a link 24 órán belül lejár. Ha nem te regisztráltál, kérjük, hagyd figyelmen kívül ezt az e-mailt.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px 30px; text-align: center;">
                            <p style="color: #999999; font-size: 12px; margin: 0;">
                                © 2025 Damareen. Minden jog fenntartva.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        text_content = f"""
Üdvözlünk, {username}!

Köszönjük, hogy regisztráltál a Damareen platformon. Az e-mail címed megerősítéséhez látogass el az alábbi linkre:

{verification_url}

Ez a link 24 órán belül lejár. Ha nem te regisztráltál, kérjük, hagyd figyelmen kívül ezt az e-mailt.

© 2025 Damareen. Minden jog fenntartva.
"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'E-mail cím megerősítése - Damareen'
        msg['From'] = f'{EmailConfig.SENDER_NAME} <{EmailConfig.SENDER_EMAIL}>'
        msg['To'] = recipient_email
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            if EmailConfig.SMTP_USE_TLS:
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False


def send_login_verification_email(recipient_email, username, verification_token):
    try:
        verification_url = f"{EmailConfig.VERIFICATION_URL_BASE}/verify-login?token={verification_token}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bejelentkezés megerősítése</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #2c3e50; padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Damareen</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #2c3e50; margin: 0 0 20px 0;">Bejelentkezés megerősítése</h2>
                            <p style="color: #555555; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Szia {username}!
                            </p>
                            <p style="color: #555555; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Bejelentkezési kísérletet észleltünk a fiókodba. A bejelentkezés megerősítéséhez kattints az alábbi gombra:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{verification_url}" style="display: inline-block; padding: 15px 40px; background-color: #27ae60; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">Bejelentkezés megerősítése</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #555555; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0;">
                                Ha nem tudod megnyitni a gombot, másold be az alábbi linket a böngésződbe:
                            </p>
                            <p style="color: #27ae60; font-size: 14px; word-break: break-all; margin: 10px 0 0 0;">
                                {verification_url}
                            </p>
                            <p style="color: #999999; font-size: 13px; line-height: 1.6; margin: 30px 0 0 0;">
                                Ez a link 24 órán belül lejár. Ha nem te próbáltál meg bejelentkezni, kérjük, változtasd meg a jelszavad azonnal.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px 30px; text-align: center;">
                            <p style="color: #999999; font-size: 12px; margin: 0;">
                                © 2025 Damareen. Minden jog fenntartva.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        text_content = f"""
Bejelentkezés megerősítése

Szia {username}!

Bejelentkezési kísérletet észleltünk a fiókodba. A bejelentkezés megerősítéséhez látogass el az alábbi linkre:

{verification_url}

Ez a link 24 órán belül lejár. Ha nem te próbáltál meg bejelentkezni, kérjük, változtasd meg a jelszavad azonnal.

© 2025 Damareen. Minden jog fenntartva.
"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Bejelentkezés megerősítése - Damareen'
        msg['From'] = f'{EmailConfig.SENDER_NAME} <{EmailConfig.SENDER_EMAIL}>'
        msg['To'] = recipient_email
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            if EmailConfig.SMTP_USE_TLS:
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False


def send_password_reset_email(recipient_email, username, reset_token):
    try:
        reset_url = f"{EmailConfig.VERIFICATION_URL_BASE}/password-reset?token={reset_token}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jelszó visszaállítása</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #2c3e50; padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Damareen</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #2c3e50; margin: 0 0 20px 0;">Jelszó visszaállítása</h2>
                            <p style="color: #555555; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Szia {username}!
                            </p>
                            <p style="color: #555555; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Jelszó visszaállítási kérelmet kaptunk a fiókodhoz. A jelszavad megváltoztatásához kattints az alábbi gombra:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" style="display: inline-block; padding: 15px 40px; background-color: #e74c3c; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">Jelszó visszaállítása</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #555555; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0;">
                                Ha nem tudod megnyitni a gombot, másold be az alábbi linket a böngésződbe:
                            </p>
                            <p style="color: #e74c3c; font-size: 14px; word-break: break-all; margin: 10px 0 0 0;">
                                {reset_url}
                            </p>
                            <p style="color: #999999; font-size: 13px; line-height: 1.6; margin: 30px 0 0 0;">
                                Ez a link 1 órán belül lejár. Ha nem te kérted a jelszó visszaállítását, hagyd figyelmen kívül ezt az e-mailt.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px 30px; text-align: center;">
                            <p style="color: #999999; font-size: 12px; margin: 0;">
                                © 2025 Damareen. Minden jog fenntartva.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        text_content = f"""
Jelszó visszaállítása

Szia {username}!

Jelszó visszaállítási kérelmet kaptunk a fiókodhoz. A jelszavad megváltoztatásához látogass el az alábbi linkre:

{reset_url}

Ez a link 1 órán belül lejár. Ha nem te kérted a jelszó visszaállítását, hagyd figyelmen kívül ezt az e-mailt.

© 2025 Damareen. Minden jog fenntartva.
"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Jelszó visszaállítása - Damareen'
        msg['From'] = f'{EmailConfig.SENDER_NAME} <{EmailConfig.SENDER_EMAIL}>'
        msg['To'] = recipient_email
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            if EmailConfig.SMTP_USE_TLS:
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False
