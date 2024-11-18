import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel

class SimpleMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple AI System Optimizer")
        self.setMinimumSize(600, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add warning label
        warning_label = QLabel("⚠️ WARNING: Command windows will appear during scanning")
        warning_label.setStyleSheet("""
            QLabel {
                color: #721c24;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 15px;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(warning_label)
        
        # Add scan button
        self.scan_button = QPushButton("Scan System")
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.scan_button)

def main():
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = SimpleMainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
