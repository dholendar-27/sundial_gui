import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QPushButton
from PySide6.QtCore import Qt, QEasingCurve, QPoint, QPropertyAnimation, Signal
from PySide6.QtGui import QPainter, QColor


class SwitchControl(QWidget):
    # Define a custom signal to emit state changes
    stateChanged = Signal(bool)  # Emits True if ON, False if OFF

    def __init__(self, parent=None, bg_color="#888888", circle_color="#FFFFFF", active_color="#FFA500",
                 animation_curve=QEasingCurve.OutBounce, animation_duration=300, checked=False):
        super().__init__(parent)

        # Set the size of the switch
        self.setFixedSize(44, 24)

        # Store colors and state
        self.bg_color = bg_color
        self.circle_color = circle_color
        self.active_color = active_color
        self._is_checked = checked  # Internal variable to track the state

        # Set the cursor to a pointing hand for the switch
        self.setCursor(Qt.PointingHandCursor)

        # Create the circle button inside the switch
        self.circle = QPushButton(self)
        self.circle.setFixedSize(20, 20)
        self.circle.setStyleSheet(f"background-color: {circle_color}; border: none; border-radius: 10px;")

        # Create animation for the circle movement
        self.animation = QPropertyAnimation(self.circle, b"pos")
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(animation_duration)

        # Set the initial position of the circle
        self.update_circle_position(animate=False)

        # Connect the circle's click event to toggle the switch
        self.circle.clicked.connect(self.toggle)

    def isChecked(self):
        """Return the current checked state."""
        return self._is_checked

    def setChecked(self, checked):
        """Set the checked state and update the UI."""
        if self._is_checked != checked:
            self._is_checked = checked
            self.update_circle_position(animate=True)
            self.update()
            self.stateChanged.emit(self._is_checked)  # Emit the stateChanged signal

    def set_circle_color(self, color):
        """Dynamically change the circle's color."""
        self.circle_color = color  # Store the new color
        self.circle.setStyleSheet(f"background-color: {color}; border: none; border-radius: 10px;")

    def toggle(self):
        """Toggle the switch state."""
        self.setChecked(not self._is_checked)

    def update_circle_position(self, animate=True):
        """Update the position of the circle based on the switch state."""
        target_x = self.width() - 24 if self._is_checked else 4
        if animate:
            self.animation.setEndValue(QPoint(target_x, 2))  # Centered vertically
            self.animation.start()
        else:
            self.circle.move(target_x, 2)

    def paintEvent(self, event):
        """Custom paint event to draw the background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # Draw the background based on the checked state
        bg_color = self.active_color if self._is_checked else self.bg_color
        painter.setBrush(QColor(bg_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

    def mousePressEvent(self, event):
        """Handle clicks on the background and toggle the switch."""
        if not self.circle.underMouse():  # If the circle itself is not clicked
            self.toggle()
        super().mousePressEvent(event)


class ExampleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Add a label to display the switch state
        self.label = QLabel('Switch is ON', self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Create the switch button
        self.switch = SwitchControl(
            self,
            bg_color="#888888",
            circle_color="#FFFFFF",
            active_color="#FFA500",  # Orange when active
            animation_duration=300,
            checked=True
        )

        # Connect the switch's stateChanged signal to the update_label method
        self.switch.stateChanged.connect(self.update_label)

        # Add the switch to the layout
        layout.addWidget(self.switch)

        # Add a clickable label to change the circle color
        self.change_color_button = QLabel('Click to change circle color', self)
        self.change_color_button.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.change_color_button)
        self.change_color_button.mousePressEvent = self.change_circle_color

        # Set the layout and window properties
        self.setLayout(layout)
        self.setWindowTitle('Switch Control Example')
        self.setGeometry(100, 100, 300, 200)

    def update_label(self, checked):
        """Update the label text based on the switch state."""
        self.label.setText('Switch is ON' if checked else 'Switch is OFF')

    def change_circle_color(self, event):
        """Change the circle color dynamically."""
        new_color = "#FF0000"  # Red color for demonstration
        self.switch.set_circle_color(new_color)

    def print_switch_state(self):
        """Print the switch state using is_checked."""
        print(f'Switch state: {"ON" if self.switch.isChecked() else "OFF"}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.show()
    sys.exit(app.exec())
