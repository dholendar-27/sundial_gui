import os
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from sd_qt.sd_desktop.ThemeManager import ThemeManager


base_path = os.path.abspath(os.path.join(__file__, "../../.."))
resources_path = os.path.join(base_path, "sd_qt", "sd_desktop", "resources")

darkTheme = os.path.join(resources_path, "DarkTheme")
lightTheme = os.path.join(resources_path, "LightTheme")



class CustomCheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(22, 22)
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_Changed.connect(self.change_theme)
        self.tick_icon = None  # Placeholder for tick icon
        self.unchecked_icon = None  # Placeholder for unchecked icon

        # Initialize with default stylesheet
        self.change_theme()

    def change_theme(self):
        # Set the icons based on the current theme
        if self.theme_manager.get_theme() == "dark":
            self.tick_icon = os.path.join(darkTheme, 'checkedbox.svg')
            self.unchecked_icon = os.path.join(darkTheme, 'uncheckedbox.svg')
        else:
            self.tick_icon = os.path.join(lightTheme, 'checkedbox.svg')
            self.unchecked_icon = os.path.join(lightTheme, 'uncheckedbox.svg')

        # Update stylesheet to apply new icons
        self.updateStyleSheet()

    def updateStyleSheet(self):
        """Apply icons in stylesheet dynamically."""
        tick_icon_path = f"url('{self.tick_icon}')" if self.tick_icon else ""
        unchecked_icon_path = f"url('{self.unchecked_icon}')" if self.unchecked_icon else ""

        self.setStyleSheet(f"""
            QCheckBox {{
                background: none;
                border: none;
                width: 22px;
                height: 22px;
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
            }}
            QCheckBox::indicator:checked {{
                image: {tick_icon_path};
            }}
            QCheckBox::indicator:unchecked {{
                image: {unchecked_icon_path};
            }}
        """)



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.checkbox = CustomCheckBox("Custom Checkbox")
        layout.addWidget(self.checkbox)

        # Set dynamic images (replace with actual paths)
        self.checkbox.setTickImage("/Users/pothireddy/Documents/Sundial/v2.0.0/activitywatch/sd-qt/sd_qt/sd_desktop/resources/LightTheme/checkedbox.svg")  # Path to tick image
        self.checkbox.setUncheckedImage("/Users/pothireddy/Documents/Sundial/v2.0.0/activitywatch/sd-qt/sd_qt/sd_desktop/resources/LightTheme/checkbox.svg")  # Path to unchecked image

        self.setLayout(layout)
        self.setWindowTitle("Custom Checkbox Example")
        self.setGeometry(100, 100, 300, 200)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
