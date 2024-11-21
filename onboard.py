import os
import sys

import requests
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QStackedLayout, QPushButton, QLabel, QHBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QRect, QObject, Signal
from PySide6 import QtGui, QtCore

from sd_qt.sd_desktop.ThemeManager import ThemeManager
from sd_qt.sd_desktop.toggleSwitch import SwitchControl
from sd_qt.sd_desktop.util import retrieve_settings, credentials

base_path = os.path.abspath(os.path.join(__file__, "../../.."))
resources_path = os.path.join(base_path, "sd_qt", "sd_desktop", "resources")

darkTheme = os.path.join(resources_path, "DarkTheme")
lightTheme = os.path.join(resources_path, "LightTheme")


class TransparentLabel(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoFillBackground(False)
        # Set the stylesheet here to make the background transparent and customize the text color
        self.setStyleSheet("""
            background-color: transparent;
        """)


class Onboarding(QWidget):
    moveNext = Signal()
    movePrev = Signal()
    move_to_dashBoard = Signal()


    def __init__(self, on_onboarding_completed):
        super().__init__()

        self.theme_manager = ThemeManager()
        self.theme_manager.theme_Changed.connect(self.change_theme)
        self.onboard_widget = QStackedWidget()
        self.on_onboarding_completed = on_onboarding_completed

        self.privacy_widget = PrivacyInfo(self.moveNext)
        self.datasecurity_widget = DataSecurity(self.moveNext,self.movePrev)



        self.onboard_widget.addWidget(self.privacy_widget)
        self.onboard_widget.addWidget(self.datasecurity_widget)


        if sys.platform == "darwin":
            self.OnboardSettings = OnboardSettings(self.moveNext)
            self.onboard_widget.addWidget(self.OnboardSettings)

            self.AccessibilitySettings = AccessibilitySettings(self.movePrev,self.move_to_dashBoard)
            self.onboard_widget.addWidget(self.AccessibilitySettings)
            self.move_to_dashBoard.connect(self.on_onboarding_completed)
        else:
            self.OnboardSettings = OnboardSettings(self.move_to_dashBoard)
            self.onboard_widget.addWidget(self.OnboardSettings)
            self.move_to_dashBoard.connect(self.on_onboarding_completed)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.onboard_widget)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.moveNext.connect(self.move_next)
        self.movePrev.connect(self.move_prev)

        self.onboard_widget.currentChanged.connect(self.change_theme)
        self.change_theme()

    def move_next(self):
        current_index = self.onboard_widget.currentIndex()
        next_index = (current_index + 1) % self.onboard_widget.count()

        # Hide current and show next
        self.onboard_widget.widget(current_index).hide()
        self.onboard_widget.widget(next_index).show()

        self.onboard_widget.setCurrentIndex(next_index)

    def move_prev(self):
        current_index = self.onboard_widget.currentIndex()
        previous_index = (current_index - 1) if current_index > 0 else self.onboard_widget.count() - 1

        # Hide current and show previous
        self.onboard_widget.widget(current_index).hide()
        self.onboard_widget.widget(previous_index).show()

        self.onboard_widget.setCurrentIndex(previous_index)

    def change_theme(self):
        # Select background image based on current theme
        if self.theme_manager.get_theme() == "dark":
            gradient_style = """
                                        background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2);
                                        border-radius: 5px;
                                        color: #FFFFFF;
                                        border: 1px solid #1D0B77;
                                    """
            solid_button_style = """
                                        background: #393939;
                                        border-radius: 5px;
                                    """
            container_style = """
                                        background-color: rgba(10, 10, 10, 0.8);  /* 80% opacity */
                                        border-radius: 5px;
                                    """
            self.background_image = os.path.join(darkTheme, "background.svg")
            privacy_image = QPixmap(os.path.join(darkTheme, "privacy.png"))
            sundial_logo = QPixmap(os.path.join(darkTheme, "dark_signin_logo.svg"))
            data_security_img = QPixmap(os.path.join(darkTheme, "Dataprivacy.svg"))
            accessibility_img = QPixmap(os.path.join(darkTheme, "accessibilty_Image.png"))
        else:
            container_style = """
                                                background-color: rgba(252, 252, 252, 0.8);  /* 80% opacity */
                                                border-radius: 5px;
                                            """
            gradient_style = """
                                                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2);
                                                border-radius: 5px;
                                                color: #FFFFFF;
                                                border: 1px solid #1D0B77;
                                            """
            solid_button_style = """
                                                background: #A1A3A5;
                                                border-radius: 5px;
                                                color: #FFFFFF;
                                            """
            self.background_image = os.path.join(lightTheme, "background.svg")
            privacy_image = QPixmap(os.path.join(lightTheme, "privacy.png"))
            sundial_logo = QPixmap(os.path.join(lightTheme, "signin_logo.svg"))
            data_security_img = QPixmap(os.path.join(lightTheme, "Dataprivacy_light.svg"))
            accessibility_img = QPixmap(os.path.join(lightTheme, "accessibility_Images.png"))

            # Apply background image stylesheet to QStackedWidget
        if os.path.exists(self.background_image):
            self.onboard_widget.setStyleSheet(f"""
                    QStackedWidget {{
                        background-image: url({self.background_image});
                        background-repeat: no-repeat;
                        background-position: center;
                        margin: 0px;
                        padding: 0px;
                    }}
                """)
        else:
            print(f"Background image not found: {self.background_image}")

        current_page = self.onboard_widget.currentWidget()
        # Set pixmap on the relevant pages
        if isinstance(current_page, PrivacyInfo):
            current_page.change_theme(privacy_image,sundial_logo)

        if isinstance(current_page, DataSecurity):
            theme_settings = {
                'gradient_style': gradient_style,
                'solid_button_style': solid_button_style,
                'data_security_img': data_security_img,
                'sundial_logo': sundial_logo,
            }
            current_page.change_theme(theme_settings)

        if isinstance(current_page, OnboardSettings):
            theme_settings = {
                'gradient_style': gradient_style,
                'solid_button_style': solid_button_style,
                'data_security_img': data_security_img,
                'sundial_logo': sundial_logo,
                'container_style': container_style,
            }
            current_page.change_theme(theme_settings)

        if isinstance(current_page, AccessibilitySettings) and sys.platform == "darwin":
            theme_settings = {
                'gradient_style': gradient_style,
                'solid_button_style': solid_button_style,
                'accessibility_img': accessibility_img,
                'sundial_logo': sundial_logo,
            }
            current_page.change_theme(theme_settings)

