from PyQt5.QtWidgets import QStatusBar

def create_status_bar(parent=None):
    status_bar = QStatusBar(parent)
    status_bar.showMessage("Ready")
    return status_bar
