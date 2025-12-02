from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QFrame,
    QScrollArea,
    QGridLayout,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt
from fractions import Fraction
from copy import deepcopy
from .gauss_jordan_qt import (
    gauss_jordan,
    format_matriz_lines,
    _extraer_soluciones,
    _fmt,
    vectores_columna_lado_a_lado,
    imprimir_vectores_con_x_igual,
)


class LeontiefWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modelo de Leontief (I - C) * X = D")
        self.n = 0
        self.entries_c = []
        self.entries_d = []
        self.matriz_final = None
        self.pasos = []

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        card = QFrame()
        card.setObjectName("Card")
        outer.addWidget(card)
        main = QVBoxLayout(card)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(14)

        top = QHBoxLayout()
        main.addLayout(top)
        btn_back = QPushButton("Volver")
        btn_back.clicked.connect(self._go_back)
        top.addWidget(btn_back)

        top.addSpacing(12)
        top.addWidget(QLabel("Tamaño (n x n):"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 10)
        self.spin_n.setValue(3)
        top.addWidget(self.spin_n)

        self.btn_crear = QPushButton("Crear tablas")
        self.btn_crear.clicked.connect(self.crear_tablas)
        top.addWidget(self.btn_crear)

        self.btn_resolver = QPushButton("Resolver modelo")
        self.btn_resolver.clicked.connect(self.resolver)
        self.btn_resolver.setEnabled(False)
        top.addWidget(self.btn_resolver)

        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.clicked.connect(self.limpiar)
        top.addWidget(self.btn_limpiar)

        top.addStretch(1)

        body = QHBoxLayout()
        body.setSpacing(14)
        main.addLayout(body, 1)

        left_frame = QFrame()
        left_frame.setObjectName("Card")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)
        body.addWidget(left_frame, 0)

        left_layout.addWidget(QLabel("Matriz de consumo C"))
        self.scroll_c = QScrollArea()
        self.scroll_c.setWidgetResizable(True)
        left_layout.addWidget(self.scroll_c)

        left_layout.addSpacing(8)
        left_layout.addWidget(QLabel("Vector de demanda final D"))
        self.scroll_d = QScrollArea()
        self.scroll_d.setWidgetResizable(True)
        left_layout.addWidget(self.scroll_d)

        right_frame = QFrame()
        right_frame.setObjectName("Card")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)
        body.addWidget(right_frame, 1)

        lbl_proc = QLabel("Procedimiento y resultados")
        lbl_proc.setAlignment(Qt.AlignLeft)
        right_layout.addWidget(lbl_proc)

        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setMinimumHeight(480)
        self.txt.setLineWrapMode(QTextEdit.NoWrap)
        right_layout.addWidget(self.txt, 1)

        self.crear_tablas()

    # ---------------------------------------------------------
    # Helpers UI
    # ---------------------------------------------------------
    def _go_back(self):
        try:
            p = self.parent()
            self.close()
            if p is not None:
                p.show()
                p.activateWindow()
        except Exception:
            self.close()

    def limpiar(self):
        self.n = 0
        self.entries_c = []
        self.entries_d = []
        self.matriz_final = None
        self.pasos = []
        self._render_grids(0)
        self.txt.clear()
        self.btn_resolver.setEnabled(False)

    def crear_tablas(self):
        n = int(self.spin_n.value())
        if n <= 0:
            QMessageBox.warning(self, "Aviso", "Ingrese un tamaño válido.")
            return
        self.n = n
        self._render_grids(n)
        self.txt.clear()
        self.btn_resolver.setEnabled(True)

    def _render_grids(self, n):
        container_c = QWidget()
        grid_c = QGridLayout(container_c)
        grid_c.setContentsMargins(8, 8, 8, 8)
        grid_c.setSpacing(6)
        self.entries_c = []
        for i in range(n):
            row_entries = []
            for j in range(n):
                e = QLineEdit()
                e.setFixedWidth(70)
                e.setAlignment(Qt.AlignCenter)
                grid_c.addWidget(e, i, j)
                row_entries.append(e)
            self.entries_c.append(row_entries)
        self.scroll_c.setWidget(container_c)

        container_d = QWidget()
        grid_d = QGridLayout(container_d)
        grid_d.setContentsMargins(8, 8, 8, 8)
        grid_d.setSpacing(6)
        self.entries_d = []
        for i in range(n):
            grid_d.addWidget(QLabel(f"d{i+1}"), i, 0)
            e = QLineEdit()
            e.setFixedWidth(80)
            e.setAlignment(Qt.AlignCenter)
            grid_d.addWidget(e, i, 1)
            self.entries_d.append(e)
        self.scroll_d.setWidget(container_d)

    # ---------------------------------------------------------
    # Lógica
    # ---------------------------------------------------------
    def _parse_fraction(self, s: str) -> Fraction:
        s = (s or "").strip()
        if s == "":
            return Fraction(0)
        s = s.replace(",", ".")
        return Fraction(s)

    def _leer_datos(self):
        if not self.entries_c or not self.entries_d:
            raise ValueError("Primero crea las tablas.")
        C = []
        for row in self.entries_c:
            fila = []
            for e in row:
                fila.append(self._parse_fraction(e.text()))
            C.append(fila)
        D = []
        for e in self.entries_d:
            D.append(self._parse_fraction(e.text()))
        return C, D

    def resolver(self):
        try:
            C, D = self._leer_datos()
            n = self.n
            I = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]
            I_minus_C = [[I[i][j] - C[i][j] for j in range(n)] for i in range(n)]
            A_aug = [row + [D[i]] for i, row in enumerate(deepcopy(I_minus_C))]
            A_inicial = deepcopy(A_aug)

            # gauss_jordan modifica A_aug en sitio; pasos = trazas
            pasos = gauss_jordan(A_aug, n, n + 1)
            soluciones, tipo, analisis = _extraer_soluciones(A_aug)
            self.pasos = pasos
            self.matriz_final = A_aug
            self._mostrar_resultados(C, D, I, I_minus_C, A_inicial, soluciones, tipo, analisis)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Ocurrió un problema al resolver: {exc}")

    def _matrix_lines(self, M):
        ancho = max((len(str(x)) for fila in M for x in fila), default=1)
        lines = []
        for i, fila in enumerate(M):
            contenido = " ".join(str(x).rjust(ancho) for x in fila)
            if i == 0:
                lines.append(f"\u23A1 {contenido} \u23A4")
            elif i == len(M) - 1:
                lines.append(f"\u23A3 {contenido} \u23A6")
            else:
                lines.append(f"\u23A2 {contenido} \u23A5")
        return lines

    def _vector_lines(self, v):
        ancho = max((len(str(x)) for x in v), default=1) if v else 1
        lines = []
        for i, val in enumerate(v):
            valstr = str(val).rjust(ancho)
            if i == 0:
                lines.append(f"\u23A1 {valstr} \u23A4")
            elif i == len(v) - 1:
                lines.append(f"\u23A3 {valstr} \u23A6")
            else:
                lines.append(f"\u23A2 {valstr} \u23A5")
        return lines

    def _write_block(self, title, lines):
        self.txt.insertPlainText(title + "\n")
        for ln in lines:
            self.txt.insertPlainText(ln + "\n")
        self.txt.insertPlainText("\n")

    def _mostrar_resultados(self, C, D, I, I_minus_C, A_inicial, soluciones, tipo, analisis):
        self.txt.clear()
        self.txt.insertPlainText("MODELO DE LEONTIEF\n\n")
        self._write_block("Datos ingresados - C", self._matrix_lines(C))
        self._write_block("Datos ingresados - D", self._vector_lines(D))
        self._write_block("Matriz identidad I", self._matrix_lines(I))
        self._write_block("Matriz (I - C)", self._matrix_lines(I_minus_C))
        self.txt.insertPlainText("Sistema (I - C) * X = D\n\n")
        self._write_block("Matriz aumentada (I - C | D)", format_matriz_lines(A_inicial))

        if self.pasos:
            self.txt.insertPlainText("Aplicando Gauss-Jordan:\n\n")
            for idx, step in enumerate(self.pasos, start=1):
                self.txt.insertPlainText(f"Paso {idx}: {step['titulo']}\n")
                if step.get("comentario"):
                    self.txt.insertPlainText(step["comentario"] + "\n")
                oper_lines = step.get("oper_lines", [])
                matriz_lines = step.get("matriz_lines", [])
                max_left = max((len(s) for s in oper_lines), default=0)
                sep = "   |   "
                max_len = max(len(oper_lines), len(matriz_lines))
                for i in range(max_len):
                    left = oper_lines[i] if i < len(oper_lines) else ""
                    right = matriz_lines[i] if i < len(matriz_lines) else ""
                    line_text = left.ljust(max_left) + (sep if right else "") + right + "\n"
                    self.txt.insertPlainText(line_text)
                self.txt.insertPlainText("\n" + "-" * 100 + "\n\n")

        self._write_block("Matriz reducida (I - C | X)", format_matriz_lines(self.matriz_final))

        if tipo == "incompatible" or soluciones is None:
            self.txt.insertPlainText("El sistema es incompatible: no existe producción que cumpla con D.\n")
        else:
            if tipo == "indeterminado":
                self.txt.insertPlainText("El sistema tiene infinitas soluciones (forma paramétrica):\n")
            self._write_block("Vector de producción total X", self._vector_lines(soluciones))

        # Mostrar forma vectorial si hay variables libres
        libres = analisis[1] if analisis else []
        if tipo == "indeterminado" and libres:
            num_vars = len(soluciones)
            particular = []
            for i in range(num_vars):
                if i in libres:
                    particular.append("0")
                else:
                    expr = str(soluciones[i])
                    for l in libres:
                        expr = expr.replace(f"x{l+1}", "0")
                    try:
                        val = eval(expr)
                    except Exception:
                        val = expr
                    particular.append(val)
            vectores_libres = []
            for l in libres:
                vector = []
                for i in range(num_vars):
                    if i == l:
                        vector.append("1")
                    else:
                        expr = str(soluciones[i])
                        if f"x{l+1}" in expr:
                            import re
                            match = re.search(rf"\\(([^)]+)\\)\\*x{l+1}", expr)
                            if match:
                                coef = match.group(1)
                            else:
                                match = re.search(rf"([\\-\\d/]+)\\*x{l+1}", expr)
                                coef = match.group(1) if match else "-1"
                            vector.append(coef)
                        else:
                            vector.append("0")
                vectores_libres.append(vector)

            lines = vectores_columna_lado_a_lado([particular] + vectores_libres,
                                                 ["  "] + [f"x{l+1}" for l in libres],
                                                 espacio_entre_vectores=4)
            imprimir_vectores_con_x_igual(self.txt, lines)

        self.txt.moveCursor(self.txt.textCursor().Start)
