import json
import os
import sys
import threading
import time
from datetime import datetime

import pytz
import requests
from PySide6 import QtGui, QtCore
from PySide6.QtCore import QRect, Qt, QSize, QPropertyAnimation, QTimer, QTime, Signal, QRunnable
from PySide6.QtGui import QPixmap, QCursor, QColor, QFont, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QStackedWidget, QSpacerItem, \
    QSizePolicy, QButtonGroup, QGraphicsOpacityEffect, QTimeEdit, QGraphicsDropShadowEffect, QScrollArea
from deepdiff import DeepDiff

from sd_qt.sd_desktop.ThemeManager import ThemeManager
from sd_qt.sd_desktop.checkBox import CustomCheckBox
from sd_qt.sd_desktop.toggleSwitch import SwitchControl
from sd_qt.sd_desktop.util import retrieve_settings, credentials, add_settings, get_events

base_path = os.path.abspath(os.path.join(__file__, "../../.."))
resources_path = os.path.join(base_path, "sd_qt", "sd_desktop", "resources")

darkTheme = os.path.join(resources_path, "DarkTheme")
lightTheme = os.path.join(resources_path, "LightTheme")

host = "http://localhost:7600/api"

class TransparentLabel(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoFillBackground(False)
        # Set the stylesheet here to make the background transparent and customize the text color
        self.setStyleSheet("""
            background-color: transparent;
        """)


# Worker class for background loading using QRunnable
class PageLoaderRunnable(QRunnable):
    def __init__(self, page_name, page_index, callback):
        super().__init__()
        self.page_name = page_name
        self.page_index = page_index
        self.callback = callback

    def run(self):
        # Simulate lightweight background loading
        self.callback(self.page_name, self.page_index)


class Dashboard(QWidget):
    signout_signal = Signal()

    def __init__(self, signout):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_Changed.connect(self.change_theme)
        self.signout = signout

        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.setupSidebar()
        self.horizontalLayout.addWidget(self.sidebar)

        self.setupStack()
        self.horizontalLayout.addWidget(self.stackedWidget)

        # Automatically load all pages once when the Dashboard is initialized
        self.startBackgroundPageLoading()

    def setupSidebar(self):
        self.sidebar = QWidget(parent=self)
        self.sidebar.setFixedSize(QSize(220, 600))

        self.verticalLayout_2 = QVBoxLayout(self.sidebar)
        self.verticalLayout_2.setContentsMargins(0, 20, 0, 0)

        # Logo Widget
        self.AppLogo = QSvgWidget(parent=self.sidebar)
        self.AppLogo.setFixedSize(QSize(200,50))
        self.label = TransparentLabel(parent=self.AppLogo)
        self.label.setGeometry(10, 0, 150, 50)
        self.verticalLayout_2.addWidget(self.AppLogo)

        # Top Button Widget
        self.top_buttons_widget = QWidget(parent=self.sidebar)
        self.top_buttons_layout = QVBoxLayout(self.top_buttons_widget)
        self.top_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.top_buttons_layout.setSpacing(2)

        button_height = 40
        activities_button = self.createSidebarButton("Activities", "/Activity.svg", button_height, "Activities", 0)
        activities_button.setChecked(True)  # Set the "Activities" button as checked by default

        settings_button = self.createSidebarButton("General settings", "/generalSettings.svg", button_height,
                                                   "GeneralSettings", 1)
        schedule_button = self.createSidebarButton("Schedule", "/schedule.svg", button_height, "Schedule", 2)

        self.button_group.addButton(activities_button)
        self.button_group.addButton(settings_button)
        self.button_group.addButton(schedule_button)

        self.top_buttons_layout.addWidget(activities_button)
        self.top_buttons_layout.addWidget(settings_button)
        self.top_buttons_layout.addWidget(schedule_button)
        self.verticalLayout_2.addWidget(self.top_buttons_widget)

        # Spacer
        self.verticalLayout_2.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom Button Widget
        self.bottom_buttons_widget = QWidget(parent=self.sidebar)
        self.bottom_buttons_layout = QVBoxLayout(self.bottom_buttons_widget)
        self.bottom_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_buttons_layout.setSpacing(2)

        profile_button = self.createSidebarButton("Profile settings", "/light_user_icon.svg", button_height, "UserProfile",
                                                  3)
        signout_button = self.createSidebarButton("Sign out", "/signout.svg", button_height, "SignOut", -1)
        self.change_theme_button = self.createButton("Change Theme", "", button_height)

        self.change_theme_button.clicked.connect(self.theme_manager.switch_theme)
        signout_button.clicked.connect(self.signout)

        self.button_group.addButton(profile_button)
        self.button_group.addButton(signout_button)

        self.bottom_buttons_layout.addWidget(profile_button)
        self.bottom_buttons_layout.addWidget(signout_button)
        self.bottom_buttons_layout.addWidget(self.change_theme_button)

        self.bottom_buttons_layout.addItem(QSpacerItem(20, 10))
        self.verticalLayout_2.addWidget(self.bottom_buttons_widget)

    def createSidebarButton(self, text, icon_path, height, page_name, page_index):
        button = QPushButton(text)
        button.setFixedHeight(height)
        button.setCursor(QCursor(Qt.PointingHandCursor))

        # Apply icon if provided
        if icon_path:
            icon_label = TransparentLabel(parent=button)
            icon_label.setGeometry(20, 10, 30, 22)
            icon_label.setPixmap(QPixmap(resources_path + icon_path))
            icon_label.setStyleSheet("background:transparent")

        button.setStyleSheet(self.getButtonStyleSheet())
        button.setCheckable(True)
        button.clicked.connect(lambda: self.onButtonClicked(page_index))
        return button

    def createButton(self, text, icon_path, height):
        button = QPushButton(text)
        button.setFixedHeight(height)
        button.setCursor(QCursor(Qt.PointingHandCursor))

        # Create an icon label if an icon path is provided
        icon_label = None
        if icon_path:
            icon_label = TransparentLabel(parent=button)
            icon_label.setGeometry(20, 10, 40, 40)  # Adjust the size and position as needed
            pixmap = QPixmap(darkTheme + icon_path)
            pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setStyleSheet("background:transparent")
            button.icon_label = icon_label  # Store reference to the icon label

        button.setStyleSheet(self.ButtonStyleSheet())

        # Add methods for changing text and icon dynamically
        def set_button_text(new_text):
            button.setText(new_text)

        def set_button_icon(new_icon_path):
            if hasattr(button, 'icon_label') and button.icon_label:
                pixmap = QPixmap(darkTheme + new_icon_path)
                pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                button.icon_label.setPixmap(pixmap)

        # Attach methods to the button instance
        button.set_text = set_button_text
        button.set_icon = set_button_icon

        return button

    def getButtonStyleSheet(self):
        theme = self.theme_manager.get_theme()
        button_background = "rgba(29, 11, 119, 0.2)" if theme == "dark" else "#F4F2FE"
        checked_text_color = "#A49DC8" if theme == "dark" else "#1D0B77"
        text_color = "#FFFFFF" if theme == "dark" else "#000000"

        return f"""
            QPushButton {{
                border: none;
                padding-left: 10px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: {button_background};
                color: {checked_text_color};
            }}
            QPushButton:checked {{
                background-color: {button_background};
                color: {checked_text_color};
            }}
        """

    def ButtonStyleSheet(self):
        theme = self.theme_manager.get_theme()
        button_background = "rgba(29, 11, 119, 0.2)" if theme == "dark" else "#F4F2FE"
        checked_text_color = "#A49DC8" if theme == "dark" else "#1D0B77"
        text_color = "#FFFFFF" if theme == "dark" else "#000000"

        return f"""
            QPushButton {{
                border: none;
                padding-left: 10px;
                color: {text_color};
            }}
        """


    def loadPage(self, page_name, page_index):
        """Sets the current page without reloading it."""
        if page_name in self.pages and self.pages[page_name] is not None:
            self.stackedWidget.setCurrentIndex(page_index)
        else:
            print(f"Error: Page '{page_name}' not loaded.")

    def setupStack(self):
        self.stackedWidget = QStackedWidget(parent=self)
        self.stackedWidget.setContentsMargins(0, 0, 0, 0)

        # Dictionary for page references (lazy loading)
        self.pages = {'Activities': None, 'GeneralSettings': None, 'Schedule': None, 'UserProfile': None}
        self.loadPage('Activities', 0)  # Load the initial page

        # Connect the theme change event
        self.stackedWidget.currentChanged.connect(self.change_theme)

    def startBackgroundPageLoading(self):
        pages_to_preload = [('Activities', 0), ('GeneralSettings', 1), ('Schedule', 2), ('UserProfile', 3)]
        for page_name, page_index in pages_to_preload:
            self.loadPageInBackground(page_name, page_index)

    def loadPageInBackground(self, page_name, page_index):
        """Perform minimal work in the slot to avoid UI blocking."""
        if self.pages[page_name] is None:
            self.initPageLoading(page_name, page_index)

    def initPageLoading(self, page_name, page_index):
        start_time = time.time()  # Start timing

        if page_name == 'Activities':
            self.pages['Activities'] = ActivitiesPage(self.theme_manager)
            self.stackedWidget.addWidget(self.pages['Activities'])
        elif page_name == 'GeneralSettings':
            self.pages['GeneralSettings'] = GeneralSettingsWidget()
            self.stackedWidget.addWidget(self.pages['GeneralSettings'])
        elif page_name == 'Schedule':
            self.pages['Schedule'] = SchedulePage()
            self.stackedWidget.addWidget(self.pages['Schedule'])
        elif page_name == 'UserProfile':
            self.pages['UserProfile'] = UserProfileDrawer()
            self.stackedWidget.addWidget(self.pages['UserProfile'])

        end_time = time.time()  # End timing
        load_time = end_time - start_time

    def onButtonClicked(self, page_index):
        self.stackedWidget.setCurrentIndex(page_index)

    def change_theme(self):
        theme = self.theme_manager.get_theme()
        stacked_widget_background, app_logo = self.getThemeColors(theme)

        self.stackedWidget.setStyleSheet(f"background-color: {stacked_widget_background};")
        self.sidebar.setStyleSheet(f"background-color: {stacked_widget_background};")
        self.label.setPixmap(QPixmap(app_logo))
        self.label.setScaledContents(True)
        self.label.setStyleSheet("margin-top:10px")

        # Update button styles
        for button in self.button_group.buttons():
            button.setStyleSheet(self.getButtonStyleSheet())

        self.change_theme_button.setStyleSheet(self.ButtonStyleSheet())
        self.change_theme_button.set_text("Light Theme" if theme == "dark" else "Dark Theme")
        self.change_theme_button.set_icon(
            os.path.join(darkTheme, "dark_theme.svg") if theme == "dark" else os.path.join(lightTheme,
                                                                                           "light_theme.svg"))


        current_page = self.stackedWidget.currentWidget()
        if current_page:
            theme_settings = self.getThemeSettings(theme, type(current_page).__name__)
            current_page.change_theme(theme_settings)

    def getThemeColors(self, theme):
        if theme == "dark":
            return "#000000", os.path.join(darkTheme, "dark_signin_logo.svg")
        return "#FFFFFF", os.path.join(lightTheme, "Sundial_homepage.svg")

    def getThemeSettings(self, theme, page_type):
        common_settings = {
            "date_background": "#171717" if theme == "dark" else "#EFEFEF",
            "container_background": "#171717" if theme == "dark" else "#F9F9F9",
            "scroll_background": "#101010" if theme == "dark" else "#F9F9F9",
            "version_text_color": "white" if theme == "dark" else "black",
            "checkbox_color": "#010101" if theme == "dark" else "#FFFFFF",
            "info_icon": os.path.join(darkTheme, "info_icon.svg") if theme == "dark" else os.path.join(lightTheme,
                                                                                                       "info.svg"),
            "user_profile" : os.path.join(darkTheme, "TTim_user.svg") if theme == "dark" else os.path.join(lightTheme,"TTim_user.svg")
        }
        page_specific_settings = {
            "ActivitiesPage": common_settings,
            "GeneralSettingsWidget": common_settings,
            "SchedulePage": {"container_background": common_settings["container_background"],
                             "info_icon": common_settings["info_icon"]},
            "UserProfileDrawer": {
                "container_background": common_settings["container_background"],
                "userprofile": "#000000" if theme == "dark" else "#FFFFFF",
                "user_profile": common_settings["user_profile"]
            },
        }
        return page_specific_settings.get(page_type, common_settings)


class ActivitiesPage(QWidget):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.displayed_events = set()
        self.current_index = 0
        self.scrollAreaWidgetContents = QWidget()

        # Connect theme change signal to style update method
        self.theme_manager.theme_Changed.connect(self.update_events_style)

        # Set up a timer for periodic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.add_dynamic_blocks)
        self.timer.start(30000)  # Update every 30 seconds

        # Initialize UI components
        self.init_ui()

    def init_ui(self):
        # Header for the Activities page
        self.Activites_header = TransparentLabel("Activities", self)
        self.Activites_header.setGeometry(10, 15, 191, 40)
        font = QtGui.QFont()
        font.setPointSize(20 if sys.platform == "darwin" else 16)
        font.setWeight(QtGui.QFont.Weight.Bold)
        self.Activites_header.setFont(font)

        # Date display widget
        self.Date_display = QWidget(self)
        self.Date_display.setGeometry(10, 70, 560, 51)

        self.Day = TransparentLabel("Today", self.Date_display)
        self.Day.setGeometry(22, 15, 58, 20)
        font.setPointSize(14 if sys.platform == "darwin" else 10)
        self.Day.setFont(font)

        # Scroll area for event blocks
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setGeometry(10, 120, 560, 460)
        self.scrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents.setGeometry(0, 0, 560, 460)
        self.main_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.main_layout.setContentsMargins(12, 5, 10, 5)

        # Set the alignment to align items at the top
        self.main_layout.setAlignment(Qt.AlignTop)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

    def add_dynamic_blocks(self):
        event_data = get_events()
        # Add new events to the layout
        if event_data:
            for event in event_data:
                if event['id'] not in self.displayed_events:
                    color = self.get_next_color()
                    event_widget = self.create_event_widget(event, color)
                    self.main_layout.addWidget(event_widget)
                    self.displayed_events.add(event['id'])

        self.update_events_style()  # Apply theme styles

    def listView(self, events):
        list_view_events = []
        local_tz = datetime.now().astimezone().tzinfo

        for event in events:
            start_time_utc = datetime.strptime(
                event['start'], "%Y-%m-%dT%H:%M:%SZ")
            end_time_utc = datetime.strptime(event['end'], "%Y-%m-%dT%H:%M:%SZ")

            start_time_local = start_time_utc.replace(
                tzinfo=pytz.utc).astimezone(local_tz).strftime("%H:%M")
            end_time_local = end_time_utc.replace(
                tzinfo=pytz.utc).astimezone(local_tz).strftime("%H:%M")

            formatted_event = {
                'time': f"{start_time_local} - {end_time_local}", 'app': event['title'], 'id': event['id'], }
            list_view_events.append(formatted_event)
        return list_view_events

    def create_event_widget(self, event, color):
        event_widget = QWidget(self.scrollAreaWidgetContents)
        event_widget.setFixedSize(525, 60)

        # Store colors as properties on the widget
        event_widget.setProperty('light_color', color['light_color'])
        event_widget.setProperty('dark_color', color['dark_color'])

        application_name = TransparentLabel(event_widget)
        application_name.setGeometry(17, 15, 420, 30)
        truncated_text = self.truncate_text(event['app'], 50)
        application_name.setText(truncated_text)
        if len(event['app']) > 50:
            application_name.setToolTip(event['app'])

        time_label = TransparentLabel(event_widget)
        time_label.setGeometry(425, 15, 261, 30)
        time_label.setText(event['time'])

        return event_widget

    def update_events_style(self):
        current_theme = self.theme_manager.get_theme()
        for event_widget in self.scrollAreaWidgetContents.findChildren(QWidget):
            light_color = event_widget.property('light_color')
            dark_color = event_widget.property('dark_color')

            # Choose color based on theme
            bg_color = dark_color if current_theme == 'dark' else light_color
            text_color = "white" if current_theme == 'dark' else "black"

            stylesheet = (
                "QWidget {"
                f"background-color: {bg_color};"
                "border-radius: 5px;"
                f"color: {text_color};"
                "}"
            )
            event_widget.setStyleSheet(stylesheet)

    def truncate_text(self, text, max_length):
        return text[:max_length] + "..." if len(text) > max_length else text

    def get_next_color(self):
        light_colors = [
            "#F5E9DA", "#E8C6E6", "#CDC8EF", "#C0D8EC", "#C8E0FF", "#E2F0D6"
        ]
        dark_colors = [
            "#443C32", "#271726", "#29263B", "#0E1E2B", "#111D2C", "#20261B"
        ]

        colors = {
            "light_color": light_colors[self.current_index % len(light_colors)],
            "dark_color": dark_colors[self.current_index % len(dark_colors)]
        }
        self.current_index = (self.current_index + 1) % len(light_colors)
        return colors

    def get_credentials(self):
        try:
            return credentials()  # Assumes a function returning credentials
        except Exception as e:
            print(f"Error retrieving credentials: {e}")
            return None

    def change_theme(self, theme_settings):
        self.Date_display.setStyleSheet(f"""
                        background-color: {theme_settings.get("date_background")};
                        border-top-left-radius: 10px;
                        border-top-right-radius: 10px;
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                    """)
        self.scrollArea.setStyleSheet(f"""
                        border: None;
                        background-color: {theme_settings.get("scroll_background")};
                        border-bottom-left-radius: 10px;
                        border-bottom-right-radius: 10px;
                    """)
        self.Day.setStyleSheet("background: transparent;")
        self.scrollArea.verticalScrollBar().setStyleSheet(f"""
                        QScrollBar:vertical {{
                            background: {theme_settings.get("scroll_background")};
                            width: 5px;
                            margin: 0px 0px 0px 0px;
                            border-radius: 5px;
                        }}
                        QScrollBar::handle:vertical {{
                            background: #B0B0B0;
                            min-height: 20px;
                            border-radius: 5px;
                        }}
                        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                            height: 0px;
                            width: 0px;
                        }}
                        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                            background: none;
                        }}
                        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                            background: none;
                        }}
                    """)


class GeneralSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.GeneralSettings_header = TransparentLabel(parent=self)
        self.GeneralSettings_header.setGeometry(QRect(10, 15, 300, 44))
        font = QtGui.QFont()
        font.setWeight(QtGui.QFont.Weight.Bold)
        font.setPointSize(20 if sys.platform == "darwin" else 16)
        self.GeneralSettings_header.setFont(font)
        self.GeneralSettings_header.setText("General settings")

        # Setup sections
        self._setup_startup_section()
        self._setup_idletime_section()
        self._setup_version_section()
        self.load_settings()

    def load_settings(self):
        settings = retrieve_settings()

        # Check if settings were retrieved correctly
        if not isinstance(settings, dict):
            print("Error: Settings data is not a dictionary.")
            return

        try:
            # Disconnect signals temporarily
            self.startup_checkbox.stateChanged.disconnect(self._on_startup_status_change)
            self.idletime_checkbox.stateChanged.disconnect(self._on_idletime_status_change)

            # Set the initial state
            self.startup_checkbox.setChecked(settings.get('launch', False))
            self.idletime_checkbox.setChecked(settings.get('idle_time', False))

        except TypeError:
            # Handle cases where disconnect might raise an error if the signal was not connected
            pass

        finally:
            # Reconnect the signals
            self.startup_checkbox.stateChanged.connect(lambda: threading.Thread(target=self._on_startup_status_change).start())
            self.idletime_checkbox.stateChanged.connect(lambda:  threading.Thread(target=self._on_idletime_status_change).start())

    def _setup_startup_section(self):
        self.startup = QWidget(parent=self)
        self.startup.setGeometry(QRect(10, 70, 550, 80))

        # Startup label
        self.startup_label = TransparentLabel(parent=self.startup)
        self.startup_label.setGeometry(QRect(20, 30, 300, 16))
        self.startup_label.setText("Launch Sundial on system startup")
        font = QtGui.QFont()
        font.setPointSize(14 if sys.platform == "darwin" else 10)
        self.startup_label.setFont(font)

        # Startup checkbox
        self.startup_checkbox = SwitchControl(
            self.startup,
            bg_color="#888888",
            circle_color="#FFFFFF",
            active_color="#FFA500",
            animation_duration=300
        )
        self.startup_checkbox.setGeometry(QRect(490, 30, 80, 21))
        self.startup_checkbox.stateChanged.connect(self._on_startup_status_change)

    def _setup_idletime_section(self):
        self.idletime = QWidget(parent=self)
        self.idletime.setGeometry(QRect(10, 160, 550, 80))

        # Idle time label
        self.idletime_label = TransparentLabel(parent=self.idletime)
        self.idletime_label.setGeometry(QRect(20, 30, 211, 16))
        self.idletime_label.setText("Enable idle time detection")
        font = QtGui.QFont()
        font.setPointSize(14 if sys.platform == "darwin" else 10)
        self.idletime_label.setFont(font)

        # Idle time checkbox
        self.idletime_checkbox = SwitchControl(
            self.idletime,
            bg_color="#888888",
            circle_color="#FFFFFF",
            active_color="#FFA500",
            animation_duration=300
        )
        self.idletime_checkbox.setGeometry(QRect(490, 30, 100, 21))
        self.idletime_checkbox.stateChanged.connect(self._on_idletime_status_change)

    def _setup_version_section(self):
        self.Version_2 = QWidget(parent=self)
        self.Version_2.setGeometry(QRect(10, 250, 550, 130))

        # Update header
        self.update_header = TransparentLabel(parent=self.Version_2)
        self.update_header.setGeometry(QRect(20, 20, 311, 16))
        font = QtGui.QFont()
        font.setPointSize(14 if sys.platform == "darwin" else 10)
        font.setWeight(QtGui.QFont.Weight.Bold)
        self.update_header.setFont(font)
        self.update_header.setText("Update")

        # Update description
        font.setPointSize(14 if sys.platform == "darwin" else 8)
        self.update_description = TransparentLabel(parent=self.Version_2)
        self.update_description.setGeometry(QRect(20, 50, 311, 16))
        self.update_description.setFont(font)
        self.update_description.setText("Your Sundial application is up to date")

        # Display current version
        self.current_version = TransparentLabel(parent=self.Version_2)
        self.current_version.setGeometry(QRect(20, 80, 311, 20))
        self.current_version.setFont(font)

        # Toast message setup
        self.startup_toast_message = QWidget(parent=self)
        self.startup_toast_message.setGeometry(QRect(830, 520, 350, 60))
        self.startup_toast_label = TransparentLabel(self.startup_toast_message)
        self.startup_toast_label.setGeometry(QRect(20, 10, 330, 40))
        font.setPointSize(14 if sys.platform == "darwin" else 12)
        self.startup_toast_label.setFont(font)
        self.startup_toast_message.setStyleSheet("border-radius: 10px; background-color:#BFF6C3")
        self.startup_toast_message.setVisible(False)

        # Animation setup for sliding in the toast message
        self.toast_animation = QPropertyAnimation(self.startup_toast_message, b"geometry")
        self.toast_animation.setDuration(500)
        self.toast_animation.setStartValue(QRect(830, 520, 350, 60))
        self.toast_animation.setEndValue(QRect(220, 520, 350, 60))
        self.toast_animation.setEasingCurve(QtCore.QEasingCurve.OutBounce)

    def show_toast_message(self, message):
        self.startup_toast_label.setText(message)
        self.startup_toast_message.setVisible(True)
        self.toast_animation.start()
        QTimer.singleShot(3000, self.hide_toast_message)

    def hide_toast_message(self):
        self.startup_toast_message.setVisible(False)

    def _on_startup_status_change(self):
        status = "start" if self.startup_checkbox.isChecked() else "stop"
        self._update_startup_status(status)

    def _on_idletime_status_change(self):
        status = "start" if self.idletime_checkbox.isChecked() else "stop"
        self._update_idletime_status(status)

    def _update_startup_status(self, status):
        params = {"status": status}
        creds = credentials()
        if creds and "token" in creds:
            self._send_request("/0/launchOnStart", creds["token"], params)

    def _update_idletime_status(self, status):
        params = {"status": status}
        creds = credentials()
        if creds and "token" in creds:
            self._send_request("/0/idletime", creds["token"], params)

    def _send_request(self, endpoint, token, params):
        try:
            response = requests.get(
                host + endpoint,
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            if response.status_code == 200:
                print(f"{endpoint} updated successfully")
            else:
                print(f"Failed to update {endpoint}: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            print(f"An error occurred while sending the request: {e}")

    def change_theme(self, theme_settings):
        self.startup_checkbox.set_circle_color(theme_settings.get('checkbox_color'))
        self.idletime_checkbox.set_circle_color(theme_settings.get('checkbox_color'))
        self.startup.setStyleSheet(
            f"border-radius: 10px; background-color: {theme_settings.get('container_background')};")
        self.idletime.setStyleSheet(
            f"border-radius: 10px; background-color: {theme_settings.get('container_background')};")
        self.Version_2.setStyleSheet(
            f"border-radius: 10px; background-color: {theme_settings.get('container_background')};")
        self.current_version.setText(
            f'<span style="color: rgba(71, 75, 79, 1);">Current app version: </span>'
            f'<span style="color: {theme_settings.get("version_text_color")}; background:transparent;">2.0.0_beta</span>'
        )


class SchedulePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)
        self.checkbox = CustomCheckBox()
        self.week_schedule = {
            'Monday': True, 'Tuesday': True, 'Wednesday': True, 'Thursday': True,
            'Friday': True, 'Saturday': True, 'Sunday': True,
            'starttime': '00:00', 'endtime': '23:59'
        }
        self.default_week_schedule = self.week_schedule.copy()
        self.settings = retrieve_settings()
        self.previous_schedule = self.settings.get('weekdays_schedule', {})
        self.setupLabelsAndFonts()
        self.setupScheduleEnabler()
        self.setupDayWidget()
        self.setupButtons()
        self.applySettingsAndStyle()

    def setupLabelsAndFonts(self):
        font_bold = QFont()
        font_bold.setWeight(QFont.Weight.Bold)

        # Schedule Label
        self.Schedule_label = TransparentLabel("Schedule", self)
        self.Schedule_label.setGeometry(10, 15, 131, 44)
        font_bold.setPointSize(20 if sys.platform == "darwin" else 16)
        self.Schedule_label.setFont(font_bold)

    def setupScheduleEnabler(self):
        # Schedule Enabler Section
        self.Schedule_enabler = QWidget(self)
        self.Schedule_enabler.setGeometry(10, 70, 550, 80)

        # Enabler Label
        label_font = QFont()
        label_font.setPointSize(14 if sys.platform == "darwin" else 10)
        self.Schedule_enabler_label = TransparentLabel("Record data only during my scheduled work hours.", self.Schedule_enabler)
        self.Schedule_enabler_label.setGeometry(20, 30, 360, 20)
        self.Schedule_enabler_label.setFont(label_font)

        # Enabler Checkbox
        self.Schedule_enabler_checkbox = SwitchControl(
            self.Schedule_enabler,
            bg_color="#888888",
            circle_color="#FFFFFF",
            active_color="#FFA500",
            animation_duration=300
        )
        self.Schedule_enabler_checkbox.setGeometry(490, 30, 100, 21)
        self.Schedule_enabler_checkbox.stateChanged.connect(self.toggle_schedule_visibility)

    def setupDayWidget(self):
        # Day Widget for schedule settings
        self.day_widget = QWidget(self)
        self.day_widget.setGeometry(10, 154, 550, 300)

        self.toggle_schedule_visibility()
        font_bold = QFont()
        font_bold.setWeight(QFont.Weight.Bold)
        font_bold.setPointSize(16 if sys.platform == "darwin" else 12)

        # Working Days Label
        self.Working_days_label = TransparentLabel("Working days", self.day_widget)
        self.Working_days_label.setGeometry(20, 20, 200, 20)
        self.Working_days_label.setFont(font_bold)

        # Info Message
        self.info_message = QWidget(self.day_widget)
        self.info_message.setGeometry(120, 45, 400, 130)
        self.info_message.setVisible(False)

        info_label_font = QFont()
        info_label_font.setWeight(QFont.Weight.Bold)
        info_label_font.setPointSize(14 if sys.platform == "darwin" else 8)
        self.info_message_label = TransparentLabel("Schedule Info", self.info_message)
        self.info_message_label.setGeometry(15, 15, 380, 20)
        self.info_message_label.setFont(info_label_font)

        self.info_message_des = TransparentLabel(
            "Please be aware that this update will affect all future events. Any activities that were previously recorded outside of scheduled times will remain visible in your activities list.", self.info_message
        )
        self.info_message_des.setGeometry(15, 50, 380, 60)
        self.info_message_des.setWordWrap(True)

        shadow = QGraphicsDropShadowEffect(self.info_message)
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.info_message.setGraphicsEffect(shadow)

        # Info Icon Button
        self.info_icon = QPushButton(parent=self.day_widget)
        self.info_icon.setGeometry(140, 20, 20, 20)
        self.info_icon.clicked.connect(self.show_message)
        self.info_icon.setIconSize(QSize(20, 20))

        # Time Selection
        self.Working_hours_label = TransparentLabel("Working hours", self.day_widget)
        self.Working_hours_label.setGeometry(20, 140, 200, 20)
        self.Working_hours_label.setFont(font_bold)

        self.From_time = QTimeEdit(self.day_widget)
        self.From_time.setGeometry(20, 180, 250, 40)
        self.From_time.setDisplayFormat("hh:mm")

        self.To_time = QTimeEdit(self.day_widget)
        self.To_time.setGeometry(285, 180, 250, 40)
        self.To_time.setDisplayFormat("hh:mm")

        self.setupScheduleCheckboxes()

    def setupScheduleCheckboxes(self):
        days = [
            {"name": "Monday", "x": 20, "y": 58},
            {"name": "Tuesday", "x": 160, "y": 58},
            {"name": "Wednesday", "x": 300, "y": 58},
            {"name": "Thursday", "x": 440, "y": 58},
            {"name": "Friday", "x": 20, "y": 98},
            {"name": "Saturday", "x": 160, "y": 98},
            {"name": "Sunday", "x": 300, "y": 98}
        ]

        font = QFont()
        font.setPointSize(14 if sys.platform == "darwin" else 10)

        # Assuming ThemeManager instance is accessible as self.theme_manager
        theme_manager = ThemeManager()

        for day in days:
            checkbox = CustomCheckBox(parent=self.day_widget)
            checkbox.setGeometry(day["x"], day["y"], 40, 40)

            label = TransparentLabel(day["name"], parent=self.day_widget)
            label.setGeometry(day["x"] + 30, day["y"] - 8, 110, 40)
            label.setFont(font)

            day_name_lower = day['name'].lower()
            setattr(self, f"{day_name_lower}_checkbox", checkbox)
            setattr(self, f"{day_name_lower}_label", label)

            # Connect theme change signal to the checkbox's change_theme method
            theme_manager.theme_Changed.connect(checkbox.change_theme)

            # Ensure checkbox updates save button state when changed
            checkbox.stateChanged.connect(self.update_save_button_state)

            # Set initial theme (to load the correct images based on the current theme)
            checkbox.change_theme()

    def setupButtons(self):
        self.Reset = QPushButton("Reset", self.day_widget)
        self.Reset.setGeometry(315, 235, 100, 50)
        self.Reset.clicked.connect(self.resetSchedule)

        self.Save = QPushButton("Save", self.day_widget)
        self.Save.setGeometry(435, 235, 100, 50)
        self.Save.clicked.connect(self.saveSchedule)

        self.From_time.timeChanged.connect(self.update_save_button_state)
        self.To_time.timeChanged.connect(self.update_save_button_state)

    def toggle_schedule_visibility(self):
        self.day_widget.setVisible(self.Schedule_enabler_checkbox.isChecked())
        threading.Thread(target=self.run_add_settings).start()

    def run_add_settings(self):
        add_settings('schedule', self.Schedule_enabler_checkbox.isChecked())

    def resetSchedule(self):
        threading.Thread(target=self.save_schedule_settings, args=(self.default_week_schedule,)).start()
        self.updateCheckboxStates(self.default_week_schedule)

        # Call update_save_button_state() to ensure Save button is properly updated after reset
        self.update_save_button_state()

    def show_message(self):
        self.info_message.setVisible(not self.info_message.isVisible())
        self.info_message.raise_()

    def updateCheckboxStates(self, weekdays):
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            checkbox = getattr(self, f"{day}_checkbox", None)
            if checkbox:
                checkbox.setChecked(weekdays.get(day.capitalize(), False))

        self.From_time.setTime(QTime.fromString(weekdays.get('starttime', "09:30"), "HH:mm"))
        self.To_time.setTime(QTime.fromString(weekdays.get('endtime', "18:30"), "HH:mm"))

    def get_current_schedule(self):
        return {
            day.capitalize(): getattr(self, f"{day}_checkbox").isChecked()
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        } | {
            'starttime': self.From_time.time().toString("HH:mm"),
            'endtime': self.To_time.time().toString("HH:mm")
        }

    def update_save_button_state(self):
        current_schedule = self.get_current_schedule()
        print(f"current_schedule: {current_schedule}")
        print(f"settings:{self.settings}")
        print(f"previous_schedule: {self.previous_schedule}")

        # Check if there are any differences between the current and previous schedule
        schedule_changed = (current_schedule != self.previous_schedule)

        if not schedule_changed or self.check_all_days_false():
            # Disable save button only if the schedule hasn't changed or all days are unchecked
            self.Save.setEnabled(False)
            self.Reset.setEnabled(True)

            # Set styles for disabled Save button
            reset_style = "color:#6A5FA2; border: 1px solid #6A5FA2; border-radius: 5px;"
            save_style = ("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(45,35,100,76), "
                          "stop:1 rgba(90,80,130,76)); border-radius:5px; color:rgba(255,255,255,0.3);")
            self.Reset.setStyleSheet(reset_style)
            self.Save.setStyleSheet(save_style)

            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(0.1)
            self.Save.setGraphicsEffect(opacity_effect)
            self.Reset.setGraphicsEffect(opacity_effect)
        else:
            self.Save.setStyleSheet(
                "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2); border-radius: 5px; color: #FFFFFF; border: 1px solid #1D0B77;")

            self.Save.setEnabled(True)
            self.Reset.setEnabled(True)

    def check_all_days_false(self):
        return not any(getattr(self, f"{day}_checkbox").isChecked() for day in
                       ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])

    def save_schedule_settings(self, schedule):
        self.previous_schedule = schedule
        add_settings('weekdays_schedule', schedule)
        self.settings = retrieve_settings()


    def saveSchedule(self):
        if self.check_all_days_false():
            return

        # Disable the Save button immediately
        self.Save.setEnabled(False)

        # Optionally, update its style to show it as disabled
        save_disabled_style = (
            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(45,35,100,76), "
            "stop:1 rgba(90,80,130,76)); border-radius:5px; color:rgba(255,255,255,0.3);")
        self.Save.setStyleSheet(save_disabled_style)

        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.1)
        self.Save.setGraphicsEffect(opacity_effect)

        # Save the current schedule in a background thread
        week_schedule = self.get_current_schedule()
        save_thread = threading.Thread(target=self.save_schedule_settings, args=(week_schedule,))
        save_thread.start()

    def applySettingsAndStyle(self):
        # Load the saved schedule from settings
        saved_schedule = self.settings.get('weekdays_schedule', self.default_week_schedule)

        # Apply the schedule settings to checkboxes and time fields
        self.updateCheckboxStates(saved_schedule)

        # Set the initial state of the "Record data only during my scheduled work hours" checkbox
        schedule_enabled = self.settings.get('schedule', False)
        self.Schedule_enabler_checkbox.setChecked(schedule_enabled)

        # Update the visibility of the day widget based on the checkbox state
        self.toggle_schedule_visibility()

        # Update the Save button state to reflect the current schedule state
        self.update_save_button_state()

    def change_theme(self, theme_settings):
        self.Schedule_enabler.setStyleSheet(f"""
                        border-top-left-radius: 10px;
                        border-top-right-radius: 10px;
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                        background-color: {theme_settings["container_background"]};
                    """)
        self.day_widget.setStyleSheet(f"""
                        .QWidget {{
                            border-top-left-radius: 0px;
                            border-top-right-radius: 0px;
                            border-bottom-left-radius: 10px;
                            border-bottom-right-radius: 10px;
                            background-color: {theme_settings["container_background"]};
                        }}
                    """)
        self.info_icon.setIcon(QIcon(theme_settings["info_icon"]))
        self.info_icon.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        self.checkbox.change_theme()


