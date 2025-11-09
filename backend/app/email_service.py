import smtplib
import secrets
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from app.email_config import EmailConfig


def generate_verification_token():
    """URL-safe random token generálás - 32 byte = 43 karakter base64-ben"""
    return secrets.token_urlsafe(32)


def get_verification_expiry():
    """Token lejárati idő - 24 óra mostantól"""
    return datetime.utcnow() + timedelta(hours=EmailConfig.VERIFICATION_TOKEN_EXPIRATION_HOURS)


def get_logo_image():
    """
    Logo képfájl betöltése az emailekhez
    Ha nem létezik, nem gond - akkor csak nem lesz logo
    """
    logo_path = os.path.join(os.path.dirname(__file__), '../../web/src/icon.png')
    try:
        with open(logo_path, 'rb') as img_file:
            img_data = img_file.read()
        return img_data
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
        return None


def send_verification_email(recipient_email, username, verification_token):
    """
    Email megerősítés küldése új regisztrációnál
    
    HTML + plain text verzió is van, ha valaki nem tud HTML-t renderelni
    A logo inline attachment-ként van beágyazva (cid:logo)
    """
    try:
        html_content = f"""
<!DOCTYPE html>
<html lang=\"hu\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Regisztráció - Damareen</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap\" rel=\"stylesheet\">
</head>
<body style=\"margin: 0; padding: 0; font-family: 'Jaro', sans-serif; background-color: #1A1A1D;\">
    <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" style=\"background-color: #1A1A1D; padding: 35px 20px;\">
        <tr>
            <td align=\"center\">
                <table width=\"600\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" style=\"background: rgba(26, 26, 29, 0.75); border: 2.5px solid rgba(196, 155, 59, 0.4); border-radius: 15px; box-shadow: 0 4px 15px rgba(196, 155, 59, 0.2);\">
                    <tr>
                        <td style=\"padding: 50px 25px 35px; text-align: center;\">
                            <img src=\"cid:logo\" alt=\"Damareen\" style=\"width: 120px; height: 120px; display: block; margin: 0 auto;\">
                        </td>
                    </tr>
                    <tr>
                        <td style=\"padding: 0 45px 50px;\">
                            <h2 style=\"color: #C49B3B; margin: 0 0 30px; font-size: 1.9rem; font-weight: bold; letter-spacing: 1px;\">Üdv, {username}!</h2>
                            <p style=\"color: #D9D9D9; font-size: 1.05rem; line-height: 1.7; margin: 0 0 28px;\">
                                Köszönjük, hogy regisztráltál a Damareen játékban! Most már része vagy a közösségnek, és kezdheted a kalandot.
                            </p>
                            <p style=\"color: rgba(217, 217, 217, 0.6); font-size: 0.88rem; line-height: 1.6; margin: 35px 0 0;\">
                                Ha nem te regisztráltál, hagyd figyelmen kívül ezt az üzenetet.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style=\"background: rgba(196, 155, 59, 0.08); padding: 25px 35px; text-align: center; border-top: 1.5px solid rgba(196, 155, 59, 0.25); border-radius: 0 0 12px 12px;\">
                            <p style=\"color: rgba(217, 217, 217, 0.5); font-size: 0.82rem; margin: 0;\">
                                © 2025 Horváth András és Balogh Barnabás
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
Damareen - Regisztráció

Üdv, {username}!

Köszönjük, hogy regisztráltál a Damareen játékban! Most már része vagy a közösségnek, és kezdheted a kalandot.

Ha nem te regisztráltál, hagyd figyelmen kívül ezt az üzenetet.

© 2025 Horváth András és Balogh Barnabás
"""

        msg = MIMEMultipart('related')
        msg['Subject'] = 'Sikeres regisztráció - Damareen'
        msg['From'] = f'{EmailConfig.SENDER_NAME} <{EmailConfig.SENDER_EMAIL}>'
        msg['To'] = recipient_email

        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')

        msg_alternative.attach(part1)
        msg_alternative.attach(part2)

        logo_data = get_logo_image()
        if logo_data:
            logo_img = MIMEImage(logo_data)
            logo_img.add_header('Content-ID', '<logo>')
            logo_img.add_header('Content-Disposition', 'inline', filename='icon.png')
            msg.attach(logo_img)

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


