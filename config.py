# config.py
class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cafe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False