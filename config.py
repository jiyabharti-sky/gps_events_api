# Holds the DB connection URI
# This is used to connect to the database


DB_USERNAME = "root"
DB_PASSWORD = "jiyabharti"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "gps_events"

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
