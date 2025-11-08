import os


class EmailConfig:
    SMTP_SERVER = 'smtp.dreamhost.com'
    SMTP_PORT = 587
    SMTP_USE_TLS = True
    SMTP_USERNAME = os.environ.get('EMAIL_USERNAME', 'damareen@deakteri.cloud')
    SMTP_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'password')
    SENDER_EMAIL = 'damareen@deakteri.cloud'
    SENDER_NAME = 'Damareen'
    
    VERIFICATION_TOKEN_EXPIRATION_HOURS = 24
    VERIFICATION_URL_BASE = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    REQUIRE_EMAIL_VERIFICATION = os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'false').lower() == 'true'
