from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = "events"

    uuid = db.Column(db.String(50), primary_key=True)
    recorded_at = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    device_uuid = db.Column(db.String(50), nullable=False)
    # metadata = db.Column(db.String(50), nullable=False)
    notification_sent = db.Column(db.Boolean, default=False, nullable=False)    
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)   
    # store "metadata" as JSON in a text column
    metadata_json = db.Column(db.Text, nullable=False, default='{}')

    notification_sent = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Event {self.uuid}>"


    def __repr__(self):
        return f"<Event {self.uuid}>"
