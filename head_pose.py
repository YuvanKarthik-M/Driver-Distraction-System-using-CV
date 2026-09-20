import cv2
import numpy as np
import math
import time
from collections import deque

# 3D face model points
FACE_3D = np.array([
    (0.0, 0.0, 0.0),
    (0.0, -330.0, -65.0),
    (-225.0, 170.0, -135.0),
    (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0),
    (150.0, -150.0, -125.0)
], dtype=np.float64)

# Corresponding MediaPipe landmarks
LANDMARKS = [1, 152, 33, 263, 61, 291]

# Head pose settings
CALIBRATION_TIME = 5.0
YAW_THRESHOLD = 25.0
YAW_RETURN_THRESHOLD = 20.0
SMOOTHING_FRAMES = 7
MAX_YAW_JUMP = 30.0


class HeadPoseDetector:

    def __init__(self):
        self.yaw_history = deque(maxlen=SMOOTHING_FRAMES)
        self.calibration_yaws = []

        self.calibration_start_time = time.time()
        self.baseline_yaw = None

        self.previous_rotation_vector = None
        self.previous_translation_vector = None
        self.previous_valid_yaw = None

        self.current_direction = "FORWARD"

    def get_euler_angles(self, rotation_matrix):
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

    def calculate_pose(self, landmarks, frame_width, frame_height):
        face_2d = []

        for landmark_index in LANDMARKS:
            landmark = landmarks[landmark_index]

            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)

            face_2d.append((x, y))

        face_2d = np.array(face_2d, dtype=np.float64)

        focal_length = frame_width

        camera_matrix = np.array([
            [focal_length, 0, frame_width / 2],
            [0, focal_length, frame_height / 2],
            [0, 0, 1]
        ], dtype=np.float64)

        distortion_matrix = np.zeros((4, 1), dtype=np.float64)

        if self.previous_rotation_vector is not None:
            success, rotation_vector, translation_vector = cv2.solvePnP(
                FACE_3D,
                face_2d,
                camera_matrix,
                distortion_matrix,
                self.previous_rotation_vector,
                self.previous_translation_vector,
                True,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
        else:
            success, rotation_vector, translation_vector = cv2.solvePnP(
                FACE_3D,
                face_2d,
                camera_matrix,
                distortion_matrix,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

        if not success:
            return None

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

        pitch, yaw, roll = self.get_euler_angles(rotation_matrix)

        yaw_is_valid = True

        if self.previous_valid_yaw is not None:
            yaw_change = abs(yaw - self.previous_valid_yaw)

            if yaw_change > MAX_YAW_JUMP:
                yaw_is_valid = False

        if yaw_is_valid:
            self.previous_rotation_vector = rotation_vector.copy()
            self.previous_translation_vector = translation_vector.copy()
            self.previous_valid_yaw = yaw

            self.yaw_history.append(yaw)

        if len(self.yaw_history) > 0:
            median_yaw = np.median(self.yaw_history)
            mean_yaw = np.mean(self.yaw_history)

            smooth_yaw = 0.7 * median_yaw + 0.3 * mean_yaw
        else:
            smooth_yaw = yaw

        if self.baseline_yaw is None:
            self.calibration_yaws.append(smooth_yaw)

            elapsed = time.time() - self.calibration_start_time

            progress = min(
                100,
                int((elapsed / CALIBRATION_TIME) * 100)
            )

            if elapsed < 2.5:
                calibration_message = "LOOK FORWARD"

            else:
                calibration_message = "CALIBRATING"

            if elapsed >= CALIBRATION_TIME:
                self.baseline_yaw = np.median(
                    self.calibration_yaws
                )

                print("Calibration complete.")
                print(
                    f"Baseline yaw: {self.baseline_yaw:.2f}"
                )

            return {
                "pitch": pitch,
                "yaw": yaw,
                "roll": roll,
                "smooth_yaw": smooth_yaw,
                "relative_yaw": None,
                "direction": "CALIBRATING",
                "calibrated": False,
                "calibration_progress": progress,
                "calibration_message": calibration_message
            }

        relative_yaw = -(smooth_yaw - self.baseline_yaw)

        if self.current_direction == "FORWARD":

            if relative_yaw < -YAW_THRESHOLD:
                self.current_direction = "LEFT"

            elif relative_yaw > YAW_THRESHOLD:
                self.current_direction = "RIGHT"

        elif self.current_direction == "LEFT":

            if relative_yaw > -YAW_RETURN_THRESHOLD:
                self.current_direction = "FORWARD"

            elif relative_yaw > YAW_THRESHOLD:
                self.current_direction = "RIGHT"

        elif self.current_direction == "RIGHT":

            if relative_yaw < YAW_RETURN_THRESHOLD:
                self.current_direction = "FORWARD"

            elif relative_yaw < -YAW_THRESHOLD:
                self.current_direction = "LEFT"

        return {
            "pitch": pitch,
            "yaw": yaw,
            "roll": roll,
            "smooth_yaw": smooth_yaw,
            "relative_yaw": relative_yaw,
            "direction": self.current_direction,
            "calibrated": True
        }