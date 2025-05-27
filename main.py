# main.py

import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication
from interface.layout.main_window import MainWindow



def main():
    """
    Central Entry Point for SPM Interface.
    Loads all components under a unified application context.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
