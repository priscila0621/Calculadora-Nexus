from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QMessageBox, QFrame,
    QRadioButton, QCheckBox, QToolButton, QMenu, QSizePolicy, QDialog,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QSize
from fractions import Fraction
from .theme import bind_font_scale_stylesheet, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from .settings_qt import open_settings_dialog


def _parse_fraction(s: str) -> Fraction:
    s = (s or "").strip()
    if s == "":
        return Fraction(0)
    return Fraction(s.replace(",", "."))


def _matrix_widget(parent: QWidget, mat):
    grid = QGridLayout()
    grid.setHorizontalSpacing(6)
    grid.setVerticalSpacing(6)
    wrapper = QWidget(parent)
    wrapper.setLayout(grid)
    for i, row in enumerate(mat):
        for j, val in enumerate(row):
            lbl = QLabel(str(val))
            lbl.setAlignment(Qt.AlignCenter)
            bind_font_scale_stylesheet(
                lbl,
                "background:#ffffff;border:1px solid #ccc;padding:6px;font-family:Segoe UI;font-size:{body}px;color:#000;font-weight:600;",
                body=14,
            )
            grid.addWidget(lbl, i, j)
    return wrapper


class _BaseMatrixWindow(QMainWindow):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        outer = QWidget(); self.setCentralWidget(outer)
        self.lay = QVBoxLayout(outer)
        self.lay.setContentsMargins(24, 24, 24, 24)
        self.lay.setSpacing(14)

        topbar = QHBoxLayout()
        topbar.setContentsMargins(0, 0, 0, 0)
        topbar.addStretch(1)
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
        act_settings = menu.addAction(gear_icon_preferred(22), "Configuración")
        act_settings.triggered.connect(self._open_settings)
        act_help = menu.addAction("Ayuda")
        act_help.triggered.connect(self._open_help)
        more_btn.setMenu(menu)
        topbar.addWidget(more_btn, 0, Qt.AlignRight)
        self.lay.addLayout(topbar)

        hdr = QLabel(title)
        hdr.setObjectName("Title")
        self.lay.addWidget(hdr)

        top = QHBoxLayout()
        self.top_controls = top  # referencia para que subclases agreguen controles de tamaño
        self.lay.addLayout(top)
        self.f_edit = QLineEdit("2"); self.f_edit.setFixedWidth(60); self.f_edit.setAlignment(Qt.AlignCenter)
        self.c_edit = QLineEdit("2"); self.c_edit.setFixedWidth(60); self.c_edit.setAlignment(Qt.AlignCenter)
        top.addWidget(QLabel("Filas:")); top.addWidget(self.f_edit)
        top.addSpacing(12)
        top.addWidget(QLabel("Columnas:")); top.addWidget(self.c_edit)
        self.btn_crear = QPushButton("Crear matrices")
        self.btn_crear.clicked.connect(self._crear)
        top.addSpacing(16)
        top.addWidget(self.btn_crear)
        top.addStretch(1)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scrollw = QWidget(); self.scroll.setWidget(self.scrollw)
        self.scrollw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid = QGridLayout(self.scrollw)
        self.grid.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.btn_run = QPushButton("Calcular")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self._run)

        # Agrupar grilla de entrada y botón para que el botón quede debajo con espacio
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(16)
        self.actions_layout.addWidget(self.scroll, 1)
        self.actions_layout.addWidget(self.btn_run)
        self.lay.addLayout(self.actions_layout)
        self._last_result_matrix = None

        # Área visual para mostrar la matriz resultante en cuadritos
        self.result_matrix_area = QScrollArea(); self.result_matrix_area.setWidgetResizable(True)
        self.result_matrix_area.setMinimumHeight(120)
        self.result_matrix_container = QWidget()
        self.result_matrix_layout = QVBoxLayout(self.result_matrix_container)
        self.result_matrix_layout.setContentsMargins(6, 6, 6, 6)
        self.result_matrix_area.setWidget(self.result_matrix_container)
        self.matrix_expand_btn = QToolButton()
        self.matrix_expand_btn.setText("⤢")
        self.matrix_expand_btn.setToolTip("Abrir matriz resultante en ventana")
        self.matrix_expand_btn.setAutoRaise(True)
        self.matrix_expand_btn.clicked.connect(self._open_matrix_expanded)
        self.result_matrix_block = QWidget()
        block_lay = QVBoxLayout(self.result_matrix_block)
        block_lay.setContentsMargins(0, 0, 0, 0)
        block_lay.setSpacing(4)
        header_row_m = QHBoxLayout()
        header_row_m.setContentsMargins(0, 0, 0, 0)
        header_row_m.addStretch(1)
        header_row_m.addWidget(self.matrix_expand_btn, 0, Qt.AlignRight)
        block_lay.addLayout(header_row_m)
        block_lay.addWidget(self.result_matrix_area)
        self.lay.addWidget(self.result_matrix_block)

        # Caja de texto con pasos/explicaciones (ya existente)
        self.result_box = QTextEdit(); self.result_box.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.result_box,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        self.result_box.setMinimumHeight(120)
        # Contenedor con botón de expansión y caja de resultados
        self.result_expand_btn = QToolButton()
        self.result_expand_btn.setText("⤢")
        self.result_expand_btn.setToolTip("Abrir resultados en ventana")
        self.result_expand_btn.setAutoRaise(True)
        self.result_expand_btn.clicked.connect(self._open_result_expanded)

        self.result_container = QWidget()
        result_layout = QVBoxLayout(self.result_container)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(4)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)
        header_row.addWidget(self.result_expand_btn, 0, Qt.AlignRight)
        result_layout.addLayout(header_row)
        result_layout.addWidget(self.result_box, 1)

        self.lay.addWidget(self.result_container, 1)

        # Ajustar proporciones para dar más espacio a la grilla de ingreso sin dejar vacíos enormes
        try:
            self.lay.setStretch(self.lay.indexOf(self.actions_layout), 2)
            self.lay.setStretch(self.lay.indexOf(self.result_matrix_block), 1)
            self.lay.setStretch(self.lay.indexOf(self.result_container), 1)
        except Exception:
            pass

    def _open_result_expanded(self):
        """Abre los resultados en una ventana separada."""
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Resultados")
            lay = QVBoxLayout(dlg)
            viewer = QTextEdit()
            viewer.setReadOnly(True)
            viewer.setPlainText(self.result_box.toPlainText())
            lay.addWidget(viewer)
            dlg.resize(720, 540)
            dlg.exec()
        except Exception:
            pass

    def _open_matrix_expanded(self):
        """Abre la última matriz resultante en una ventana separada."""
        M = getattr(self, "_last_result_matrix", None)
        if not M:
            QMessageBox.information(self, "Sin matriz", "Primero genera una matriz resultante.")
            return
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Matriz resultante")
            lay = QVBoxLayout(dlg)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(_matrix_widget(self, M))
            lay.addWidget(scroll)
            dlg.resize(640, 480)
            dlg.exec()
        except Exception:
            pass

        self.entries = []
        try:
            self.op_label.setText("Operacion: Multiplicacion (A x B)")
        except Exception:
            pass

    def _open_settings(self):
        try:
            open_settings_dialog(self)
        except Exception:
            pass

    def _open_help(self):
        try:
            text = self._get_help_text()
        except Exception:
            text = None
        if not text:
            text = (
                "Ingresa las dimensiones y los valores de las matrices. "
                "Usa Calcular para obtener el resultado y revisa el detalle generado."
            )
        QMessageBox.information(self, "Ayuda", text)

    def _get_help_text(self) -> str:
        return ""

    def _update_input_scroll_from_cols(self, cols: int):
        if cols <= 5:
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _update_input_min_height(self, rows: int):
        """Ajusta la altura mínima del área de entrada según la cantidad de filas."""
        approx = rows * 56 + 140  # altura estimada por fila + padding compacto
        # Pensado para ver hasta ~10 filas sin dejar vacíos grandes
        target = max(320, min(750, approx))
        self.scroll.setMinimumHeight(target)
        try:
            self.scrollw.setMinimumHeight(max(0, target - 120))
        except Exception:
            pass

    def _crear(self):
        try:
            self._setup_entries()
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Datos invalidos: {exc}")

    def _setup_entries(self):
        # override in subclasses for multiple matrices
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)
        filas = int(self.f_edit.text()); cols = int(self.c_edit.text())
        self._update_input_scroll_from_cols(cols)
        self._update_input_min_height(filas)
        self.entries = []
        g = QGridLayout(); g.setHorizontalSpacing(6); g.setVerticalSpacing(6)
        box = QFrame(); box.setLayout(g)
        self.grid.addWidget(QLabel("Matriz"), 0, 0, alignment=Qt.AlignHCenter)
        self.grid.addWidget(box, 1, 0)
        for i in range(filas):
            row = []
            for j in range(cols):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                g.addWidget(e, i, j)
                row.append(e)
            self.entries.append(row)
        self.btn_run.setEnabled(True)

    def _setup_entries_addsub(self, f: int, c: int):
        # Construye dos grillas f x c (A y B) para suma/resta; A se rellena con el último resultado
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._update_input_scroll_from_cols(c)
        self._update_input_min_height(f)
        self.entries = []
        for m in range(2):
            g = QGridLayout(); g.setHorizontalSpacing(6); g.setVerticalSpacing(6)
            box = QFrame(); box.setLayout(g)
            title = "Matriz A (resultado)" if m == 0 else "Matriz B (nueva)"
            self.grid.addWidget(QLabel(title), 0, m, alignment=Qt.AlignHCenter)
            self.grid.addWidget(box, 1, m)
            mat_entries = []
            for i in range(f):
                row = []
                for j in range(c):
                    e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                    if m == 0 and hasattr(self, "_last_result") and self._last_result and i < len(self._last_result) and j < len(self._last_result[0]):
                        e.setText(str(self._last_result[i][j]))
                    g.addWidget(e, i, j)
                    row.append(e)
                mat_entries.append(row)
            self.entries.append(mat_entries)
        self.btn_run.setEnabled(True)

    def _leer(self):
        filas = len(self.entries)
        cols = len(self.entries[0]) if filas else 0
        A = []
        for i in range(filas):
            row = []
            for j in range(cols):
                row.append(_parse_fraction(self.entries[i][j].text()))
            A.append(row)
        return A

    def _show_matrix_result(self, M, title: str = "Matriz resultante"):
        """Muestra la matriz M en el contenedor visual como cuadritos con un título.
        Limpia el contenedor anterior y añade un widget generado por _matrix_widget.
        """
        # limpiar contenedor previo
        try:
            for i in reversed(range(self.result_matrix_layout.count())):
                w = self.result_matrix_layout.itemAt(i).widget()
                if w:
                    w.setParent(None)
        except Exception:
            pass
        # añadir título y matriz
        lbl = QLabel(title)
        bind_font_scale_stylesheet(
            lbl,
            "font-weight:bold;font-size:{body}px;padding:6px;",
            body=14,
        )
        self.result_matrix_layout.addWidget(lbl, 0)
        matw = _matrix_widget(self, M)
        self.result_matrix_layout.addWidget(matw, 1)
        self._last_result_matrix = M
        self._last_result_matrix = M
        # Desactivar scroll si la matriz es compacta; activar solo para anchos grandes
        rows = len(M)
        cols = len(M[0]) if rows else 0
        if cols <= 5:
            self.result_matrix_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.result_matrix_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            # Ajustar altura para evitar barras innecesarias
            approx_row_height = 36
            target_h = max(120, min(360, rows * approx_row_height + 40))
            self.result_matrix_area.setMinimumHeight(target_h)
        else:
            self.result_matrix_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.result_matrix_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # for accessibility, also set textual representation in result_box if empty
        try:
            if not self.result_box.toPlainText().strip():
                lines = []
                for r in M:
                    lines.append(" ".join(str(v) for v in r))
                self.result_box.setPlainText(title + "\n\n" + "\n".join(lines))
        except Exception:
            pass

    def _run(self):
        raise NotImplementedError


