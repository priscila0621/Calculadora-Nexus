from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from fractions import Fraction
from independencia_lineal import son_linealmente_independientes
from .theme import bind_font_scale_stylesheet


class IndependenciaWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Independencia lineal de vectores")
        self._rows = 3
        self._cols = 3
        self.entries = []

        outer = QWidget(); self.setCentralWidget(outer)
        lay = QVBoxLayout(outer)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        title = QLabel("Independencia lineal de vectores")
        title.setObjectName("Title")
        lay.addWidget(title)

        cfg = QHBoxLayout(); lay.addLayout(cfg)
        cfg.addWidget(QLabel("Dimensión (filas):"))
        self.f_edit = QLineEdit(str(self._rows)); self.f_edit.setFixedWidth(60); self.f_edit.setAlignment(Qt.AlignCenter)
        cfg.addWidget(self.f_edit)
        cfg.addSpacing(12)
        cfg.addWidget(QLabel("Cantidad de vectores (columnas):"))
        self.c_edit = QLineEdit(str(self._cols)); self.c_edit.setFixedWidth(60); self.c_edit.setAlignment(Qt.AlignCenter)
        cfg.addWidget(self.c_edit)
        self.btn_crear = QPushButton("Crear cuadrícula")
        self.btn_crear.clicked.connect(self._rebuild)
        cfg.addSpacing(16); cfg.addWidget(self.btn_crear)
        cfg.addStretch(1)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        lay.addWidget(self.scroll, 1)
        self.gridw = QWidget(); self.grid = QGridLayout(self.gridw)
        self.grid.setHorizontalSpacing(8); self.grid.setVerticalSpacing(8)
        self.scroll.setWidget(self.gridw)

        btns = QHBoxLayout(); lay.addLayout(btns)
        self.btn_check = QPushButton("Verificar independencia")
        self.btn_check.clicked.connect(self._verificar)
        btns.addWidget(self.btn_check)
        btns.addStretch(1)

        self.out = QTextEdit(); self.out.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.out,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        lay.addWidget(self.out, 1)

        self._rebuild()

    def _rebuild(self):
        try:
            f = max(1, int(self.f_edit.text())); c = max(1, int(self.c_edit.text()))
        except Exception:
            QMessageBox.warning(self, "Aviso", "Dimensiones inválidas.")
            return
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)
        self.entries = []
        for j in range(c):
            h = QLabel(f"v{j+1}"); h.setAlignment(Qt.AlignCenter); self.grid.addWidget(h, 0, j)
        for i in range(f):
            row = []
            for j in range(c):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.grid.addWidget(e, i+1, j)
                row.append(e)
            self.entries.append(row)

    def _verificar(self):
        # Construye vectores columna y delega al método existente para el texto
        try:
            f = len(self.entries)
            c = len(self.entries[0]) if f else 0
            matriz = []
            for i in range(f):
                fila = []
                for j in range(c):
                    s = (self.entries[i][j].text() or "0").strip()
                    fila.append(float(Fraction(s)))
                matriz.append(fila)
            columnas = [[matriz[i][j] for i in range(f)] for j in range(c)]
            ok, texto = son_linealmente_independientes(columnas)
            self.out.clear()
            self.out.insertPlainText(texto)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo verificar: {exc}")

