import json
import os
import sys
import threading

import requests
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication, QTimer, Signal
from PySide6.QtGui import QPixmap, Qt, QIcon, QCursor, QMovie
from PySide6.QtWidgets import QWidget, QStackedWidget, QHBoxLayout, QApplication, QPushButton, QLabel, QSizePolicy, \
    QVBoxLayout, QLineEdit, QToolButton, QComboBox, QGraphicsDropShadowEffect

from sd_core.cache import clear_credentials, add_password
from sd_qt.sd_desktop.ThemeManager import ThemeManager
from sd_qt.sd_desktop.util import credentials

# Define paths
base_path = os.path.abspath(os.path.join(__file__, "../../.."))
resources_path = os.path.join(base_path, "sd_qt","sd_desktop", "resources")

darkTheme = os.path.join(resources_path, "DarkTheme")
lightTheme = os.path.join(resources_path, "LightTheme")

user_details = {

}

class TransparentLabel(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoFillBackground(False)
        # Set the stylesheet here to make the background transparent and customize the text color
        self.setStyleSheet("""
            background-color: transparent;
        """)

class SignIn(QWidget):
    goToCompanyPageSignal = Signal()
    loginSuccess = Signal(dict)
    companyPageSwitch = Signal()
    move_on = Signal()
    navigate_to_next_page = Signal()


    def __init__(self,on_sign_in_completed):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_Changed.connect(self.apply_background_image)  # Update background on theme change
        # Create QStackedWidget and layout
        self.signin_widget = QStackedWidget()
        self.on_sign_in_completed = on_sign_in_completed
        self.server_check_timer = QTimer(self)  # Add a QTimer for server checks
        self.server_check_timer.timeout.connect(self.check_server_and_move)

        # Add loading page and homepage with lazy loading
        self.loading_page = LoadingPage()
        self.homepage = HomePage(self.navigate_to_next_page)
        self.signin = SignInPage(self.loginSuccess)
        self.company = CompanyPage(self.companyPageSwitch, self.move_on)
        self.signin_widget.addWidget(self.loading_page)
        self.signin_widget.addWidget(self.homepage)
        self.signin_widget.addWidget(self.signin)
        self.signin_widget.addWidget(self.company)

        self.loginSuccess.connect(self.company.process_login_response)
        self.companyPageSwitch.connect(self.navigate_to_company)
        self.move_on.connect(self.on_sign_in_completed)
        self.navigate_to_next_page.connect(self.navigate)
        self.signin_widget.currentChanged.connect(self.apply_background_image)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.signin_widget)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Initial background setup
        self.apply_background_image()
        self.start_server_check_timer()

    def start_server_check_timer(self):
        """Start checking the server status every second."""
        self.server_check_timer.start(1000)

    def check_server_and_move(self):
        """Check the server status and move to the dashboard if available."""
        # Assuming you have a function check_server_status in SignInPage for server availability check
        if self.signin.check_server_status():  # Use your server status check here
            self.server_check_timer.stop()  # Stop the timer once server is available
            self.navigate_to_dashboard()  # Move to the dashboard

    def navigate_to_dashboard(self):
        """Function to navigate to the dashboard or next page."""
        # Assuming `homepage` is the dashboard in your case
        dashboard_index = self.signin_widget.indexOf(self.homepage)
        if dashboard_index != -1:
            self.signin_widget.setCurrentIndex(dashboard_index)

    def navigate_to_company(self):
        # Find the index of the company page widget in the QStackedWidget
        company_index = self.signin_widget.indexOf(self.company)

        # Set the current index to the company page
        if company_index != -1:  # Ensure the page exists in the stack
            self.signin_widget.setCurrentIndex(company_index)


    def navigate(self):
        # Get the current page index and the current widget
        current_index = self.signin_widget.currentIndex()
        current_widget = self.signin_widget.widget(current_index)

        # Move to the next page, wrapping around if necessary
        if current_index < self.signin_widget.count() - 1:
            next_index = (current_index + 1) % self.signin_widget.count()
            self.signin_widget.setCurrentIndex(next_index)
            current_widget.deleteLater()

    def apply_background_image(self):
        # Select background image based on current theme
        if self.theme_manager.get_theme() == "dark":
            self.background_image = os.path.join(darkTheme, "background.svg")
            sundial_logo = os.path.join(darkTheme, "loader_sundial_logo.svg")
            homepage_subtitle = os.path.join(darkTheme, "signin_subtitle.svg")
            homepage_SundialLogo = os.path.join(darkTheme, "dark_des_logo.svg")
            sign_in_SundialLogo = os.path.join(darkTheme, "dark_signin_logo.svg")
            signin_link_color = "#A49DC8"
            hide_pass = os.path.join(darkTheme, 'hide_pass.svg')
            show_pass = os.path.join(darkTheme, "show_pass.svg")
            background_color = "#010101"
            border_color = "#313131"
            placeholder_color = "#F8F8F8"
            # Company selection
            company_SundialLogo = os.path.join(darkTheme, "dark_signin_logo.svg")
            forgot_password_color = "#F8F8F8"
        else:
            self.background_image = os.path.join(lightTheme, "background.svg")
            sundial_logo = os.path.join(lightTheme, "loader_sundial_logo.svg")
            homepage_subtitle = os.path.join(lightTheme, "signin_subtitle.svg")
            homepage_SundialLogo = os.path.join(lightTheme, "description_logo.svg")
            # signin
            sign_in_SundialLogo = os.path.join(lightTheme, "signin_logo.svg")
            signin_link_color = "#1D0B77"
            show_pass = os.path.join(lightTheme, "show_pass.svg")
            hide_pass = os.path.join(lightTheme, "hide_pass.svg")
            background_color = "#FFFFFF"
            border_color = "#DDDDDD"
            placeholder_color = "#474B4F"
            # Company Selection
            company_SundialLogo = os.path.join(lightTheme, "signin_logo.svg")
            forgot_password_color = "#474B4F"

            # Apply background image stylesheet to QStackedWidget
        if os.path.exists(self.background_image):
            self.signin_widget.setStyleSheet(f"""
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

        sundial_pixmap = QPixmap(sundial_logo)
        subtitle_pixmap = QPixmap(homepage_subtitle)
        current_page = self.signin_widget.currentWidget()
        print(current_page)

        # Set pixmap on the relevant pages
        if isinstance(current_page, LoadingPage):
            current_page.set_logo_pixmap(sundial_pixmap)

        elif isinstance(current_page, HomePage):
            current_page.set_logo(subtitle_pixmap,homepage_SundialLogo)

        elif isinstance(current_page, SignInPage):
            theme_settings = {
                "sign_in_SundialLogo" : sign_in_SundialLogo,
                "signin_link_color" : signin_link_color,
                "hide_pass" : hide_pass,
                "show_pass" : show_pass,
                "background_color" : background_color,
                "border_color" : border_color,
                "placeholder_color" : placeholder_color,
                "forgot_password_color": forgot_password_color

            }
            current_page.change_theme(theme_settings)

        elif isinstance(current_page, CompanyPage):
            theme_settings = {
                "background_color": background_color,
                "border_color": border_color,
            }
            current_page.change_theme(company_SundialLogo,theme_settings)





class HomePage(QWidget):
    def __init__(self,navigate_to_next_page):
        super().__init__()

        self.navigate_to_next_page = navigate_to_next_page
        # Sundial logo
        self.homepage_Sundial_logo = TransparentLabel("Sundial Logo", self)
        self.homepage_Sundial_logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.homepage_Sundial_logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.homepage_Sundial_logo.setGeometry(220, 50, 350, 100)

        # Subtitle
        self.homepage_subtitle = TransparentLabel(self)
        self.homepage_subtitle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.homepage_subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.homepage_subtitle.setGeometry(125, 200, 550, 124)

        # Description
        self.description = TransparentLabel("Automated, AI-driven time tracking software of the future", self)
        self.description.setGeometry(QtCore.QRect(198, 350, 480, 30))
        font = QtGui.QFont()
        font.setPointSize(16 if sys.platform == "darwin" else 12)
        self.description.setFont(font)

        # Sign in button
        self.signIn_button = QPushButton("Sign in", self)
        self.signIn_button.setGeometry(QtCore.QRect(150, 450, 500, 60))
        self.signIn_button.setObjectName("signInButton")
        self.signIn_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.signIn_button.clicked.connect(self.navigate_to_next_page.emit)

    def set_logo(self, homepage_subtitle_pixmap, homepage_Sundial_logo):
        self.homepage_subtitle.setPixmap(homepage_subtitle_pixmap)
        self.homepage_subtitle.setStyleSheet("background-color: none;")

        sign_in_pixmap = QPixmap(homepage_Sundial_logo)
        self.homepage_Sundial_logo.setPixmap(sign_in_pixmap)
        self.homepage_Sundial_logo.setStyleSheet("background: transparent;")

        self.signIn_button.setStyleSheet("""
                                       QPushButton#signInButton {
                                           border: none;
                                           background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1D0B77, stop:1 #6A5FA2);
                                           color: #ffffff;
                                           border-radius: 10px;
                                           padding: 10px;
                                           font-size: 16px;
                                       }
                                   """)




class LoadingPage(QWidget):
    def __init__(self):
        super().__init__()

        self.Sundial_logo = TransparentLabel(self)
        self.Sundial_logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Create a QVBoxLayout and add the TransparentLabel to it
        layout = QVBoxLayout(self)
        layout.addWidget(self.Sundial_logo)

        # Set alignment to center the TransparentLabel within the widget
        layout.setAlignment(self.Sundial_logo, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def set_logo_pixmap(self, pixmap):
        """ Set logo pixmap only when needed to optimize rendering """
        self.Sundial_logo.setPixmap(pixmap)
        self.Sundial_logo.setStyleSheet("background: transparent;")



class SignInPage(QWidget):


    def __init__(self, loginSuccess):
        super().__init__()
        self.hide_pass = None
        self.show_pass = None
        self.companies = None
        self.companyid = None
        self.host = "http://localhost:7600/api"
        self.loginSuccess = loginSuccess

        self.setGeometry(0, 0, 800, 600)
        self.setContentsMargins(0, 0, 0, 0)

        # Background setup
        self.sign_in_background = TransparentLabel(self)
        self.sign_in_background.setContentsMargins(0, 0, 0, 0)
        self.sign_in_background.setScaledContents(True)
        self.sign_in_background.setGeometry(0, 0, 800, 600)

        # Sundial Logo
        self.sign_in_Sundial_logo = TransparentLabel("Sundial Logo", parent=self)
        self.sign_in_Sundial_logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.sign_in_Sundial_logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo_width, logo_height = 283, 100
        self.sign_in_Sundial_logo.setGeometry(250, 30, logo_width, logo_height)

        # Sign-in widget
        self.signin_widget = QWidget(self)
        self.signin_widget.setGeometry(135, 130, 534, 409)

        # Welcome message
        self.welcomeMessage = TransparentLabel("Welcome back!", parent=self.signin_widget)
        self.welcomeMessage.setGeometry(QtCore.QRect(40, 25, 280, 39))
        font = QtGui.QFont()
        font.setPointSize(28 if sys.platform == "darwin" else 26)
        self.welcomeMessage.setFont(font)

        # New User label
        self.newUserLabel = TransparentLabel("New user?", parent=self.signin_widget)
        self.newUserLabel.setGeometry(QtCore.QRect(40, 80, 81, 20))
        font.setPointSize(14 if sys.platform == "darwin" else 10)
        self.newUserLabel.setFont(font)

        # Signup label with hyperlink
        self.signupLabel = TransparentLabel(parent=self.signin_widget)
        self.signupLabel.setGeometry(QtCore.QRect(120, 80, 150, 20))
        self.signupLabel.setFont(font)
        self.signupLabel.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.signupLabel.setOpenExternalLinks(True)

        # Email input field
        font.setPointSize(16 if sys.platform == "darwin" else 10)
        self.emailField =QLineEdit(parent=self.signin_widget)
        self.emailField.setGeometry(QtCore.QRect(40, 120, 444, 60))
        self.emailField.setPlaceholderText("User name or Email")
        self.emailField.setFont(font)

        # Password input field
        self.passwordField = QLineEdit(self.signin_widget)
        self.passwordField.setGeometry(40, 200, 444, 60)
        self.passwordField.setPlaceholderText("Password")
        self.passwordField.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordField.setFont(font)

        icon_path = os.path.join(lightTheme, 'show_pass.svg')
        icon = QPixmap(icon_path).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.showPassButton = QToolButton(self)
        self.showPassButton.setGeometry(0, 0, 44, 44)
        self.showPassButton.setIcon(QIcon(icon))
        self.showPassButton.setCheckable(True)
        self.showPassButton.setToolTip('View password')
        self.showPassButton.setCursor(QCursor(Qt.PointingHandCursor))

        print(f"ToolTip set: {self.showPassButton.toolTip()}")

        # Connect the toggle action to show/hide password
        self.showPassButton.toggled.connect(self.showPassword)

        # Create a layout to insert the QToolButton inside the QLineEdit
        layout = QHBoxLayout(self.passwordField)
        layout.addStretch()
        layout.addWidget(self.showPassButton)
        layout.setContentsMargins(0, 0, 10, 0)
        self.passwordField.setLayout(layout)

        self.errorMessageLabel = TransparentLabel(parent=self.signin_widget)
        self.errorMessageLabel.setGeometry(QtCore.QRect(40, 280, 334, 20))
        font.setPointSize(12 if sys.platform == "darwin" else 10)
        self.errorMessageLabel.setFont(font)
        self.errorMessageLabel.setVisible(False)
        self.errorMessageLabel.setStyleSheet("color: red;")

        self.Forgot_password_Label = TransparentLabel(parent=self.signin_widget)
        self.Forgot_password_Label.setGeometry(QtCore.QRect(360, 280, 200, 23))
        if sys.platform == "darwin":
            font.setPointSize(14)
        else:
            font.setPointSize(10)
        self.Forgot_password_Label.setFont(font)
        self.Forgot_password_Label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.Forgot_password_Label.setOpenExternalLinks(True)

        self.sign_In_button = QPushButton("Sign in", parent=self.signin_widget)
        self.sign_In_button.setGeometry(QtCore.QRect(40, 320, 444, 60))
        self.sign_In_button.setObjectName("sign_In_button")
        self.sign_In_button.setCursor(QtGui.QCursor(
            QtCore.Qt.CursorShape.PointingHandCursor))
        self.sign_In_button.setFont(font)

        self.loader_overlay = QWidget(self)
        self.loader_overlay.setGeometry(0, 0, 800, 600)
        self.loader_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.loader_overlay.setVisible(False)

        # Centered loader animation
        self.loading_animation = QLabel(self.loader_overlay)
        self.loading_animation.setStyleSheet("background:none")
        self.loading_animation.setGeometry((800 // 2) - 50, (600 // 2) - 50, 100, 100)  # Centered position
        self.loading_animation.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.loading_movie = QMovie(resources_path+"\loader.gif")  # Replace with the actual path to your GIF
        self.loading_animation.setMovie(self.loading_movie)

        self.signin_message = QWidget(parent=self)
        self.signin_message.setGeometry(QtCore.QRect(800, 480, 400, 60))
        self.signin_message_label = TransparentLabel(self.signin_message)
        self.signin_message_label.setGeometry(QtCore.QRect(20, 10, 330, 40))

        self.sign_In_button.clicked.connect(self.initiate_login)

    def showPassword(self, checked):
        """Toggle password visibility and update the icon."""
        if checked:
            self.passwordField.setEchoMode(QLineEdit.EchoMode.Normal)
            icon = QIcon(self.hide_pass)
            self.showPassButton.setIcon(icon)
            self.showPassButton.setToolTip('Hide password')
        else:
            self.passwordField.setEchoMode(QLineEdit.EchoMode.Password)
            # print(f"Setting show password icon: {icon_path}")  # Debugging: check the icon path
            icon = QIcon(self.show_pass)
            self.showPassButton.setIcon(icon)
            self.showPassButton.setToolTip('View password')

    def start_loader(self):
        self.loader_overlay.setVisible(True)
        self.loading_movie.start()

    def stop_loader(self):
        self.loader_overlay.setVisible(False)
        self.loading_movie.stop()

    def initiate_login(self):
        # Show the loading overlay
        self.start_loader()
        email = self.emailField.text()
        password = self.passwordField.text()

        user_details['email']  =  email
        user_details['password'] = password

        if not self.check_server_status():
            self.stop_loader()
            self.show_error_message(
                "Server not available. Please try again later.")
            return

        if not email and not password:
            self.stop_loader()
            self.show_error_message("User name and Password empty.")
            return

        if not email:
            self.stop_loader()
            self.show_error_message("User name is empty.")
            return
        elif not password:
            self.stop_loader()
            self.show_error_message("Password is empty.")
            return

        # Run the login request in a separate thread
        threading.Thread(target=self.perform_login_request,
                         args=(email, password)).start()

    def perform_login_request(self, email, password):
        payload = {"userName": email, "password": password, "companyId": self.companyid or ""}
        try:
            response = requests.post(self.host + "/0/ralvie/login", json=payload,
                                     headers={'Content-Type': 'application/json'})
            print(response.text)

            if response.ok:
                response_data = response.json()
                if response_data["code"] == "UASI0011":
                    self.sundail_token = response_data['data']['token']
                    self.stop_loader()  # Stop the loader if the login is successful
                elif response_data["code"] == "RCW00001":
                    self.loginSuccess.emit(response.json())
                    self.stop_loader()  # Stop the loader on successful login
                else:
                    self.stop_loader()  # Stop the loader for unexpected response codes
                    self.show_error_message(response_data["message"])
            else:
                self.stop_loader()  # Ensure loader stops on HTTP error response
                self.show_error_message("Server error. Please try again.")
        except Exception as e:
            self.stop_loader()  # Stop the loader on exception
            self.show_error_message(f"Error during login: {str(e)}")

    def show_error_message(self, message):
        self.errorMessageLabel.setText(message)
        self.errorMessageLabel.setVisible(True)
        QTimer.singleShot(
            5000, lambda: self.errorMessageLabel.setVisible(False))

    def check_server_status(self):
        try:
            response = requests.get(
                self.host + "/0/server_status")
            return response.status_code == 200
        except requests.RequestException:
            return False


    def change_theme(self,theme_settings):
        print(theme_settings)
        sign_in_pixmap = QPixmap(theme_settings.get("sign_in_SundialLogo"))
        self.sign_in_Sundial_logo.setPixmap(sign_in_pixmap)
        self.sign_in_Sundial_logo.setStyleSheet("background: transparent;")
        urlLink = f'<a href="https://ralvie.minervaiotstaging.com/pages/verify-email" style="color: {theme_settings.get("signin_link_color")}; text-decoration: none;">Sign up here</a>'
        self.signupLabel.setText(urlLink)
        self.show_pass = theme_settings.get("show_pass")
        self.hide_pass = theme_settings.get("hide_pass")
        self.passwordField.setStyleSheet(f"""
            QLineEdit {{
                background: {theme_settings.get("background_color", "#010101")};
                border: 1px solid {theme_settings.get("border_color", "#313131")};
                border-radius: 10px;
                padding: 10px;
                opacity: 1;
                padding-right: 60px;
            }}
            QLineEdit::placeholder {{
                color: {theme_settings.get("placeholder_color", "#F8F8F8")};
                font-size: 14px;
            }}
        """)

        self.emailField.setStyleSheet(f"""
            QLineEdit {{
                background: {theme_settings.get("background_color", "#010101")};
                border: 1px solid {theme_settings.get("border_color", "#313131")};
                border-radius: 10px;
                padding: 10px;
                opacity: 1;
            }}
            QLineEdit::placeholder {{
                color: {theme_settings.get("placeholder_color", "#F8F8F8")};
                font-size: 14px;
            }}
        """)
        urlLink = f'<a href="https://ralvie.minervaiotstaging.com/pages/verify-user" style="text-decoration: none;color:{theme_settings.get("forgot_password_color")}; opacity:0.8">Forgot password?</a>'
        self.Forgot_password_Label.setText(urlLink)
        self.sign_In_button.setStyleSheet("""
                                                               QPushButton#sign_In_button {
                                                                   border: none;
                                                                   background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1D0B77, stop:1 #6A5FA2);
                                                                   color: #ffffff;
                                                                   border-radius: 10px;
                                                                   padding: 10px;
                                                                   font-size: 16px;
                                                               }

                                                           """)
        self.signin_widget.setStyleSheet(
            f'background-color: {theme_settings.get("background_color", "#010101")}; border-radius: 10px; opacity: 1;'
        )
        self.signin_widget.setWindowOpacity(1.0)

        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setXOffset(0)
        shadow_effect.setYOffset(0)
        shadow_effect.setColor(QtGui.QColor(0, 0, 0, 160))


class CompanyPage(QWidget):
    def __init__(self,companyPageSwitch, move_on):
        super().__init__()

        self.companyPageSwitch = companyPageSwitch
        self.move_on = move_on

        self.host = "http://localhost:7600/api"
        # Sundial Logo Label
        self.company_Sundial_logo = TransparentLabel("Sundial Logo", parent=self)
        self.company_Sundial_logo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.company_Sundial_logo.setAlignment(QtCore.Qt.AlignCenter)
        logo_width, logo_height = 283, 100
        self.company_Sundial_logo.setGeometry(250, 30, logo_width, logo_height)

        # Company Widget
        self.company_widget = QWidget(self)
        self.company_widget.setGeometry(135, 170, 534, 309)


        # Company Message Label
        self.CompanyMessage = TransparentLabel("Organization", parent=self.company_widget)
        self.CompanyMessage.setGeometry(QtCore.QRect(40, 25, 280, 39))
        font = QtGui.QFont()
        font.setPointSize(24 if sys.platform == "darwin" else 18)
        self.CompanyMessage.setFont(font)

        # Company Selection ComboBox
        self.companySelect = QComboBox(self.company_widget)
        self.companySelect.setGeometry(QtCore.QRect(40, 100, 454, 60))

        # Error Message Label
        self.companyErrorMessageLabel = TransparentLabel(parent=self.company_widget)
        self.companyErrorMessageLabel.setGeometry(QtCore.QRect(42, 170, 334, 20))
        font.setPointSize(12 if sys.platform == "darwin" else 10)
        self.companyErrorMessageLabel.setFont(font)
        self.companyErrorMessageLabel.setVisible(False)
        self.companyErrorMessageLabel.setStyleSheet("color: red;")

        # Button for Company Selection
        font.setPointSize(14 if sys.platform == "darwin" else 10)
        self.company_select_button =QPushButton("Get started", parent=self.company_widget)
        self.company_select_button.setGeometry(QtCore.QRect(40, 200, 454, 50))
        self.company_select_button.setFont(font)
        self.company_select_button.clicked.connect(self.handle_company_selection)

        self.company_loader_overlay = QWidget(self)
        self.company_loader_overlay.setGeometry(0, 0, 800, 600)
        self.company_loader_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.company_loader_overlay.setVisible(False)

        # Centered loader animation
        self.company_loading_animation = QLabel(self.company_loader_overlay)
        self.company_loading_animation.setStyleSheet("background:none")
        self.company_loading_animation.setGeometry((800 // 2) - 50, (600 // 2) - 50, 100, 100)  # Centered position
        self.company_loading_animation.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.company_loading_movie = QMovie(resources_path+"\loader.gif")  # Replace with the actual path to your GIF
        self.company_loading_animation.setMovie(self.company_loading_movie)

    def start_loader(self):
        self.company_loader_overlay.setVisible(True)
        self.company_loader_overlay.raise_()
        self.company_loading_movie.start()
        # print("==================================++++> " + str(self.company_loader_overlay.isVisible()))
        # print("==================================++++> " + str(self.company_loading_movie.frameCount()))
        self.company_loader_overlay.repaint() 

    def stop_loader(self):
        self.company_loader_overlay.setVisible(False)
        self.company_loading_movie.stop()

    def process_login_response(self, response_data):
        if response_data["code"] == 'RCW00001':
            self.companies = response_data['data']['companies']

            if self.companies:
                self.populate_company_combobox()
                self.companyPageSwitch.emit()
            else:
                self.show_compnay_error_message("No companies available for selection.")
        elif response_data["code"] in ['RCE0024', 'RCE0103']:
            self.show_compnay_error_message(response_data["message"])
        else:
            self.show_compnay_error_message(response_data.get("message", "Unknown error"))

    def populate_company_combobox(self):
        self.companySelect.clear()
        unique_company_names = {company['name'] for company in self.companies}
        self.companySelect.addItems(unique_company_names)

    def show_compnay_error_message(self, message):
        self.companyErrorMessageLabel.setText(message)
        self.companyErrorMessageLabel.setVisible(True)
        QTimer.singleShot(5000, lambda: self.companyErrorMessageLabel.setVisible(False))

    def change_theme(self, sundial_logo, theme_settings):
        company_pixmap = QPixmap(sundial_logo)
        self.company_Sundial_logo.setPixmap(company_pixmap)
        self.company_Sundial_logo.setStyleSheet("background: transparent;")

        self.companySelect.setStyleSheet(f"""
                       QComboBox {{
                           background: {theme_settings.get("background_color")};
                           border: 1px solid {theme_settings.get("border_color")};
                           border-radius: 10px;
                           font-size: 16px;
                           padding-right: 20px;
                           padding-left: 10px;
                       }}
                       QComboBox::drop-down {{
                           border: none;
                           margin-right: 10px;
                       }}
                   """)

        self.company_select_button.setStyleSheet("""
                           QPushButton {
                               border: none;
                               background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1D0B77, stop:1 #6A5FA2);
                               color: #ffffff;
                               border-radius: 10px;
                               padding: 10px;
                               font-size: 16px;
                           }
                       """)
        self.company_widget.setStyleSheet(
            f"background-color: {theme_settings.get('background_color')}; border-radius: 10px; opacity: 1;"
        )

    def handle_company_selection(self):
        self.selected_company = self.companySelect.currentText()
        self.continue_with_selected_company()

    def continue_with_selected_company(self):
        self.companyid = next(
            (comp['id'] for comp in self.companies if comp['name'] == self.selected_company), None)
        if self.companyid:
            self.start_loader()
            email = user_details.get("email", None)
            password = user_details.get("password", None)
            self.perform_login_request(email, password, self.companyid)
        else:
            self.stop_loader()
            self.show_compnay_error_message("Company selection error.")

    def perform_login_request(self, email, password, companyid):
        payload = {"userName": email, "password": password, "companyId": companyid or ""}
        try:
            response = requests.post(self.host + "/0/ralvie/login", json=payload,
                                     headers={'Content-Type': 'application/json'})
            print(response.text)
            if response.ok:
                response_data = response.json()
                if response_data["code"] == "UASI0011":
                    self.sundail_token = response_data['data']['token']
                    clear_credentials("SD_KEYS")
                    cached_credentials = credentials()
                    cached_credentials['Sundial'] = True
                    add_password("SD_KEYS", json.dumps(cached_credentials))
                    self.move_on.emit()
                else:
                    self.stop_loader()
                    self.show_compnay_error_message(response_data["message"])
        except Exception as e:
            self.stop_loader()
            self.show_compnay_error_message(f"Error during login: {str(e)}")
        finally:
            self.stop_loader()
            self.restore_ui_state()

    def restore_ui_state(self):
        self.company_select_button.setIcon(QIcon())  # Clear the icon
        self.company_select_button.setText("Get started")
        self.companySelect.setDisabled(False)
        self.company_select_button.setDisabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignIn()
    window.show()
    sys.exit(app.exec())
