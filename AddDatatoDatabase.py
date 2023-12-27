import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': ""
})

ref = db.reference('Students')

data = {
    "407957":
        {
            "name": "Muhammad Huzaifa",
            "major": "Electrical Engineering",
            "starting_year": 2022,
            "total_attendance": 7,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "407955":
        {
            "name": "Mulana Tariq Jameel",
            "major": "Islamic",
            "starting_year": 2023,
            "total_attendance": 12,
            "standing": "G",
            "year": 1,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
}

for key, value in data.items():
    ref.child(key).set(value)
