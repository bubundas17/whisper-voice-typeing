import sys
from PyQt5.QtWidgets import QApplication
from whisper_sst.gui.system_tray import SystemTrayApp

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray_app = SystemTrayApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
