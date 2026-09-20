import cv2
import mediapipe as mp
import winsound

from face_landmarks import get_ear, LEFT_EYE, RIGHT_EYE
from head_pose import HeadPoseDetector
from detection import DriverDetector


# MediaPipe Face Landmarker setup
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="face_landmarker.task"
    ),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

# Create detectors
head_detector = HeadPoseDetector()
driver_detector = DriverDetector()

# Open camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Create MediaPipe landmarker
with FaceLandmarker.create_from_options(options) as landmarker:

    timestamp_ms = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read frame.")
            break

        # Mirror camera
        frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Create MediaPipe image
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

            # Calculate EAR
            ear = get_ear(landmarks)

            # Calculate head pose
            pose = head_detector.calculate_pose(
                landmarks,
                w,
                h
            )

            if pose is not None:

                # Get head direction
                direction = pose["direction"]

                # Combine EAR and head pose
                detection = driver_detector.update(
                    ear,
                    direction
                )

                # Get detection results
                status = detection["status"]
                eye_status = detection["eye_status"]
                closed_duration = detection["closed_duration"]
                distraction_duration = detection["distraction_duration"]

                # Draw all face landmarks
                for landmark in landmarks:

                    x = int(landmark.x * w)
                    y = int(landmark.y * h)

                    cv2.circle(
                        frame,
                        (x, y),
                        1,
                        (255, 255, 0),
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
                        2,
                        (0, 0, 255),
                        -1
                    )

                # Display EAR
                cv2.putText(
                    frame,
                    f"EAR: {ear:.2f}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                # Display eye status
                cv2.putText(
                    frame,
                    f"Eyes: {eye_status}",
                    (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                # Display closed duration
                cv2.putText(
                    frame,
                    f"Closed: {closed_duration:.1f}s",
                    (20, 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                # Display raw yaw
                cv2.putText(
                    frame,
                    f"Raw Yaw: {pose['yaw']:.2f}",
                    (20, 125),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                # Display smooth yaw
                cv2.putText(
                    frame,
                    f"Smooth Yaw: {pose['smooth_yaw']:.2f}",
                    (20, 155),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                # Display relative yaw
                if pose["relative_yaw"] is not None:

                    cv2.putText(
                        frame,
                        f"Relative Yaw: {pose['relative_yaw']:.2f}",
                        (20, 185),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 255),
                        2
                    )

                # Display direction
                cv2.putText(
                    frame,
                    f"Direction: {direction}",
                    (20, 220),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

                # Display distraction duration
                if distraction_duration > 0:

                    cv2.putText(
                        frame,
                        f"Away: {distraction_duration:.1f}s",
                        (20, 300),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 165, 255),
                        2
                    )

                # Select status display color
                if status == "ATTENTIVE":
                    status_color = (0, 255, 0)
                else:
                    status_color = (0, 0, 255)

                # Display final status
                cv2.putText(
                    frame,
                    f"STATUS: {status}",
                    (20, 255),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    status_color,
                    2
                )

                # Trigger alarm
                if detection["alert"]:

                    winsound.Beep(
                        1000,
                        500
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

        # Display camera
        cv2.imshow(
            "Driver Distraction Detection",
            frame
        )

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

# Release camera
cap.release()

# Close OpenCV windows
cv2.destroyAllWindows()