class PrivacyInfo(QWidget):
    def __init__(self,moveNext):
        super().__init__()

        self.moveNext = moveNext
        # Privacy image setup
        self.privacy_img = TransparentLabel(self)
        self.privacy_img.setGeometry(395, 30, 450, 500)
        self.privacy_img.setScaledContents(True)
        self.privacy_img.setStyleSheet("background: transparent;")  # Make sure the label background is transparent

        # Sundiallogo setup
        self.privacy_sundial_logo = TransparentLabel(self)
        self.privacy_sundial_logo.setGeometry(20, 20, 150, 40)
        self.privacy_sundial_logo.setScaledContents(True)

        # Header with dynamic font sizing
        font = QtGui.QFont()
        font.setPointSize(28 if sys.platform == "darwin" else 12)
        font.setWeight(QFont.Weight.Bold)
        self.privacy_header = TransparentLabel(self)
        self.privacy_header.setGeometry(26, 160, 400, 40)
        self.privacy_header.setText('Our Pledge to Privacy')
        self.privacy_header.setFont(font)

        # Privacy info text setup
        info_font = QtGui.QFont()
        info_font.setPointSize(12 if sys.platform == "darwin" else 8)

        self.privacy_info = TransparentLabel(self)
        self.privacy_info.setGeometry(30, 229, 332, 90)
        self.privacy_info.setText(
            'We understand how important your privacy is. That’s why all your data is securely encrypted and used '
            'only to match your activities with the right projects. Rest assured, it’s protected and won’t be shared '
            'with anyone outside the system.'
        )
        self.privacy_info.setFont(info_font)
        self.privacy_info.setWordWrap(True)

        self.privacy_info_2 = TransparentLabel(self)
        self.privacy_info_2.setGeometry(30, 320, 332, 80)
        self.privacy_info_2.setText(
            'With Ralvie Cloud, you can trust that your data is handled with care, so you can focus on your work '
            'with peace of mind.'
        )
        self.privacy_info_2.setFont(info_font)
        self.privacy_info_2.setWordWrap(True)
        self.privacy_info_2.setStyleSheet("background: transparent;")  # Transparent background for this text too

        # Next button styling and setup
        self.privacy_next_btn = QPushButton(self)
        self.privacy_next_btn.setGeometry(QtCore.QRect(32, 401, 80, 40))
        self.privacy_next_btn.setText("Next")
        self.privacy_next_btn.setStyleSheet(
            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2); "
            "border-radius: 5px; color: #FFFFFF; border: 1px solid #1D0B77;"
        )

        self.privacy_next_btn.clicked.connect(lambda: self.moveNext.emit())

    def change_theme(self, privacy_image, sundial_logo):
        self.privacy_img.setPixmap(privacy_image)
        self.privacy_sundial_logo.setPixmap(sundial_logo)

