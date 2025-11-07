import os


class EmailConfig:
    SMTP_SERVER = 'smtp.dreamhost.com'
    SMTP_PORT = 587
    SMTP_USE_TLS = True
    SMTP_USERNAME = os.environ.get('EMAIL_USERNAME', 'damareen@deakteri.fun')
    SMTP_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'password')
    SENDER_EMAIL = 'damareen@deakteri.fun'
    SENDER_NAME = 'Damareen'
    
    VERIFICATION_TOKEN_EXPIRATION_HOURS = 24
    VERIFICATION_URL_BASE = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
