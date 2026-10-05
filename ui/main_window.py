from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QProgressBar,
    QSizePolicy
)

from PySide6.QtCore import Qt, QByteArray, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter
from PySide6.QtSvg import QSvgRenderer

from .camera_widget import CameraWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DRIVER SENTINEL - AI Distraction & Drowsiness Monitoring")
        self.resize(1280, 780)

        self.detection_paused = False
        self.alarm_muted = False

        self.camera = CameraWidget()

        self.setup_icons()
        self.build_ui()

        self.camera.frame_ready.connect(self.update_camera)
        self.camera.detection_ready.connect(self.update_detection)
        self.camera.error.connect(self.show_error)

    def setup_icons(self):

        self.pause_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#F8FAFC" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="4" width="4" height="16" rx="1"/>
        <rect x="14" y="4" width="4" height="16" rx="1"/>
        </svg>
        """

        self.play_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#F8FAFC" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polygon points="6 3 20 12 6 21 6 3"/>
        </svg>
        """

        self.volume_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#F8FAFC" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <path d="M15.5 8.5a5 5 0 0 1 0 7"/>
        <path d="M19 5a9 9 0 0 1 0 14"/>
        </svg>
        """

        self.mute_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#F8FAFC" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <line x1="23" y1="9" x2="17" y2="15"/>
        <line x1="17" y1="9" x2="23" y2="15"/>
        </svg>
        """

        self.close_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#EF4444" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        """

        self.target_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#38BDF8" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
        </svg>
        """

    def create_lucide_icon(self, svg_data):

        renderer = QSvgRenderer(
            QByteArray(svg_data.encode())
        )

        pixmap = QPixmap(28, 28)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)

        # ==================================================
        # HEADER
        # ==================================================
        header_widget = QWidget()
        header_widget.setObjectName("appHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        title = QLabel("DRIVER SENTINEL")
        title.setObjectName("title")

        subtitle = QLabel("AI REAL-TIME VISION & ATTENTIVENESS MONITOR")
        subtitle.setObjectName("subtitle")

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        self.active_status = QLabel("● ACTIVE")
        self.active_status.setObjectName("activeStatus")
        self.active_status.setProperty("state", "ACTIVE")

        header_layout.addLayout(title_container)
        header_layout.addStretch()
        header_layout.addWidget(self.active_status)

        main_layout.addWidget(header_widget)

        # ==================================================
        # MAIN CONTENT LAYOUT (LEFT CAMERA + RIGHT DASHBOARD)
        # ==================================================
        content = QHBoxLayout()
        content.setSpacing(20)

        # --------------------------------------------------
        # LEFT SECTION (Camera & Control Panel)
        # --------------------------------------------------
        left_section = QVBoxLayout()
        left_section.setSpacing(14)

        camera_panel = QFrame()
        camera_panel.setObjectName("cameraPanel")
        camera_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        camera_layout = QVBoxLayout(camera_panel)
        camera_layout.setContentsMargins(10, 10, 10, 10)

        self.camera_display = QLabel()
        self.camera_display.setAlignment(Qt.AlignCenter)
        self.camera_display.setObjectName("cameraPlaceholder")
        self.camera_display.setText("Initializing AI Vision Feed...")
        self.camera_display.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        camera_layout.addWidget(self.camera_display)
        left_section.addWidget(camera_panel, 1)

        # Floating Control Bar
        control_bar = QFrame()
        control_bar.setObjectName("controlBar")
        controls_layout = QHBoxLayout(control_bar)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(12)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.create_lucide_icon(self.pause_svg))
        self.pause_button.setIconSize(QSize(22, 22))
        self.pause_button.setObjectName("iconButton")
        self.pause_button.setToolTip("Pause / Resume Vision Stream")
        self.pause_button.clicked.connect(self.toggle_pause)

        self.mute_button = QPushButton()
        self.mute_button.setIcon(self.create_lucide_icon(self.volume_svg))
        self.mute_button.setIconSize(QSize(22, 22))
        self.mute_button.setObjectName("iconButton")
        self.mute_button.setToolTip("Mute / Unmute Audio Alarm")
        self.mute_button.clicked.connect(self.toggle_mute)

        self.recalibrate_button = QPushButton(" 🎯  Recalibrate Yaw")
        self.recalibrate_button.setObjectName("recalibrateButton")
        self.recalibrate_button.setToolTip("Reset head orientation baseline")
        self.recalibrate_button.clicked.connect(self.recalibrate_head_pose)

        exit_button = QPushButton()
        exit_button.setIcon(self.create_lucide_icon(self.close_svg))
        exit_button.setIconSize(QSize(22, 22))
        exit_button.setObjectName("exitIconButton")
        exit_button.setToolTip("Exit Application")
        exit_button.clicked.connect(self.close)

        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.mute_button)
        controls_layout.addWidget(self.recalibrate_button)
        controls_layout.addStretch()
        controls_layout.addWidget(exit_button)

        left_section.addWidget(control_bar)

        # --------------------------------------------------
        # RIGHT SECTION (Dashboard & Telemetry)
        # --------------------------------------------------
        right_section = QVBoxLayout()
        right_section.setSpacing(14)

        dashboard = QFrame()
        dashboard.setObjectName("dashboard")
        dashboard.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        dashboard_layout = QVBoxLayout(dashboard)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(14)

        # Section Header
        self.system_label = QLabel("TELEMETRY & SYSTEM STATUS")
        self.system_label.setObjectName("sectionTitle")
        self.system_label.setAlignment(Qt.AlignCenter)
        dashboard_layout.addWidget(self.system_label)

        # System Status Hero Card
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setProperty("status", "STARTING")

        status_card_layout = QVBoxLayout(self.status_card)
        status_card_layout.setContentsMargins(16, 14, 16, 14)
        status_card_layout.setSpacing(4)

        self.system_status = QLabel("INITIALIZING")
        self.system_status.setObjectName("systemStatus")
        self.system_status.setAlignment(Qt.AlignCenter)

        self.status_subtitle = QLabel("Connecting camera stream...")
        self.status_subtitle.setObjectName("statusSubtitle")
        self.status_subtitle.setAlignment(Qt.AlignCenter)

        status_card_layout.addWidget(self.system_status)
        status_card_layout.addWidget(self.status_subtitle)

        dashboard_layout.addWidget(self.status_card)

        # --------------------------------------------------
        # METRIC ROW 1: EAR & EYES
        # --------------------------------------------------
        metrics_row1 = QHBoxLayout()
        metrics_row1.setSpacing(12)

        self.ear_card = self.create_gauge_card(
            "EYE ASPECT RATIO (EAR)",
            "--",
            "Threshold: 0.20"
        )
        self.ear_meter = self.ear_card.visual_meter

        self.eyes_card = self.create_metric_card(
            "EYE STATE",
            "--",
            "State"
        )

        metrics_row1.addWidget(self.ear_card, 1)
        metrics_row1.addWidget(self.eyes_card, 1)

        dashboard_layout.addLayout(metrics_row1)

        # --------------------------------------------------
        # METRIC ROW 2: YAW & DIRECTION
        # --------------------------------------------------
        metrics_row2 = QHBoxLayout()
        metrics_row2.setSpacing(12)

        self.yaw_card = self.create_gauge_card(
            "HEAD YAW ANGLE",
            "--",
            "Threshold: ±25.0°"
        )
        self.yaw_meter = self.yaw_card.visual_meter
        self.yaw_meter.setProperty("meterType", "YAW")

        self.direction_card = self.create_metric_card(
            "HEAD ORIENTATION",
            "--",
            "Facing"
        )

        metrics_row2.addWidget(self.yaw_card, 1)
        metrics_row2.addWidget(self.direction_card, 1)

        dashboard_layout.addLayout(metrics_row2)

        # Alarm indicator
        self.alarm_label = QLabel("🔊  Audio Alert Armed")
        self.alarm_label.setObjectName("alarm")
        self.alarm_label.setAlignment(Qt.AlignCenter)
        dashboard_layout.addWidget(self.alarm_label)

        # --------------------------------------------------
        # CALIBRATION OVERLAY WIDGET
        # --------------------------------------------------
        self.calibration_widget = QFrame()
        self.calibration_widget.setObjectName("calibrationWidget")
        calibration_layout = QVBoxLayout(self.calibration_widget)
        calibration_layout.setContentsMargins(20, 20, 20, 20)
        calibration_layout.setSpacing(10)

        self.calibration_title = QLabel("HEAD POSE CALIBRATION")
        self.calibration_title.setObjectName("calibrationTitle")
        self.calibration_title.setAlignment(Qt.AlignCenter)

        self.calibration_icon = QLabel("🎯")
        self.calibration_icon.setObjectName("calibrationIcon")
        self.calibration_icon.setAlignment(Qt.AlignCenter)

        self.calibration_instruction = QLabel("LOOK FORWARD")
        self.calibration_instruction.setObjectName("calibrationInstruction")
        self.calibration_instruction.setAlignment(Qt.AlignCenter)

        self.calibration_description = QLabel(
            "Position your head centered and look straight\n"
            "at the camera to establish baseline yaw orientation."
        )
        self.calibration_description.setObjectName("calibrationDescription")
        self.calibration_description.setAlignment(Qt.AlignCenter)

        self.calibration_progress = QProgressBar()
        self.calibration_progress.setObjectName("calibrationProgress")
        self.calibration_progress.setRange(0, 100)
        self.calibration_progress.setValue(0)
        self.calibration_progress.setTextVisible(False)

        self.calibration_state = QLabel("CALIBRATING...")
        self.calibration_state.setObjectName("calibrationState")
        self.calibration_state.setAlignment(Qt.AlignCenter)

        calibration_layout.addWidget(self.calibration_title)
        calibration_layout.addSpacing(6)
        calibration_layout.addWidget(self.calibration_icon)
        calibration_layout.addWidget(self.calibration_instruction)
        calibration_layout.addWidget(self.calibration_description)
        calibration_layout.addSpacing(10)
        calibration_layout.addWidget(self.calibration_progress)
        calibration_layout.addWidget(self.calibration_state)

        dashboard_layout.addWidget(self.calibration_widget)
        self.calibration_widget.hide()

        right_section.addWidget(dashboard)

        # --------------------------------------------------
        # DURATION CARDS (SESSION METRICS)
        # --------------------------------------------------
        duration_layout = QHBoxLayout()
        duration_layout.setSpacing(12)

        self.closed_duration_card = self.create_duration_card(
            "CUMULATIVE EYES CLOSED",
            "0.00 s"
        )

        self.distraction_duration_card = self.create_duration_card(
            "CUMULATIVE DISTRACTED",
            "0.00 s"
        )

        duration_layout.addWidget(self.closed_duration_card, 1)
        duration_layout.addWidget(self.distraction_duration_card, 1)

        right_section.addLayout(duration_layout)

        # Empty layout filler
        empty_area = QFrame()
        empty_area.setObjectName("emptyArea")
        empty_area.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        right_section.addWidget(empty_area, 1)

        # --------------------------------------------------
        # ASSEMBLE CONTENT
        # --------------------------------------------------
        content.addLayout(left_section, 6)
        content.addLayout(right_section, 5)

        main_layout.addLayout(content, 1)

    # ======================================================
    # HELPER COMPONENT BUILDERS
    # ======================================================

    def create_metric_card(self, name, value, subtext):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        label = QLabel(name)
        label.setObjectName("metricName")

        val_label = QLabel(value)
        val_label.setObjectName("metricValue")

        sub_label = QLabel(subtext)
        sub_label.setObjectName("metricState")

        layout.addWidget(label)
        layout.addWidget(val_label)
        layout.addWidget(sub_label)

        card.value_label = val_label
        card.sub_label = sub_label

        return card

    def create_gauge_card(self, name, value, subtext):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        label = QLabel(name)
        label.setObjectName("metricName")

        val_label = QLabel(value)
        val_label.setObjectName("metricValue")

        meter = QProgressBar()
        meter.setObjectName("visualMeter")
        meter.setRange(0, 100)
        meter.setValue(0)
        meter.setTextVisible(False)

        sub_label = QLabel(subtext)
        sub_label.setObjectName("metricState")

        layout.addWidget(label)
        layout.addWidget(val_label)
        layout.addWidget(meter)
        layout.addWidget(sub_label)

        card.value_label = val_label
        card.visual_meter = meter
        card.sub_label = sub_label

        return card

    def create_duration_card(self, name, value):
        card = QFrame()
        card.setObjectName("durationCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        label = QLabel(name)
        label.setObjectName("durationName")

        val_label = QLabel(value)
        val_label.setObjectName("durationValue")
        val_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        layout.addWidget(val_label)

        card.value_label = val_label

        return card

    # ======================================================
    # CAMERA & DETECTION SLOTS
    # ======================================================

    def update_camera(self, image):
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.camera_display.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.camera_display.setPixmap(scaled)

    def update_detection(self, data):

        direction = data.get("direction", "--")

        # Calibration Mode
        if direction == "CALIBRATING":
            self.show_calibration(data)
            return

        self.hide_calibration()

        # No Face Detected
        if not data.get("face_detected", False):
            self.system_status.setText("NO FACE")
            self.status_subtitle.setText("Camera searching for driver face...")
            self.update_status_style("NO FACE")

            self.ear_card.value_label.setText("--")
            self.ear_meter.setValue(0)
            self.eyes_card.value_label.setText("--")
            self.eyes_card.sub_label.setText("No face")

            self.yaw_card.value_label.setText("--")
            self.yaw_meter.setValue(50)
            self.direction_card.value_label.setText("NO FACE")
            self.direction_card.sub_label.setText("Out of frame")
            return

        status = data.get("status", "ATTENTIVE")
        ear = data.get("ear", 0.0)
        eye_status = data.get("eye_status", "--")
        yaw = data.get("yaw")
        eye_closed_total = data.get("eye_closed_total", 0.0)
        distraction_total = data.get("distraction_total", 0.0)

        # Update Status Hero Card
        self.system_status.setText(status)
        self.update_status_subtitle(status)
        self.update_status_style(status)

        # Update EAR Gauge
        self.ear_card.value_label.setText(f"{ear:.2f}")
        ear_percent = min(100, max(0, int((ear / 0.40) * 100)))
        self.ear_meter.setValue(ear_percent)

        if ear < 0.20:
            self.ear_meter.setProperty("meterType", "EAR_WARNING")
            self.ear_card.sub_label.setText("⚠️ BELOW THRESHOLD")
            self.ear_card.sub_label.setStyleSheet("color: #EF4444;")
        else:
            self.ear_meter.setProperty("meterType", "NORMAL")
            self.ear_card.sub_label.setText("Threshold: 0.20 (Normal)")
            self.ear_card.sub_label.setStyleSheet("color: #38BDF8;")

        self.ear_meter.style().unpolish(self.ear_meter)
        self.ear_meter.style().polish(self.ear_meter)

        # Update Eyes Card
        self.eyes_card.value_label.setText(eye_status)
        if eye_status == "OPEN":
            self.eyes_card.sub_label.setText("Driver eyes open")
            self.eyes_card.sub_label.setStyleSheet("color: #00F59B;")
        else:
            self.eyes_card.sub_label.setText("⚠️ Eyes closed")
            self.eyes_card.sub_label.setStyleSheet("color: #EF4444;")

        # Update Yaw Gauge (-45 to +45 mapped to 0-100%)
        if yaw is None:
            self.yaw_card.value_label.setText("--")
            self.yaw_meter.setValue(50)
            self.yaw_card.sub_label.setText("Baseline pending")
        else:
            self.yaw_card.value_label.setText(f"{yaw:.1f}°")
            yaw_percent = min(100, max(0, int(((yaw + 45.0) / 90.0) * 100)))
            self.yaw_meter.setValue(yaw_percent)

            if abs(yaw) >= 25.0:
                self.yaw_card.sub_label.setText("⚠️ TURNED AWAY")
                self.yaw_card.sub_label.setStyleSheet("color: #EF4444;")
            else:
                self.yaw_card.sub_label.setText("Centered (±25° normal)")
                self.yaw_card.sub_label.setStyleSheet("color: #38BDF8;")

        # Update Direction Card
        self.direction_card.value_label.setText(direction)
        if direction == "FORWARD":
            self.direction_card.sub_label.setText("Looking at road")
            self.direction_card.sub_label.setStyleSheet("color: #00F59B;")
        else:
            self.direction_card.sub_label.setText(f"Turned towards {direction.lower()}")
            self.direction_card.sub_label.setStyleSheet("color: #EF4444;")

        # Update Duration Cards
        self.closed_duration_card.value_label.setText(f"{eye_closed_total:.2f} s")
        self.distraction_duration_card.value_label.setText(f"{distraction_total:.2f} s")

    def update_status_subtitle(self, status):
        if status == "ATTENTIVE":
            self.status_subtitle.setText("Driver is focused on road. All systems nominal.")
        elif status == "DROWSY":
            self.status_subtitle.setText("⚠️ DROWSINESS ALERT: Driver eyes closed for > 1.0s!")
        elif "DISTRACTED" in status:
            self.status_subtitle.setText("⚠️ DISTRACTION ALERT: Driver turned away from road!")
        else:
            self.status_subtitle.setText("System monitoring active.")

    def show_calibration(self, data):
        self.system_label.hide()
        self.status_card.hide()

        self.ear_card.hide()
        self.eyes_card.hide()
        self.yaw_card.hide()
        self.direction_card.hide()
        self.alarm_label.hide()

        self.closed_duration_card.hide()
        self.distraction_duration_card.hide()

        self.calibration_widget.show()

        progress = data.get("calibration_progress", 0)
        message = data.get("calibration_message", "LOOK FORWARD")

        self.calibration_instruction.setText(message)
        self.calibration_progress.setValue(progress)
        self.calibration_state.setText(f"CALIBRATING BASELINE  •  {progress}%")

        self.active_status.setText("● CALIBRATING")
        self.active_status.setProperty("state", "CALIBRATING")
        self.active_status.style().unpolish(self.active_status)
        self.active_status.style().polish(self.active_status)

    def hide_calibration(self):
        if not self.calibration_widget.isVisible():
            return

        self.calibration_widget.hide()

        self.system_label.show()
        self.status_card.show()

        self.ear_card.show()
        self.eyes_card.show()
        self.yaw_card.show()
        self.direction_card.show()
        self.alarm_label.show()

        self.closed_duration_card.show()
        self.distraction_duration_card.show()

        if self.detection_paused:
            self.active_status.setText("● PAUSED")
            self.active_status.setProperty("state", "PAUSED")
        else:
            self.active_status.setText("● ACTIVE")
            self.active_status.setProperty("state", "ACTIVE")

        self.active_status.style().unpolish(self.active_status)
        self.active_status.style().polish(self.active_status)

    def update_status_style(self, status):
        self.status_card.setProperty("status", status)
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)

        self.system_status.setProperty("status", status)
        self.system_status.style().unpolish(self.system_status)
        self.system_status.style().polish(self.system_status)

        if "DROWSY" in status or "DISTRACTED" in status:
            self.active_status.setText("⚠️ ALERT")
            self.active_status.setProperty("state", "ALERT")
        elif status == "ATTENTIVE" and not self.detection_paused:
            self.active_status.setText("● ACTIVE")
            self.active_status.setProperty("state", "ACTIVE")

        self.active_status.style().unpolish(self.active_status)
        self.active_status.style().polish(self.active_status)

    def toggle_pause(self):
        self.detection_paused = not self.detection_paused
        self.camera.pause(self.detection_paused)

        if self.detection_paused:
            self.pause_button.setIcon(self.create_lucide_icon(self.play_svg))
            self.pause_button.setToolTip("Resume Detection Stream")
            self.active_status.setText("● PAUSED")
            self.active_status.setProperty("state", "PAUSED")
        else:
            self.pause_button.setIcon(self.create_lucide_icon(self.pause_svg))
            self.pause_button.setToolTip("Pause Detection Stream")
            self.active_status.setText("● ACTIVE")
            self.active_status.setProperty("state", "ACTIVE")

        self.active_status.style().unpolish(self.active_status)
        self.active_status.style().polish(self.active_status)

    def toggle_mute(self):
        self.alarm_muted = not self.alarm_muted
        self.camera.mute_alarm(self.alarm_muted)

        if self.alarm_muted:
            self.mute_button.setIcon(self.create_lucide_icon(self.mute_svg))
            self.mute_button.setToolTip("Unmute Audio Alarm")
            self.alarm_label.setText("🔇  Audio Alert MUTED")
            self.alarm_label.setProperty("muted", "true")
        else:
            self.mute_button.setIcon(self.create_lucide_icon(self.volume_svg))
            self.mute_button.setToolTip("Mute Audio Alarm")
            self.alarm_label.setText("🔊  Audio Alert Armed")
            self.alarm_label.setProperty("muted", "false")

        self.alarm_label.style().unpolish(self.alarm_label)
        self.alarm_label.style().polish(self.alarm_label)

    def recalibrate_head_pose(self):
        self.camera.recalibrate()

    def show_error(self, message):
        self.camera_display.setText(f"Camera Stream Error:\n{message}")

    def closeEvent(self, event):
        self.camera.stop()
        event.accept()