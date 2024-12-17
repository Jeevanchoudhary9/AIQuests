import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['UPLOAD_FOLDER'] = './uploaded_files'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
    app.secret_key = 'supersecretkey'

    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

    db.init_app(app)

    from .routes.user import user_bpt
    from .routes.moderator import moderator_bpt
    from .routes.organization import organization_bpt
    from .routes.up_down_votes import votes_bpt
    from .routes.question_answer import QA_bpt
    from .routes.other import other_bpt

    app.register_blueprint(user_bpt, url_prefix='/')
    app.register_blueprint(moderator_bpt, url_prefix='/')
    app.register_blueprint(organization_bpt,url_prefix='/')
    app.register_blueprint(votes_bpt,url_prefix='/')
    app.register_blueprint(QA_bpt,url_prefix='/')
    app.register_blueprint(other_bpt,url_prefix='/')

    return app