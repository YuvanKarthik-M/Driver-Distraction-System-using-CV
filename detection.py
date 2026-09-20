import time

# Detection settings
EAR_THRESHOLD = 0.20
DROWSY_TIME = 1.0
DISTRACTION_TIME = 2.0


class DriverDetector:

    def __init__(self):
        self.eyes_closed = False
        self.closed_start_time = None

        self.distraction_start_time = None
        self.distraction_direction = None

        self.previous_status = "ATTENTIVE"

    def update(self, ear, direction):
        current_time = time.time()

        # Check eye state
        if ear < EAR_THRESHOLD:

            eye_status = "CLOSED"

            if not self.eyes_closed:
                self.eyes_closed = True
                self.closed_start_time = current_time

            closed_duration = (
                current_time - self.closed_start_time
            )

        else:

            eye_status = "OPEN"
            self.eyes_closed = False
            self.closed_start_time = None
            closed_duration = 0

        # Check head direction
        head_turned = direction in ["LEFT", "RIGHT"]

        if head_turned:

            if self.distraction_start_time is None:
                self.distraction_start_time = current_time
                self.distraction_direction = direction

            elif direction != self.distraction_direction:
                self.distraction_start_time = current_time
                self.distraction_direction = direction

            distraction_duration = (
                current_time - self.distraction_start_time
            )

        else:

            self.distraction_start_time = None
            self.distraction_direction = None
            distraction_duration = 0

        # Determine drowsiness
        drowsy = (
            self.eyes_closed and
            closed_duration >= DROWSY_TIME
        )

        # Determine distraction
        distracted = (
            head_turned and
            distraction_duration >= DISTRACTION_TIME
        )

        # Determine final status
        if drowsy and distracted:

            status = "DROWSY + DISTRACTED"

        elif drowsy:

            status = "DROWSY"

        elif distracted:

            if direction == "LEFT":
                status = "DISTRACTED - LEFT"
            else:
                status = "DISTRACTED - RIGHT"

        else:

            status = "ATTENTIVE"

        # Trigger alarm only when entering an alert state
        alert = (
            status != "ATTENTIVE" and
            self.previous_status == "ATTENTIVE"
        )

        self.previous_status = status

        return {
            "eye_status": eye_status,
            "closed_duration": closed_duration,
            "distraction_duration": distraction_duration,
            "status": status,
            "alert": alert
        }