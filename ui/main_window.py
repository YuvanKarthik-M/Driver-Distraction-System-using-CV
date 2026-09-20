from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QProgressBar
)

from PySide6.QtCore import Qt, QByteArray, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter
from PySide6.QtSvg import QSvgRenderer

from .camera_widget import CameraWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Driver Distraction Detection")
        self.resize(1400, 800)

        self.detection_paused = False
        self.alarm_muted = False

        self.camera = CameraWidget()

        self.setup_icons()
        self.build_ui()

        self.camera.frame_ready.connect(self.update_camera)
        self.camera.detection_ready.connect(self.update_detection)
        self.camera.error.connect(self.show_error)

    def setup_icons(self):

        # Pause icon
        self.pause_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#e5e7eb" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="4" width="4" height="16" rx="1"/>
        <rect x="14" y="4" width="4" height="16" rx="1"/>
        </svg>
        """

        # Play icon
        self.play_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#e5e7eb" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polygon points="6 3 20 12 6 21 6 3"/>
        </svg>
        """

        # Volume icon
        self.volume_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#e5e7eb" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <path d="M15.5 8.5a5 5 0 0 1 0 7"/>
        <path d="M19 5a9 9 0 0 1 0 14"/>
        </svg>
        """

        # Mute icon
        self.mute_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#e5e7eb" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <line x1="23" y1="9" x2="17" y2="15"/>
        <line x1="17" y1="9" x2="23" y2="15"/>
        </svg>
        """

        # Close icon
        self.close_svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
        width="24" height="24" viewBox="0 0 24 24"
        fill="none" stroke="#e5e7eb" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
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
        main_layout.setSpacing(30)

        # Header
        header = QHBoxLayout()

        title = QLabel("DRIVER DISTRACTION DETECTION")
        title.setObjectName("title")

        self.active_status = QLabel("● ACTIVE")
        self.active_status.setObjectName("activeStatus")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.active_status)

        main_layout.addLayout(header)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(20)

        # Left section
        left_section = QVBoxLayout()
        left_section.setSpacing(12)

        # Camera panel
        camera_panel = QFrame()
        camera_panel.setObjectName("cameraPanel")
        camera_panel.setFixedHeight(440)

        camera_layout = QVBoxLayout(camera_panel)
        camera_layout.setContentsMargins(10, 10, 10, 10)

        self.camera_display = QLabel()
        self.camera_display.setAlignment(Qt.AlignCenter)
        self.camera_display.setObjectName("cameraPlaceholder")
        self.camera_display.setText("Starting camera...")

        camera_layout.addWidget(self.camera_display)

        left_section.addWidget(camera_panel)

        # Camera controls
        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(
            self.create_lucide_icon(self.pause_svg)
        )
        self.pause_button.setIconSize(QSize(22, 22))
        self.pause_button.setObjectName("iconButton")
        self.pause_button.setToolTip("Pause detection")
        self.pause_button.clicked.connect(self.toggle_pause)

        self.mute_button = QPushButton()
        self.mute_button.setIcon(
            self.create_lucide_icon(self.volume_svg)
        )
        self.mute_button.setIconSize(QSize(22, 22))
        self.mute_button.setObjectName("iconButton")
        self.mute_button.setToolTip("Mute alarm")
        self.mute_button.clicked.connect(self.toggle_mute)

        exit_button = QPushButton()
        exit_button.setIcon(
            self.create_lucide_icon(self.close_svg)
        )
        exit_button.setIconSize(QSize(22, 22))
        exit_button.setObjectName("exitIconButton")
        exit_button.setToolTip("Exit application")
        exit_button.clicked.connect(self.close)

        controls.addWidget(self.pause_button)
        controls.addWidget(self.mute_button)
        controls.addWidget(exit_button)

        left_section.addLayout(controls)

        left_section.addStretch()

        # Right section
        right_section = QVBoxLayout()
        right_section.setSpacing(14)

        # Dashboard
        dashboard = QFrame()
        dashboard.setObjectName("dashboard")

        dashboard_layout = QVBoxLayout(dashboard)
        dashboard_layout.setContentsMargins(20, 24, 20, 20)
        dashboard_layout.setSpacing(14)

        # System title
        self.system_label = QLabel("SYSTEM STATUS")
        self.system_label.setObjectName("sectionTitle")
        self.system_label.setAlignment(Qt.AlignCenter)

        dashboard_layout.addWidget(self.system_label)

        # Normal status
        self.system_status = QLabel("STARTING")
        self.system_status.setObjectName("systemStatus")
        self.system_status.setAlignment(Qt.AlignCenter)

        dashboard_layout.addWidget(self.system_status)

        # Metric cards
        metrics = QHBoxLayout()

        self.ear_card = self.create_metric(
            "EAR",
            "--"
        )

        self.eyes_card = self.create_metric(
            "EYES",
            "--"
        )

        metrics.addWidget(self.ear_card)
        metrics.addWidget(self.eyes_card)

        dashboard_layout.addLayout(metrics)

        metrics2 = QHBoxLayout()

        self.yaw_card = self.create_metric(
            "YAW",
            "--"
        )

        self.direction_card = self.create_metric(
            "DIRECTION",
            "--"
        )

        metrics2.addWidget(self.yaw_card)
        metrics2.addWidget(self.direction_card)

        dashboard_layout.addLayout(metrics2)

        # Alarm
        self.alarm_label = QLabel("🔊  Alarm ON")
        self.alarm_label.setObjectName("alarm")
        self.alarm_label.setAlignment(Qt.AlignCenter)

        dashboard_layout.addWidget(self.alarm_label)

        # Calibration screen
        self.calibration_widget = QFrame()
        self.calibration_widget.setObjectName(
            "calibrationWidget"
        )

        calibration_layout = QVBoxLayout(
            self.calibration_widget
        )

        calibration_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        calibration_layout.setSpacing(10)

        self.calibration_title = QLabel(
            "DRIVER CALIBRATION"
        )

        self.calibration_title.setObjectName(
            "calibrationTitle"
        )

        self.calibration_title.setAlignment(
            Qt.AlignCenter
        )

        self.calibration_icon = QLabel("◉")

        self.calibration_icon.setObjectName(
            "calibrationIcon"
        )

        self.calibration_icon.setAlignment(
            Qt.AlignCenter
        )

        self.calibration_instruction = QLabel(
            "LOOK FORWARD"
        )

        self.calibration_instruction.setObjectName(
            "calibrationInstruction"
        )

        self.calibration_instruction.setAlignment(
            Qt.AlignCenter
        )

        self.calibration_description = QLabel(
            "Keep your head centered\n"
            "and look towards the road"
        )

        self.calibration_description.setObjectName(
            "calibrationDescription"
        )

        self.calibration_description.setAlignment(
            Qt.AlignCenter
        )

        self.calibration_progress = QProgressBar()

        self.calibration_progress.setRange(
            0,
            100
        )

        self.calibration_progress.setValue(0)

        self.calibration_progress.setTextVisible(
            False
        )

        self.calibration_state = QLabel(
            "CALIBRATING..."
        )

        self.calibration_state.setObjectName(
            "calibrationState"
        )

        self.calibration_state.setAlignment(
            Qt.AlignCenter
        )

        calibration_layout.addWidget(
            self.calibration_title
        )

        calibration_layout.addSpacing(10)

        calibration_layout.addWidget(
            self.calibration_icon
        )

        calibration_layout.addWidget(
            self.calibration_instruction
        )

        calibration_layout.addWidget(
            self.calibration_description
        )

        calibration_layout.addSpacing(15)

        calibration_layout.addWidget(
            self.calibration_progress
        )

        calibration_layout.addWidget(
            self.calibration_state
        )

        dashboard_layout.addWidget(
            self.calibration_widget
        )

        self.calibration_widget.hide()

        right_section.addWidget(
            dashboard
        )

        # Empty area
        empty_area = QFrame()
        empty_area.setObjectName("emptyArea")

        right_section.addWidget(
            empty_area,
            1
        )

        content.addLayout(
            left_section,
            1
        )

        content.addLayout(
            right_section,
            1
        )

        main_layout.addLayout(
            content,
            1
        )

    def create_metric(
        self,
        name,
        value
    ):

        card = QFrame()
        card.setObjectName("metricCard")

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            14,
            10,
            14,
            10
        )

        layout.setSpacing(4)

        label = QLabel(name)
        label.setObjectName("metricName")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        layout.addWidget(label)
        layout.addWidget(value_label)

        card.value_label = value_label

        return card

    def update_camera(
        self,
        image
    ):

        pixmap = QPixmap.fromImage(
            image
        )

        scaled = pixmap.scaled(
            self.camera_display.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.camera_display.setPixmap(
            scaled
        )

    def update_detection(
        self,
        data
    ):

        # Calibration mode
        if data.get(
            "direction"
        ) == "CALIBRATING":

            self.show_calibration(
                data
            )

            return

        # Return to normal dashboard
        self.hide_calibration()

        # No face
        if not data.get(
            "face_detected",
            False
        ):

            self.system_status.setText(
                "NO FACE"
            )

            self.ear_card.value_label.setText(
                "--"
            )

            self.eyes_card.value_label.setText(
                "--"
            )

            self.yaw_card.value_label.setText(
                "--"
            )

            self.direction_card.value_label.setText(
                "NO FACE"
            )

            self.update_status_style(
                "NO FACE"
            )

            return

        # Detection values
        status = data.get(
            "status",
            "ATTENTIVE"
        )

        ear = data.get(
            "ear",
            0.0
        )

        eye_status = data.get(
            "eye_status",
            "--"
        )

        yaw = data.get(
            "yaw"
        )

        direction = data.get(
            "direction",
            "--"
        )

        # Status
        self.system_status.setText(
            status
        )

        # EAR
        self.ear_card.value_label.setText(
            f"{ear:.2f}"
        )

        # Eyes
        self.eyes_card.value_label.setText(
            eye_status
        )

        # Yaw
        if yaw is None:

            self.yaw_card.value_label.setText(
                "--"
            )

        else:

            self.yaw_card.value_label.setText(
                f"{yaw:.1f}°"
            )

        # Direction
        self.direction_card.value_label.setText(
            direction
        )

        self.update_status_style(
            status
        )

    def show_calibration(
        self,
        data
    ):

        # Hide normal dashboard
        self.system_label.hide()
        self.system_status.hide()

        self.ear_card.hide()
        self.eyes_card.hide()
        self.yaw_card.hide()
        self.direction_card.hide()

        self.alarm_label.hide()

        # Show calibration
        self.calibration_widget.show()

        progress = data.get(
            "calibration_progress",
            0
        )

        message = data.get(
            "calibration_message",
            "LOOK FORWARD"
        )

        self.calibration_instruction.setText(
            message
        )

        self.calibration_progress.setValue(
            progress
        )

        self.calibration_state.setText(
            f"CALIBRATING  •  {progress}%"
        )

        self.active_status.setText(
            "● CALIBRATING"
        )

        self.active_status.setStyleSheet(
            "color: #ffc107;"
        )

    def hide_calibration(
        self
    ):

        if not self.calibration_widget.isVisible():

            return

        # Hide calibration
        self.calibration_widget.hide()

        # Restore normal dashboard
        self.system_label.show()
        self.system_status.show()

        self.ear_card.show()
        self.eyes_card.show()
        self.yaw_card.show()
        self.direction_card.show()

        self.alarm_label.show()

        self.active_status.setText(
            "● ACTIVE"
        )

        self.active_status.setStyleSheet(
            "color: #00e676;"
        )

    def update_status_style(
        self,
        status
    ):

        if status == "ATTENTIVE":

            self.system_status.setStyleSheet(
                "color: #00e676;"
            )

        elif status == "CALIBRATING":

            self.system_status.setStyleSheet(
                "color: #ffc107;"
            )

        elif status == "NO FACE":

            self.system_status.setStyleSheet(
                "color: #9e9e9e;"
            )

        else:

            self.system_status.setStyleSheet(
                "color: #ff3b30;"
            )

    def toggle_pause(
        self
    ):

        self.detection_paused = (
            not self.detection_paused
        )

        self.camera.pause(
            self.detection_paused
        )

        if self.detection_paused:

            self.pause_button.setIcon(
                self.create_lucide_icon(
                    self.play_svg
                )
            )

            self.pause_button.setToolTip(
                "Resume detection"
            )

            self.active_status.setText(
                "● PAUSED"
            )

            self.active_status.setStyleSheet(
                "color: #ffc107;"
            )

        else:

            self.pause_button.setIcon(
                self.create_lucide_icon(
                    self.pause_svg
                )
            )

            self.pause_button.setToolTip(
                "Pause detection"
            )

            self.active_status.setText(
                "● ACTIVE"
            )

            self.active_status.setStyleSheet(
                "color: #00e676;"
            )

    def toggle_mute(
        self
    ):

        self.alarm_muted = (
            not self.alarm_muted
        )

        self.camera.mute_alarm(
            self.alarm_muted
        )

        if self.alarm_muted:

            self.mute_button.setIcon(
                self.create_lucide_icon(
                    self.mute_svg
                )
            )

            self.mute_button.setToolTip(
                "Unmute alarm"
            )

            self.alarm_label.setText(
                "🔇  Alarm MUTED"
            )

        else:

            self.mute_button.setIcon(
                self.create_lucide_icon(
                    self.volume_svg
                )
            )

            self.mute_button.setToolTip(
                "Mute alarm"
            )

            self.alarm_label.setText(
                "🔊  Alarm ON"
            )

    def show_error(
        self,
        message
    ):

        self.camera_display.setText(
            f"Camera error:\n{message}"
        )

    def closeEvent(
        self,
        event
    ):

        self.camera.stop()

        event.accept()