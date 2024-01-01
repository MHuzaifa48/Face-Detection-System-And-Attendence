import os
import pickle
import numpy as np
import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, db, storage, exceptions as firebase_exceptions
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': " ",
    'storageBucket': " "
})

bucket = storage.bucket()

# Initialize video capture
cap = cv2.VideoCapture(0)  # Change the index if necessary
cap.set(3, 640)
cap.set(4, 480)

# Check if the camera is opened successfully
if not cap.isOpened():
    print("Error: Unable to open the camera.")
    exit()

# Load the background image
imgBackground = cv2.imread('Resources/background.png')

# Import mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]

# Load the encoding file
print("Loading Encode File ...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)

encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgStudent = []

while True:
    # Capture frame
    success, img = cap.read()

    # Check if the frame is captured successfully
    if not success:
        print("Error: Unable to capture frame. Exiting...")
        break

    # Resize and convert the frame once
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList) - 1)]

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)
            if not matches[matchIndex]:
                modeType = 0
                counter = 0
                cv2.putText(imgBackground, "Invalid Person", (275, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Face Attendance System", imgBackground)
                cv2.waitKey(1)

            else:
                confidence = 1 - faceDis[matchIndex]  # Confidence is a value between 0 and 1
                if confidence >= 0.5:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imgBackground = cv2.rectangle(imgBackground, (int(bbox[0]), int(bbox[1])),
                                                  (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3])), (0, 255, 0), 2)
                    id = studentIds[matchIndex]

                    if counter == 0:
                        cv2.putText(imgBackground, "Loading", (275, 400), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (255, 255, 255), 2)
                        cv2.imshow("Face Attendance System", imgBackground)
                        cv2.waitKey(1)
                        counter = 1
                        modeType = 1

                    try:
                        # Try to access the student information from the database
                        studentInfo = db.reference(f'Students/{id}').get()
                    except firebase_exceptions.FirebaseError as e:
                        print(f"Error accessing Firebase: {e}")
                        counter = 0
                        modeType = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList) - 1)]
                        continue

                    blob = bucket.get_blob(f'images/{id}.png')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)

                    datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()

                    if secondsElapsed > 30:
                        ref = db.reference(f'Students/{id}')
                        studentInfo['total_attendance'] += 1
                        ref.child('total_attendance').set(studentInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList) - 1)]

                    if counter != 0:
                        if counter == 1:
                            # Your existing code for displaying student information here
                            counter += 1

                        if modeType != 3:
                            if 10 < counter < 20:
                                modeType = 2

                            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList) - 1)]

                            if counter <= 10:
                                # Your existing code for displaying student information here
                                counter += 1

                            if counter >= 20:
                                counter = 0
                                modeType = 0
                                studentInfo = []
                                imgStudent = []
                                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList) - 1)]

    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance System", imgBackground)
    key = cv2.waitKey(1)

    if key == ord('q'):  # Press 'q' to exit
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
