import cv2
import mediapipe as mp
import math
import time

# Helper function: calculate distance between two landmarks
def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )

# Eye landmark indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Calculate Eye Aspect Ratio (EAR)

def calculate_ear(landmarks, eye):

    p1 = landmarks[eye[0]]
    p2 = landmarks[eye[1]]
    p3 = landmarks[eye[2]]
    p4 = landmarks[eye[3]]
    p5 = landmarks[eye[4]]
    p6 = landmarks[eye[5]]

    vertical1 = distance(p2, p6)
    vertical2 = distance(p3, p5)
    horizontal = distance(p1, p4)

    ear = (vertical1 + vertical2) / (2 * horizontal)
    return ear

# MediaPipe Tasks setup

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options = BaseOptions(model_asset_path="face_landmarker.task"),
    running_mode = VisionRunningMode.VIDEO,
    num_faces = 1
)

# Settings
EAR_THRESHOLD = 0.20
DROWSY_TIME = 2.0

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

# Start MediaPipe

eyes_closed = False
closed_start_time = None

with FaceLandmarker.create_from_options(options) as landmarker:

    timestamp_ms = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("ERROR: Could not read frame.")
            break

        # Convert BGR → RGB as MediaPipe expects RGB images
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Convert OpenCV image to MediaPipe Image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # Detect face landmarks
        result = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        timestamp_ms += 33

        if result.face_landmarks:

            landmarks = result.face_landmarks[0]

            # Calculate left and right EAR and average
            left_ear = calculate_ear(
                landmarks,
                LEFT_EYE
            )
            right_ear = calculate_ear(
                landmarks,
                RIGHT_EYE
            )
            ear = (left_ear + right_ear) / 2

            # Determine eye state

            if ear < EAR_THRESHOLD:
                eye_status = "CLOSED"
                if not eyes_closed:
                    eyes_closed = True
                    closed_start_time = time.time()
                closed_duration = time.time() - closed_start_time
            
            else:
                eye_status = "OPEN"
                eyes_closed = False
                closed_start_time = None
                closed_duration = 0

            # Determine drowsiness
            
            if eyes_closed and closed_duration >= DROWSY_TIME:
                status = "DROWSY"
            else:
                status = "NORMAL"
            

            # Display EAR value
            cv2.putText(
                frame,
                f"EAR: {ear:.2f}",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Display eye status
            cv2.putText(
                frame,
                f"Eyes: {eye_status}",
                (30, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Display closed duration
            cv2.putText(
                frame,
                f"Closed: {closed_duration:1f}s",
                (30, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Display Final Status
            cv2.putText(
                frame,
                f"Status: {status}",
                (30, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255) if status == "DROWSY" else (0,255,0),
                2
            )

            # Draw all 478 face landmarks

            h, w, _ = frame.shape

            for landmark in landmarks:

                x = int(landmark.x * w)
                y = int(landmark.y * h)

                cv2.circle(
                    frame,
                    (x, y),
                    1,
                    (0, 255, 0),
                    -1
                )

            # Highlight eye landmarks
            for index in LEFT_EYE + RIGHT_EYE:
                landmark = landmarks[index]
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(
                    frame,
                    (x, y),
                    4,
                    (0, 0, 255),
                    -1
                )

        else:
            # No Face Detected
            cv2.putText(
                frame,
                "No Face Detected",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2
            )


        # Display webcam
        cv2.imshow(
            "Driver Camera",
            frame
        )

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

# Cleanup
cap.release()
cv2.destroyAllWindows()