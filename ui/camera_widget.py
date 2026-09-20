import cv2
import time
import winsound
import mediapipe as mp

from PySide6.QtCore import QObject, Signal, Slot, QThread
from PySide6.QtGui import QImage
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from face_landmarks import get_ear
from head_pose import HeadPoseDetector
from detection import DriverDetector


MODEL_PATH = "face_landmarker.task"


class DetectionWorker(QObject):

    frame_ready = Signal(QImage)
    detection_ready = Signal(dict)
    error = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = True
        self.paused = False
        self.alarm_muted = False

        self.cap = None
        self.landmarker = None

        self.head_pose = HeadPoseDetector()
        self.detector = DriverDetector()

    @Slot()
    def run(self):

        try:
            base_options = python.BaseOptions(
                model_asset_path=MODEL_PATH
            )

            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1
            )

            self.landmarker = vision.FaceLandmarker.create_from_options(
                options
            )

            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                self.error.emit("Could not open camera.")
                return

            while self.running:

                ret, frame = self.cap.read()

                if not ret:
                    continue

                # Mirror only the displayed/processed camera view
                frame = cv2.flip(frame, 1)

                if not self.paused:
                    self.process_frame(frame)

                self.send_frame(frame)

        except Exception as e:
            self.error.emit(str(e))

        finally:
            self.release()

    def process_frame(self, frame):

        height, width = frame.shape[:2]

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp = int(time.time() * 1000)

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp
        )

        if not result.face_landmarks:
            self.detection_ready.emit({
                "face_detected": False,
                "eye_status": "--",
                "ear": 0.0,
                "yaw": 0.0,
                "direction": "NO FACE",
                "status": "NO FACE",
                "alert": False
            })
            return

        landmarks = result.face_landmarks[0]

        ear = get_ear(landmarks)

        pose = self.head_pose.calculate_pose(
            landmarks,
            width,
            height
        )

        if pose is None:
            return

        direction = pose["direction"]

        if direction == "CALIBRATING":

            detection_result = {
                "face_detected": True,
                "ear": ear,
                "eye_status": "OPEN" if ear >= 0.20 else "CLOSED",
                "yaw": pose["relative_yaw"],
                "direction": "CALIBRATING",
                "status": "CALIBRATING",
                "calibration_progress": pose["calibration_progress"],
                "calibration_message": pose["calibration_message"],
                "alert": False
            }

            self.detection_ready.emit(
                detection_result
            )

            return

        detection = self.detector.update(
            ear,
            direction
        )

        detection_result = {
            "face_detected": True,
            "ear": ear,
            "eye_status": detection["eye_status"],
            "yaw": pose["relative_yaw"],
            "direction": direction,
            "status": detection["status"],
            "alert": detection["alert"]
        }

        self.detection_ready.emit(detection_result)

        if detection["alert"] and not self.alarm_muted:
            self.trigger_alarm()

    def trigger_alarm(self):

        try:
            winsound.Beep(1000, 500)
        except Exception:
            pass

    def send_frame(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channels = rgb.shape

        image = QImage(
            rgb.data,
            width,
            height,
            channels * width,
            QImage.Format_RGB888
        ).copy()

        self.frame_ready.emit(image)

    def set_paused(self, paused):

        self.paused = paused

    def set_alarm_muted(self, muted):

        self.alarm_muted = muted

    def stop(self):

        self.running = False

    def release(self):

        if self.cap is not None:
            self.cap.release()

        if self.landmarker is not None:
            self.landmarker.close()


class CameraWidget(QObject):

    frame_ready = Signal(QImage)
    detection_ready = Signal(dict)
    error = Signal(str)

    def __init__(self):
        super().__init__()

        self.thread = QThread()
        self.worker = DetectionWorker()

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.frame_ready.connect(
            self.frame_ready
        )

        self.worker.detection_ready.connect(
            self.detection_ready
        )

        self.worker.error.connect(
            self.error
        )

        self.thread.start()

    def pause(self, value):

        self.worker.set_paused(value)

    def mute_alarm(self, value):

        self.worker.set_alarm_muted(value)

    def stop(self):

        self.worker.stop()

        self.thread.quit()
        self.thread.wait()