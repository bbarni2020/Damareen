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
        verification_url = f"{EmailConfig.VERIFICATION_URL_BASE}/auth.html?token={verification_token}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-mail megerősítés</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0F0D13;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0F0D13; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background: rgba(196, 155, 59, 0.02); border: 2.5px solid rgba(196, 155, 59, 0.35); border-radius: 18px; overflow: hidden;">
                    <tr>
                        <td style="padding: 35px 25px; text-align: center;">
                            <h1 style="font-family: 'Jaro', sans-serif; color: #C49B3B; margin: 0 0 35px 0; font-size: 3rem; letter-spacing: 3px; text-shadow: 0 0 25px rgba(196, 155, 59, 0.4);">Damareen</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 35px 40px 35px;">
                            <h2 style="color: #C49B3B; margin: 0 0 25px 0; font-size: 1.8rem; font-weight: bold;">Üdvözlünk, {username}!</h2>
                            <p style="color: #D9D9D9; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                                Köszönjük, hogy regisztráltál a Damareen platformon. Az e-mail címed megerősítéséhez kattints az alábbi gombra:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{verification_url}" style="display: inline-block; padding: 13px 55px; background: rgba(196, 155, 59, 0.08); border: 2.8px solid #C49B3B; border-radius: 27px; color: #C49B3B; text-decoration: none; font-size: 1.25rem; font-weight: bold; box-shadow: 0 3px 12px rgba(196, 155, 59, 0.25);">E-mail megerősítése</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #D9D9D9; font-size: 14px; line-height: 1.6; margin: 25px 0 10px 0;">
                                Ha nem tudod megnyitni a gombot, másold be az alábbi linket a böngésződbe:
                            </p>
                            <p style="color: #C49B3B; font-size: 14px; word-break: break-all; margin: 10px 0 0 0;">
                                {verification_url}
                            </p>
                            <p style="color: rgba(217, 217, 217, 0.6); font-size: 13px; line-height: 1.6; margin: 30px 0 0 0;">
                                Ez a link 24 órán belül lejár. Ha nem te regisztráltál, kérjük, hagyd figyelmen kívül ezt az e-mailt.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: rgba(196, 155, 59, 0.05); padding: 20px 30px; text-align: center; border-top: 1px solid rgba(196, 155, 59, 0.2);">
                            <p style="color: rgba(217, 217, 217, 0.5); font-size: 12px; margin: 0;">
                                © 2025 Horváth András és Balogh Barnabás. Minden jog fenntartva.
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

© 2025 Horváth András és Balogh Barnabás. Minden jog fenntartva.
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


def send_login_notification_email(recipient_email, username):
    try:
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bejelentkezés észlelve</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0F0D13;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0F0D13; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background: rgba(196, 155, 59, 0.02); border: 2.5px solid rgba(196, 155, 59, 0.35); border-radius: 18px; overflow: hidden;">
                    <tr>
                        <td style="padding: 35px 25px; text-align: center;">
                            <h1 style="font-family: 'Jaro', sans-serif; color: #C49B3B; margin: 0 0 35px 0; font-size: 3rem; letter-spacing: 3px; text-shadow: 0 0 25px rgba(196, 155, 59, 0.4);">Damareen</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 35px 40px 35px;">
                            <h2 style="color: #C49B3B; margin: 0 0 25px 0; font-size: 1.8rem; font-weight: bold;">Bejelentkezés a fiókodba</h2>
                            <p style="color: #D9D9D9; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Szia {username}!
                            </p>
                            <p style="color: #D9D9D9; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                                Most bejelentkeztél a Damareen fiókodba. Ha ez te voltál, akkor minden rendben – jó játékot kívánunk!
                            </p>
                            <p style="color: rgba(217, 217, 217, 0.6); font-size: 13px; line-height: 1.6; margin: 30px 0 0 0;">
                                Ha nem te voltál, változtasd meg azonnal a jelszavad a fiókod védelme érdekében.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: rgba(196, 155, 59, 0.05); padding: 20px 30px; text-align: center; border-top: 1px solid rgba(196, 155, 59, 0.2);">
                            <p style="color: rgba(217, 217, 217, 0.5); font-size: 12px; margin: 0;">
                                © 2025 Horváth András és Balogh Barnabás. Minden jog fenntartva.
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
Bejelentkezés a fiókodba

Szia {username}!

Most bejelentkeztél a Damareen fiókodba. Ha ez te voltál, akkor minden rendben – jó játékot kívánunk!

Ha nem te voltál, változtasd meg azonnal a jelszavad a fiókod védelme érdekében.

© 2025 Horváth András és Balogh Barnabás. Minden jog fenntartva.
"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Bejelentkezés a fiókodba - Damareen'
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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0F0D13;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0F0D13; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background: rgba(196, 155, 59, 0.02); border: 2.5px solid rgba(196, 155, 59, 0.35); border-radius: 18px; overflow: hidden;">
                    <tr>
                        <td style="padding: 35px 25px; text-align: center;">
                            <h1 style="font-family: 'Jaro', sans-serif; color: #C49B3B; margin: 0 0 35px 0; font-size: 3rem; letter-spacing: 3px; text-shadow: 0 0 25px rgba(196, 155, 59, 0.4);">Damareen</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 35px 40px 35px;">
                            <h2 style="color: #C49B3B; margin: 0 0 25px 0; font-size: 1.8rem; font-weight: bold;">Jelszó visszaállítása</h2>
                            <p style="color: #D9D9D9; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Szia {username}!
                            </p>
                            <p style="color: #D9D9D9; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                                Jelszó visszaállítási kérelmet kaptunk a fiókodhoz. A jelszavad megváltoztatásához kattints az alábbi gombra:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" style="display: inline-block; padding: 13px 55px; background: rgba(196, 155, 59, 0.08); border: 2.8px solid #C49B3B; border-radius: 27px; color: #C49B3B; text-decoration: none; font-size: 1.25rem; font-weight: bold; box-shadow: 0 3px 12px rgba(196, 155, 59, 0.25);">Jelszó visszaállítása</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #D9D9D9; font-size: 14px; line-height: 1.6; margin: 25px 0 10px 0;">
                                Ha nem tudod megnyitni a gombot, másold be az alábbi linket a böngésződbe:
                            </p>
                            <p style="color: #C49B3B; font-size: 14px; word-break: break-all; margin: 10px 0 0 0;">
                                {reset_url}
                            </p>
                            <p style="color: rgba(217, 217, 217, 0.6); font-size: 13px; line-height: 1.6; margin: 30px 0 0 0;">
                                Ez a link 1 órán belül lejár. Ha nem te kérted a jelszó visszaállítását, hagyd figyelmen kívül ezt az e-mailt.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: rgba(196, 155, 59, 0.05); padding: 20px 30px; text-align: center; border-top: 1px solid rgba(196, 155, 59, 0.2);">
                            <p style="color: rgba(217, 217, 217, 0.5); font-size: 12px; margin: 0;">
                                © 2025 Horváth András és Balogh Barnabás. Minden jog fenntartva.
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

© 2025 Horváth András és Balogh Barnabás. Minden jog fenntartva.
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