class DataSecurity(QWidget):
    def __init__(self, moveNext,movePrev):
        super().__init__()

        self.moveNext = moveNext
        self.movePrev = movePrev
        self.datasecurity_img = TransparentLabel(self)
        self.datasecurity_img.setGeometry(452, 193, 308, 223)  # Set the size of the background
        self.datasecurity_img.setScaledContents(True)  # Ensure the background scales properly

        self.datasecurity_sundial_logo = TransparentLabel(self)
        self.datasecurity_sundial_logo.setGeometry(20, 20, 150, 40)  # Set the size of the background
        self.datasecurity_sundial_logo.setScaledContents(True)

        font = QtGui.QFont()
        if sys.platform == "darwin":
            font.setPointSize(28)
        else:
            font.setPointSize(12)
        font.setWeight(QFont.Weight.Bold)
        self.datasecurity_header = TransparentLabel(self)
        self.datasecurity_header.setGeometry(30, 160, 400, 40)  # Set the size of the background
        self.datasecurity_header.setText('Data Security & Encryption')
        self.datasecurity_header.setFont(font)

        info_font = QtGui.QFont()
        if sys.platform == "darwin":
            font.setPointSize(12)
        else:
            font.setPointSize(8)
        self.datasecurity_info = TransparentLabel(self)
        self.datasecurity_info.setGeometry(30, 225, 332, 80)  # Set the size of the background
        self.datasecurity_info.setText(
            "The database where your data is stored is fully encrypted, and it's securely synced to Ralvie Cloud with end-to-end encryption. Your information stays protected throughout the entire process.")
        self.datasecurity_info.setFont(info_font)
        self.datasecurity_info.setWordWrap(True)

        self.datasecurity_back_btn = QPushButton(self)
        self.datasecurity_back_btn.setGeometry(QtCore.QRect(30, 330, 80, 40))
        self.datasecurity_back_btn.setText("Back")

        self.datasecurity_next_btn = QPushButton(self)
        self.datasecurity_next_btn.setGeometry(QtCore.QRect(130, 330, 80, 40))
        self.datasecurity_next_btn.setText("Next")

        self.datasecurity_next_btn.clicked.connect(lambda: self.moveNext.emit())
        self.datasecurity_back_btn.clicked.connect(lambda: self.movePrev.emit())

    def change_theme(self, theme_settings):
        self.datasecurity_img.setPixmap(theme_settings.get('data_security_img'))
        self.datasecurity_sundial_logo.setPixmap(theme_settings.get('sundial_logo'))
        self.setStyleSheet("background-color: #e0e0e0;")
        self.datasecurity_next_btn.setStyleSheet(theme_settings.get('gradient_style'))
        self.datasecurity_back_btn.setStyleSheet(theme_settings.get('solid_button_style'))
        self.datasecurity_img.setScaledContents(True)

