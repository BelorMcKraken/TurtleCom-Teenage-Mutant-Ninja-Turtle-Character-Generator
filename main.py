import sys
import ctypes

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
)

from app.config import project_root
from app.ui.main_window import MainWindow, DARK_QSS, APP_NAME, APP_VERSION


class Splash(QWidget):
    def __init__(self, pixmap: QPixmap | None, title: str) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)

        panel = QWidget()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(10)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignHCenter)
        if pixmap is not None and not pixmap.isNull():
            self.logo.setPixmap(pixmap.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        panel_layout.addWidget(self.logo)

        self.text = QLabel(title)
        self.text.setAlignment(Qt.AlignHCenter)
        panel_layout.addWidget(self.text)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        panel_layout.addWidget(self.bar)

        outer.addWidget(panel)

        self.setStyleSheet(
            """
            #panel {
                background: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 14px;
            }
            QLabel { color: #e6e6e6; }
            QProgressBar {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 2px;
                text-align: center;
                color: #e6e6e6;
            }
            QProgressBar::chunk {
                background-color: #3d6dcc;
                border-radius: 6px;
            }
            """
        )
        self.adjustSize()

    def set_progress(self, value: int, message: str | None = None) -> None:
        self.bar.setValue(max(0, min(100, int(value))))
        if message is not None:
            self.text.setText(message)


def main() -> int:
    # ---- Windows taskbar icon fix ----
    if sys.platform == "win32":
        app_id = f"{APP_NAME}.{APP_VERSION}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Icon path
    icon_path = project_root() / "assets" / "images" / "TurtleCom Logo.png"
    icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()

    if not icon.isNull():
        app.setWindowIcon(icon)

    # Start dark mode ON by default
    app.setStyleSheet(DARK_QSS)

    # Splash with progress bar
    pixmap = QPixmap(str(icon_path)) if icon_path.exists() else QPixmap()
    splash = Splash(pixmap if not pixmap.isNull() else None, f"{APP_NAME} {APP_VERSION}\nLoading...")
    splash.show()
    app.processEvents()

    splash.set_progress(15, f"{APP_NAME} {APP_VERSION}\nStarting...")
    app.processEvents()

    splash.set_progress(45, "Loading rules...")
    app.processEvents()

    splash.set_progress(75, "Building UI...")
    app.processEvents()

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)

    splash.set_progress(100, "Ready!")
    app.processEvents()

    window.show()
    splash.close()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())