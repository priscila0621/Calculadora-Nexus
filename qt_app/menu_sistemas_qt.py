from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QToolButton,
    QMenu,
    QMessageBox,
)
from PySide6.QtCore import Qt
from .theme import install_toggle_shortcut, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from .settings_qt import open_settings_dialog


class MenuSistemasWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resolver sistemas de ecuaciones lineales")

        outer = QWidget()
        self.setCentralWidget(outer)
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(24, 24, 24, 24)
        outer_lay.setSpacing(18)

        nav = QFrame()
        nav.setObjectName("TopNav")
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(18, 12, 18, 12)
        nav_lay.setSpacing(12)

        btn_back = QPushButton("\u2190")
        btn_back.setObjectName("BackButton")
        btn_back.setFixedSize(42, 42)
        btn_back.setToolTip("Volver")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._go_back)
        nav_lay.addWidget(btn_back)

        nav_lay.addSpacing(6)

        btn_gauss = QPushButton("Gauss-Jordan")
        btn_gauss.setMinimumHeight(36)
        btn_gauss.clicked.connect(self._open_gauss)
        nav_lay.addWidget(btn_gauss)

        btn_gauss_simple = QPushButton("Gauss")
        btn_gauss_simple.setMinimumHeight(36)
        btn_gauss_simple.clicked.connect(self._open_gauss_simple)
        nav_lay.addWidget(btn_gauss_simple)

        btn_cramer = QPushButton("M\u00e9todo de Cramer")
        btn_cramer.setMinimumHeight(36)
        btn_cramer.clicked.connect(self._open_cramer)
        nav_lay.addWidget(btn_cramer)

        btn_leontief = QPushButton("Modelo de Leontief")
        btn_leontief.setMinimumHeight(36)
        btn_leontief.clicked.connect(self._open_leontief)
        nav_lay.addWidget(btn_leontief)

        nav_lay.addStretch(1)
        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip("M\u00e1s opciones")
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            from PySide6.QtCore import QSize
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        menu = QMenu(more_btn)
        act_settings = menu.addAction(gear_icon_preferred(22), "Configuraci\u00f3n")
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        nav_lay.addWidget(more_btn, 0, Qt.AlignRight)
        outer_lay.addWidget(nav)

        card = QFrame()
        card.setObjectName("Card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(32, 28, 32, 28)
        card_lay.setSpacing(16)

        title = QLabel("Resolver sistemas de ecuaciones lineales")
        title.setObjectName("Title")
        card_lay.addWidget(title)

        subtitle = QLabel(
            "Selecciona un m\u00e9todo desde la barra superior para iniciar la resoluci\u00f3n. "
            "Cada m\u00f3dulo muestra los pasos algor\u00edtmicos y permite exportar resultados limpios."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        card_lay.addWidget(subtitle)

        insights = QLabel(
            "\u2022 Gauss: eliminaci\u00f3n hacia matriz triangular con sustituci\u00f3n posterior.\n"
            "\u2022 Gauss-Jordan: ideal para pivotear matrices aumentadas y diagnosticar la naturaleza del sistema.\n"
            "\u2022 M\u00e9todo de Cramer: ejecuta determinantes autom\u00e1ticamente cuando la matriz es invertible.\n"
            "\u2022 Modelo de Leontief: resuelve (I - C) * X = D para sistemas insumo-producto."
        )
        insights.setWordWrap(True)
        card_lay.addWidget(insights)

        card_lay.addStretch(1)
        outer_lay.addWidget(card, 1)

        install_toggle_shortcut(self)

    def _go_back(self):
        try:
            p = self.parent()
            self.close()
            if p is not None:
                p.show()
                p.activateWindow()
        except Exception:
            self.close()

    def _open_gauss(self):
        try:
            from .sistemas.gauss_jordan_qt import GaussJordanWindow
            w = GaussJordanWindow(parent=self)
            w.showMaximized()
            self._child = w
        except Exception as exc:
            self._show_error("Gauss-Jordan", exc)

    def _open_cramer(self):
        try:
            from .sistemas.cramer_qt import CramerWindow
            w = CramerWindow(parent=self)
            w.showMaximized()
            self._child = w
        except Exception as exc:
            self._show_error("Cramer", exc)

    def _open_gauss_simple(self):
        try:
            from .sistemas.gauss_qt import GaussWindow
            w = GaussWindow(parent=self)
            w.showMaximized()
            self._child = w
        except Exception as exc:
            self._show_error("Gauss", exc)

    def _open_leontief(self):
        try:
            from .sistemas.leontief_qt import LeontiefWindow
            w = LeontiefWindow(parent=self)
            w.showMaximized()
            self._child = w
        except Exception as exc:
            self._show_error("Leontief", exc)

    def _open_settings(self):
        open_settings_dialog(self)

    def _show_error(self, modulo, exc):
        import traceback, os
        tb = traceback.format_exc()
        path = os.path.join(os.path.dirname(__file__), "error_traceback.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        msg = (
            f"No se pudo abrir la ventana. Se ha guardado el detalle en:\n{path}\n\n"
            f"Por favor, pega aqu\u00ed el contenido de ese archivo.\n\nError: {exc}"
        )
        try:
            QMessageBox.critical(self, f"Error al abrir {modulo}", msg)
        except Exception:
            print(f"Error abriendo {modulo}:", exc)
            print(tb)
