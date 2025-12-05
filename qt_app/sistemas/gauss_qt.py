from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QMessageBox, QFrame,
    QToolButton, QMenu, QSlider, QDialog, QDialogButtonBox, QPlainTextEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextCursor
from fractions import Fraction
from copy import deepcopy
import re
from ..theme import bind_font_scale_stylesheet, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from ..settings_qt import open_settings_dialog


def _fmt(x):
    try:
        return str(x)
    except Exception:
        return f"{x}"


class GaussWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Método de Eliminación de Gauss")
        self._entries = []
        self._rows = 3
        self._cols_no_b = 3
        self.pasos_guardados = []
        self.matriz_triangular = None
        self.matriz_final = None
        self.matriz_original = None
        self.detalle_button = None
        self.mostrando_detalles = False

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        card = QFrame()
        card.setObjectName("Card")
        outer.addWidget(card)
        main = QVBoxLayout(card)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(16)

        top = QHBoxLayout()
        main.addLayout(top)
        self.btn_back = QPushButton("Volver")
        self.btn_back.clicked.connect(self._go_back)
        top.addWidget(self.btn_back)
        top.addSpacing(24)

        row_container = QWidget()
        row_layout = QVBoxLayout(row_container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        row_label = QLabel("Filas")
        row_label.setAlignment(Qt.AlignHCenter)
        row_layout.addWidget(row_label)
        row_controls = QHBoxLayout()
        row_controls.setContentsMargins(0, 0, 0, 0)
        row_controls.setSpacing(6)
        self.row_slider = QSlider(Qt.Horizontal)
        self.row_slider.setRange(1, 12)
        self.row_slider.setSingleStep(1)
        self.row_slider.setPageStep(1)
        self.row_slider.setTickInterval(1)
        self.row_slider.setTickPosition(QSlider.TicksBelow)
        self.row_slider.setValue(self._rows)
        self.row_slider.valueChanged.connect(self._on_rows_changed)
        self.row_slider.setFixedWidth(160)
        row_controls.addWidget(self.row_slider, 1)
        self.row_value_label = QLabel(str(self._rows))
        self.row_value_label.setFixedWidth(32)
        self.row_value_label.setAlignment(Qt.AlignCenter)
        row_controls.addWidget(self.row_value_label)
        row_layout.addLayout(row_controls)
        top.addWidget(row_container)

        top.addSpacing(18)

        col_container = QWidget()
        col_layout = QVBoxLayout(col_container)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(4)
        col_label = QLabel("Columnas")
        col_label.setAlignment(Qt.AlignHCenter)
        col_layout.addWidget(col_label)
        col_controls = QHBoxLayout()
        col_controls.setContentsMargins(0, 0, 0, 0)
        col_controls.setSpacing(6)
        self.col_slider = QSlider(Qt.Horizontal)
        self.col_slider.setRange(1, 12)
        self.col_slider.setSingleStep(1)
        self.col_slider.setPageStep(1)
        self.col_slider.setTickInterval(1)
        self.col_slider.setTickPosition(QSlider.TicksBelow)
        self.col_slider.setValue(self._cols_no_b)
        self.col_slider.valueChanged.connect(self._on_cols_changed)
        self.col_slider.setFixedWidth(160)
        col_controls.addWidget(self.col_slider, 1)
        self.col_value_label = QLabel(str(self._cols_no_b))
        self.col_value_label.setFixedWidth(32)
        self.col_value_label.setAlignment(Qt.AlignCenter)
        col_controls.addWidget(self.col_value_label)
        col_layout.addLayout(col_controls)
        top.addWidget(col_container)

        top.addSpacing(24)
        self.btn_limpiar = QPushButton("Limpiar pantalla")
        self.btn_limpiar.clicked.connect(self._limpiar)
        top.addWidget(self.btn_limpiar)
        # nueva opción: ingreso por ecuaciones (texto)
        self.btn_ingresar_ecuaciones = QPushButton("Ingresar ecuaciones")
        self.btn_ingresar_ecuaciones.clicked.connect(self._open_ecuaciones_dialog)
        top.addWidget(self.btn_ingresar_ecuaciones)
        top.addSpacing(18)
        top.addStretch(1)
        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip("Más opciones")
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        menu = QMenu(more_btn)
        try:
            act_settings = menu.addAction(gear_icon_preferred(22), "Configuración")
        except Exception:
            act_settings = menu.addAction("Configuración")
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        top.addWidget(more_btn, 0, Qt.AlignRight)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        main.addWidget(self.scroll)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(8)
        self.scroll.setWidget(self.grid_container)

        title = QLabel("Resultados")
        title.setObjectName("Subtitle")
        main.addWidget(title)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.result,
            "font-family: Consolas, monospace; font-size: {body}px;",
            body=12,
        )
        main.addWidget(self.result, 1)

        self.btn_resolver = QPushButton("Resolver")
        self.btn_resolver.clicked.connect(self._resolver)
        self.btn_resolver.setEnabled(False)
        main.addWidget(self.btn_resolver)

        bottom = QHBoxLayout()
        main.addLayout(bottom)
        bottom.addStretch(1)
        self.detalle_button = QPushButton("Ver pasos detallados")
        self.detalle_button.setEnabled(False)
        self.detalle_button.clicked.connect(self._toggle_detalles)
        bottom.addWidget(self.detalle_button)

        self._rebuild_grid(self._rows, self._cols_no_b + 1)

    def _limpiar(self):
        self._entries = []
        while self.grid_layout.count():
            w = self.grid_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.result.clear()
        self.btn_resolver.setEnabled(False)
        self.pasos_guardados = []
        self.matriz_triangular = None
        self.matriz_final = None
        self.matriz_original = None
        self.mostrando_detalles = False
        try:
            if self.detalle_button:
                self.detalle_button.setEnabled(False)
        except Exception:
            pass

    def _rebuild_grid(self, filas: int, columnas: int):
        old = [[e.text() for e in row] for row in self._entries] if self._entries else []
        self._limpiar()
        for j in range(columnas - 1):
            h = QLabel(f"x{j+1}")
            h.setStyleSheet("font-weight: 700;")
            h.setAlignment(Qt.AlignHCenter)
            self.grid_layout.addWidget(h, 0, j)
        h = QLabel("b")
        h.setStyleSheet("font-weight: 700;")
        h.setAlignment(Qt.AlignHCenter)
        self.grid_layout.addWidget(h, 0, columnas - 1)
        self._entries = []
        for i in range(filas):
            row = []
            for j in range(columnas):
                e = QLineEdit()
                e.setPlaceholderText("0")
                e.setAlignment(Qt.AlignCenter)
                e.textChanged.connect(self._on_change)
                self.grid_layout.addWidget(e, i + 1, j)
                row.append(e)
            self._entries.append(row)

        for i, row in enumerate(self._entries):
            for j, e in enumerate(row):
                try:
                    e.setText(old[i][j])
                except Exception:
                    pass
        self.btn_resolver.setEnabled(True)

    def _on_change(self):
        self.matriz_triangular = None
        self.matriz_final = None
        self.mostrando_detalles = False
        try:
            if self.detalle_button:
                self.detalle_button.setEnabled(False)
        except Exception:
            pass
        self._preview_sistema()

    def _on_rows_changed(self, val: int):
        self._rows = val
        self.row_value_label.setText(str(val))
        self._rebuild_grid(self._rows, self._cols_no_b + 1)

    def _on_cols_changed(self, val: int):
        self._cols_no_b = val
        self.col_value_label.setText(str(val))
        self._rebuild_grid(self._rows, self._cols_no_b + 1)

    def _open_ecuaciones_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Ingresar ecuaciones")
        lay = QVBoxLayout(dlg)
        info = QLabel("Ingrese una ecuación por línea. Ejemplo: 2x + 3y = 5\nUse variables como x, y, z o x1, x2...")
        info.setWordWrap(True)
        lay.addWidget(info)
        editor = QPlainTextEdit()
        editor.setPlaceholderText("Ej:\n2x + 3y = 5\n-x + 4y = 1")
        lay.addWidget(editor, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)
        if dlg.exec() != QDialog.Accepted:
            return
        text = editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Vacío", "No ingresaste ecuaciones.")
            return
        try:
            M = self._parse_equations_text(text)
        except Exception as exc:
            QMessageBox.critical(self, "Error de parseo", f"No se pudieron interpretar las ecuaciones: {exc}")
            return
        filas = len(M)
        columnas = len(M[0]) if filas else 0
        if filas == 0:
            QMessageBox.warning(self, "Error", "No se detectaron ecuaciones válidas.")
            return
        self._rows = filas
        self._cols_no_b = columnas - 1
        if self.row_slider.maximum() < self._rows:
            self.row_slider.setMaximum(self._rows)
        if self.col_slider.maximum() < self._cols_no_b:
            self.col_slider.setMaximum(self._cols_no_b)
        self.row_slider.blockSignals(True)
        self.row_slider.setValue(self._rows)
        self.row_slider.blockSignals(False)
        self.row_value_label.setText(str(self._rows))
        self.col_slider.blockSignals(True)
        self.col_slider.setValue(self._cols_no_b)
        self.col_slider.blockSignals(False)
        self.col_value_label.setText(str(self._cols_no_b))
        self._rebuild_grid(self._rows, self._cols_no_b + 1)
        for i in range(filas):
            for j in range(columnas):
                val = M[i][j]
                self._entries[i][j].setText(str(val))

    def _resolver(self):
        try:
            A = []
            for i in range(self._rows):
                fila = []
                for j in range(self._cols_no_b + 1):
                    txt = self._entries[i][j].text().strip()
                    if txt == "":
                        txt = "0"
                    fila.append(Fraction(txt))
                A.append(fila)
            self.matriz_original = deepcopy(A)
            pasos, triangular = self._gauss_eliminacion(A, self._rows, self._cols_no_b + 1)
            self.pasos_guardados = pasos
            self.matriz_triangular = deepcopy(triangular)
            self.matriz_final = self._rref_para_soluciones(deepcopy(triangular))
            self._show_summary()
            if self.detalle_button:
                self.detalle_button.setEnabled(bool(self.pasos_guardados))
                self.detalle_button.setText("Ver pasos detallados")
            self.mostrando_detalles = False
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {exc}")

    def _show_summary(self):
        self.result.clear()
        self.result.insertPlainText("===== SOLUCIÓN FINAL (Gauss) =====\n\n")

        if self.matriz_original:
            self.result.insertPlainText("Sistema de ecuaciones ingresado:\n")
            for ln in self._formatear_sistema_ecuaciones(self.matriz_original):
                self.result.insertPlainText(ln + "\n")
            vec_lines = self._formatear_vectorial(self.matriz_original)
            if vec_lines:
                self.result.insertPlainText("\nForma vectorial equivalente:\n")
                for ln in vec_lines:
                    self.result.insertPlainText(ln + "\n")
            self.result.insertPlainText("\n")

        if self.matriz_triangular:
            self.result.insertPlainText("Matriz triangular superior obtenida:\n")
            for ln in self._format_matriz_lines(self.matriz_triangular):
                self.result.insertPlainText(ln + "\n")
            self.result.insertPlainText("\n")

        if self.matriz_final is None:
            self.result.insertPlainText("(no hay soluciones calculadas)\n")
            return

        soluciones, tipo = self._extraer_soluciones(self.matriz_final)
        if tipo == "incompatible":
            self.result.insertPlainText("El sistema es inconsistente: fila 0 = b con b ≠ 0.\n")
        elif tipo == "determinado":
            self.result.insertPlainText("Solución única:\n")
            self.result.insertPlainText(
                "Un sistema tiene solucion unica cuando todas sus ecuaciones se cruzan en un solo punto.\n"
                "Ese punto es el valor exacto de cada variable que cumple todas las ecuaciones al mismo tiempo.\n\n"
            )
            for i, val in enumerate(soluciones):
                self.result.insertPlainText(f"x{i+1} = {val}\n")
        elif tipo == "indeterminado":
            self.result.insertPlainText("Infinitas soluciones:\n")
            for i, val in enumerate(soluciones):
                self.result.insertPlainText(f"x{i+1} = {val}\n")
            libres = [idx for idx, val in enumerate(soluciones) if isinstance(val, str) and "variable libre" in val]
            inter_desc = "Se intersectan los dos planos? "
            if len(libres) == 1:
                inter_desc += "Si. Su interseccion es una recta descrita por la solucion parametrica mostrada."
            elif len(libres) >= 2:
                inter_desc += "Si. Los planos coinciden y la interseccion es un plano completo con infinitos puntos en comun."
            else:
                inter_desc += "Si. Comparten infinitos puntos en comun."
            self.result.insertPlainText("\n" + inter_desc + "\n\n")
            pivot_cols, free_cols, pivot_row_for_col = self._analizar_rref(self.matriz_final)
            if free_cols:
                self.result.insertPlainText("Conjunto solucion (forma vectorial):\n\n")
                num_vars = len(soluciones)
                particular = []
                for j in range(num_vars):
                    if j in free_cols:
                        particular.append(Fraction(0))
                    else:
                        irow = pivot_row_for_col.get(j, None)
                        particular.append(self.matriz_final[irow][-1] if irow is not None else Fraction(0))
                vectores_libres = []
                for l in free_cols:
                    v = [Fraction(0)] * num_vars
                    v[l] = Fraction(1)
                    for j in pivot_cols:
                        irow = pivot_row_for_col[j]
                        v[j] = -self.matriz_final[irow][l]
                    vectores_libres.append(v)
                es_homogeneo = all(self.matriz_original[i][-1] == 0 for i in range(len(self.matriz_original))) if self.matriz_original else False
                if not es_homogeneo:
                    nombres = ["  "] + [f"x{l+1}" for l in free_cols]
                    vectores = [particular] + vectores_libres
                else:
                    nombres = [f"x{l+1}" for l in free_cols]
                    vectores = vectores_libres
                lines = self.vectores_columna_lado_a_lado(vectores, nombres, espacio_entre_vectores=4)
                self.imprimir_vectores_con_x_igual(lines)
                libres_str = ", ".join([f"x{l+1}" for l in free_cols])
                self.result.insertPlainText(f"\nDonde {libres_str} son parámetros libres.\n")

        self.result.moveCursor(QTextCursor.End)

    def _toggle_detalles(self):
        if not self.detalle_button.isEnabled() or not self.pasos_guardados:
            return
        if self.mostrando_detalles:
            self._show_summary()
            self.detalle_button.setText("Ver pasos detallados")
            self.mostrando_detalles = False
        else:
            self._show_detalles()
            self.detalle_button.setText("Ocultar pasos detallados")
            self.mostrando_detalles = True

    def _show_detalles(self):
        self.result.clear()
        for step in self.pasos_guardados:
            self._insert_header(step["titulo"], step.get("comentario", ""))
            oper_lines = step["oper_lines"]
            matriz_lines = step["matriz_lines"]
            max_left = max((len(s) for s in oper_lines), default=0)
            sep = "   |   "
            max_len = max(len(oper_lines), len(matriz_lines))
            for i in range(max_len):
                left = oper_lines[i] if i < len(oper_lines) else ""
                right = matriz_lines[i] if i < len(matriz_lines) else ""
                line_text = left.ljust(max_left) + (sep if right else "") + right + "\n"
                self.result.insertPlainText(line_text)
            self.result.insertPlainText("\n" + "-" * 110 + "\n\n")

        if self.matriz_triangular:
            self.result.insertPlainText("Matriz triangular superior final:\n")
            for ln in self._format_matriz_lines(self.matriz_triangular):
                self.result.insertPlainText(ln + "\n")
            self.result.insertPlainText("\n")

        self.result.insertPlainText("===== SOLUCIÓN FINAL =====\n")
        soluciones, tipo = self._extraer_soluciones(self.matriz_final)
        if tipo == "incompatible":
            self.result.insertPlainText("Sistema incompatible.\n")
        elif tipo == "determinado":
            self.result.insertPlainText(
                "Solución única:\n"
                "Un sistema tiene solucion unica cuando todas sus ecuaciones se cruzan en un solo punto.\n"
                "Ese punto es el valor exacto de cada variable que cumple todas las ecuaciones al mismo tiempo.\n"
            )
            for i, val in enumerate(soluciones):
                self.result.insertPlainText(f"x{i+1} = {val}\n")
        elif tipo == "indeterminado":
            self.result.insertPlainText("Infinitas soluciones:\n")
            for i, val in enumerate(soluciones):
                self.result.insertPlainText(f"x{i+1} = {val}\n")
            libres = [idx for idx, val in enumerate(soluciones) if isinstance(val, str) and "variable libre" in val]
            inter_desc = "Se intersectan los dos planos? "
            if len(libres) == 1:
                inter_desc += "Si. Su interseccion es una recta descrita por la solucion parametrica mostrada."
            elif len(libres) >= 2:
                inter_desc += "Si. Los planos coinciden y la interseccion es un plano completo con infinitos puntos en comun."
            else:
                inter_desc += "Si. Comparten infinitos puntos en comun."
            self.result.insertPlainText(inter_desc + "\n")
            pivot_cols, free_cols, pivot_row_for_col = self._analizar_rref(self.matriz_final)
            if free_cols:
                self.result.insertPlainText("Conjunto solucion (forma vectorial):\n\n")
                num_vars = len(soluciones)
                particular = []
                for j in range(num_vars):
                    if j in free_cols:
                        particular.append(Fraction(0))
                    else:
                        irow = pivot_row_for_col.get(j, None)
                        particular.append(self.matriz_final[irow][-1] if irow is not None else Fraction(0))
                vectores_libres = []
                for l in free_cols:
                    v = [Fraction(0)] * num_vars
                    v[l] = Fraction(1)
                    for j in pivot_cols:
                        irow = pivot_row_for_col[j]
                        v[j] = -self.matriz_final[irow][l]
                    vectores_libres.append(v)
                es_homogeneo = all(self.matriz_original[i][-1] == 0 for i in range(len(self.matriz_original))) if self.matriz_original else False
                if not es_homogeneo:
                    nombres = ["  "] + [f"x{l+1}" for l in free_cols]
                    vectores = [particular] + vectores_libres
                else:
                    nombres = [f"x{l+1}" for l in free_cols]
                    vectores = vectores_libres
                lines = self.vectores_columna_lado_a_lado(vectores, nombres, espacio_entre_vectores=4)
                self.imprimir_vectores_con_x_igual(lines)
                libres_str = ", ".join([f"x{l+1}" for l in free_cols])
                self.result.insertPlainText(f"\nDonde {libres_str} son parámetros libres.\n")
        else:
            for i, val in enumerate(soluciones):
                self.result.insertPlainText(f"x{i+1} = {val}\n")
        self.result.moveCursor(QTextCursor.End)

    def _insert_header(self, titulo: str, comentario: str = ""):
        self.result.insertPlainText("Operación: ")
        start = self.result.textCursor().position()
        self.result.insertPlainText(titulo)
        end = self.result.textCursor().position()
        if comentario:
            self.result.insertPlainText("  —  " + comentario)
        self.result.insertPlainText("\n\n")

    def _gauss_eliminacion(self, A, n, m):
        pasos = []
        fila_pivote = 0
        for col in range(m - 1):
            pivote = None
            for f in range(fila_pivote, n):
                if A[f][col] != 0:
                    pivote = f
                    break
            if pivote is None:
                continue

            if pivote != fila_pivote:
                A[fila_pivote], A[pivote] = A[pivote], A[fila_pivote]
                pasos.append({
                    "titulo": f"F{fila_pivote+1} ↔ F{pivote+1}",
                    "comentario": f"Intercambio de filas para colocar pivote en columna {col+1}",
                    "oper_lines": [],
                    "matriz_lines": self._format_matriz_lines(A)
                })

            divisor = A[fila_pivote][col]
            if divisor == 0:
                fila_pivote += 1
                continue
            if divisor != 1:
                A[fila_pivote] = [val / divisor for val in A[fila_pivote]]
                pasos.append({
                    "titulo": f"F{fila_pivote+1} → F{fila_pivote+1}/{divisor}",
                    "comentario": f"Normalización del pivote en columna {col+1}",
                    "oper_lines": [],
                    "matriz_lines": self._format_matriz_lines(A)
                })

            for f in range(fila_pivote + 1, n):
                if A[f][col] != 0:
                    factor = A[f][col]
                    original_fila = A[f][:]
                    A[f] = [original_fila[j] - factor * A[fila_pivote][j] for j in range(m)]
                    oper_lines = self._format_operacion_vertical_lines(
                        A[fila_pivote], original_fila, factor, A[f], fila_pivote + 1, f + 1
                    )
                    pasos.append({
                        "titulo": f"F{f+1} → F{f+1} - ({factor})F{fila_pivote+1}",
                        "comentario": f"Anular elemento en columna {col+1}",
                        "oper_lines": oper_lines,
                        "matriz_lines": self._format_matriz_lines(A)
                    })
            fila_pivote += 1
            if fila_pivote >= n:
                break
        return pasos, A

    def _rref_para_soluciones(self, A):
        n = len(A)
        m = len(A[0]) if A else 0
        fila_pivote = 0
        for col in range(m - 1):
            pivote = None
            for f in range(fila_pivote, n):
                if A[f][col] != 0:
                    pivote = f
                    break
            if pivote is None:
                continue

            if pivote != fila_pivote:
                A[fila_pivote], A[pivote] = A[pivote], A[fila_pivote]

            divisor = A[fila_pivote][col]
            if divisor == 0:
                fila_pivote += 1
                continue
            if divisor != 1:
                A[fila_pivote] = [val / divisor for val in A[fila_pivote]]

            for f in range(n):
                if f != fila_pivote and A[f][col] != 0:
                    factor = A[f][col]
                    A[f] = [A[f][j] - factor * A[fila_pivote][j] for j in range(m)]

            fila_pivote += 1
            if fila_pivote >= n:
                break
        return A

    def _format_operacion_vertical_lines(self, fila_pivote, fila_actual, factor, fila_result, idx_piv, idx_obj):
        ancho = max(len(str(x)) for x in fila_result) if fila_result else 1

        def fmt(lst):
            return " ".join(str(x).rjust(ancho) for x in lst)

        escala = [(-factor) * val for val in fila_pivote]

        if factor < 0:
            factor_str = f"+{abs(factor)}"
        else:
            factor_str = f"-{factor}"

        lines = [
            f"{factor_str}F{idx_piv} : {fmt(escala)}",
            f"+F{idx_obj}   : {fmt(fila_actual)}",
            " " * 10 + "-" * (ancho * len(fila_result) + len(fila_result) - 1),
            f"=F{idx_obj}   : {fmt(fila_result)}"
        ]
        return lines

    def _format_matriz_lines(self, A):
        ancho = max((len(str(x)) for fila in A for x in fila), default=1)
        lines = []
        for fila in A:
            line = " ".join(str(x).rjust(ancho) for x in fila)
            lines.append(line)
        return lines

    def _extraer_soluciones(self, A):
        if not A:
            return [], "determinado"
        n = len(A)
        m = len(A[0])
        num_vars = m - 1
        soluciones = [None] * num_vars

        for i in range(n):
            if all(A[i][j] == 0 for j in range(num_vars)) and A[i][-1] != 0:
                return None, "incompatible"

        pivotes = [-1] * n
        columnas_pivote = []
        for i in range(n):
            for j in range(num_vars):
                if A[i][j] == 1 and all(A[k][j] == 0 for k in range(n) if k != i):
                    pivotes[i] = j
                    columnas_pivote.append(j)
                    break

        libres = [j for j in range(num_vars) if j not in columnas_pivote]

        if libres:
            expresiones = {}
            for i in range(n):
                if pivotes[i] != -1:
                    partes = []
                    if A[i][-1] != 0:
                        partes.append(str(A[i][-1]))
                    for j in libres:
                        coef = -A[i][j]
                        if coef != 0:
                            partes.append(f"({coef})*x{j+1}")
                    expr = " + ".join(partes) if partes else "0"
                    expresiones[pivotes[i]] = expr

            for j in range(num_vars):
                if j in expresiones:
                    soluciones[j] = expresiones[j]
                elif j in libres:
                    soluciones[j] = f"x{j+1} es variable libre"
                else:
                    soluciones[j] = "0"
            return soluciones, "indeterminado"

        for i in range(min(n, num_vars)):
            if pivotes[i] != -1:
                soluciones[pivotes[i]] = A[i][-1]
        return soluciones, "determinado"

    def _analizar_rref(self, A):
        n = len(A)
        m = len(A[0])
        num_vars = m - 1
        piv_col_por_fila = [-1] * n
        piv_fila_por_col = {}
        for i in range(n):
            for j in range(num_vars):
                if A[i][j] == 1 and all(A[k][j] == 0 for k in range(n) if k != i):
                    piv_col_por_fila[i] = j
                    piv_fila_por_col[j] = i
                    break
        pivot_cols = [j for j in piv_col_por_fila if j != -1]
        free_cols = [j for j in range(num_vars) if j not in pivot_cols]
        return pivot_cols, free_cols, piv_fila_por_col

    def _formatear_sistema_ecuaciones(self, A_aug):
        if not A_aug:
            return []
        n = len(A_aug)
        m = len(A_aug[0])
        num_vars = max(0, m - 1)

        def coef_term(c, j):
            if c == 0:
                return None
            var = f"x{j+1}"
            if c == 1:
                return f"{var}"
            if c == -1:
                return f"- {var}"
            return f"{c}{var}"

        lines = []
        for i in range(n):
            parts = []
            for j in range(num_vars):
                t = coef_term(A_aug[i][j], j)
                if t is None:
                    continue
                if not parts:
                    parts.append(str(t))
                else:
                    tt = str(t)
                    if tt.startswith("-"):
                        clean = tt[2:] if tt.startswith("- ") else tt[1:]
                        parts.append(f"- {clean}")
                    else:
                        parts.append(f"+ {tt}")
            left = " ".join(parts) if parts else "0"
            right = str(A_aug[i][-1]) if m > 0 else "0"
            lines.append(f"{left} = {right}")
        return lines

    def _formatear_vectorial(self, A_aug):
        """Devuelve la forma vectorial por columnas: sum(xj * columna_j) = b."""
        if not A_aug:
            return []
        n = len(A_aug)
        m = len(A_aug[0])
        num_vars = max(0, m - 1)
        if num_vars == 0:
            return []

        # Preparar columnas de coeficientes y del vector b
        cols = [[A_aug[i][j] for i in range(n)] for j in range(num_vars)]
        b_col = [A_aug[i][-1] for i in range(n)] if m > 0 else [0] * n

        # Anchos para alinear
        coef_ancho = max((len(str(v)) for col in cols for v in col), default=1)
        b_ancho = max((len(str(v)) for v in b_col), default=1)
        var_names = [f"x{j+1}" for j in range(num_vars)]
        var_ancho = max((len(v) for v in var_names), default=1)

        def col_block(values, width):
            lines = []
            for v in values:
                lines.append(f"[ {str(v).rjust(width)} ]")
            return lines

        col_lines = [col_block(col, coef_ancho) for col in cols]
        b_lines = col_block(b_col, b_ancho)

        # Combinar en expresion fila a fila
        lines = []
        for i in range(n):
            parts = []
            for idx, block in enumerate(col_lines):
                label = var_names[idx] if i == 0 else " " * var_ancho
                parts.append(f"{label} {block[i]}")
            left = " + ".join(parts)
            lines.append(f"{left} = {b_lines[i]}")
        return lines

    def vectores_columna_lado_a_lado(self, vectores, nombres, espacio_entre_vectores=4):
        if not vectores:
            return []
        n = len(vectores[0])
        m = len(vectores)
        encabezados = [nombres[0]] + [f"+ {nombres[idx]}" for idx in range(1, m)]
        max_encabezado = max((len(e) for e in encabezados), default=0)
        max_num_len = 1
        for v in vectores:
            for fila in range(n):
                max_num_len = max(max_num_len, len(str(v[fila])))
        bloque_ancho = max_encabezado + 3 + max_num_len + 2
        sep = " " * espacio_entre_vectores
        lines = []
        for fila in range(n):
            line = ""
            for idx, v in enumerate(vectores):
                valstr = str(v[fila]).rjust(max_num_len)
                if fila == 0:
                    li, ri = "\u23A1", "\u23A4"
                elif fila == n - 1:
                    li, ri = "\u23A3", "\u23A6"
                else:
                    li, ri = "\u23A2", "\u23A5"
                if fila == 0:
                    encabezado = encabezados[idx].rjust(max_encabezado)
                    bloque = f"{encabezado} {li} {valstr} {ri}"
                else:
                    bloque = " " * max_encabezado + f" {li} {valstr} {ri}"
                bloque = bloque.ljust(bloque_ancho)
                if idx < m - 1:
                    bloque += sep
                line += bloque
            lines.append(line.rstrip())
        return lines

    def imprimir_vectores_con_x_igual(self, lines):
        if not lines:
            return
        x_eq = "x ="
        first = lines[0]
        pos = first.find("\u23A1")
        pos = 0 if pos < 0 else pos
        x_pos = max(0, pos - len(x_eq) - 1)
        for i, l in enumerate(lines):
            if i == 0:
                self.result.insertPlainText(" " * x_pos + x_eq + " " + l + "\n")
            else:
                self.result.insertPlainText(" " * (x_pos + len(x_eq) + 1) + l + "\n")

    def _preview_sistema(self):
        if getattr(self, "matriz_triangular", None) is not None:
            return
        try:
            if not getattr(self, "_entries", None):
                return
            A_aug = []
            for i in range(self._rows):
                fila = []
                for j in range(self._cols_no_b + 1):
                    val_str = self._entries[i][j].text().strip() if self._entries else "0"
                    if val_str == "":
                        val_str = "0"
                    fila.append(Fraction(val_str))
                A_aug.append(fila)
            lines = self._formatear_sistema_ecuaciones(A_aug)
            self.result.clear()
            if lines:
                self.result.append("Vista previa del sistema:\n")
                for ln in lines:
                    self.result.append(ln)
                vec_lines = self._formatear_vectorial(A_aug)
                if vec_lines:
                    self.result.append("\nForma vectorial equivalente:")
                    for ln in vec_lines:
                        self.result.append(ln)
        except Exception:
            pass

    def _go_back(self):
        try:
            p = self.parent()
            self.close()
            if p is not None:
                p.show()
                p.activateWindow()
        except Exception:
            self.close()

    def _open_settings(self):
        open_settings_dialog(self)

    def _parse_equations_text(self, text: str):
        """Parsea texto con una ecuación por línea y devuelve la matriz aumentada inferida."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            raise ValueError("No hay líneas.")
        var_names = []
        var_indexed = False
        max_index = 0
        term_re = re.compile(r'([+-]?\s*(?:\d+(?:/\d+)?|\d*\.\d+)?)([a-zA-Z]\w*)')
        const_re = re.compile(r'([+-]?\s*(?:\d+(?:/\d+)?|\d*\.\d+))')
        parsed = []
        for ln in lines:
            if '=' not in ln:
                raise ValueError(f"Falta '=' en la línea: {ln}")
            left, right = ln.split('=', 1)
            left = left.strip()
            right = right.strip()
            terms = term_re.findall(left)
            vars_in_line = [v for (_coef, v) in terms]
            for v in vars_in_line:
                m_idx = re.match(r'^[a-zA-Z]+(\d+)$', v)
                if m_idx:
                    var_indexed = True
                    max_index = max(max_index, int(m_idx.group(1)))
                if v not in var_names:
                    var_names.append(v)
            coef_map = {}
            for coef_str, var in terms:
                cstr = coef_str.replace(" ", "")
                if cstr in ("", "+", "-"):
                    coef_val = Fraction(1 if cstr != "-" else -1, 1)
                else:
                    coef_val = Fraction(cstr)
                coef_map[var] = coef_map.get(var, Fraction(0)) + coef_val
            const_match = const_re.findall(right)
            if len(const_match) != 1:
                raise ValueError(f"No se pudo leer el término independiente en: {ln}")
            b_val = Fraction(const_match[0].replace(" ", ""))
            parsed.append((coef_map, b_val))
        if var_indexed:
            num_vars = max_index
            var_order = [f"x{i}" for i in range(1, num_vars + 1)]
        else:
            var_order = var_names
            num_vars = len(var_order)
        matriz = []
        for coef_map, b_val in parsed:
            fila = []
            for var in var_order:
                fila.append(coef_map.get(var, Fraction(0)))
            fila.append(b_val)
            matriz.append(fila)
        return matriz