class SumaMatricesWindow(_BaseMatrixWindow):
    def __init__(self, parent=None):
        super().__init__("Suma de Matrices", parent)
        self.num_edit = QLineEdit("2"); self.num_edit.setFixedWidth(60); self.num_edit.setAlignment(Qt.AlignCenter)
        self.top_controls.insertWidget(0, QLabel("Nº matrices:"))
        self.top_controls.insertWidget(1, self.num_edit)
        self.scalars_container = QFrame()
        self.scalars_container.setObjectName("ScalarsPanel")
        self.scalars_container.setStyleSheet(
            "QFrame#ScalarsPanel {"
            "background-color: transparent;"
            "border: 1px solid rgba(176, 122, 140, 0.35);"
            "border-radius: 12px;"
            "}"
        )
        self.scalars_layout = QHBoxLayout(self.scalars_container)
        self.scalars_layout.setContentsMargins(18, 10, 18, 10)
        self.scalars_layout.setSpacing(12)
        info_lbl = QLabel("Escalares por matriz (deja 1 si no aplica):")
        self.scalars_layout.addWidget(info_lbl)
        self.scalars_controls_layout = QHBoxLayout()
        self.scalars_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.scalars_controls_layout.setSpacing(8)
        self.scalars_layout.addLayout(self.scalars_controls_layout, 1)
        # Ubicar a la derecha del botón "Crear matrices"
        try:
            self.top_controls.insertWidget(self.top_controls.count() - 1, self.scalars_container, 0)
        except Exception:
            self.top_controls.addWidget(self.scalars_container)

        self.scalar_controls = []
        try:
            self._ensure_scalar_controls(int(self.num_edit.text()))
        except Exception:
            self._ensure_scalar_controls(0)

    def _ensure_scalar_controls(self, count: int):
        while self.scalars_controls_layout.count():
            item = self.scalars_controls_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.scalar_controls = []
        if count <= 0:
            self.scalars_controls_layout.addStretch(1)
            return
        for idx in range(count):
            pair = QFrame()
            pair_layout = QVBoxLayout(pair)
            pair_layout.setContentsMargins(4, 2, 4, 2)
            pair_layout.setSpacing(4)
            lbl = QLabel(f"k{idx+1}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setToolTip("Escalar a aplicar sobre la matriz correspondiente. Deja 1 si no aplica.")
            pair_layout.addWidget(lbl)
            edit = QLineEdit("1")
            edit.setFixedWidth(70)
            edit.setAlignment(Qt.AlignCenter)
            edit.setToolTip("Valor del escalar (por defecto 1).")
            pair_layout.addWidget(edit)
            self.scalars_controls_layout.addWidget(pair)
            self.scalar_controls.append(edit)
        self.scalars_controls_layout.addStretch(1)

    def _scale_matrices(self, matrices):
        scaled = []
        logs = []
        scalars = []
        for idx, mat in enumerate(matrices):
            try:
                scalar_value = _parse_fraction(self.scalar_controls[idx].text()) if idx < len(self.scalar_controls) else Fraction(1)
            except Exception as exc:
                raise ValueError(f"Escalar inválido en Matriz {idx+1}: {exc}") from exc
            scalars.append(scalar_value)
            new_matrix = []
            for row in mat:
                new_matrix.append([scalar_value * val for val in row])
            scaled.append(new_matrix)
            if scalar_value != 1:
                logs.append(f"Matriz {idx+1}: se multiplicó por k{idx+1} = {scalar_value}")
        return scaled, logs, scalars

    def _setup_entries(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)
        filas = int(self.f_edit.text()); cols = int(self.c_edit.text()); n = int(self.num_edit.text())
        self._update_input_scroll_from_cols(cols)
        self._ensure_scalar_controls(n)
        self.entries = []
        for m in range(n):
            g = QGridLayout(); g.setHorizontalSpacing(6); g.setVerticalSpacing(6)
            box = QFrame(); box.setLayout(g)
            self.grid.addWidget(QLabel(f"Matriz {m+1}"), 0, m, alignment=Qt.AlignHCenter)
            self.grid.addWidget(box, 1, m)
            mat_entries = []
            for i in range(filas):
                row = []
                for j in range(cols):
                    e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                    g.addWidget(e, i, j)
                    row.append(e)
                mat_entries.append(row)
            self.entries.append(mat_entries)
        self.btn_run.setEnabled(True)

    def _leer_all(self):
        mats = []
        for grid in self.entries:
            filas = len(grid); cols = len(grid[0]) if filas else 0
            M = []
            for i in range(filas):
                row = []
                for j in range(cols):
                    row.append(_parse_fraction(grid[i][j].text()))
                M.append(row)
            mats.append(M)
        return mats

    def _run(self):
        mats = self._leer_all()
        if not mats:
            QMessageBox.warning(self, "Aviso", "Crea las matrices antes de calcular.")
            return
        try:
            scaled_mats, logs, scalars = self._scale_matrices(mats)
        except ValueError as exc:
            QMessageBox.warning(self, "Aviso", str(exc))
            return
        filas = len(scaled_mats[0]); cols = len(scaled_mats[0][0]) if filas else 0
        result = [[sum(m[i][j] for m in scaled_mats) for j in range(cols)] for i in range(filas)]
        def format_matrix_lines(M):
            if not M: return []
            w = max(len(str(x)) for r in M for x in r)
            lines = []
            for i, r in enumerate(M):
                if i == 0:
                    l, rbr = "\u23A1", "\u23A4"  # âŽ¡ âŽ¤
                elif i == len(M)-1:
                    l, rbr = "\u23A3", "\u23A6"  # âŽ£ âŽ¦
                else:
                    l, rbr = "\u23A2", "\u23A5"  # âŽ¢ âŽ¥
                body = " ".join(str(x).rjust(w) for x in r)
                lines.append(f"{l} {body} {rbr}")
            return lines
        self.result_box.clear()
        # mostrar matriz resultante visualmente
        try:
            self._show_matrix_result(result, title="Matriz resultante")
        except Exception:
            pass
        if logs:
            self.result_box.insertPlainText("Escalares aplicados antes de sumar:\n")
            for line in logs:
                self.result_box.insertPlainText(f" - {line}\n")
            self.result_box.insertPlainText("\n")
        self.result_box.insertPlainText("Matriz resultante\n\n")
        for ln in format_matrix_lines(result):
            self.result_box.insertPlainText(ln + "\n")
        self.result_box.insertPlainText("\nDetalle de la suma por posicion\n")
        for i in range(filas):
            for j in range(cols):
                expr_parts = []
                scaled_parts = []
                for idx, mat in enumerate(mats):
                    scalar_val = scalars[idx] if idx < len(scalars) else Fraction(1)
                    original_val = mat[i][j]
                    if scalar_val != 1:
                        expr_parts.append(f"({scalar_val}*{original_val})")
                    else:
                        expr_parts.append(str(original_val))
                    scaled_parts.append(str(scaled_mats[idx][i][j]))
                expr_text = " + ".join(expr_parts)
                scaled_text = " + ".join(scaled_parts)
                if expr_text == scaled_text:
                    line = f"[{i+1},{j+1}]: {expr_text} = {result[i][j]}"
                else:
                    line = f"[{i+1},{j+1}]: {expr_text} = {scaled_text} = {result[i][j]}"
                self.result_box.insertPlainText(line + "\n")

    def _get_help_text(self) -> str:
        return (
            "Suma de matrices:\n"
            "1) Ingresa filas y columnas (todas las matrices deben tener el mismo tamaño).\n"
            "2) Define cuántas matrices sumar y, si quieres, aplica escalares k1, k2...\n"
            "3) Pulsa \"Crear matrices\" para generar los tableros y luego \"Calcular\" para ver la suma y el detalle."
        )


class RestaMatricesWindow(SumaMatricesWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resta de Matrices")
        try:
            header = self.findChild(QLabel, "Title")
            if header is not None:
                header.setText("Resta de Matrices")
        except Exception:
            pass

    def _run(self):
        mats = self._leer_all()
        if not mats:
            QMessageBox.warning(self, "Aviso", "Crea las matrices antes de calcular.")
            return
        try:
            scaled_mats, logs, scalars = self._scale_matrices(mats)
        except ValueError as exc:
            QMessageBox.warning(self, "Aviso", str(exc))
            return
        filas = len(scaled_mats[0]); cols = len(scaled_mats[0][0]) if filas else 0
        result = [
            [
                scaled_mats[0][i][j] - sum(scaled_mats[k][i][j] for k in range(1, len(scaled_mats)))
                for j in range(cols)
            ]
            for i in range(filas)
        ]
        def _fmt_mat(M):
            if not M: return []
            w = max(len(str(x)) for r in M for x in r)
            out = []
            for i, r in enumerate(M):
                if i == 0: l,rbr = "\u23A1","\u23A4"
                elif i == len(M)-1: l,rbr = "\u23A3","\u23A6"
                else: l,rbr = "\u23A2","\u23A5"
                out.append(f"{l} {' '.join(str(x).rjust(w) for x in r)} {rbr}")
            return out
        self.result_box.clear()
        try:
            self._show_matrix_result(result, title="Matriz resultante")
        except Exception:
            pass
        if logs:
            self.result_box.insertPlainText("Escalares aplicados antes de restar:\n")
            for line in logs:
                self.result_box.insertPlainText(f" - {line}\n")
            self.result_box.insertPlainText("\n")
        self.result_box.insertPlainText("Matriz resultante\n\n")
        for ln in _fmt_mat(result):
            self.result_box.insertPlainText(ln + "\n")
        self.result_box.insertPlainText("\nDetalle de la resta por posicion\n")
        for i in range(filas):
            for j in range(cols):
                expr_text = ""
                scaled_text = ""
                if mats:
                    scalar0 = scalars[0] if scalars else Fraction(1)
                    base_val = mats[0][i][j]
                    base_expr = f"({scalar0}*{base_val})" if scalar0 != 1 else str(base_val)
                    base_scaled = str(scaled_mats[0][i][j])
                    rest_expr = []
                    rest_scaled = []
                    for idx in range(1, len(mats)):
                        scalar_val = scalars[idx] if idx < len(scalars) else Fraction(1)
                        orig_val = mats[idx][i][j]
                        rest_expr.append(f"({scalar_val}*{orig_val})" if scalar_val != 1 else str(orig_val))
                        rest_scaled.append(str(scaled_mats[idx][i][j]))
                    if rest_expr:
                        expr_text = base_expr + " - " + " - ".join(rest_expr)
                        scaled_text = base_scaled + " - " + " - ".join(rest_scaled)
                    else:
                        expr_text = base_expr
                        scaled_text = base_scaled
                if not expr_text:
                    line = f"[{i+1},{j+1}]: {result[i][j]}"
                elif expr_text == scaled_text:
                    line = f"[{i+1},{j+1}]: {expr_text} = {result[i][j]}"
                else:
                    line = f"[{i+1},{j+1}]: {expr_text} = {scaled_text} = {result[i][j]}"
                self.result_box.insertPlainText(line + "\n")

    def _get_help_text(self) -> str:
        return (
            "Resta de matrices:\n"
            "1) Filas y columnas deben coincidir entre A y B.\n"
            "2) Completa los valores (puedes reutilizar un resultado previo como A si lo tienes).\n"
            "3) Opcional: aplica escalares kA y kB antes de restar. Luego presiona \"Calcular\"."
        )


class MultiplicacionMatricesWindow(_BaseMatrixWindow):
    def __init__(self, parent=None):
        super().__init__("Multiplicacion de Matrices", parent)
        # Habilitar scroll vertical para toda la ventana cuando hay muchas filas
        try:
            inner = self.centralWidget()
            scroll_host = QScrollArea()
            scroll_host.setWidgetResizable(True)
            scroll_host.setWidget(inner)
            wrapper = QWidget()
            wrap_lay = QVBoxLayout(wrapper)
            wrap_lay.setContentsMargins(0, 0, 0, 0)
            wrap_lay.setSpacing(4)
            wrap_lay.addWidget(scroll_host)
            self.setCentralWidget(wrapper)
        except Exception:
            pass
        # Para multiplicación pedimos A (f x c) y B (c x p)
        self.p_edit = QLineEdit("2"); self.p_edit.setFixedWidth(60); self.p_edit.setAlignment(Qt.AlignCenter)
        row = self.top_controls
        row.addSpacing(12); row.addWidget(QLabel("Columnas B:")); row.addWidget(self.p_edit)
        # Escalares opcionales por matriz
        row.addSpacing(18)
        self.op_label = QLabel("Operacion: Multiplicacion (A x B)")
        self.lay.addWidget(self.op_label)
        self.scalarA_edit = QLineEdit("1"); self.scalarA_edit.setFixedWidth(70); self.scalarA_edit.setAlignment(Qt.AlignCenter)
        row.addWidget(QLabel("Escalar A:")); row.addWidget(self.scalarA_edit)
        row.addSpacing(8)
        self.scalarB_edit = QLineEdit("1"); self.scalarB_edit.setFixedWidth(70); self.scalarB_edit.setAlignment(Qt.AlignCenter)
        row.addWidget(QLabel("Escalar B:")); row.addWidget(self.scalarB_edit)
        try:
            self.actions_layout.setSpacing(8)
            pasos_pre = [] 
            pass
        except Exception:
            pass
        # Encadenar: botón para usar el último resultado como A
        self._last_result = None
        self._chain_btn = QPushButton("Usar resultado como A")
        self._chain_btn.setEnabled(False)
        self._chain_btn.clicked.connect(self._use_result_as_A)
        # Botones para sumar/restar con otra matriz del mismo tamaño
        chain_row = QHBoxLayout()
        self._chain_add_btn = QPushButton("Sumar resultado con otra matriz")
        self._chain_sub_btn = QPushButton("Restar otra matriz al resultado")
        self._chain_add_btn.setEnabled(False)
        self._chain_sub_btn.setEnabled(False)
        self._chain_add_btn.clicked.connect(lambda: self._prepare_add_sub('add'))
        self._chain_sub_btn.clicked.connect(lambda: self._prepare_add_sub('sub'))
        chain_row.addWidget(self._chain_add_btn)
        chain_row.addWidget(self._chain_sub_btn)
        # Colocar los botones justo debajo de las matrices dentro del mismo bloque
        try:
            self.actions_layout.addWidget(self._chain_btn, 0, Qt.AlignLeft)
        except Exception:
            self.actions_layout.addWidget(self._chain_btn)
        self.actions_layout.addLayout(chain_row)

    def _setup_entries(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)
        f = int(self.f_edit.text()); c = int(self.c_edit.text()); p = int(self.p_edit.text())
        self._update_input_scroll_from_cols(max(c, p))
        self._update_input_min_height(max(f, c))
        self.entries = []
        for m, (rows, cols) in enumerate(((f, c), (c, p))):
            g = QGridLayout(); g.setHorizontalSpacing(6); g.setVerticalSpacing(6)
            box = QFrame(); box.setLayout(g)
            self.grid.addWidget(QLabel("Matriz A" if m == 0 else "Matriz B"), 0, m, alignment=Qt.AlignHCenter)
            self.grid.addWidget(box, 1, m)
            mat_entries = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                    g.addWidget(e, i, j)
                    row.append(e)
                mat_entries.append(row)
            self.entries.append(mat_entries)
        self.btn_run.setEnabled(True)

    def _run(self):
        Agrid, Bgrid = self.entries
        A = [[_parse_fraction(e.text()) for e in row] for row in Agrid]
        B = [[_parse_fraction(e.text()) for e in row] for row in Bgrid]
        # Si hay una operación de suma/resta pendiente
        if hasattr(self, "_op_mode") and self._op_mode in ("add", "sub"):
            fa, ca = len(A), len(A[0]) if A else 0
            fb, cb = len(B), len(B[0]) if B else 0
            if fa != fb or ca != cb:
                QMessageBox.warning(self, "Aviso", "Para sumar/restar, A y B deben tener las mismas dimensiones.")
                return
            As = [row[:] for row in A]
            Bs = [row[:] for row in B]
            pasos_pre = []
            try:
                kA = _parse_fraction(self.scalarA_edit.text() or "1")
                if kA != 1:
                    pasos_pre.append(f"Aplicando escalar kA = {kA} a Matriz A:")
                    for i in range(fa):
                        for j in range(ca):
                            pasos_pre.append(f"a{i+1}{j+1} := {kA}*{As[i][j]} = {kA*As[i][j]}")
                            As[i][j] = kA * As[i][j]
            except Exception:
                pass
            try:
                kB = _parse_fraction(self.scalarB_edit.text() or "1")
                if kB != 1:
                    if pasos_pre:
                        pasos_pre.append("")
                    pasos_pre.append(f"Aplicando escalar kB = {kB} a Matriz B:")
                    for i in range(fb):
                        for j in range(cb):
                            pasos_pre.append(f"b{i+1}{j+1} := {kB}*{Bs[i][j]} = {kB*Bs[i][j]}")
                            Bs[i][j] = kB * Bs[i][j]
            except Exception:
                pass
            R = [[Fraction(0) for _ in range(ca)] for _ in range(fa)]
            pasos = []
            for i in range(fa):
                for j in range(ca):
                    if self._op_mode == "add":
                        R[i][j] = As[i][j] + Bs[i][j]
                        pasos.append(f"c{i+1}{j+1} = {As[i][j]} + {Bs[i][j]} = {R[i][j]}")
                    else:
                        R[i][j] = As[i][j] - Bs[i][j]
                        pasos.append(f"c{i+1}{j+1} = {As[i][j]} - {Bs[i][j]} = {R[i][j]}")
            # Mostrar resultado y pasos
            def _fmt_mat(M):
                if not M: return []
                w = max(len(str(x)) for r in M for x in r)
                out = []
                for i, r in enumerate(M):
                    if i == 0: l,rbr = "\u23A1","\u23A4"
                    elif i == len(M)-1: l,rbr = "\u23A3","\u23A6"
                    else: l,rbr = "\u23A2","\u23A5"
                    out.append(f"{l} {' '.join(str(x).rjust(w) for x in r)} {rbr}")
                return out
            try:
                self._show_matrix_result(R, title="Matriz resultante")
            except Exception:
                pass
            self.result_box.clear()
            self.result_box.insertPlainText("Matriz resultante\n\n")
            for ln in _fmt_mat(R):
                self.result_box.insertPlainText(ln + "\n")
            self.result_box.insertPlainText("\n")
            pasos_total = []
            if pasos_pre:
                pasos_total.append("Pasos de escalado (antes de sumar/restar):")
                pasos_total.extend(pasos_pre)
                pasos_total.append("")
            pasos_total.append("Suma de matrices (A + B):" if self._op_mode == "add" else "Resta de matrices (A - B):")
            pasos_total.extend(pasos)
            for line in pasos_total:
                self.result_box.insertPlainText(line + "\n")
            self._last_result = R
            try:
                self._chain_btn.setEnabled(True)
                self._chain_add_btn.setEnabled(True)
                self._chain_sub_btn.setEnabled(True)
            except Exception:
                pass
            self._op_mode = None
            return
        fa, ca = len(A), len(A[0]) if A else 0
        fb, cb = len(B), len(B[0]) if B else 0
        if ca != fb:
            QMessageBox.warning(self, "Aviso", "Las columnas de A deben coincidir con las filas de B.")
            return
        # Escalado previo por matriz (si se solicita)
        pasos_pre = []
        As = [row[:] for row in A]; Bs = [row[:] for row in B]
        try:
            kA = _parse_fraction(self.scalarA_edit.text() or "1")
            if kA != 1:
                pasos_pre.append(f"Aplicando escalar kA = {kA} a Matriz A:")
                for i in range(fa):
                    for j in range(ca):
                        pasos_pre.append(f"a{i+1}{j+1} := {kA}*{As[i][j]} = {kA*As[i][j]}")
                        As[i][j] = kA * As[i][j]
        except Exception:
            pass
        try:
            kB = _parse_fraction(self.scalarB_edit.text() or "1")
            if kB != 1:
                pasos_pre.append("")
                pasos_pre.append(f"Aplicando escalar kB = {kB} a Matriz B:")
                for i in range(fb):
                    for j in range(cb):
                        pasos_pre.append(f"b{i+1}{j+1} := {kB}*{Bs[i][j]} = {kB*Bs[i][j]}")
                        Bs[i][j] = kB * Bs[i][j]
        except Exception:
            pass

        R = [[Fraction(0) for _ in range(cb)] for _ in range(fa)]
        pasos = []
        for i in range(fa):
            for j in range(cb):
                terms = []
                s = Fraction(0)
                for k in range(ca):
                    a = As[i][k]; b = Bs[k][j]
                    terms.append(f"{a}*{b}")
                    s += a * b
                R[i][j] = s
                pasos.append(f"c{i+1}{j+1} = " + " + ".join(terms) + f" = {s}")
        # Precedencia: primero pasos de escalares (A y B), luego sección de multiplicación
        pasos_total = []
        if pasos_pre:
            pasos_total.extend(["Pasos de escalado (antes de multiplicar):"]) 
            pasos_total.extend(pasos_pre)
            pasos_total.append("")
        pasos_total.append("Multiplicación (c_ij):")
        pasos_total.extend(pasos)
        def _fmt_mat(M):
            if not M: return []
            w = max(len(str(x)) for r in M for x in r)
            out = []
            for i, r in enumerate(M):
                if i == 0: l,rbr = "\u23A1","\u23A4"
                elif i == len(M)-1: l,rbr = "\u23A3","\u23A6"
                else: l,rbr = "\u23A2","\u23A5"
                out.append(f"{l} {' '.join(str(x).rjust(w) for x in r)} {rbr}")
            return out
        self.result_box.clear()
        try:
            self._show_matrix_result(R, title="Matriz resultante")
        except Exception:
            pass
        self.result_box.clear()
        self.result_box.insertPlainText("Matriz resultante\n\n")
        for ln in _fmt_mat(R):
            self.result_box.insertPlainText(ln + "\n")
        self.result_box.insertPlainText("\n")
        self.result_box.insertPlainText("Procedimiento paso a paso:\n")
        for line in pasos_total:
            self.result_box.insertPlainText(line + "\n")
        # Habilitar encadenado del resultado para nueva multiplicación
        self._last_result = R
        try:
            self._chain_btn.setEnabled(True)
            self._chain_add_btn.setEnabled(True)
            self._chain_sub_btn.setEnabled(True)
        except Exception:
            pass

    def _use_result_as_A(self):
        if not hasattr(self, "_last_result") or not self._last_result:
            return
        fa = len(self._last_result)
        cb = len(self._last_result[0]) if fa else 0
        self.f_edit.setText(str(fa))
        self.c_edit.setText(str(cb))
        # reconstruir grillas y volcar resultado en A
        self._setup_entries()
        try:
            self.op_label.setText("Operacion: Multiplicacion (A x B)")
        except Exception:
            pass
        try:
            Agrid, _Bgrid = self.entries
        except Exception:
            return
        for i in range(fa):
            for j in range(cb):
                Agrid[i][j].setText(str(self._last_result[i][j]))

    def _prepare_add_sub(self, op: str):
        # Prepara entradas para suma/resta mostrando A = resultado previo y B vacía
        if not hasattr(self, "_last_result") or not self._last_result:
            return
        try:
            self.op_label.setText("Operacion: " + ("Suma (A + B)" if op=="add" else "Resta (A - B)"))
        except Exception:
            pass
        self._op_mode = op
        fa = len(self._last_result)
        cb = len(self._last_result[0]) if fa else 0
        self._setup_entries_addsub(fa, cb)

    def _get_help_text(self) -> str:
        return (
            "Multiplicación A x B:\n"
            "1) Filas/columnas de A y columnas de B (filas de B = columnas de A).\n"
            "2) Llena A y B; opcionalmente aplica kA o kB antes de multiplicar.\n"
            "3) Presiona \"Calcular\". Si quieres sumar/restar el resultado con otra matriz, usa los botones debajo."
        )


class TranspuestaMatrizWindow(_BaseMatrixWindow):
    def __init__(self, parent=None):
        super().__init__("Transpuesta de Matriz", parent)
        # Envolver todo el contenido con scroll general
        try:
            inner = self.centralWidget()
            scroll_host = QScrollArea()
            scroll_host.setWidgetResizable(True)
            scroll_host.setWidget(inner)
            wrapper = QWidget()
            wrap_lay = QVBoxLayout(wrapper)
            wrap_lay.setContentsMargins(0, 0, 0, 0)
            wrap_lay.setSpacing(4)
            wrap_lay.addWidget(scroll_host)
            self.setCentralWidget(wrapper)
        except Exception:
            pass
        # Botón compacto para abrir la matriz resultante en ventana ampliada
        self._last_transpose = None
        try:
            expand_row = QHBoxLayout()
            expand_row.setContentsMargins(0, 0, 0, 0)
            expand_row.addStretch(1)
            self.expand_btn = QToolButton()
            self.expand_btn.setText("⤢")  # similar a maximizar
            self.expand_btn.setToolTip("Ver matriz resultante en ventana")
            self.expand_btn.setAutoRaise(True)
            self.expand_btn.clicked.connect(self._open_expanded_result)
            expand_row.addWidget(self.expand_btn, 0, Qt.AlignRight)
            insert_at = self.actions_layout.indexOf(self.btn_run) + 1 if hasattr(self, "actions_layout") else -1
            if insert_at >= 0:
                self.actions_layout.insertLayout(insert_at, expand_row)
            else:
                self.actions_layout.addLayout(expand_row)
        except Exception:
            pass

        # Controles adicionales para operaciones avanzadas (vector/matriz B y tipo de operación)
        try:
            adv_row = QHBoxLayout()
            adv_row.setContentsMargins(0, 0, 0, 0)
            self.adv_checkbox = QCheckBox("Operaciones avanzadas")
            self.adv_checkbox.setToolTip("Mostrar opciones para ingresar un vector/matriz B y elegir operaciones")
            self.adv_checkbox.toggled.connect(self._toggle_adv)
            adv_row.addWidget(self.adv_checkbox)
            adv_row.addStretch(1)
            self.actions_layout.addLayout(adv_row)

            # Panel oculto con opciones
            self.adv_panel = QWidget()
            adv_layout = QVBoxLayout(self.adv_panel)
            adv_layout.setContentsMargins(6, 6, 6, 6)
            # Operaciones disponibles (radio)
            ops_row = QHBoxLayout()
            self.rb_transpose = QRadioButton("A^T (Transponer A)")
            self.rb_atx = QRadioButton("A^T x (transpuesta por vector)")
            self.rb_axT = QRadioButton("(Ax)^T")
            self.rb_xTA_T = QRadioButton("x^T A^T")
            self.rb_xxT = QRadioButton("x x^T")
            self.rb_xTx = QRadioButton("x^T x (producto escalar)")
            self.rb_custom = QRadioButton("Expresión personalizada")
            self.rb_transpose.setChecked(True)
            for rb in (self.rb_transpose, self.rb_atx, self.rb_axT, self.rb_xTA_T, self.rb_xxT, self.rb_xTx, self.rb_custom):
                ops_row.addWidget(rb)
            adv_layout.addLayout(ops_row)

            # Entrada libre de expresiones (debajo de las radios)
            expr_row_top = QHBoxLayout()
            expr_row_top.setContentsMargins(0, 0, 0, 0)
            expr_row_top.addWidget(QLabel("Expresión:"))
            self.expr_edit = QLineEdit()
            self.expr_edit.setPlaceholderText("Ej: A+B, (Ax)^T, x^T A, x x^T, A^T B, (Ax)^T")
            expr_row_top.addWidget(self.expr_edit)
            adv_layout.addLayout(expr_row_top)

            # Área para ingresar vector/matriz B
            self.grid_b = QGridLayout()
            self.grid_b.setHorizontalSpacing(6)
            self.grid_b.setVerticalSpacing(6)
            bframe = QFrame(); bframe.setLayout(self.grid_b)
            adv_layout.addWidget(QLabel("Matriz/Vector B (opcional)"))
            adv_layout.addWidget(bframe)
            self.vector_entries = []  # lista de QLineEdit (columna o matrix)
            # Botón para configurar tamaño de B
            size_row = QHBoxLayout()
            self.b_rows = QLineEdit("2"); self.b_rows.setFixedWidth(60); self.b_rows.setAlignment(Qt.AlignCenter)
            self.b_cols = QLineEdit("1"); self.b_cols.setFixedWidth(60); self.b_cols.setAlignment(Qt.AlignCenter)
            btn_b_create = QPushButton("Crear B")
            btn_b_create.clicked.connect(self._crear_b)
            size_row.addWidget(QLabel("Filas B:")); size_row.addWidget(self.b_rows)
            size_row.addSpacing(8)
            size_row.addWidget(QLabel("Columnas B:")); size_row.addWidget(self.b_cols)
            size_row.addSpacing(12)
            size_row.addWidget(btn_b_create)
            adv_layout.addLayout(size_row)

            self.adv_panel.setVisible(False)
            self.actions_layout.addWidget(self.adv_panel)

            self.adv_panel.setVisible(False)
            self.actions_layout.addWidget(self.adv_panel)
        except Exception:
            pass

        # Historial de resultados: guardar y comparar varias operaciones sin borrar entradas
        try:
            self.results_history = []  # lista de tuples (title, matrix, pasos_text)
            hist_frame = QFrame()
            hist_layout = QVBoxLayout(hist_frame)
            hist_layout.setContentsMargins(6, 6, 6, 6)
            hist_layout.addWidget(QLabel("Historial de resultados"))
            self.history_list = QListWidget()
            hist_layout.addWidget(self.history_list)
            hbtns = QHBoxLayout()
            self.btn_hist_save = QPushButton("Guardar resultado")
            self.btn_hist_show = QPushButton("Mostrar")
            self.btn_hist_del = QPushButton("Eliminar")
            self.btn_hist_save.clicked.connect(self._history_save)
            self.btn_hist_show.clicked.connect(self._history_show)
            self.btn_hist_del.clicked.connect(self._history_del)
            hbtns.addWidget(self.btn_hist_save)
            hbtns.addWidget(self.btn_hist_show)
            hbtns.addWidget(self.btn_hist_del)
            hist_layout.addLayout(hbtns)
            # Preview area (uses same matrix widget) dentro de un scroll
            self.history_preview = QScrollArea(); self.history_preview.setWidgetResizable(True)
            ph = QWidget(); ph_l = QVBoxLayout(ph); ph_l.setContentsMargins(0,0,0,0)
            ph_l.addWidget(QLabel("Vista previa del resultado seleccionado"))
            self.history_preview.setWidget(ph)
            hist_layout.addWidget(self.history_preview)
            self.lay.addWidget(hist_frame)
        except Exception:
            pass

    def _run(self):
        # Leer matriz A
        A = self._leer()
        # helpers
        def transpose(M):
            r = len(M); c = len(M[0]) if r else 0
            return [[M[i][j] for i in range(r)] for j in range(c)]

        def mul(M, N):
            # M: r x m, N: m x c
            r = len(M); m = len(M[0]) if r else 0
            nrows = len(N); nc = len(N[0]) if nrows else 0
            if m != nrows:
                raise ValueError("Dimensiones incompatibles para multiplicación")
            R = [[Fraction(0) for _ in range(nc)] for __ in range(r)]
            for i in range(r):
                for j in range(nc):
                    s = Fraction(0)
                    for k in range(m):
                        s += Fraction(M[i][k]) * Fraction(N[k][j])
                    R[i][j] = s
            return R

        def read_B():
            # devuelve matrix B como lista de lists (Fraction)
            if not self.vector_entries:
                return None
            rows = len(self.vector_entries)
            cols = len(self.vector_entries[0]) if rows and isinstance(self.vector_entries[0], list) else 1
            B = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    row.append(_parse_fraction(self.vector_entries[i][j].text()))
                B.append(row)
            return B

        # Determinar operación y generar procedimiento paso a paso según formato requerido
        try:
            steps = []
            title = ""
            result_matrix = None

            def mat_lines(M):
                if M is None:
                    return ["(vacío)"]
                return [" ".join(str(x) for x in row) for row in M]

            def dims(M):
                if M is None: return "0x0"
                r = len(M); c = len(M[0]) if r else 0
                return f"{r}x{c}"

            def show_inputs():
                steps.append("1) Operación: " + title)
                steps.append("2) Matrices/Vectores ingresados:")
                # A
                steps.append(f"   A (dim {dims(A)}):")
                for ln in mat_lines(A):
                    steps.append("     " + ln)
                # B if present
                if getattr(self, 'adv_checkbox', None) and self.adv_checkbox.isChecked():
                    B_local = read_B()
                    if B_local is not None:
                        steps.append(f"   B (dim {dims(B_local)}):")
                        for ln in mat_lines(B_local):
                            steps.append("     " + ln)

            # operación por defecto: solo transponer A
            if not (getattr(self, 'adv_checkbox', None) and self.adv_checkbox.isChecked()):
                title = "A^T"
                T = transpose(A)
                result_matrix = T
                show_inputs()
                steps.append("3) Cálculo de transpuestas (si aplica):")
                steps.append("   Se calcula A^T:")
                for i in range(len(A)):
                    for j in range(len(A[0]) if A else 0):
                        steps.append(f"     T[{j+1},{i+1}] = A[{i+1},{j+1}] = {A[i][j]}")
                steps.append("4) Verificación de dimensiones:")
                steps.append(f"   A^T dim {dims(T)}")
                steps.append("   Regla: Para multiplicación no aplica (solo transpuesta).")
                steps.append("5) Cálculo paso a paso:")
                steps.append("   (no hay multiplicación; la transpuesta está mostrada arriba)")
                steps.append("6) Resultado final:")
                steps.append("   Matriz resultante:")
                for ln in mat_lines(T):
                    steps.append("     " + ln)
            else:
                # operaciones avanzadas: leer B
                B = read_B()
                # Si el usuario seleccionó "Expresión personalizada", evaluarla aquí
                if getattr(self, 'rb_custom', None) and self.rb_custom.isChecked():
                    title = f"Expresión personalizada"
                    expr = (getattr(self, 'expr_edit', None).text() if getattr(self, 'expr_edit', None) else '').strip()
                    if not expr:
                        result_matrix = None
                        show_inputs()
                        steps.append("3) No hay expresión ingresada.")
                        steps.append("6) Resultado final:")
                        steps.append("   Operación indefinida.")
                    else:
                        show_inputs()
                        steps.append("3) Evaluación de la expresión ingresada:")
                        try:
                            s = self._preprocess_expr(expr)
                            tokens = self._tokenize(s)
                            postfix = self._to_postfix(tokens)
                            R, eval_steps = self._eval_postfix(postfix, A, B)
                            result_matrix = R
                            # mostrar matriz destacada
                            try:
                                self._show_matrix_result(R, title=f"Expresión: {expr}")
                            except Exception:
                                pass
                            for st in eval_steps:
                                steps.append("   " + st)
                            steps.append("6) Resultado final:")
                            for ln in mat_lines(R): steps.append("     " + ln)
                        except Exception as e:
                            # mostrar alerta al usuario
                            try:
                                QMessageBox.warning(self, "Operación indefinida", self._format_error_message(e))
                            except Exception:
                                pass
                            steps.append("   Error: " + str(e))
                            steps.append("6) Resultado final:")
                            steps.append("   Operación indefinida.")
                            result_matrix = None
                    # luego continuar (no ejecutar otras ramas)
                    self.result_box.clear()
                    for idx, s in enumerate(steps, start=1 if steps and steps[0].startswith('1)') else 1):
                        self.result_box.insertPlainText(s + "\n")
                    try:
                        self._last_shown_matrix = result_matrix
                        self._last_shown_title = title
                        self._last_shown_steps = "\n".join(steps)
                        try: self.btn_hist_save.setEnabled(True)
                        except Exception: pass
                    except Exception:
                        pass
                    return
                # preparar nombres
                if self.rb_transpose.isChecked():
                    title = "A^T"
                    T = transpose(A)
                    result_matrix = T
                    show_inputs()
                    steps.append("3) Cálculo de transpuestas (si aplica):")
                    steps.append("   Se calcula A^T como se muestra a continuación:")
                    for i in range(len(A)):
                        for j in range(len(A[0]) if A else 0):
                            steps.append(f"     T[{j+1},{i+1}] = A[{i+1},{j+1}] = {A[i][j]}")
                    steps.append("4) Verificación de dimensiones:")
                    steps.append(f"   A^T dim {dims(T)}")
                    steps.append("   Regla: ninguna multiplicación requerida.")
                    steps.append("5) Cálculo paso a paso:")
                    steps.append("   (ver paso 3)")
                    steps.append("6) Resultado final:")
                    steps.append("   Matriz resultante:")
                    for ln in mat_lines(T): steps.append("     " + ln)

                elif self.rb_atx.isChecked():
                    title = "A^T · B"
                    T = transpose(A)
                    result_matrix = None
                    show_inputs()
                    steps.append("3) Cálculo de transpuestas (si aplica):")
                    steps.append(f"   Se calcula A^T (dim {dims(T)}):")
                    for ln in mat_lines(T): steps.append("     " + ln)
                    steps.append("4) Verificación de dimensiones:")
                    rT = len(T); cT = len(T[0]) if rT else 0
                    rB = len(B) if B is not None else 0; cB = len(B[0]) if rB else 0
                    steps.append(f"   A^T dim {rT}x{cT}; B dim {rB}x{cB}.")
                    steps.append("   Regla: columnas de la primera deben coincidir con filas de la segunda.")
                    ok = (cT == rB)
                    if ok:
                        steps.append("   La operación está definida porque las dimensiones son compatibles.")
                        # multiplicar
                        R = mul(T, B)
                        result_matrix = R
                        steps.append("5) Cálculo paso a paso:")
                        for i in range(len(R)):
                            for j in range(len(R[0])):
                                terms = [f"{T[i][k]}·{B[k][j]}" for k in range(cT)]
                                steps.append(f"   R[{i+1},{j+1}] = " + " + ".join(terms) + f" = {R[i][j]}")
                        steps.append("6) Resultado final:")
                        for ln in mat_lines(R): steps.append("     " + ln)
                    else:
                        steps.append("   La operación NO está definida porque columnas de A^T ≠ filas de B.")
                        steps.append("6) Resultado final:")
                        steps.append("   Operación indefinida.")

                elif self.rb_axT.isChecked():
                    title = "(A · B)^T"
                    result_matrix = None
                    show_inputs()
                    steps.append("3) Cálculo de transpuestas (si aplica):")
                    steps.append("   (primero calculamos A·B y luego su transpuesta)")
                    steps.append("4) Verificación de dimensiones:")
                    rA = len(A); cA = len(A[0]) if rA else 0
                    rB = len(B) if B is not None else 0; cB = len(B[0]) if rB else 0
                    steps.append(f"   A dim {rA}x{cA}; B dim {rB}x{cB}.")
                    steps.append("   Regla: columnas de A deben coincidir con filas de B.")
                    ok = (cA == rB)
                    if ok:
                        steps.append("   La operación está definida porque las dimensiones son compatibles.")
                        R = mul(A, B)
                        steps.append("5) Cálculo paso a paso de A·B:")
                        for i in range(len(R)):
                            for j in range(len(R[0])):
                                terms = [f"{A[i][k]}·{B[k][j]}" for k in range(cA)]
                                steps.append(f"   (A·B)[{i+1},{j+1}] = " + " + ".join(terms) + f" = {R[i][j]}")
                        RT = transpose(R)
                        result_matrix = RT
                        steps.append("   Ahora transponemos el resultado:")
                        for i in range(len(R)):
                            for j in range(len(R[0])):
                                steps.append(f"   ((A·B)^T)[{j+1},{i+1}] = (A·B)[{i+1},{j+1}] = {R[i][j]}")
                        steps.append("6) Resultado final:")
                        for ln in mat_lines(RT): steps.append("     " + ln)
                    else:
                        steps.append("   La operación NO está definida porque columnas de A ≠ filas de B.")
                        steps.append("6) Resultado final:")
                        steps.append("   Operación indefinida.")

                elif self.rb_xTA_T.isChecked():
                    title = "x^T · A^T"
                    result_matrix = None
                    show_inputs()
                    steps.append("3) Cálculo de transpuestas (si aplica):")
                    XB = transpose(B) if B is not None else None
                    TA = transpose(A)
                    steps.append(f"   x^T (transpuesta de B) dim {dims(XB)}")
                    for ln in mat_lines(XB): steps.append("     " + ln)
                    steps.append(f"   A^T dim {dims(TA)}")
                    for ln in mat_lines(TA): steps.append("     " + ln)
                    steps.append("4) Verificación de dimensiones:")
                    rXB = len(XB) if XB is not None else 0; cXB = len(XB[0]) if rXB else 0
                    rTA = len(TA); cTA = len(TA[0]) if rTA else 0
                    steps.append(f"   x^T dim {rXB}x{cXB}; A^T dim {rTA}x{cTA}.")
                    steps.append("   Regla: columnas de la primera deben coincidir con filas de la segunda.")
                    ok = (cXB == rTA)
                    if ok:
                        steps.append("   La operación está definida porque las dimensiones son compatibles.")
                        R = mul(XB, TA)
                        result_matrix = R
                        steps.append("5) Cálculo paso a paso:")
                        for i in range(len(R)):
                            for j in range(len(R[0])):
                                terms = [f"{XB[i][k]}·{TA[k][j]}" for k in range(rTA)]
                                steps.append(f"   R[{i+1},{j+1}] = " + " + ".join(terms) + f" = {R[i][j]}")
                        steps.append("6) Resultado final:")
                        for ln in mat_lines(R): steps.append("     " + ln)
                    else:
                        steps.append("   La operación NO está definida porque columnas de x^T ≠ filas de A^T.")
                        steps.append("6) Resultado final:")
                        steps.append("   Operación indefinida.")

                elif self.rb_xxT.isChecked():
                    title = "x · x^T"
                    result_matrix = None
                    show_inputs()
                    steps.append("3) Cálculo de transpuestas (si aplica):")
                    XT = transpose(B) if B is not None else None
                    steps.append(f"   x dim {dims(B)}; x^T dim {dims(XT)}")
                    steps.append("4) Verificación de dimensiones:")
                    rB = len(B) if B is not None else 0; cB = len(B[0]) if rB else 0
                    steps.append(f"   x dim {rB}x{cB}; x^T dim {dims(XT)}")
                    steps.append("   Regla: columnas de la primera deben coincidir con filas de la segunda.")
                    ok = (cB == (len(XT) if XT is not None else 0))
                    if ok:
                        steps.append("   La operación está definida porque las dimensiones son compatibles.")
                        R = mul(B, XT)
                        result_matrix = R
                        steps.append("5) Cálculo paso a paso:")
                        # inner dimension = número de columnas de B
                        m = len(B[0]) if (B and len(B[0])>0) else 0
                        for i in range(len(R)):
                            for j in range(len(R[0])):
                                terms = [f"{B[i][k]}·{XT[k][j]}" for k in range(m)]
                                steps.append(f"   R[{i+1},{j+1}] = " + " + ".join(terms) + f" = {R[i][j]}")
                        steps.append("6) Resultado final:")
                        for ln in mat_lines(R): steps.append("     " + ln)
                    else:
                        steps.append("   La operación NO está definida porque columnas de x ≠ filas de x^T.")
                        steps.append("6) Resultado final:")
                        steps.append("   Operación indefinida.")

                elif self.rb_xTx.isChecked():
                    title = "x^T · x"
                    result_matrix = None
                    show_inputs()
                    steps.append("3) Cálculo de transpuestas (si aplica):")
                    XT = transpose(B) if B is not None else None
                    steps.append(f"   x^T dim {dims(XT)}; x dim {dims(B)}")
                    steps.append("4) Verificación de dimensiones:")
                    rXT = len(XT) if XT is not None else 0; cXT = len(XT[0]) if rXT else 0
                    rB = len(B) if B is not None else 0; cB = len(B[0]) if rB else 0
                    steps.append(f"   x^T dim {rXT}x{cXT}; x dim {rB}x{cB}.")
                    steps.append("   Regla: columnas de la primera deben coincidir con filas de la segunda.")
                    ok = (cXT == rB)
                    if ok:
                        steps.append("   La operación está definida porque las dimensiones son compatibles.")
                        R = mul(XT, B)
                        result_matrix = R
                        steps.append("5) Cálculo paso a paso:")
                        # scalar 1x1
                        terms = [f"{XT[0][k]}·{B[k][0]}" for k in range(rB)]
                        value = R[0][0]
                        steps.append("   x^T x = " + " + ".join(terms) + f" = {value}")
                        for k in range(rB):
                            prod = XT[0][k] * B[k][0]
                            steps.append(f"     componente {k+1}: {XT[0][k]}·{B[k][0]} = {prod}")
                        steps.append("6) Resultado final:")
                        steps.append(f"   Escalar resultante: {value}")
                    else:
                        steps.append("   La operación NO está definida porque columnas de x^T ≠ filas de x.")
                        steps.append("6) Resultado final:")
                        steps.append("   Operación indefinida.")
                else:
                    raise ValueError("Operación no soportada")

            # mostrar resultado y pasos
            # Mostrar la matriz destacada si existe; si no existe, informar al usuario con un popup
            try:
                if result_matrix is not None:
                    try:
                        self._show_matrix_result(result_matrix, title=title or "Resultado")
                    except Exception:
                        pass
                else:
                    # intentar extraer una línea de razón desde los pasos
                    reason = None
                    for ln in steps:
                        if "NO está definida" in ln or "Operación indefinida" in ln or "NO está definida porque" in ln:
                            reason = ln
                            break
                    if not reason and steps:
                        # fallback: tomar las últimas líneas de pasos
                        reason = "\n".join(steps[-3:])
                    try:
                        QMessageBox.warning(self, "Operación indefinida", self._format_error_message(reason or "La operación no está definida."))
                    except Exception:
                        pass
            except Exception:
                pass
            self.result_box.clear()
            for idx, s in enumerate(steps, start=1 if steps and steps[0].startswith('1)') else 1):
                self.result_box.insertPlainText(s + "\n")

            # actualizar última matriz mostrada (para historial)
            try:
                self._last_shown_matrix = result_matrix
                self._last_shown_title = title
                self._last_shown_steps = "\n".join(steps)
                try: self.btn_hist_save.setEnabled(True)
                except Exception: pass
            except Exception:
                pass

        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def _open_expanded_result(self):
        T = getattr(self, "_last_transpose", None)
        if not T:
            QMessageBox.information(self, "Sin resultado", "Primero calcula la transpuesta.")
            return
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Matriz resultante (Transpuesta)")
            lay = QVBoxLayout(dlg)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(_matrix_widget(self, T))
            lay.addWidget(scroll)
            dlg.resize(640, 480)
            dlg.exec()
        except Exception:
            pass

    def _toggle_adv(self, show: bool):
        try:
            self.adv_panel.setVisible(bool(show))
        except Exception:
            pass

    def _crear_b(self):
        # construir la grilla B en self.grid_b según b_rows/b_cols
        try:
            for i in reversed(range(self.grid_b.count())):
                w = self.grid_b.itemAt(i).widget()
                if w:
                    w.setParent(None)
        except Exception:
            pass
        try:
            rows = int(self.b_rows.text()); cols = int(self.b_cols.text())
        except Exception:
            QMessageBox.warning(self, "Aviso", "Dimensiones B inválidas")
            return
        self.vector_entries = []
        for i in range(rows):
            row = []
            for j in range(cols):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.grid_b.addWidget(e, i, j)
                row.append(e)
            self.vector_entries.append(row)

    # --- Evaluador de expresiones avanzado ---
    def _read_B(self):
        if not getattr(self, 'vector_entries', None):
            return None
        rows = len(self.vector_entries)
        cols = len(self.vector_entries[0]) if rows and isinstance(self.vector_entries[0], list) else 1
        B = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(_parse_fraction(self.vector_entries[i][j].text()))
            B.append(row)
        return B

    def _transpose(self, M):
        if M is None:
            return None
        r = len(M); c = len(M[0]) if r else 0
        return [[M[i][j] for i in range(r)] for j in range(c)]

    def _mul(self, A, B):
        if A is None or B is None:
            raise ValueError("Operación requiere dos operandos")
        ra = len(A); ca = len(A[0]) if ra else 0
        rb = len(B); cb = len(B[0]) if rb else 0
        if ca != rb:
            raise ValueError(f"Operación no definida: {ca} columnas != {rb} filas")
        R = [[Fraction(0) for _ in range(cb)] for __ in range(ra)]
        for i in range(ra):
            for j in range(cb):
                s = Fraction(0)
                for k in range(ca):
                    s += A[i][k] * B[k][j]
                R[i][j] = s
        return R

    def _preprocess_expr(self, s: str) -> str:
        s = (s or "").replace(' ', '')
        out = ''
        prev = ''
        for ch in s:
            if prev and ((prev in 'ABx)') and (ch in 'ABx(')):
                out += '*'
            out += ch
            prev = ch
        return out

    def _tokenize(self, s: str):
        tokens = []
        i = 0
        while i < len(s):
            if s[i].isalpha():
                if s[i] in ('A','B','x'):
                    if i+2 <= len(s)-1 and s[i+1] == '^' and s[i+2] == 'T':
                        tokens.append(s[i]); tokens.append('^T'); i += 3; continue
                    tokens.append(s[i]); i += 1; continue
                else:
                    raise ValueError('Token desconocido: '+s[i])
            if s.startswith('^T', i):
                tokens.append('^T'); i += 2; continue
            if s[i] in '+-*()':
                tokens.append(s[i]); i += 1; continue
            if s[i].isspace():
                i += 1; continue
            raise ValueError('Caracter invalido: '+s[i])
        return tokens

    def _to_postfix(self, tokens):
        out = []; ops = []
        prec = {'+':1,'-':1,'*':2}
        for t in tokens:
            if t in ('A','B','x'):
                out.append(t)
            elif t == '^T':
                out.append('^T')
            elif t in prec:
                while ops and ops[-1] in prec and prec[ops[-1]] >= prec[t]:
                    out.append(ops.pop())
                ops.append(t)
            elif t == '(':
                ops.append(t)
            elif t == ')':
                while ops and ops[-1] != '(':
                    out.append(ops.pop())
                if not ops: raise ValueError('Paréntesis desbalanceados')
                ops.pop()
            else:
                raise ValueError('Token inesperado: '+str(t))
        while ops:
            if ops[-1] in '()': raise ValueError('Paréntesis desbalanceados')
            out.append(ops.pop())
        return out

    def _eval_postfix(self, postfix, A, B):
        # Use named operands on the stack so we can generate readable step descriptions.
        stack = []  # elements are tuples (name, matrix)
        pasos = []
        temp_idx = 1

        def mat_to_lines(M):
            return [" ".join(str(v) for v in row) for row in M]

        for t in postfix:
            if t == 'A':
                stack.append(('A', A))
            elif t == 'B':
                if B is None: raise ValueError('B no definida')
                stack.append(('B', B))
            elif t == 'x':
                if B is None: raise ValueError('x (B) no definida')
                if len(B[0]) != 1:
                    raise ValueError('x requiere que B sea un vector columna (1 columna)')
                stack.append(('x', B))
            elif t == '^T':
                if not stack: raise ValueError('^T sin operando')
                name, mat = stack.pop()
                R = self._transpose(mat)
                new_name = f"C{temp_idx}"
                temp_idx += 1
                pasos.append(f"Paso: Transponer {name} -> {new_name}")
                pasos.extend(mat_to_lines(R))
                stack.append((new_name, R))
            elif t in ('+','-','*'):
                if len(stack) < 2: raise ValueError('Operandos insuficientes')
                right_name, right = stack.pop()
                left_name, left = stack.pop()
                new_name = f"C{temp_idx}"
                temp_idx += 1
                if t == '+':
                    R = [[left[i][j] + right[i][j] for j in range(len(left[0]))] for i in range(len(left))]
                    pasos.append(f"Paso: Suma {left_name} + {right_name} -> {new_name}")
                    pasos.append("Suma elemento a elemento:")
                    for i in range(len(R)):
                        row_expr = "   ".join(f"{left[i][j]}+{right[i][j]}" for j in range(len(R[0])))
                        pasos.append(row_expr)
                    pasos.append("Resultado intermedio {} = {}:" .format(new_name, ''))
                    pasos.extend(mat_to_lines(R))
                elif t == '-':
                    R = [[left[i][j] - right[i][j] for j in range(len(left[0]))] for i in range(len(left))]
                    pasos.append(f"Paso: Resta {left_name} - {right_name} -> {new_name}")
                    pasos.append("Resta elemento a elemento:")
                    for i in range(len(R)):
                        row_expr = "   ".join(f"{left[i][j]}-{right[i][j]}" for j in range(len(R[0])))
                        pasos.append(row_expr)
                    pasos.append("Resultado intermedio {} = {}:" .format(new_name, ''))
                    pasos.extend(mat_to_lines(R))
                else:
                    R = self._mul(left, right)
                    pasos.append(f"Paso: Multiplicación {left_name} · {right_name} -> {new_name}")
                    pasos.append("Calcular entradas como suma de productos:")
                    for i in range(len(R)):
                        for j in range(len(R[0])):
                            terms = [f"{left[i][k]}·{right[k][j]}" for k in range(len(left[0]))]
                            pasos.append(f"R[{i+1},{j+1}] = " + " + ".join(terms) + f" = {R[i][j]}")
                stack.append((new_name, R))
            else:
                raise ValueError('Token desconocido: '+str(t))
        if len(stack) != 1: raise ValueError('Expresión inválida; pila final: '+str(len(stack)))
        final_name, final_mat = stack[0]
        return final_mat, pasos

    def _format_error_message(self, msg) -> str:
        """Convertir mensajes técnicos a un texto claro en español."""
        try:
            s = str(msg or "").strip()
        except Exception:
            return "Operación indefinida."
        sl = s.lower()
        if "list index out of range" in sl:
            return "Índice fuera de rango: probablemente las dimensiones de las matrices no coinciden o la expresión accede a una posición inexistente. Revisa las dimensiones y la expresión."
        if "columnas" in sl and "filas" in sl:
            return "Dimensiones incompatibles: las columnas de la primera matriz no coinciden con las filas de la segunda. Ajusta las dimensiones."
        if "b no definida" in sl or "b is none" in sl:
            return "La matriz/vector B no está definida. Crea B antes de usarla en la expresión."
        if "x requiere" in sl or "x (b) no definida" in sl or "x (b)" in sl:
            return "Vector x no definido o B no es un vector columna. Asegura que B tenga una sola columna para usarlo como vector x."
        if "operandos insuficientes" in sl or "insuficientes" in sl:
            return "Expresión inválida: faltan operandos para algún operador. Revisa la sintaxis de la expresión."
        if "paréntesis" in sl or "desbalance" in sl:
            return "Expresión inválida: paréntesis desbalanceados o mal colocados. Revisa los paréntesis."
        # fallback: devolver mensaje con prefijo en español
        return "Operación indefinida: " + s

    def _eval_expression(self):
        pass

    # Historial helpers
    def _history_save(self):
        try:
            M = getattr(self, '_last_shown_matrix', None)
            title = getattr(self, '_last_shown_title', None)
            pasos = getattr(self, '_last_shown_steps', None)
            if M is None:
                # if last_result_matrix holds something useful, use it
                M = getattr(self, '_last_result_matrix', None)
            if M is None:
                QMessageBox.information(self, "Nada para guardar", "No hay resultado visible para guardar en el historial.")
                return
            idx = len(self.results_history) + 1
            item_title = f"{idx}. {title}"
            self.results_history.append((item_title, M, pasos))
            self.history_list.addItem(item_title)
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def _history_show(self):
        try:
            cur = self.history_list.currentRow()
            if cur < 0 or cur >= len(self.results_history):
                QMessageBox.information(self, "Selecciona uno", "Selecciona un resultado del historial para mostrar.")
                return
            title, M, pasos = self.results_history[cur]
            self._show_matrix_result(M, title=title)
            if pasos:
                self.result_box.clear()
                self.result_box.insertPlainText(title + "\n\n" + pasos)
            # actualizar preview
            try:
                self.history_preview.setWidget(_matrix_widget(self, M))
            except Exception:
                pass
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def _history_del(self):
        try:
            cur = self.history_list.currentRow()
            if cur < 0:
                return
            self.history_list.takeItem(cur)
            del self.results_history[cur]
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))