def send_login_notification_email(recipient_email, username):
    try:
        html_content = f"""
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bejelentkezés - Damareen</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: 'Jaro', sans-serif; background-color: #1A1A1D;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #1A1A1D; padding: 35px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background: rgba(26, 26, 29, 0.75); border: 2.5px solid rgba(196, 155, 59, 0.4); border-radius: 15px; box-shadow: 0 4px 15px rgba(196, 155, 59, 0.2);">
                    <tr>
                        <td style="padding: 50px 25px 35px; text-align: center;">
                            <img src="cid:logo" alt="Damareen" style="width: 120px; height: 120px; display: block; margin: 0 auto;">
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 45px 50px;">
                            <h2 style="color: #C49B3B; margin: 0 0 30px; font-size: 1.9rem; font-weight: bold; letter-spacing: 1px;">Szia, {username}!</h2>
                            <p style="color: #D9D9D9; font-size: 1.05rem; line-height: 1.7; margin: 0 0 25px;">
                                Most bejelentkeztél a Damareen fiókodba. Ha te voltál, akkor minden oké – jó játékot!
                            </p>
                            <p style="color: rgba(217, 217, 217, 0.6); font-size: 0.88rem; line-height: 1.6; margin: 35px 0 0;">
                                Ha nem ismered fel ezt a bejelentkezést, változtasd meg a jelszavad azonnal.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: rgba(196, 155, 59, 0.08); padding: 25px 35px; text-align: center; border-top: 1.5px solid rgba(196, 155, 59, 0.25); border-radius: 0 0 12px 12px;">
                            <p style="color: rgba(217, 217, 217, 0.5); font-size: 0.82rem; margin: 0;">
                                © 2025 Horváth András és Balogh Barnabás
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
Damareen - Bejelentkezés

Szia, {username}!

Most bejelentkeztél a Damareen fiókodba. Ha te voltál, akkor minden oké – jó játékot!

Ha nem ismered fel ezt a bejelentkezést, változtasd meg a jelszavad azonnal.

© 2025 Horváth András és Balogh Barnabás
"""
        
        msg = MIMEMultipart('related')
        msg['Subject'] = 'Bejelentkezés a fiókodba - Damareen'
        msg['From'] = f'{EmailConfig.SENDER_NAME} <{EmailConfig.SENDER_EMAIL}>'
        msg['To'] = recipient_email
        
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg_alternative.attach(part1)
        msg_alternative.attach(part2)
        
        logo_data = get_logo_image()
        if logo_data:
            logo_img = MIMEImage(logo_data)
            logo_img.add_header('Content-ID', '<logo>')
            logo_img.add_header('Content-Disposition', 'inline', filename='icon.png')
            msg.attach(logo_img)
        
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
        reset_url = f"{EmailConfig.VERIFICATION_URL_BASE}auth.html?token={reset_token}&reset=true"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jelszó visszaállítás - Damareen</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: 'Jaro', sans-serif; background-color: #1A1A1D;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #1A1A1D; padding: 35px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background: rgba(26, 26, 29, 0.75); border: 2.5px solid rgba(196, 155, 59, 0.4); border-radius: 15px; box-shadow: 0 4px 15px rgba(196, 155, 59, 0.2);">
                    <tr>
                        <td style="padding: 50px 25px 35px; text-align: center;">
                            <img src="cid:logo" alt="Damareen" style="width: 120px; height: 120px; display: block; margin: 0 auto;">
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 45px 50px;">
                            <h2 style="color: #C49B3B; margin: 0 0 30px; font-size: 1.9rem; font-weight: bold; letter-spacing: 1px;">Szia, {username}!</h2>
                            <p style="color: #D9D9D9; font-size: 1.05rem; line-height: 1.7; margin: 0 0 28px;">
                                Jelszó visszaállítást kértél. Kattints a gombra egy új jelszó beállításához:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 35px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" style="display: inline-block; padding: 13px 55px; background: transparent; border: 3px solid #C49B3B; border-radius: 8px; color: #C49B3B; text-decoration: none; font-family: 'Jaro', sans-serif; font-size: 1.25rem; font-weight: bold; letter-spacing: 2px; box-shadow: 0 4px 15px rgba(196, 155, 59, 0.2);">Visszaállítás</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #D9D9D9; font-size: 0.95rem; line-height: 1.6; margin: 30px 0 12px;">
                                Ha a gomb nem működik, másold be ezt a linket:
                            </p>
                            <p style="color: #C49B3B; font-size: 0.92rem; word-break: break-all; margin: 0;">
                                {reset_url}
                            </p>
                            <p style="color: rgba(217, 217, 217, 0.6); font-size: 0.88rem; line-height: 1.6; margin: 35px 0 0;">
                                A link 1 órán belül lejár. Ha nem te kérted, hagyd figyelmen kívül ezt az üzenetet.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: rgba(196, 155, 59, 0.08); padding: 25px 35px; text-align: center; border-top: 1.5px solid rgba(196, 155, 59, 0.25); border-radius: 0 0 12px 12px;">
                            <p style="color: rgba(217, 217, 217, 0.5); font-size: 0.82rem; margin: 0;">
                                © 2025 Horváth András és Balogh Barnabás
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
Damareen - Jelszó visszaállítás

Szia, {username}!

Jelszó visszaállítást kértél. Használd az alábbi linket egy új jelszó beállításához:

{reset_url}

A link 1 órán belül lejár. Ha nem te kérted, hagyd figyelmen kívül ezt az üzenetet.

© 2025 Horváth András és Balogh Barnabás
"""
        
        msg = MIMEMultipart('related')
        msg['Subject'] = 'Jelszó visszaállítása - Damareen'
        msg['From'] = f'{EmailConfig.SENDER_NAME} <{EmailConfig.SENDER_EMAIL}>'
        msg['To'] = recipient_email
        
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg_alternative.attach(part1)
        msg_alternative.attach(part2)
        
        logo_data = get_logo_image()
        if logo_data:
            logo_img = MIMEImage(logo_data)
            logo_img.add_header('Content-ID', '<logo>')
            logo_img.add_header('Content-Disposition', 'inline', filename='icon.png')
            msg.attach(logo_img)
        
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
