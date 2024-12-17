from flask_cors import CORS
from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

CORS(app)

if __name__ == '__main__':
    app.run(debug=True)