class DeterminanteMatrizWindow(_BaseMatrixWindow):
    def __init__(self, parent=None):
        super().__init__("Determinante de Matriz", parent)
        # En determinante queremos que los resultados queden justo debajo del botón y con scroll general
        try:
            # Eliminar el panel de matriz resultante (no se usa aquí) para evitar huecos
            self.lay.removeWidget(self.result_matrix_block)
            self.result_matrix_block.setParent(None)
            # Mover el cuadro de resultados debajo del botón Calcular
            self.lay.removeWidget(self.result_container)
            self.result_box.setMinimumHeight(200)
            self.actions_layout.setSpacing(6)
            self.actions_layout.addWidget(self.result_container)
            self.actions_layout.addStretch(1)
        except Exception:
            pass
        try:
            inner = self.centralWidget()
            scroll_host = QScrollArea()
            scroll_host.setWidgetResizable(True)
            scroll_host.setWidget(inner)
            wrapper = QWidget()
            wrap_lay = QVBoxLayout(wrapper)
            wrap_lay.setContentsMargins(0, 0, 0, 0)
            wrap_lay.setSpacing(0)
            wrap_lay.addWidget(scroll_host)
            self.setCentralWidget(wrapper)
        except Exception:
            pass

    def _run(self):
        A = self._leer()
        det, steps = determinante_con_pasos_ascii(A)
        self.result_box.clear()
        self.result_box.insertPlainText("Pasos detallados\n\n")
        for s in steps:
            self.result_box.insertPlainText(s + "\n")
        self.result_box.insertPlainText(f"\nDeterminante: {det}\n")


