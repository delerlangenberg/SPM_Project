import sys
from PyQt5.QtWidgets import QApplication
from interface.layout.main_window import MainWindow  # adjust import to your project structure

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
