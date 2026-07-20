import os
import sys
from flask import Flask
from app.models import db
from app.routes import main

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "app", "templates"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bipagen-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bipagen.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
app.register_blueprint(main)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
