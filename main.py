import json
import sys
import time  # Import time module for measuring load time
import schedule
from pathlib import Path
from PySide6.QtCore import QSettings, Signal, QEvent, QTimer
from PySide6.QtWidgets import QMainWindow, QApplication, QStackedWidget, QSystemTrayIcon, QMenu, QMessageBox, QCheckBox, QWidgetAction, QPushButton
from PySide6.QtGui import QIcon, QSurfaceFormat, QAction
from sd_qt.sd_desktop.ThemeManager import ThemeManager
from sd_core.cache import add_password
from sd_qt.sd_desktop.Dashboard import Dashboard
from sd_qt.sd_desktop.onboard import Onboarding
from sd_qt.sd_desktop.signin import SignIn
from sd_qt.sd_desktop.util import credentials
from sd_qt.restart import manage_watchers
from sd_qt.sd_desktop.util import events_cache
from PySide6 import QtCore
import requests
import logging

from sd_qt.sd_desktop.util import add_settings, retrieve_settings
if sys.platform == "darwin":
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory, NSApplicationActivationPolicyRegular

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    onboard_navigate = Signal()  # Signal to trigger navigation check

    def __init__(self):
        super().__init__()

        self.host = "http://localhost:7600/api"
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_Changed.connect(self.theme_manager.switch_theme)
        self.setWindowTitle("Sundial")
        self.setFixedSize(800, 600)
        self.setContentsMargins(0, 0, 0, 0)  # Removes any margins around the layout

        # Use QSettings to store onboarding completion status
        self.settings = QSettings("ralvie.ai", "Sundial")

        # Create a QStackedWidget to manage different screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize widgets
        self.sign_in_widget = SignIn(self.on_sign_in_completed)
        self.onboard_widget = Onboarding(self.on_onboarding_completed)
        self.main_app_widget = None  # Load lazily after onboarding or sign-in

        # Connect navigate signal to navigation handler
        self.onboard_navigate.connect(self.handle_navigation)

        # Add widgets to the stack
        self.stack.addWidget(self.sign_in_widget)
        self.stack.addWidget(self.onboard_widget)

        # Start with the SignIn screen
        self.view_stack()

        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.run_scheduled_tasks)
        self.schedule_timer.start(20000)  # 20 seconds in milliseconds

        self.expanded_menu = None  # Initialize expanded_menu attribute

        # Schedule the manage_watchers task
        schedule.every(20).seconds.do(manage_watchers)

        self.menu = QMenu()

        # Setup system tray icon
        self.setupSystemTray()

        self.retrieve = retrieve_settings()

    def run_scheduled_tasks(self):
        """Run scheduled tasks."""
        schedule.run_pending()

    def handle_navigation(self):
        """Check if onboarding is needed and navigate accordingly."""
        onboarding_status = self.settings.value("onboarding_complete", "")

        if onboarding_status == "gGvGS*f+d9x<*E9sjk":
            # Show the main app screen
            if not self.main_app_widget:
                self.main_app_widget = Dashboard(self.sign_out)
                self.stack.addWidget(self.main_app_widget)

            self.stack.setCurrentWidget(self.main_app_widget)
        else:
            self.stack.setCurrentWidget(self.onboard_widget)

    def on_sign_in_completed(self):
        """Called after the sign-in is completed."""
        if not self.main_app_widget:
            self.main_app_widget = Dashboard(self.sign_out)
            self.stack.addWidget(self.main_app_widget)

        self.onboard_navigate.emit()

        if self.sign_in_widget:
            self.stack.removeWidget(self.sign_in_widget)
            self.sign_in_widget.deleteLater()
            self.sign_in_widget = None

    def on_onboarding_completed(self):
        """Called after the onboarding is completed."""
        # self.settings.setValue("onboarding_complete", "j?KEgMKb:^kNMpX:Bx=7s")
        self.settings.setValue("onboarding_complete", "gGvGS*f+d9x<*E9sjk")
        # gGvGS*f+d9x<*E9sjk
        self.onboard_navigate.emit()

        if self.onboard_widget:
            self.stack.removeWidget(self.onboard_widget)
            self.onboard_widget.deleteLater()
            self.onboard_widget = None

    def view_stack(self):
        """Determine the initial screen based on credentials."""
        creds = credentials()
        if creds and creds.get('Sundial'):
            if not self.main_app_widget:
                self.main_app_widget = Dashboard(self.sign_out)
                self.stack.addWidget(self.main_app_widget)
            self.stack.setCurrentWidget(self.main_app_widget)
        else:
            if not self.sign_in_widget:
                self.sign_in_widget = SignIn(self.on_sign_in_completed)
                self.stack.addWidget(self.sign_in_widget)
            self.stack.setCurrentWidget(self.sign_in_widget)

    def sign_out(self):
        """Sign out the user and return to the sign-in screen."""
        events_cache.clear()
        cached_creds = credentials()
        if cached_creds:
            cached_creds['Sundial'] = False
            add_password("SD_KEYS", json.dumps(cached_creds))

        if not self.sign_in_widget:
            self.sign_in_widget = SignIn(self.on_sign_in_completed)
            self.stack.addWidget(self.sign_in_widget)

        self.stack.setCurrentWidget(self.sign_in_widget)
        # self.settings.setValue("onboarding_complete", "")

        if self.main_app_widget:
            self.stack.removeWidget(self.main_app_widget)
            self.main_app_widget.deleteLater()
            self.main_app_widget = None

    def setupSystemTray(self):
        """Setup the system tray icon and menu."""
        scriptdir = Path(__file__).parent.parent
        QtCore.QDir.addSearchPath("icons", str(scriptdir.parent / "media/logo/"))
        QtCore.QDir.addSearchPath("icons", str(scriptdir.parent.parent / "Resources/aw_qt/media/logo/"))

        # Set the icon based on the platform
        if sys.platform == "darwin":
            icon_path = "icons:black-monochrome-logo.png"
        else:
            icon_path = "icons:logo.png"
        icon = QIcon(icon_path)

        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Sundial Application")

        # Create a menu for the tray icon
        self.menu = QMenu()

        # "Open" action to show the window
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show_window)
        self.menu.addAction(open_action)

        # "Quit" action to quit the application
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        self.menu.addAction(quit_action)

        # Add "Logged In Menu" trigger
        login_action = QAction("Login", self)
        self.menu.addAction(login_action)
        login_action.triggered.connect(self.show_login_menu)

        # Set the context menu for the tray icon
        self.tray_icon.setContextMenu(self.menu)

        # Show the tray icon
        self.tray_icon.show()

        # Connect the tray icon activation to a function
        self.tray_icon.activated.connect(self.on_tray_icon_activated)


    def update_dock_icon_policy(self):
        """Update the dock icon based on the current window state (macOS specific)."""
        if sys.platform == "darwin":
            app = NSApplication.sharedApplication()
            if not self.isVisible():
                app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # Hide from dock if hidden
            else:
                app.setActivationPolicy_(NSApplicationActivationPolicyRegular)  # Show in dock if visible

    def showEvent(self, event):
        """Ensure dock icon updates when the window is shown (macOS specific)."""
        super().showEvent(event)
        if sys.platform == "darwin":
            self.update_dock_icon_policy()

    def hideEvent(self, event):
        """Ensure dock icon updates when the window is hidden (macOS specific)."""
        super().hideEvent(event)
        if sys.platform == "darwin":
            self.update_dock_icon_policy()

    def closeEvent(self, event):
        """Override close event to minimize to tray instead of closing."""
        event.ignore()  # Ignore the close event to prevent application from closing
        self.hide()  # Hide the window to the tray instead
        self.tray_icon.showMessage(
            "Tray Application",
            "Application minimized to tray. Click the tray icon to restore.",
            QSystemTrayIcon.Information,
            2000
        )
        if sys.platform == "darwin":
            self.update_dock_icon_policy()  # Update the dock icon visibility

    def show_window(self):
        """Show the window when the 'Open' option in tray is clicked."""
        self.show()
        self.raise_()
        self.activateWindow()
        if sys.platform == "darwin":
            self.update_dock_icon_policy()
        self.showNormal()  # Restore the window from minimized state if minimized

    def quit_application(self):
        """Quit the application gracefully."""
        from sd_core.util import stop_server  # Import the stop_server function
        stop_server()
        QApplication.quit()

    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()  # Show the window when the tray icon is clicked

    def changeEvent(self, event):
        """Handle window state changes to adjust the look and feel."""
        if event.type() == QEvent.WindowStateChange:
            if self.isActiveWindow():
                self.setStyleSheet("background-color: white;")
            else:
                self.setStyleSheet("background-color: lightgray;")
        super(MainWindow, self).changeEvent(event)

    # =========================================================================================
    # Open2

    def show_login_menu(self):
        """Show the login menu with checkboxes for schedule days."""
        if self.expanded_menu is None:
            self.expanded_menu = QMenu("Logged In Menu", self.menu)

            # Add sub-actions
            open_dashboard_action = QAction("Open Dashboard", self)
            launch_on_start_action = QAction("Launch on Start", self)
            idle_time_action = QAction("Idle Time", self)
            quit_action = QAction("Quit", self)

            # Add schedule submenu
            schedule_menu = QMenu("Schedule", self.expanded_menu)
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            self.schedule_checkboxes = {}
            for day in days_of_week:
                checkbox_action = QWidgetAction(schedule_menu)
                checkbox = QCheckBox(day)
                checkbox_action.setDefaultWidget(checkbox)
                schedule_menu.addAction(checkbox_action)
                self.schedule_checkboxes[day] = checkbox 
                # Optional: Connect checkbox state changes to a function
                checkbox.stateChanged.connect(lambda state, d=day: self.handle_checkbox_state(d, state))
            
            save_action = QWidgetAction(schedule_menu)
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_schedule_settings)
            save_action.setDefaultWidget(save_button)
            schedule_menu.addAction(save_action)

            weekdays_schedule = self.retrieve.get('weekdays_schedule', {})
            logger.info(f"Weekdys_schedule====> {weekdays_schedule}")

            pre_launch = self.retrieve.get('launch', False)
            pre_idle = self.retrieve.get('idle_time', False)

            for day, is_checked in weekdays_schedule.items():
                if day in self.schedule_checkboxes:
                    self.schedule_checkboxes[day].setChecked(is_checked)

            launch_on_start_action.setCheckable(True)  # Make it checkable
            idle_time_action.setCheckable(True)

            launch_on_start_action.setChecked(pre_launch)
            idle_time_action.setChecked(pre_idle)

            # Add actions to the expanded menu
            self.expanded_menu.addMenu(schedule_menu)
            self.expanded_menu.addAction(open_dashboard_action)
            self.expanded_menu.addAction(launch_on_start_action)
            self.expanded_menu.addAction(idle_time_action)
            self.expanded_menu.addAction(quit_action)

            # Event handling for the new actions
            open_dashboard_action.triggered.connect(self.open_dashboard)
            launch_on_start_action.triggered.connect(self.start_up_status)
            idle_time_action.triggered.connect(self.set_idle_time)
            quit_action.triggered.connect(self.quit_application)
            
            self.tray_icon.setContextMenu(self.expanded_menu)

            # Replace the "Login" action with the expanded menu
            self.menu.clear()
            self.menu.addMenu(self.expanded_menu)

    def save_schedule_settings(self):
        """Collect the state of schedule checkboxes and save settings."""
        schedule_data = {day: checkbox.isChecked() for day, checkbox in self.schedule_checkboxes.items()}
        print("Schedule settings to save:", schedule_data)
        # You can serialize the schedule_data to save it
        add_settings("weekdays_schedule", schedule_data)
        
    def handle_checkbox_state(self, day, state):
        """Handle state change for schedule checkboxes."""
        state_text = "checked" if state == QtCore.Qt.Checked else "unchecked"
        print(f"{day} is {state_text}.")

    def start_up_status(self, state):
        # status = "start" if self.start_up_checkbox.isChecked() else "stop"
        print("STATE============> " + str(state))
        status = 'start'
        if state == True:
            status = 'start'
        else:
            status = 'stop'
        self.launch_on_start(status)

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
    
    def open_dashboard(self):
        self.show_message("Opening Dashboard (Placeholder).")

    def set_idle_time(self, state):
        status = 'start'
        if state == True:
            status = 'start'
        else:
            status = 'stop'
        self._update_idletime_status(status)

    def _update_idletime_status(self, status):
        params = {"status": status}
        creds = credentials()
        if creds and "token" in creds:
            self._send_request("/0/idletime", creds["token"], params)

    def _send_request(self, endpoint, token, params):
        try:
            response = requests.get(
                self.host + endpoint,
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            if response.status_code == 200:
                print(f"{endpoint} updated successfully")
            else:
                print(f"Failed to update {endpoint}: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            print(f"An error occurred while sending the request: {e}")

    def show_message(self, message):
        """Display a message to the user."""
        QMessageBox.information(None, "Information", message)


def run_application():
    # Start the timer to measure load time
    start_time = time.time()

    format = QSurfaceFormat()
    format.setVersion(3, 3)  # Example: OpenGL version 3.3
    format.setProfile(QSurfaceFormat.CoreProfile)  # Use the core profile
    QSurfaceFormat.setDefaultFormat(format)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Stop the timer after the window is shown
    end_time = time.time()
    load_time = end_time - start_time
    print(f"Application load time: {load_time:.2f} seconds")

    sys.exit(app.exec())

if __name__ == "__main__":
    run_application()
