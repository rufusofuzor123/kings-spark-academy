import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kings-spark-academy-secure-key-2026')
    
    # Render PostgreSQL Internal Database URL with SQLite fallback for local testing
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///kings_spark.db')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('static', 'uploads', 'passports')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB Max upload
    
    # External APIs
    SMS_API_KEY = os.environ.get('SMS_API_KEY', 'your_sms_api_key')
    SMS_SENDER_ID = 'KingsSpark'
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_xxxxxxxxxxxxxxxx')