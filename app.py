import json
import os
import boto3
import mysql.connector
from flask import Flask, jsonify, request
from datetime import datetime
from dotenv import load_dotenv
import uuid as uuid_lib

# load environment variables
load_dotenv()

app = Flask(__name__)

# MySQL connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="jiyabharti",
    database="gps_events"
)
mycursor = mydb.cursor(dictionary=True)  

# sent to AWS S3 client
s3 = boto3.client(
    "s3"
)

# to check if the connection is made

print(os.getenv("AWS_REGION"))

print(os.getenv("AWS_SECRET_ACCESS_KEY"))


print(os.getenv("AWS_ACCESS_KEY_ID"))




@app.route("/export-events", methods=["GET"])
def export_events():
    """ Export event records as a JSON file and upload to AWS S3 """
    try:
        # rtrieve all events from the database
        sql_query = "SELECT * FROM events"
        mycursor.execute(sql_query)
        events = mycursor.fetchall()

        if not events:
            return jsonify({"error": "No events found"}), 404

        json_data = json.dumps(events, default=str, indent=4)  

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"events_backup_{timestamp}.json"

        s3.put_object(Bucket="gpsevents-sky", Key=file_name, Body=json_data, ContentType="application/json")

        file_url = f"https://{"gpsevents-sky"}.s3.amazonaws.com/{file_name}"

        return jsonify({"message": "Export successful", "file_url": file_url}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to export events: {str(e)}"}), 500




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



# in-memory database for now
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
        """ Save event to database  """
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

    
    required_fields = ['uuid', 'category', 'device_uuid']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    
    try:
        uuid_obj = uuid_lib.UUID(data["uuid"], version=4)
    except ValueError:
        return jsonify({"error": "Invalid UUID format"}), 400

    
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

        # innsert the event into the database
        sql = """INSERT INTO events 
                 (uuid, recorded_at, received_at, created_at, updated_at, category, device_uuid, `metadata`, notification_sent, is_deleted) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, CAST(%s AS JSON), %s, %s)"""
        values = (
            str(uuid_obj), 
            recorded_at, 
            received_at, 
            now, 
            now, 
            data["category"], 
            data["device_uuid"], 
            json.dumps(metadata), 
            False, 
            False
        )

        mycursor.execute(sql, values)
        mydb.commit()

        # no success message, just the event data - like confluence
        return jsonify({
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
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to create event: {str(e)}"}), 422

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

        event_data = {
            "uuid": event[0],
            "recorded_at": event[1].isoformat() if event[1] else None,
            "received_at": event[2].isoformat() if event[2] else None,
            "created_at": event[3].isoformat() if event[3] else None,
            "updated_at": event[4].isoformat() if event[4] else None,
            "category": event[5],
            "device_uuid": event[6],
            "metadata": json.loads(event[7]) if event[7] else {}, 
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

        # converts query result into a list of dictionaries
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
                "metadata": json.loads(event[7]) if event[7] else {}, 
                "notification_sent": bool(event[8]),
                "is_deleted": bool(event[9])
            })

        return jsonify(event_list), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve events: {str(e)}"}), 500

    # delete an event
    
@app.route('/delete-event/<string:event_uuid>', methods=['DELETE'])
def delete_event(event_uuid):
    """ soft dleteevent by setting is_deleted to true in MySQL """
    try:
        # Check if the event exists and its current is_deleted status
        sql_check = "SELECT is_deleted FROM events WHERE uuid = %s"
        mycursor.execute(sql_check, (event_uuid,))
        event = mycursor.fetchone()

        if not event:
            return jsonify({"error": "Event not found"}), 404

        
        if event[0]:  
            return jsonify({"error": "Event is already deleted"}), 422

        # Update is_deleted flag to true
        sql_update = "UPDATE events SET is_deleted = TRUE, updated_at = NOW() WHERE uuid = %s"
        mycursor.execute(sql_update, (event_uuid,))
        mydb.commit()

        return "", 204  # confluence says no message should be returned just success

    except Exception as e:
        return jsonify({"error": f"Failed to delete event: {str(e)}"}), 500


    
@app.route('/update-event/<string:event_uuid>', methods=['PUT'])
def update_event(event_uuid):
    """ Set notification_sent to true for an event in MySQL """
    try:
        event_uuid = event_uuid.strip()

        # check if the event exists and get current notification_sent status
        sql_check = "SELECT notification_sent FROM events WHERE uuid = %s"
        mycursor.execute(sql_check, (event_uuid,))
        event = mycursor.fetchone()

        if not event:
            return jsonify({"error": "Event not found"}), 404

        # check if notification_sent is already true
        if event[0]:  
            return jsonify({"error": "Notification already sent"}), 422

        # update notification_sent to true
        sql_update = "UPDATE events SET notification_sent = TRUE, updated_at = NOW() WHERE uuid = %s"
        mycursor.execute(sql_update, (event_uuid,))
        mydb.commit()

        # =get updated event details
        sql_get = """SELECT uuid, recorded_at, received_at, created_at, updated_at, category, 
                            device_uuid, metadata, notification_sent, is_deleted 
                     FROM events WHERE uuid = %s"""
        mycursor.execute(sql_get, (event_uuid,))
        updated_event = mycursor.fetchone()

        return jsonify({
            "uuid": updated_event[0],
            "recorded_at": updated_event[1].isoformat() if updated_event[1] else None,
            "received_at": updated_event[2].isoformat() if updated_event[2] else None,
            "created_at": updated_event[3].isoformat() if updated_event[3] else None,
            "updated_at": updated_event[4].isoformat() if updated_event[4] else None,
            "category": updated_event[5],
            "device_uuid": updated_event[6],
            "metadata": json.loads(updated_event[7]) if updated_event[7] else {},
            "notification_sent": bool(updated_event[8]),
            "is_deleted": bool(updated_event[9])
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update event: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

