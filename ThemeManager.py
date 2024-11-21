import sys
import qdarktheme  # type: ignore
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QSettings, Signal, QObject
from PySide6.QtGui import QPalette, QColor


class ThemeManager(QObject):  # Inherit from QObject
    theme_Changed = Signal(str)  # Define the signal as a class attribute

    def __init__(self):
        super().__init__()
        self.settings = QSettings('ralvie.ai', 'theme')
        self.apply_theme(self.get_theme())
        self.theme_Changed.connect(self.apply_theme)  # Apply theme whenever theme_Changed is emitted

    def set_theme(self, theme: str) -> None:
        self.settings.setValue('theme', theme)
        self.theme_Changed.emit(theme)  # Emit the signal with the theme parameter

    def get_theme(self) -> str:
        return self.settings.value('theme', 'auto')

    def apply_theme(self, theme: str) -> None:
        """
        Apply the selected theme to the application and set background color.
        """
        if theme == "dark":
            qdarktheme.setup_theme("dark")
        elif theme == "light":
            qdarktheme.setup_theme("light")
        else:  # 'auto' mode
            palette = QApplication.instance().palette()
            auto_theme = "light" if palette.color(QPalette.ColorRole.Window).lightness() > 128 else "dark"
            qdarktheme.setup_theme(auto_theme)

    def set_background_color(self, color: str) -> None:
        """
        Set the application background color.
        @param color: str, color code in hex format.
        """
        palette = QApplication.instance().palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        QApplication.instance().setPalette(palette)

    def switch_theme(self) -> None:
        current_theme = self.get_theme()
        if current_theme == "light":
            self.set_theme("dark")
        elif current_theme == "dark":
            self.set_theme("light")
        else:  # 'auto' mode, switch to light or dark based on current brightness
            palette = QApplication.instance().palette()
            auto_theme = "light" if palette.color(QPalette.ColorRole.Window).lightness() > 128 else "dark"
            self.set_theme(auto_theme)


class MainWindow(QMainWindow):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("Theme Switcher")

        # Set up button and layout
        self.button = QPushButton("Toggle Theme")
        self.button.clicked.connect(self.toggle_theme)

        layout = QVBoxLayout()
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_theme(self):
        self.theme_manager.switch_theme()


if __name__ == '__main__':
    app = QApplication([])  # Initialize QApplication
    theme_manager = ThemeManager()

    # Set up main window with theme manager
    main_window = MainWindow(theme_manager)
    main_window.show()

    sys.exit(app.exec())
