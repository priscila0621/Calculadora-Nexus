from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QMessageBox, QFrame,
    QComboBox,
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
        self.scroll.setAlignment(Qt.AlignTop)
        lay.addWidget(self.scroll)
        self.gridw = QWidget(); self.grid = QGridLayout(self.gridw)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(8); self.grid.setVerticalSpacing(4)
        self.grid.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.gridw)

        metodo_row = QHBoxLayout(); lay.addLayout(metodo_row)
        metodo_row.addWidget(QLabel("Método:"))
        self.metodo_combo = QComboBox()
        self.metodo_combo.addItem("Gauss-Jordan", "gauss")
        self.metodo_combo.addItem("Determinante (cuadrada)", "determinante")
        metodo_row.addWidget(self.metodo_combo)
        metodo_row.addStretch(1)

        btns = QHBoxLayout(); lay.addLayout(btns)
        self.btn_check_cols = QPushButton("Verificar columnas")
        self.btn_check_cols.clicked.connect(lambda: self._verificar("columna"))
        btns.addWidget(self.btn_check_cols)
        self.btn_check_rows = QPushButton("Verificar filas")
        self.btn_check_rows.clicked.connect(lambda: self._verificar("fila"))
        btns.addWidget(self.btn_check_rows)
        btns.addStretch(1)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        self.status_label.setStyleSheet(
            """
            QLabel {
                border-radius: 10px;
                padding: 12px;
                font-weight: 700;
                color: #ffffff;
                background: #9ca3af;
            }
            """
        )
        lay.addWidget(self.status_label)

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
            h = QLabel(f"v{j+1}"); h.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(h, 0, j, alignment=Qt.AlignHCenter | Qt.AlignBottom)
        for i in range(f):
            row = []
            for j in range(c):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.grid.addWidget(e, i+1, j)
                row.append(e)
            self.entries.append(row)

    def _verificar(self, orientacion="columna"):
        # Construye vectores (columna o fila) y delega al método existente para el texto
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
            if orientacion == "fila":
                vectores = [fila for fila in matriz]
            else:
                vectores = [[matriz[i][j] for i in range(f)] for j in range(c)]
            metodo = self.metodo_combo.currentData() or "gauss"
            ok, texto = son_linealmente_independientes(vectores, metodo=metodo)

            # Asegura que el bocado de estado siempre se muestre tras verificar
            self.status_label.setVisible(True)
            if ok:
                self.status_label.setText("Linealmente INDEPENDIENTE")
                self.status_label.setStyleSheet(
                    """
                    QLabel {
                        border-radius: 10px;
                        padding: 12px;
                        font-weight: 700;
                        color: #ffffff;
                        background: #b2768f;
                        letter-spacing: 0.5px;
                    }
                    """
                )
            else:
                self.status_label.setText("Linealmente DEPENDIENTE")
                self.status_label.setStyleSheet(
                    """
                    QLabel {
                        border-radius: 10px;
                        padding: 12px;
                        font-weight: 700;
                        color: #ffffff;
                        background: #d08da7;
                        letter-spacing: 0.5px;
                    }
                    """
                )

            header_lines = []
            if orientacion == "fila":
                header_lines.append("Modo: vectores fila (se toman las filas como vectores).")
            else:
                header_lines.append("Modo: vectores columna (se toman las columnas como vectores).")
            metodo_desc = "Gauss-Jordan (sistema homogéneo)" if metodo == "gauss" else "Determinante (col=vec)"
            header_lines.append(f"Método: {metodo_desc}")

            self.out.clear()
            self.out.insertPlainText("\n".join(header_lines) + "\n\n" + texto)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo verificar: {exc}")

