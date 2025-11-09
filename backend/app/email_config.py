import os


class EmailConfig:
    # SMTP szerver beállítások - Dreamhost-ot használunk
    SMTP_SERVER = 'smtp.dreamhost.com'
    SMTP_PORT = 587
    SMTP_USE_TLS = True  # TLS kell, különben nem fog menni
    
    # Email credentials - .env-ből jönnek
    SMTP_USERNAME = os.environ.get('EMAIL_USERNAME', 'damareen@deakteri.cloud')
    SMTP_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'password')
    SENDER_EMAIL = 'damareen@deakteri.cloud'
    SENDER_NAME = 'Damareen'
    
    # Verification token 24 óráig él
    VERIFICATION_TOKEN_EXPIRATION_HOURS = 24
    VERIFICATION_URL_BASE = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Email verifikáció ki/be kapcsolása - dev-ben ki van kapcsolva
    REQUIRE_EMAIL_VERIFICATION = os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'false').lower() == 'true'
