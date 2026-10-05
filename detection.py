import time

# Detection settings
EAR_THRESHOLD = 0.20
DROWSY_TIME = 1.0
DISTRACTION_TIME = 2.0
REPEAT_ALARM_INTERVAL = 1.0


class DriverDetector:

    def __init__(self):
        # Eye detection
        self.eyes_closed = False
        self.closed_start_time = None

        # Distraction detection
        self.distraction_start_time = None
        self.distraction_direction = None

        # Cumulative alert durations
        self.total_eye_closed_time = 0.0
        self.total_distraction_time = 0.0

        # Time when an actual alert-duration timer begins
        self.eye_alert_start_time = None
        self.distraction_alert_start_time = None

        self.previous_status = "ATTENTIVE"
        self.last_alarm_time = None

    def reset(self):
        self.eyes_closed = False
        self.closed_start_time = None
        self.distraction_start_time = None
        self.distraction_direction = None
        self.eye_alert_start_time = None
        self.distraction_alert_start_time = None
        self.previous_status = "ATTENTIVE"
        self.last_alarm_time = None

    def update(self, ear, direction):
        current_time = time.monotonic()

        # --------------------------------------------------
        # Check eye state
        # --------------------------------------------------

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
            closed_duration = 0.0

            # Stop active eye alert timer
            if self.eye_alert_start_time is not None:

                self.total_eye_closed_time += (
                    current_time - self.eye_alert_start_time
                )

                self.eye_alert_start_time = None

        # --------------------------------------------------
        # Check head direction
        # --------------------------------------------------

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
            distraction_duration = 0.0

            # Stop active distraction timer
            if self.distraction_alert_start_time is not None:

                self.total_distraction_time += (
                    current_time -
                    self.distraction_alert_start_time
                )

                self.distraction_alert_start_time = None

        # --------------------------------------------------
        # Determine drowsiness
        # --------------------------------------------------

        drowsy = (
            self.eyes_closed and
            closed_duration >= DROWSY_TIME
        )

        # Start eye alert timer ONLY after threshold
        if (
            drowsy and
            self.eye_alert_start_time is None
        ):

            self.eye_alert_start_time = current_time

        # --------------------------------------------------
        # Determine distraction
        # --------------------------------------------------

        distracted = (
            head_turned and
            distraction_duration >= DISTRACTION_TIME
        )

        # Start distraction timer ONLY after threshold
        if (
            distracted and
            self.distraction_alert_start_time is None
        ):

            self.distraction_alert_start_time = current_time

        # --------------------------------------------------
        # Determine final status
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Trigger alarm sound logic:
        # Initial alarm after waiting time, then repeats every
        # 2 seconds if user remains distracted/drowsy until
        # returning to ATTENTIVE state.
        # --------------------------------------------------

        if status != "ATTENTIVE":
            if self.last_alarm_time is None:
                alert = True
                self.last_alarm_time = current_time
            elif current_time - self.last_alarm_time >= REPEAT_ALARM_INTERVAL:
                alert = True
                self.last_alarm_time = current_time
            else:
                alert = False
        else:
            self.last_alarm_time = None
            alert = False

        self.previous_status = status

        # --------------------------------------------------
        # Current cumulative display values
        # --------------------------------------------------

        eye_closed_total = self.total_eye_closed_time

        if self.eye_alert_start_time is not None:
            eye_closed_total += (
                current_time -
                self.eye_alert_start_time
            )

        distraction_total = self.total_distraction_time

        if self.distraction_alert_start_time is not None:
            distraction_total += (
                current_time -
                self.distraction_alert_start_time
            )

        return {
            "eye_status": eye_status,
            "closed_duration": closed_duration,
            "distraction_duration": distraction_duration,
            "eye_closed_total": eye_closed_total,
            "distraction_total": distraction_total,
            "status": status,
            "alert": alert
        }