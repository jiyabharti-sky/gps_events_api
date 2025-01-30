from flask import Flask, request, jsonify
from datetime import datetime
import uuid as uuid_lib
import json

app = Flask(__name__)




import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="jiyabharti",
  database="gps_events"
)






mycursor = mydb.cursor()
mycursor.execute("""CREATE TABLE IF NOT EXISTS events (
    uuid VARCHAR(36) PRIMARY KEY,
    recorded_at DATETIME,
    received_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    category VARCHAR(255),
    device_uuid VARCHAR(36),
    `metadata` JSON,  -- Ensure this column exists
    notification_sent BOOLEAN,
    is_deleted BOOLEAN
);""")



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

    # Validate required fields
    required_fields = ['uuid', 'category', 'device_uuid']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Ensure UUID is valid
    try:
        uuid_obj = uuid_lib.UUID(data["uuid"], version=4)
    except ValueError:
        return jsonify({"error": "Invalid UUID format"}), 400

    # Validate category
    allowed_categories = [
        "DeviceOnline", "DeviceOffline", "DeviceHeartbeat", "DevicePairingStarted", 
        "DevicePairingFailed", "DevicePaired", "DeviceUnpairingStarted", "DeviceUnpairingFailed", 
        "DeviceUnpaired", "DeviceBatteryLow", "DeviceCharging", "DeviceChargingCompleted"
    ]

    if data["category"] not in allowed_categories:
        return jsonify({"error": "Invalid category"}), 400

    metadata = data.get("metadata", {})

    try:
        recorded_at = datetime.fromisoformat(data.get("recorded_at", datetime.utcnow().isoformat()))
        received_at = datetime.utcnow()
        now = datetime.utcnow()

        # Correct SQL query with JSON handling
        sql = """INSERT INTO events 
                 (uuid, recorded_at, received_at, created_at, updated_at, category, device_uuid, `metadata`, notification_sent, is_deleted) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, CAST(%s AS JSON), %s, %s)"""
        values = (str(uuid_obj), recorded_at, received_at, now, now, 
                  data["category"], data["device_uuid"], json.dumps(metadata), False, False)

        mycursor.execute(sql, values)
        mydb.commit()

        return jsonify({"message": "Event created successfully", "event": {
            "uuid": str(uuid_obj),
            "recorded_at": recorded_at.isoformat(),
            "received_at": received_at.isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "category": data["category"],
            "device_uuid": data["device_uuid"],
            "metadata": metadata,
            "notification_sent": False,
            "is_deleted": False
        }}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to create event: {str(e)}"}), 500

# get one event

@app.route('/event/<string:event_uuid>', methods=['GET'])
def get_event(event_uuid):
    """ Retrieve an event using its UUID from MySQL """
    try:
        # Query MySQL for the event
        sql = "SELECT uuid, recorded_at, received_at, created_at, updated_at, category, device_uuid, metadata, notification_sent, is_deleted FROM events WHERE uuid = %s"
        mycursor.execute(sql, (event_uuid,))
        event = mycursor.fetchone()

        # If no event is found
        if not event:
            return jsonify({"error": "Event not found"}), 404

        # Convert MySQL row to a dictionary
        event_data = {
            "uuid": event[0],
            "recorded_at": event[1].isoformat() if event[1] else None,
            "received_at": event[2].isoformat() if event[2] else None,
            "created_at": event[3].isoformat() if event[3] else None,
            "updated_at": event[4].isoformat() if event[4] else None,
            "category": event[5],
            "device_uuid": event[6],
            "metadata": json.loads(event[7]) if event[7] else {},  # Convert JSON string to Python dict
            "notification_sent": bool(event[8]),
            "is_deleted": bool(event[9])
        }

        return jsonify(event_data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve event: {str(e)}"}), 500

    
    # get all events

@app.route('/get-events', methods=['GET'])
def get_all_events():
    """ Retrieve all events from MySQL """
    try:
        # Fetch all events from MySQL
        sql = "SELECT uuid, recorded_at, received_at, created_at, updated_at, category, device_uuid, metadata, notification_sent, is_deleted FROM events"
        mycursor.execute(sql)
        events = mycursor.fetchall()

        # Convert query result into a list of dictionaries
        event_list = []
        for event in events:
            event_list.append({
                "uuid": event[0],
                "recorded_at": event[1].isoformat() if event[1] else None,
                "received_at": event[2].isoformat() if event[2] else None,
                "created_at": event[3].isoformat() if event[3] else None,
                "updated_at": event[4].isoformat() if event[4] else None,
                "category": event[5],
                "device_uuid": event[6],
                "metadata": json.loads(event[7]) if event[7] else {},  # Convert JSON string to Python dict
                "notification_sent": bool(event[8]),
                "is_deleted": bool(event[9])
            })

        return jsonify(event_list), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve events: {str(e)}"}), 500

    # delete an event
    
@app.route('/delete-event/<string:event_uuid>', methods=['DELETE'])
def delete_event(event_uuid):
    """ Permanently delete a selected event by UUID from MySQL """
    try:
        # Check if the event exists
        sql_check = "SELECT uuid FROM events WHERE uuid = %s"
        mycursor.execute(sql_check, (event_uuid,))
        event = mycursor.fetchone()

        if not event:
            return jsonify({"error": "Event not found"}), 404

        # Delete the event from the database
        sql_delete = "DELETE FROM events WHERE uuid = %s"
        mycursor.execute(sql_delete, (event_uuid,))
        mydb.commit()

        return jsonify({"message": f"Event {event_uuid} permanently deleted"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete event: {str(e)}"}), 500


    
@app.route('/update-event/<string:event_uuid>', methods=['PUT'])
def update_event(event_uuid):
    """ Update an existing event by UUID in MySQL """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is missing or invalid"}), 400
        event_uuid = event_uuid.strip()

        # Check if the event exists
        sql_check = "SELECT uuid FROM events WHERE uuid = %s"
        mycursor.execute(sql_check, (event_uuid,))
        event = mycursor.fetchone()

        if not event:
            return jsonify({"error": f"Event not found: {event_uuid}"}), 404

        # Allowed categories check
        if "category" in data:
            allowed_categories = [
                "DeviceOnline", "DeviceOffline", "DeviceHeartbeat", "DevicePairingStarted", 
                "DevicePairingFailed", "DevicePaired", "DeviceUnpairingStarted", "DeviceUnpairingFailed", 
                "DeviceUnpaired", "DeviceBatteryLow", "DeviceCharging", "DeviceChargingCompleted"
            ]
            if data["category"] not in allowed_categories:
                return jsonify({"error": "Invalid category"}), 400

        # Build dynamic SQL update query
        update_fields = []
        values = []

        if "category" in data:
            update_fields.append("category = %s")
            values.append(data["category"])

        if "metadata" in data:
            update_fields.append("metadata = %s")
            values.append(json.dumps(data["metadata"]))  # Convert dict to JSON string

        if "notification_sent" in data:
            update_fields.append("notification_sent = %s")
            values.append(bool(data["notification_sent"]))

        # Always update `updated_at`
        update_fields.append("updated_at = NOW()")

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        # Execute update query
        sql_update = f"UPDATE events SET {', '.join(update_fields)} WHERE uuid = %s"
        values.append(event_uuid)

        mycursor.execute(sql_update, tuple(values))
        mydb.commit()

        return jsonify({"message": f"Event {event_uuid} updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update event: {str(e)}"}), 500




if __name__ == '__main__':
    app.run(debug=True)

