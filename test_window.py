import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Window")
        self.setMinimumSize(400, 300)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add a test label
        label = QLabel("Test Label - If you can see this, labels are working!")
        label.setStyleSheet("background-color: yellow; padding: 20px; font-size: 16px;")
        layout.addWidget(label)
        
        # Add a test button
        button = QPushButton("Test Button")
        button.setStyleSheet("background-color: lightblue; padding: 10px; font-size: 14px;")
        layout.addWidget(button)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