# LÃ³gica de determinante con el mismo formato que Tk
def determinante_con_pasos(matrix, level: int = 0):
    # Wrapper hacia versión ASCII limpia
    return determinante_con_pasos_ascii(matrix, level)

def determinante_con_pasos_ascii(matrix, level: int = 0):
    n = len(matrix)
    indent = "    " * level
    steps = []
    sep = indent + ("-" * 70)

    def fmt(x: Fraction) -> str:
        return str(x.numerator) if isinstance(x, Fraction) and x.denominator == 1 else str(x)

    def mat_lines(M, ind=""):
        return [ind + "[ " + "  ".join(fmt(c) for c in r) + " ]" for r in M]

    def is_upper(M):
        for i in range(1, len(M)):
            for j in range(0, i):
                if M[i][j] != 0: return False
        return True

    def is_lower(M):
        for i in range(len(M)):
            for j in range(i+1, len(M)):
                if M[i][j] != 0: return False
        return True

    def minor(M, r, c):
        return [[M[i][j] for j in range(len(M)) if j != c] for i in range(len(M)) if i != r]

    if n == 1:
        value = matrix[0][0]
        steps.append(f"{indent}Caso base 1x1: det(A) = {fmt(value)}")
        return value, steps

    if n == 2:
        a11, a12 = matrix[0]
        a21, a22 = matrix[1]
        p1 = a11*a22; p2 = a12*a21; det = p1-p2
        steps.append(f"{indent}Caso base 2x2:")
        steps.extend(mat_lines(matrix, indent+"    "))
        steps.append(f"{indent}|A| = {fmt(a11)}*{fmt(a22)} - {fmt(a12)}*{fmt(a21)}")
        steps.append(f"{indent}    = {fmt(p1)} - {fmt(p2)}")
        steps.append(f"{indent}    = {fmt(det)}")
        return det, steps

    if is_upper(matrix) or is_lower(matrix):
        tipo = "superior" if is_upper(matrix) else "inferior"
        diag = [matrix[i][i] for i in range(n)]
        det = Fraction(1)
        for v in diag: det *= v
        steps.append(f"{indent}La matriz es triangular {tipo}.")
        steps.append(f"{indent}Producto de la diagonal principal: {' * '.join(fmt(v) for v in diag)} = {fmt(det)}")
        return det, steps

    steps.append(f"{indent}Expansion por cofactores a lo largo de la primera fila")
    steps.append(f"{indent}det(A) = " + " + ".join(f"a1{j+1}C1{j+1}" for j in range(n)))
    contrib = []
    for j in range(n):
        a = matrix[0][j]
        sgn = Fraction(1 if j%2==0 else -1)
        steps.append(sep)
        steps.append(f"{indent}Elemento a1{j+1} = {fmt(a)} (signo {'+' if sgn>0 else '-'})")
        if a == 0:
            steps.append(f"{indent}Como a1{j+1} = 0, su contribucion es nula y se omite.")
            contrib.append(Fraction(0)); continue
        sub = minor(matrix,0,j)
        steps.append(f"{indent}Submatriz M1{j+1} (eliminando fila 1 y columna {j+1}):")
        steps.extend(mat_lines(sub, indent+"    "))
        sd, sd_steps = determinante_con_pasos_ascii(sub, level+1)
        steps.extend(sd_steps)
        steps.append(f"{indent}det(M1{j+1}) = {fmt(sd)}")
        c = sgn*sd
        steps.append(f"{indent}C1{j+1} = ({'+' if sgn>0 else '-'}1) * {fmt(sd)} = {fmt(c)}")
        term = a*c
        steps.append(f"{indent}Contribucion parcial: {fmt(a)} * {fmt(c)} = {fmt(term)}")
        contrib.append(term)
    steps.append(sep)
    total = sum(contrib, Fraction(0))
    steps.append(f"{indent}Suma total de contribuciones: det(A) = " + " + ".join(fmt(x) for x in contrib) + f" = {fmt(total)}")
    return total, steps