class OnboardSettings(QWidget):
    def __init__(self, moveNext):
        super().__init__()

        self.host = "http://localhost:7600/api"
        self.moveNext = moveNext
        self.settings_sundial_logo = TransparentLabel(self)
        self.settings_sundial_logo.setGeometry(20, 20, 150, 40)
        self.settings_sundial_logo.setScaledContents(True)

        font = QtGui.QFont()
        font.setPointSize(28 if sys.platform == "darwin" else 12)
        font.setWeight(QFont.Weight.Bold)
        self.settings_header = TransparentLabel(self)
        self.settings_header.setGeometry(30, 99, 400, 40)
        self.settings_header.setText('Settings')
        self.settings_header.setFont(font)

        self.start_up = QWidget(self)
        self.start_up.setGeometry(QtCore.QRect(30, 168, 740, 60))

        self.start_up_label = TransparentLabel(self.start_up)
        self.start_up_label.setGeometry(QtCore.QRect(20, 22, 211, 16))
        self.start_up_label.setText("Launch Sundial on system startup")
        font.setPointSize(12 if sys.platform == "darwin" else 10)
        self.start_up_label.setFont(font)

        self.start_up_checkbox = SwitchControl(
            self.start_up,
            bg_color="#888888",
            circle_color="#FFFFFF",
            active_color="#FFA500",  # Orange when active
            animation_duration=300
        )
        self.start_up_checkbox.setGeometry(QRect(680, 20, 100, 21))

        settings_font = QtGui.QFont()
        settings_font.setPointSize(12 if sys.platform == "darwin" else 8)

        self.start_up_info = TransparentLabel(self)
        self.start_up_info.setGeometry(30, 220, 700, 30)
        self.start_up_info.setText("Automatically capture your break time when you take a nap.")
        self.start_up_info.setFont(settings_font)
        self.start_up_info.setWordWrap(True)

        self.idle_time = QWidget(self)
        self.idle_time.setGeometry(QtCore.QRect(30, 285, 740, 60))
        self.idle_time_label = TransparentLabel(parent=self.idle_time)
        self.idle_time_label.setGeometry(QtCore.QRect(20, 22, 211, 16))
        self.idle_time_label.setText("Enable idle time detection")

        self.idle_time_checkbox = SwitchControl(
            self.idle_time,
            bg_color="#888888",
            circle_color="#FFFFFF",
            active_color="#FFA500",  # Orange when active
            animation_duration=300
        )
        self.idle_time_checkbox.setGeometry(QtCore.QRect(680, 20, 100, 21))
        self.idle_time_checkbox.raise_()

        self.idle_time_info = TransparentLabel(self)
        self.idle_time_info.setGeometry(30, 340, 700, 30)
        self.idle_time_info.setText(
            "We recommend to let Sundial launch on system start up automatically to avoid missing any activity hours"
        )
        self.idle_time_info.setFont(settings_font)
        self.idle_time_info.setWordWrap(True)

        self.settings_back_btn = QPushButton(self)
        self.settings_back_btn.setGeometry(QtCore.QRect(460, 422, 145, 40))
        self.settings_back_btn.setText("Skip && do it later")

        self.settings_next_btn = QPushButton(self)
        self.settings_next_btn.setGeometry(QtCore.QRect(625, 422, 145, 40))
        self.settings_next_btn.setText("Save && continue")

        self.settings_back_btn.clicked.connect(lambda: self.moveNext.emit())
        self.settings_next_btn.clicked.connect(lambda: self.moveNext.emit())

        self.update_checkboxes()

        self.start_up_checkbox.stateChanged.connect(self.start_up_status)
        self.idle_time_checkbox.stateChanged.connect(self.idle_time_status)

    def change_theme(self, theme_settings):
        self.idle_time.setStyleSheet(theme_settings.get('container_style'))
        self.start_up.setStyleSheet(theme_settings.get('container_style'))
        self.settings_sundial_logo.setPixmap(theme_settings.get('sundial_logo'))
        self.settings_back_btn.setStyleSheet(theme_settings.get('solid_button_style'))
        self.settings_next_btn.setStyleSheet(theme_settings.get('gradient_style'))
        # Retrieve settings and update checkboxes

    def update_checkboxes(self):
        settings = retrieve_settings()
        self.start_up_checkbox.setChecked(settings.get('launch', False))
        self.idle_time_checkbox.setChecked(settings.get('idle_time', False))

        # Connect checkbox signals to slot methods

    def idle_time_status(self):
        status = "start" if self.idle_time_checkbox.isChecked() else "stop"
        self.enable_idletime(status)

    def start_up_status(self):
        status = "start" if self.start_up_checkbox.isChecked() else "stop"
        self.launch_on_start(status)

    def enable_idletime(self, status):
        params = {"status": status}
        creds = credentials()

        if creds and "token" in creds:
            sundial_token = creds["token"]
            self.send_request(f"{self.host}/0/idletime", sundial_token, params)

    def launch_on_start(self, status):
        params = {"status": status}
        creds = credentials()

        if creds and "token" in creds:
            sundial_token = creds["token"]
            self.send_request(f"{self.host}/0/launchOnStart", sundial_token, params)

    def send_request(self, url, token, params):
        try:
            response = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
            if response.status_code == 200:
                print("Request successful")
            else:
                print(f"Request failed: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            print(f"An error occurred while sending the request: {e}")

class AccessibilitySettings(QWidget):
    def __init__(self,movePrev, move_to_dashBoard):
        super().__init__()

        self.movePrev = movePrev
        self.move_to_dashBoard = move_to_dashBoard
        self.accessibility_sundial_logo = QLabel(self)
        self.accessibility_sundial_logo.setGeometry(20, 20, 150, 40)  # Set the size of the background
        self.accessibility_sundial_logo.setScaledContents(True)

        self.accessibility_img = QLabel(self)
        self.accessibility_img.setGeometry(436, 154, 344, 293)
        self.accessibility_img.setScaledContents(True)
        self.accessibility_img.setStyleSheet(
            "background: transparent;")  # Make sure the label background is transparent

        font = QtGui.QFont()
        font.setPointSize(28 if sys.platform == "darwin" else 24)
        font.setWeight(QFont.Weight.Bold)
        self.accessibility_header = QLabel(self)
        self.accessibility_header.setGeometry(30, 160, 400, 40)
        self.accessibility_header.setText('Accessibility Permissions')
        self.accessibility_header.setFont(font)

        info_font = QtGui.QFont()
        info_font.setPointSize(12 if sys.platform == "darwin" else 8)

        self.accessibility_info = QLabel(self)
        self.accessibility_info.setGeometry(30, 220, 332, 90)
        self.accessibility_info.setText(
            'To enhance your experience with the app, please enable Sundial in the accessibility permissions. This allows the app to track your system activities for better functionality.'
        )
        self.accessibility_info.setFont(info_font)
        self.accessibility_info.setWordWrap(True)

        self.accessibility_back_btn = QPushButton(self)
        self.accessibility_back_btn.setGeometry(QtCore.QRect(30, 330, 80, 40))
        self.accessibility_back_btn.setText("Back")

        self.accessibility_next_btn = QPushButton(self)
        self.accessibility_next_btn.setGeometry(QtCore.QRect(130, 330, 100, 40))
        self.accessibility_next_btn.setText("Complete")

        # Connect the "Next" button to the function to check and prompt for accessibility permissions
        self.accessibility_back_btn.clicked.connect(lambda: self.movePrev.emit())
        self.accessibility_next_btn.clicked.connect(lambda: self.move_to_dashBoard.emit())

    def change_theme(self, theme_settings):
        self.accessibility_sundial_logo.setPixmap(theme_settings.get('sundial_logo'))
        self.accessibility_img.setPixmap(theme_settings.get('accessibility_img'))
        self.accessibility_back_btn.setStyleSheet(theme_settings.get('solid_button_style'))
        self.accessibility_next_btn.setStyleSheet(theme_settings.get('gradient_style'))

