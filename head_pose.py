import cv2
import mediapipe as mp
import numpy as np
import math
import time
from collections import deque

# MediaPipe Face Landmarker
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "face_landmarker.task"

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.IMAGE,
    num_faces=1
)

landmarker = FaceLandmarker.create_from_options(options)

# Camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# 3D face model points
face_3d = np.array([
    (0.0, 0.0, 0.0),             # Nose
    (0.0, -330.0, -65.0),        # Chin
    (-225.0, 170.0, -135.0),     # Left eye
    (225.0, 170.0, -135.0),      # Right eye
    (-150.0, -150.0, -125.0),    # Left mouth
    (150.0, -150.0, -125.0)      # Right mouth
], dtype=np.float64)

# Corresponding MediaPipe landmarks
LANDMARKS = [1, 152, 33, 263, 61, 291]

# Settings
CALIBRATION_TIME = 3.0
YAW_THRESHOLD = 20.0
YAW_RETURN_THRESHOLD = 12.0
DISTRACTION_TIME = 1.0
SMOOTHING_FRAMES = 7
MAX_YAW_JUMP = 30.0

# Variables
yaw_history = deque(maxlen=SMOOTHING_FRAMES)
calibration_yaws = []
calibration_start_time = time.time()
baseline_yaw = None
distraction_start_time = None
distraction_direction = None
previous_rotation_vector = None
previous_translation_vector = None
previous_valid_yaw = None
current_direction = "FORWARD"

def get_euler_angles(rotation_matrix):
    sy = math.sqrt(
        rotation_matrix[0, 0] ** 2 +
        rotation_matrix[1, 0] ** 2
    )

    singular = sy < 1e-6

    if not singular:
        pitch = math.degrees(math.atan2(
            rotation_matrix[1, 2],
            rotation_matrix[2, 2]
        ))

        yaw = math.degrees(math.atan2(
            -rotation_matrix[2, 0],
            sy
        ))

        roll = math.degrees(math.atan2(
            rotation_matrix[1, 0],
            rotation_matrix[0, 0]
        ))
        
    else:
        pitch = math.degrees(math.atan2(
            rotation_matrix[1, 2],
            rotation_matrix[2, 2]
        ))

        yaw = math.degrees(math.atan2(
            -rotation_matrix[2, 0],
            sy
        ))

        roll = 0

    return pitch, yaw, roll

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame")
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Convert frame to MediaPipe format
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = landmarker.detect(mp_image)

    if result.face_landmarks:
        landmarks = result.face_landmarks[0]
        face_2d = []

        # Get required landmarks
        for landmark_index in LANDMARKS:
            landmark = landmarks[landmark_index]
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            face_2d.append((x, y))

            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

        face_2d = np.array(face_2d, dtype=np.float64)

        # Camera matrix
        focal_length = w
        camera_matrix = np.array([
            [focal_length, 0, w / 2],
            [0, focal_length, h / 2],
            [0, 0, 1]
        ], dtype=np.float64)

        distortion_matrix = np.zeros((4, 1), dtype=np.float64)

        # Use previous pose as the starting estimate
        if previous_rotation_vector is not None:
            success, rotation_vector, translation_vector = cv2.solvePnP(
                face_3d,
                face_2d,
                camera_matrix,
                distortion_matrix,
                previous_rotation_vector,
                previous_translation_vector,
                True,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
        else:
            success, rotation_vector, translation_vector = cv2.solvePnP(
                face_3d,
                face_2d,
                camera_matrix,
                distortion_matrix,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

        if success:
            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
            pitch, yaw, roll = get_euler_angles(rotation_matrix)

            # Reject sudden unstable yaw changes
            yaw_is_valid = True

            if previous_valid_yaw is not None:
                yaw_change = abs(yaw - previous_valid_yaw)

                if yaw_change > MAX_YAW_JUMP:
                    yaw_is_valid = False

            if yaw_is_valid:
                previous_rotation_vector = rotation_vector.copy()
                previous_translation_vector = translation_vector.copy()
                previous_valid_yaw = yaw
                yaw_history.append(yaw)

            # Median + mean smoothing
            if len(yaw_history) > 0:
                median_yaw = np.median(yaw_history)
                mean_yaw = np.mean(yaw_history)
                smooth_yaw = 0.7 * median_yaw + 0.3 * mean_yaw
            else:
                smooth_yaw = yaw

            # Calibration
            if baseline_yaw is None:
                calibration_yaws.append(smooth_yaw)

                elapsed = time.time() - calibration_start_time
                remaining = CALIBRATION_TIME - elapsed

                cv2.putText(
                    frame,
                    "CALIBRATING...",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    3
                )

                cv2.putText(
                    frame,
                    "Look straight at the camera",
                    (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Time: {max(0, remaining):.1f}s",
                    (20, 125),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

                if elapsed >= CALIBRATION_TIME:
                    baseline_yaw = np.median(calibration_yaws)
                    print("Calibration complete.")
                    print(f"Baseline yaw: {baseline_yaw:.2f}")

            else:
                # Calculate yaw relative to calibrated forward position
                relative_yaw = -(smooth_yaw - baseline_yaw)

                # Hysteresis prevents rapid direction switching
                if current_direction == "FORWARD":
                    if relative_yaw < -YAW_THRESHOLD:
                        current_direction = "LEFT"
                    elif relative_yaw > YAW_THRESHOLD:
                        current_direction = "RIGHT"

                elif current_direction == "LEFT":
                    if relative_yaw > -YAW_RETURN_THRESHOLD:
                        current_direction = "FORWARD"
                    elif relative_yaw > YAW_THRESHOLD:
                        current_direction = "RIGHT"

                elif current_direction == "RIGHT":
                    if relative_yaw < YAW_RETURN_THRESHOLD:
                        current_direction = "FORWARD"
                    elif relative_yaw < -YAW_THRESHOLD:
                        current_direction = "LEFT"

                direction = current_direction

                # Distraction timer
                if direction in ["LEFT", "RIGHT"]:
                    if distraction_start_time is None:
                        distraction_start_time = time.time()
                        distraction_direction = direction
                    elif direction != distraction_direction:
                        distraction_start_time = time.time()
                        distraction_direction = direction

                    distraction_duration = (
                        time.time() - distraction_start_time
                    )
                else:
                    distraction_start_time = None
                    distraction_direction = None
                    distraction_duration = 0

                # Final status
                if (
                    distraction_start_time is not None
                    and distraction_duration >= DISTRACTION_TIME
                ):
                    status = "DISTRACTED"
                else:
                    status = "ATTENTIVE"

                # Display values
                cv2.putText(
                    frame,
                    f"Raw Yaw: {yaw:.2f}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Smooth Yaw: {smooth_yaw:.2f}",
                    (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Relative Yaw: {relative_yaw:.2f}",
                    (20, 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Baseline: {baseline_yaw:.2f}",
                    (20, 125),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Pitch: {pitch:.2f}",
                    (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"Roll: {roll:.2f}",
                    (180, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    direction,
                    (20, 195),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0),
                    3
                )

                if distraction_start_time is not None:
                    cv2.putText(
                        frame,
                        f"Away: {distraction_duration:.1f}s",
                        (20, 235),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 165, 255),
                        2
                    )

                cv2.putText(
                    frame,
                    status,
                    (20, 285),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0) if status == "ATTENTIVE" else (0, 0, 255),
                    3
                )

        else:
            cv2.putText(
                frame,
                "HEAD POSE UNSTABLE",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

    else:
        cv2.putText(
            frame,
            "NO FACE DETECTED",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    cv2.imshow("Driver Head Pose Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()