class InversaMatrizWindow(_BaseMatrixWindow):
    def __init__(self, parent=None):
        super().__init__("Inversa de Matriz", parent)
        # Añadir selección de método y opción de animar
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Método:"))
        self.rb_adj = QRadioButton("Adjunta (1×1,2×2,3×3)")
        self.rb_gj = QRadioButton("Gauss-Jordan")
        self.rb_adj.setChecked(True)
        method_row.addWidget(self.rb_adj)
        method_row.addWidget(self.rb_gj)
        method_row.addStretch(1)
        self.cb_anim = QCheckBox("Animar paso a paso")
        method_row.addWidget(self.cb_anim)
        # Insertar el row antes del resultado (result_box está al final); lo insertamos
        # en la posición anterior al último widget para que aparezca sobre el resultado.
        self.lay.insertLayout(self.lay.count() - 1, method_row)

        # Visual container (para mostrar matrices cofactores/adjunta/inversa de forma visual)
        self.visual_frame = QFrame()
        self.visual_frame.setLayout(QHBoxLayout())
        self.visual_frame.layout().setSpacing(18)
        self.lay.insertWidget(self.lay.count() - 1, self.visual_frame)

    def _setup_entries(self):
        # Fuerza matriz cuadrada: usa filas para columnas
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)
        n = int(self.f_edit.text())
        self.c_edit.setText(str(n))
        self.entries = []
        g = QGridLayout(); g.setHorizontalSpacing(6); g.setVerticalSpacing(6)
        box = QFrame(); box.setLayout(g)
        self.grid.addWidget(QLabel("Matriz A (nÃ—n)"), 0, 0, alignment=Qt.AlignHCenter)
        self.grid.addWidget(box, 1, 0)
        for i in range(n):
            row = []
            for j in range(n):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                g.addWidget(e, i, j)
                row.append(e)
            self.entries.append(row)
        self.btn_run.setEnabled(True)

    def _run(self):
        A = self._leer()
        n = len(A)
        if n == 0 or any(len(r) != n for r in A):
            QMessageBox.warning(self, "Aviso", "Ingrese una matriz cuadrada nÃ—n.")
            return
        # convertir a Fraction y construir identidad
        Aw = [[_parse_fraction(str(x)) for x in row] for row in A]
        Iw = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]

        def augmented_lines(Ax, Ix):
            ancho = 1
            for i in range(n):
                for v in Ax[i] + Ix[i]:
                    ancho = max(ancho, len(str(v)))
            lines = []
            for i in range(n):
                left = " ".join(str(x).rjust(ancho) for x in Ax[i])
                right = " ".join(str(x).rjust(ancho) for x in Ix[i])
                lines.append(f"{left}   |   {right}")
            return lines

        def operacion_vertical_aug(fp, fa, f, fr):
            # fp, fa, fr ya son filas completas (A|I) como listas
            ancho = max(len(str(x)) for x in fr) if fr else 1
            def fmt(lst):
                return " ".join(str(x).rjust(ancho) for x in lst)
            escala = [(-f) * val for val in fp]
            factor_str = f"+{abs(f)}" if f < 0 else f"-{f}"
            lines = [
                f"{factor_str}R : {fmt(escala)}",
                f"+R        : {fmt(fa)}",
                " " * 10 + "-" * (ancho * len(fr) + len(fr) - 1),
                f"=R        : {fmt(fr)}",
            ]
            return lines

        # helper: limpiar visuales y resultado
        def _clear_visuals():
            lay = self.visual_frame.layout()
            for i in reversed(range(lay.count())):
                w = lay.itemAt(i).widget()
                if w:
                    w.setParent(None)

        _clear_visuals()
        self.result_box.clear()

        # RREF helper (copiado y adaptado de la versión Tk)
        def rref_info(A_matrix):
            M = [row[:] for row in A_matrix]
            rows = len(M); cols = len(M[0]) if rows else 0
            row = 0
            piv_cols = []
            for col in range(cols):
                if row >= rows:
                    break
                piv = None
                for r in range(row, rows):
                    if M[r][col] != 0:
                        piv = r; break
                if piv is None:
                    continue
                if piv != row:
                    M[row], M[piv] = M[piv], M[row]
                a = M[row][col]
                if a != 1:
                    M[row] = [v / a for v in M[row]]
                for r in range(rows):
                    if r == row: continue
                    f = M[r][col]
                    if f != 0:
                        M[r] = [M[r][j] - f * M[row][j] for j in range(cols)]
                piv_cols.append(col)
                row += 1
            free_cols = [j for j in range(cols) if j not in piv_cols]
            return M, piv_cols, free_cols

        def explain_cde(A_matrix):
            R, piv_cols, free_cols = rref_info(A_matrix)
            lines = []
            lines.append("Comprobación de invertibilidad (c, d, e):")
            lines.append("")
            lines.append("RREF de A:")
            if R:
                maxw = max(len(str(v)) for fila in R for v in fila)
                for fila in R:
                    lines.append(" ".join(str(v).rjust(maxw) for v in fila))
            lines.append("")
            nA = len(A_matrix)
            if len(piv_cols) != nA:
                lines.append(f"- (c) No tiene n posiciones pivote: {len(piv_cols)} de {nA}.")
            else:
                lines.append(f"- (c) Tiene n posiciones pivote: {len(piv_cols)} de {nA}.")
            if free_cols:
                j0 = free_cols[0]
                x = [Fraction(0) for _ in range(nA)]
                x[j0] = Fraction(1)
                for r, pc in enumerate(piv_cols):
                    if j0 < len(R[0]):
                        x[pc] = -R[r][j0]
                lines.append("")
                lines.append("- (d) Existe solución no trivial para Ax = 0. Ejemplo:")
                lines.append("x = [ " + ", ".join(str(v) for v in x) + " ]ᵗ")
                lines.append("")
                lines.append("- (e) Por consiguiente, las columnas de A son linealmente dependientes (no LI).")
            else:
                lines.append("")
                lines.append("- (d) Ax=0 solo tiene la solución trivial.")
                lines.append("- (e) Las columnas de A son linealmente independientes.")
            return lines

        def explain_cde_text(A_matrix):
            """Return a single string with the explanation lines joined for message boxes."""
            return "\n".join(explain_cde(A_matrix))

        # Ejecutar Gauss-Jordan solo si no se eligió explícitamente el método Adjunta
        pivot_cols = []
        if not (self.rb_adj.isChecked() and n <= 3):
            # Mostrar la matriz aumentada inicial [A | I]
            _clear_visuals()
            box_start = QFrame(); box_start.setLayout(QVBoxLayout())
            box_start.layout().addWidget(QLabel("Matriz aumentada [A | I]:"))
            h = QHBoxLayout()
            h.addWidget(_matrix_widget(self, Aw))
            h.addWidget(_matrix_widget(self, Iw))
            box_start.layout().addLayout(h)
            self.visual_frame.layout().addWidget(box_start)

            fila_pivote = 0
            for col in range(n):
                piv = None
                for r in range(fila_pivote, n):
                    if Aw[r][col] != 0:
                        piv = r; break
                if piv is None:
                    continue
                if piv != fila_pivote:
                    Aw[fila_pivote], Aw[piv] = Aw[piv], Aw[fila_pivote]
                    Iw[fila_pivote], Iw[piv] = Iw[piv], Iw[fila_pivote]
                    self.result_box.insertPlainText("Operación: ")
                    self.result_box.insertPlainText(f"R{fila_pivote+1} \u2194 R{piv+1}\n\n")
                    for ln in augmented_lines(Aw, Iw):
                        self.result_box.insertPlainText(ln + "\n")
                    self.result_box.insertPlainText("\n" + ("-" * 110) + "\n\n")

                a = Aw[fila_pivote][col]
                if a == 0:
                    fila_pivote += 1
                    if fila_pivote >= n:
                        break
                    continue
                if a != 1:
                    Aw[fila_pivote] = [v / a for v in Aw[fila_pivote]]
                    Iw[fila_pivote] = [v / a for v in Iw[fila_pivote]]
                    self.result_box.insertPlainText("Operación: ")
                    self.result_box.insertPlainText(f"R{fila_pivote+1} \u2192 R{fila_pivote+1}/{a}\n\n")
                    for ln in augmented_lines(Aw, Iw):
                        self.result_box.insertPlainText(ln + "\n")
                    self.result_box.insertPlainText("\n" + ("-" * 110) + "\n\n")

                for r in range(n):
                    if r == fila_pivote: continue
                    f = Aw[r][col]
                    if f == 0: continue
                    origA = Aw[r][:]; origI = Iw[r][:]
                    pivA = Aw[fila_pivote][:]; pivI = Iw[fila_pivote][:]
                    Aw[r] = [origA[j] - f * pivA[j] for j in range(n)]
                    Iw[r] = [origI[j] - f * pivI[j] for j in range(n)]
                    fp = pivA + pivI
                    fa = origA + origI
                    fr = Aw[r] + Iw[r]
                    left_lines = operacion_vertical_aug(fp, fa, f, fr)
                    right_lines = augmented_lines(Aw, Iw)
                    self.result_box.insertPlainText("Operación: ")
                    self.result_box.insertPlainText(f"R{r+1} \u2192 R{r+1} - ({f})R{fila_pivote+1}\n\n")
                    max_left = max(len(s) for s in left_lines) if left_lines else 0
                    sep = "   |   "
                    max_len = max(len(left_lines), len(right_lines))
                    for i in range(max_len):
                        l = left_lines[i] if i < len(left_lines) else ""
                        rr = right_lines[i] if i < len(right_lines) else ""
                        self.result_box.insertPlainText(l.ljust(max_left) + (sep if rr else "") + rr + "\n")
                    self.result_box.insertPlainText("\n" + ("-" * 110) + "\n\n")

                pivot_cols.append(col)
                fila_pivote += 1
                if fila_pivote >= n: break

        # Determinar si hay n pivotes (nota: si se saltó GJ, pivot_cols estará vacío)
        invertible_by_piv = (len(pivot_cols) == n)

        # Si Gauss-Jordan se ejecutó y la matriz es invertible, mostrar visualmente
        # la transformación final [I | A^-1] de forma ordenada en la interfaz.
        if not (self.rb_adj.isChecked() and n <= 3) and invertible_by_piv:
            _clear_visuals()
            box_final_left = QFrame(); box_final_left.setLayout(QVBoxLayout())
            box_final_left.layout().addWidget(QLabel("Matriz Identidad(I):"))
            box_final_left.layout().addWidget(_matrix_widget(self, Aw))
            box_final_right = QFrame(); box_final_right.setLayout(QVBoxLayout())
            box_final_right.layout().addWidget(QLabel("Matriz Inversa (A⁻¹):"))
            box_final_right.layout().addWidget(_matrix_widget(self, Iw))
            self.visual_frame.layout().addWidget(box_final_left)
            self.visual_frame.layout().addWidget(box_final_right)
            # También añadir una sección textual final en el recuadro de pasos
            self.result_box.insertPlainText("\nMatriz aumentada final [I | A⁻¹]:\n")
            for ln in augmented_lines(Aw, Iw):
                self.result_box.insertPlainText(ln + "\n")

        # Si Gauss-Jordan se ejecutó (pivot_cols no vacío) y no es invertible, mostrar diálogo
        if pivot_cols and len(pivot_cols) != n:
            # Construir mensaje explicativo usando las reglas c/d/e
            expl = explain_cde_text(Aw)
            QMessageBox.critical(self, "Sin inversa (Gauss-Jordan)", "La matriz no es invertible.\n\n" + expl)
            # Además anexar la explicación al cuadro de pasos para evidencia
            self.result_box.insertPlainText("\n" + expl + "\n")
            # Si se llegó aquí por elegir Adjunta pero n>3, no return — dejar que flujo continúe.
            # Si se llegó por GJ deliberado, no continuar con adjunta mostrando matrices.
            if not (self.rb_adj.isChecked() and n <= 3):
                return

        # Si el usuario eligió adjunta y la dimensión es adecuada, usar adjunta
        if self.rb_adj.isChecked():
            if n > 3:
                QMessageBox.information(self, "Info", "Adjunta solo disponible para n ≤ 3. Usando Gauss-Jordan.")
            else:
                # Calcular determinante
                det, det_steps = determinante_con_pasos_ascii(Aw)

                # Helper para submatrices
                def minor(M, r, c):
                    return [[M[i][j] for j in range(len(M)) if j != c] for i in range(len(M)) if i != r]

                # Helper para formatear submatrices en varias líneas
                def format_submatrix(M):
                    if not M:
                        return "[]"
                    rows = ["[" + ", ".join(str(x) for x in r) + "]" for r in M]
                    if len(rows) == 1:
                        return "[" + rows[0] + "]"
                    return "[" + ",\n           ".join(rows) + "]"

                # Mostrar el procedimiento del determinante de forma ordenada (expansión por cofactores
                # en la primera fila). Si resulta 0, NO se muestran matrices, sólo este procedimiento
                # y un mensaje claro al usuario.
                self.result_box.insertPlainText("1) Cálculo del determinante |A|\n")
                self.result_box.insertPlainText("Expansión por cofactores en la primera fila:\n\n")

                # Para cada elemento de la primera fila mostrar su menor y el valor del cofactor
                first_row_contribs = []
                for j in range(n):
                    sub = minor(Aw, 0, j)
                    sub_det, _ = determinante_con_pasos_ascii(sub)
                    sign = 1 if (j % 2 == 0) else -1
                    cofactor = Fraction(sign) * sub_det

                    # Formatear submatriz en bloque alineado (cada fila en su propia línea)
                    sub_rows = ["[" + ", ".join(str(x) for x in r) + "]" for r in sub]
                    if len(sub_rows) == 1:
                        sub_block = sub_rows[0]
                        self.result_box.insertPlainText(
                            f"M1{j+1} = det({sub_block}) = {sub_det}   →  C1{j+1} = ({'+' if sign>0 else '-'})·{sub_det} = {cofactor}\n\n"
                        )
                    else:
                        sub_block = "[\n" + "\n".join("    " + r for r in sub_rows) + "\n]"
                        self.result_box.insertPlainText(
                            f"M1{j+1} = det({sub_block}) = {sub_det}   →  C1{j+1} = ({'+' if sign>0 else '-'})·{sub_det} = {cofactor}\n\n"
                        )

                    first_row_contribs.append((Aw[0][j], cofactor))

                # Fórmula por cofactores y evaluación
                terms = " + ".join(f"a1{j+1}·C1{j+1}" for j in range(n))
                self.result_box.insertPlainText("|A| = " + terms + "\n")
                eval_terms = " + ".join(f"({Aw[0][j]})({first_row_contribs[j][1]})" for j in range(n))
                self.result_box.insertPlainText("    = " + eval_terms + "\n")
                total = sum(Aw[0][j] * first_row_contribs[j][1] for j in range(n))
                self.result_box.insertPlainText(f"    = {total}\n\n")

                # Si el determinante es cero, mostrar mensaje crítico y un bloque de conclusión
                if total == 0:
                    QMessageBox.critical(self, "Sin inversa", "La matriz no es invertible porque su determinante es 0.")
                    # Mensaje final con formato claro y alineado
                    self.result_box.insertPlainText("Resultado:\n\n")
                    self.result_box.insertPlainText("El determinante de la matriz es 0.\n\n")
                    self.result_box.insertPlainText("Esto significa que la matriz no es invertible,\n")
                    self.result_box.insertPlainText("ya que su determinante es igual a cero.\n\n")
                    self.result_box.insertPlainText("Por lo tanto, no existe la matriz inversa A⁻¹.\n\n")
                    # además mostrar la explicación c/d/e en el recuadro para aportar evidencia adicional
                    for l in explain_cde(Aw):
                        self.result_box.insertPlainText(l + "\n")
                    return

                # Si det != 0, entonces construir cofactores y adjunta
                cof = [[None for _ in range(n)] for __ in range(n)]
                for i in range(n):
                    for j in range(n):
                        sub = minor(Aw, i, j)
                        sub_det, _ = determinante_con_pasos(sub)
                        cof[i][j] = Fraction((1 if ((i + j) % 2 == 0) else -1)) * sub_det

                # adjunta = transpuesta de cofactores
                adj = [[cof[j][i] for j in range(n)] for i in range(n)]

                # Mostrar visualmente: A, Adj(A), A^{-1}
                _clear_visuals()
                boxA = QFrame(); boxA.setLayout(QVBoxLayout())
                boxA.layout().addWidget(QLabel("Matriz A:"))
                boxA.layout().addWidget(_matrix_widget(self, Aw))
                boxAdj = QFrame(); boxAdj.setLayout(QVBoxLayout())
                boxAdj.layout().addWidget(QLabel("Adj(A) (transpuesta de la matriz de cofactores):"))
                boxAdj.layout().addWidget(_matrix_widget(self, adj))

                # preparar contenedor para la inversa
                boxInv = QFrame(); boxInv.setLayout(QVBoxLayout())
                boxInv.layout().addWidget(QLabel("A⁻¹ (inversa):"))

                self.visual_frame.layout().addWidget(boxA)
                self.visual_frame.layout().addWidget(boxAdj)
                self.visual_frame.layout().addWidget(boxInv)

                # Formato mejorado y legible del recuadro de pasos
                # 1) Cálculo del determinante |A| por expansión por cofactores en la primera fila
                self.result_box.insertPlainText("1) Calculo del determinante |A|\n")
                self.result_box.insertPlainText("Expansión por cofactores en la primera fila:\n\n")
                # Listar M1j y C1j para j=1..n con espacios y saltos claros
                for j in range(n):
                    sub = minor(Aw, 0, j)
                    sub_det, sub_steps = determinante_con_pasos_ascii(sub)
                    sign = 1 if (j % 2 == 0) else -1
                    sub_fmt = format_submatrix(sub)
                    self.result_box.insertPlainText(f"M1{j+1} = det({sub_fmt}) = {sub_det}\n")
                    # añadir una línea con flecha → C1j
                    self.result_box.insertPlainText(f"    -> C1{j+1} = ({'+' if sign>0 else '-'})·{sub_det} = {Fraction(sign)*sub_det}\n\n")

                # fórmula del determinante por cofactores (primera fila) y evaluación
                terms = " + ".join(f"a1{j+1}·C1{j+1}" for j in range(n))
                self.result_box.insertPlainText("|A| = " + terms + "\n")
                eval_terms = " + ".join(f"({Aw[0][j]})({Fraction(cof[0][j])})" for j in range(n))
                self.result_box.insertPlainText("    = " + eval_terms + "\n")
                total = sum(Aw[0][j] * cof[0][j] for j in range(n))
                self.result_box.insertPlainText(f"    = {total}\n\n")

                # Si el determinante es cero, informar y mostrar el diálogo de error.
                if total == 0:
                    QMessageBox.critical(self, "Sin inversa", "La matriz no es invertible porque su determinante es 0.")
                    # Ya mostramos el procedimiento del determinante arriba; terminar.
                    return

                # 2) Matriz de cofactores de A (tabla compacta)
                self.result_box.insertPlainText("2) Matriz de cofactores de A\n")
                sep = "-" * 75
                self.result_box.insertPlainText(sep + "\n")
                self.result_box.insertPlainText("| Posición |       M_ij (submatriz)       | det(M_ij) |  C_ij  |\n")
                self.result_box.insertPlainText(sep + "\n")
                for i in range(n):
                    for j in range(n):
                        sub = minor(Aw, i, j)
                        sub_det, _ = determinante_con_pasos_ascii(sub)
                        cij = cof[i][j]
                        sub_str = format_submatrix(sub)
                        # separar visualmente cada fila
                        self.result_box.insertPlainText(f"| C{i+1}{j+1} | {sub_str:<30} | {str(sub_det):>8} | {str(cij):>6} |\n")

                # 3) Matriz Adjunta
                self.result_box.insertPlainText("3) Matriz Adjunta\n")
                self.result_box.insertPlainText("Adj(A) = (Cof(A))ᵀ  (traspuesta de la matriz de cofactores)\n\n")
                for ln in (" ".join(str(v) for v in row) for row in adj):
                    self.result_box.insertPlainText(ln + "\n")
                self.result_box.insertPlainText("\n")

                # 4) Cálculo de la inversa (det != 0 en este punto)
                inv = [[adj[i][j] / total for j in range(n)] for i in range(n)]
                # Mostrar resultado numérico y visual
                boxInv.layout().addWidget(_matrix_widget(self, inv))
                self.visual_frame.layout().addWidget(boxInv)
                self.result_box.insertPlainText("4) Cálculo de la inversa\n")
                self.result_box.insertPlainText(f"Como |A| = {total},\nA⁻¹ = (1 / |A|) · Adj(A)\n")
                self.result_box.insertPlainText(f"A⁻¹ = (1 / {total}) · Adj(A)\n\n")
                self.result_box.insertPlainText("A⁻¹ =\n")
                for ln in (" ".join(str(v) for v in row) for row in inv):
                    self.result_box.insertPlainText(ln + "\n")

                # Conclusión (comprobación c/d/e)
                self.result_box.insertPlainText("\nConclusión: la matriz es invertible y la inversa se ha calculado como arriba.\n\n")
                for l in explain_cde(Aw):
                    self.result_box.insertPlainText(l + "\n")
                return

        # Si llegamos aquí, proceder con Gauss-Jordan (sea por selección o por limitación de adjunta)
        if not self.cb_anim.isChecked():
            # mostrar explicación aunque no se anime
            pass

        if not invertible_by_piv:
            # Mostrar pasos (ya se hicieron) y justificar con c/d/e
            self.result_box.insertPlainText("\nLa matriz no es invertible (no se encontraron n pivotes).\n\n")
            for l in explain_cde(Aw):
                self.result_box.insertPlainText(l + "\n")
            return

        # Mostrar inversa
        self.result_box.insertPlainText("Matriz inversa:\n\n")
        self.result_box.insertPlainText("\n".join(" ".join(str(v) for v in row) for row in Iw) + "\n")
        # mensaje final: es invertible y por qué
        self.result_box.insertPlainText("\nConclusión: La matriz es invertible porque:\n")
        for l in explain_cde(Aw):
            self.result_box.insertPlainText(l + "\n")






