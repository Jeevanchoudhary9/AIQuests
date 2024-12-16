from dotenv import load_dotenv
import os
import ssl
import nltk
# ssl._create_default_https_context = ssl._create_unverified_context
# nltk.download('wordnet')


load_dotenv()
from app import app

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = './uploaded_files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
app.secret_key = 'supersecretkey'
# app.config['SESSION_TIME'] = os.getenv('SESSION_TIME')





