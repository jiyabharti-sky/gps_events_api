from flask import Flask, request, jsonify
from datetime import datetime
import uuid as uuid_lib

app = Flask(__name__)

# In-memory database for now (Replace with actual DB)
EVENTS_DB = []

class Event:
    def __init__(self, uuid, recorded_at, received_at, created_at, updated_at, category, device_uuid, metadata, notification_sent, is_deleted):
        self.uuid = uuid
        self.recorded_at = recorded_at
        self.received_at = received_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.category = category
        self.device_uuid = device_uuid
        self.metadata = metadata
        self.notification_sent = notification_sent
        self.is_deleted = is_deleted

    def save(self):
        """ Save event to database (Replace with actual DB logic) """
        EVENTS_DB.append(self)

    def to_dict(self):
        """ Convert object to dictionary for JSON response """
        return {
            "uuid": self.uuid,
            "recorded_at": self.recorded_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "category": self.category,
            "device_uuid": self.device_uuid,
            "metadata": self.metadata,
            "notification_sent": self.notification_sent,
            "is_deleted": self.is_deleted,
        }


@app.route('/create-event', methods=['POST'])
def create_event():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.json

    # validate requird fields
    required_fields = ['uuid', 'category', 'device_uuid']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Ensure UUID is valid?
    try:
        uuid_obj = uuid_lib.UUID(data["uuid"], version=4)
    except ValueError:
        return jsonify({"error": "Invalid UUID format"}), 400

    # checking here for valid category as per the criteria
    allowed_categories = [
        "DeviceOnline", "DeviceOffline", "DeviceHeartbeat", "DevicePairingStarted", 
        "DevicePairingFailed", "DevicePaired", "DeviceUnpairingStarted", "DeviceUnpairingFailed", 
        "DeviceUnpaired", "DeviceBatteryLow", "DeviceCharging", "DeviceChargingCompleted"
    ]
    
    if data["category"] not in allowed_categories:
        return jsonify({"error": "Invalid category"}), 400

    # Parse metadata as mentioned on confluence 
    metadata = data.get("metadata", {})

    try:
        recorded_at = datetime.fromisoformat(data.get("recorded_at", datetime.utcnow().isoformat()))
        received_at = datetime.utcnow()
        now = datetime.utcnow()

        new_event = Event(
            uuid=str(uuid_obj),
            recorded_at=recorded_at,
            received_at=received_at,
            created_at=now,
            updated_at=now,
            category=data["category"],
            device_uuid=data["device_uuid"],
            metadata=metadata,
            notification_sent=False,
            is_deleted=False
        )

        new_event.save()

        return jsonify({"message": "Event created successfully", "event": new_event.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to create event: {str(e)}"}), 500
    

@app.route('/event/<string:event_uuid>', methods=['GET'])
def get_event(event_uuid):
    """ Retrieve an event using its UUID """
    try:
        # Search for the event in the in-memory database
        event = next((e for e in EVENTS_DB if e.uuid == event_uuid), None)

        if not event:
            return jsonify({"error": "Event not found"}), 404

        return jsonify(event.to_dict()), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve event: {str(e)}"}), 500
    

@app.route('/get-events', methods=['GET'])
def get_all_events():
    # """ Retrieve all events """
    try:
        return jsonify([event.to_dict() for event in EVENTS_DB]), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve events: {str(e)}"}), 500
    
    
@app.route('/delete-event/<string:event_uuid>', methods=['DELETE'])
def delete_event(event_uuid):
    # """ Permanently delete a selected event by UUID """
    try:
        global EVENTS_DB  # use global to modify the list

        # Find the event index..dotdot
        event_index = next((index for index, e in enumerate(EVENTS_DB) if e.uuid == event_uuid), None)

        if event_index is None:
            return jsonify({"error": "Event not found"}), 404

        # Remove the event from the list, should not come up in get_eventS
        del EVENTS_DB[event_index]

        return jsonify({"message": f"Event {event_uuid} permanently deleted"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete event: {str(e)}"}), 500
    

    
@app.route('/update-event/<string:event_uuid>', methods=['PUT'])
def update_event(event_uuid):
    """ Update an existing event by UUID """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is missing or invalid"}), 400

        # find the event by UUID, not Device UUID only event one
        for event in EVENTS_DB:
            if str(event.uuid).strip() == event_uuid.strip():

                # Update only provided fields, that way it prevents mistakes
                if "category" in data:
                    allowed_categories = [
                        "DeviceOnline", "DeviceOffline", "DeviceHeartbeat", "DevicePairingStarted", 
                        "DevicePairingFailed", "DevicePaired", "DeviceUnpairingStarted", "DeviceUnpairingFailed", 
                        "DeviceUnpaired", "DeviceBatteryLow", "DeviceCharging", "DeviceChargingCompleted"
                    ]
                    if data["category"] not in allowed_categories:
                        return jsonify({"error": "Invalid category"}), 400
                    event.category = data["category"]

                if "metadata" in data:
                    event.metadata = data["metadata"]

                if "notification_sent" in data:
                    event.notification_sent = bool(data["notification_sent"])

                # update timestamp
                event.updated_at = datetime.utcnow()

                return jsonify({"message": f"Event {event_uuid} updated successfully", "event": event.to_dict()}), 200

        return jsonify({"error": "Event not found"}), 404

    except Exception as e:
        return jsonify({"error": f"Failed to update event: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(debug=True)