class UserProfileDrawer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        QTimer.singleShot(0, self.load_user_details)

        self.profile_header = TransparentLabel(parent=self)
        self.profile_header.setGeometry(QtCore.QRect(10, 15, 300, 44))
        font = QtGui.QFont()
        if sys.platform == "darwin":
            font.setPointSize(20)
        else:
            font.setPointSize(16)
        font.setWeight(QFont.Weight.Bold)
        self.profile_header.setFont(font)
        self.profile_header.setText("Profile Settings")

        font = QtGui.QFont()
        if sys.platform == "darwin":
            font.setPointSize(14)
        else:
            font.setPointSize(10)

        self.profile_container = QWidget(parent=self)
        self.profile_container.setGeometry(QtCore.QRect(10, 70, 550, 140))

        self.profile_image = QWidget(parent=self.profile_container)
        self.profile_image.setGeometry(QtCore.QRect(20, 20, 82, 82))

        self.FirstName = TransparentLabel("Name", parent=self.profile_container)
        self.FirstName.setGeometry(QtCore.QRect(140, 20, 121, 20))
        self.FirstName.setFont(font)

        self.Email = TransparentLabel("Email", parent=self.profile_container)
        self.Email.setGeometry(QtCore.QRect(140, 50, 121, 20))
        self.Email.setFont(font)

        self.mobile = TransparentLabel("Mobile", parent=self.profile_container)
        self.mobile.setGeometry(QtCore.QRect(140, 80, 121, 20))
        self.mobile.setFont(font)

        self.company = TransparentLabel("Company", parent=self.profile_container)
        self.company.setGeometry(QtCore.QRect(140, 110, 121, 20))
        self.company.setFont(font)

        self.first_name_value = TransparentLabel(parent=self.profile_container)
        self.first_name_value.setGeometry(QtCore.QRect(220, 20, 500, 20))
        self.first_name_value.setFont(font)

        self.email_value = TransparentLabel(parent=self.profile_container)
        self.email_value.setGeometry(QtCore.QRect(220, 50, 221, 20))
        self.email_value.setFont(font)

        self.mobile_value = TransparentLabel(parent=self.profile_container)
        self.mobile_value.setGeometry(QtCore.QRect(220, 80, 221, 20))
        self.mobile_value.setFont(font)

        self.company_value = TransparentLabel(parent=self.profile_container)
        self.company_value.setGeometry(QtCore.QRect(220, 110, 500, 20))
        self.company_value.setFont(font)

    def load_user_details(self):
        """Load and display the logged-in user's details."""
        user_details = credentials()  # Replace this with actual data fetching

        if not user_details:
            self.clear_user_detail_fields()
            return

        # Update fields using helper function for consistent UI updates
        self._update_field(self.first_name_value, user_details.get('firstname', ''))
        self._update_field(self.email_value, user_details.get('email', ''))
        self._update_field(self.company_value, user_details.get('companyName', ''))

        # Update mobile directly as tooltip logic isn't required
        self.mobile_value.setText(user_details.get('phone', ''))

        # Refresh UI components to reflect new data
        self._refresh_ui()

    def clear_user_detail_fields(self):
        """Clear user detail fields in the UI."""
        for field in [self.first_name_value, self.email_value, self.mobile_value, self.company_value]:
            field.setText("")
            field.setToolTip("")

    def _update_field(self, widget, text, max_length=30):
        """Helper function to update text and set tooltip if text is truncated."""
        if len(text) > max_length:
            widget.setText(self.ellipsis(text, max_length))
            widget.setToolTip(text)
        else:
            widget.setText(text)
            widget.setToolTip("")

    def _refresh_ui(self):
        """Trigger update to ensure UI components refresh and display updated information."""
        for widget in [self.first_name_value, self.email_value, self.mobile_value, self.company_value]:
            widget.update()

    def ellipsis(self, value, length):
        """Truncate the text to a specified length and add ellipsis if needed."""
        return value[:length] + "..." if len(value) > length else value

    def change_theme(self, theme_settings):
        self.profile_container.setStyleSheet(
            f"border-radius: 10px; background-color: {theme_settings.get('container_background')};")
        self.profile_image.setFixedSize(100, 100)
        self.profile_image.setStyleSheet(f"""
                        border-radius: 50%;
                        background-color: {theme_settings.get("userprofile")};
                        background-image: url({theme_settings.get("user_profile")});
                        background-position: center;
                        background-repeat: no-repeat;
                    """)