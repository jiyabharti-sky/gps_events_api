# Contains the Flask routes (POST /events, GET /events, etc.) plus the DB initialisation.
# app.py
from flask import Flask
from models import db
import config

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def home():
    return "Hello from Bootstrap Service!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
