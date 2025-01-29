from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

class Event:
    def __init__(self, uuid, recorded_at, received_at, created_at, updated_at, category, device_uuid, metadata_json, notification_sent, is_deleted):
        self.uuid = uuid
        self.recorded_at = recorded_at
        self.received_at = received_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.category = category
        self.device_uuid = device_uuid
        self.metadata_json = metadata_json
        self.notification_sent = notification_sent
        self.is_deleted = is_deleted

    def save(self):
        # db????
        pass

@app.route('/create-event', methods=['POST'])
def create_event():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.json
    
    # Validate required fields
    required_fields = ['uuid', 'category', 'device_uuid']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    metadata_dict = data.get("metadata", {})

    try:
        recorded_at = datetime.now()
        received_at = datetime.now()
        now = datetime.now()

        new_event = Event(
            uuid=data["uuid"],
            recorded_at=recorded_at,
            received_at=received_at,
            created_at=now,
            updated_at=now,
            category=data["category"],
            device_uuid=data["device_uuid"],
            metadata_json=json.dumps(metadata_dict),
            notification_sent=False,
            is_deleted=False
        )

        new_event.save()

        return jsonify({"message": "Event created successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        return jsonify({"error": f"Failed to create event: {str(e)}"}), 500
    

@app.route('/get-event', methods=['GET'])
    
def get_events():
        try:
            events = Event.query.all()
            events_list = [event.to_dict() for event in events]
            return jsonify(events_list), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
