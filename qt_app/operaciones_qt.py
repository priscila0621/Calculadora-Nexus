from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFrame,
    QMessageBox,
    QToolButton,
    QMenu,
    QScrollArea,
    QComboBox,
    QDialog,
    QTextEdit as QTextEditWidget,
    QDialogButtonBox,
    QInputDialog,
    QListWidget,
    QTabWidget,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextCursor
from fractions import Fraction
from determinante_matriz_app import determinante_con_pasos
from .theme import bind_font_scale_stylesheet, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from .settings_qt import open_settings_dialog


class _ClickCombo(QComboBox):
    """Combo compacto que se despliega al hacer click."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setMinimumWidth(220)
        self.setCursor(Qt.PointingHandCursor)
        self.setEditable(False)


def _parse_fraction(s: str) -> Fraction:
    s = (s or "").strip().replace(",", ".")
    if s == "":
        return Fraction(0)
    return Fraction(s)


def _fmt(x: Fraction) -> str:
    return f"{x.numerator}" if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


class OperacionesMatricesWindow(QMainWindow):
    """
    Interprete de expresiones con matrices, vectores y escalares.
    Ejemplos: A(u+v), Au + Av, 3A + 2B, A(Bu + Cv), M*(u - 3v)
    Reglas: sumas entre mismo tipo/dimension; productos escalar*X, X*escalar,
    matriz*matriz y matriz*vector (no vector*matriz).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Algebra de matrices y vectores")
        self.objects = {}  # nombre -> {"type": "matrix"/"vector"/"scalar", "value": ...}
        self.matrix_entries = []
        self.vector_entries = []
        self.saved_results = []  # lista de {'name', 'expr', 'proc', 'result'}
        self._last_eval = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer = QWidget()
        scroll.setWidget(outer)
        self.setCentralWidget(scroll)

        root = QVBoxLayout(outer)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

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
        more_btn.setMenu(menu)
        topbar.addWidget(more_btn, 0, Qt.AlignRight)
        root.addLayout(topbar)

        title = QLabel("Algebra de matrices y vectores")
        title.setObjectName("Title")
        root.addWidget(title)

        subtitle = QLabel(
            "Define matrices, vectores y escalares, guardalos con un nombre (A, B, u, v, c...) "
            "y escribe una expresion como A(u+v), 3A+2B o A(Bu+Cv). El motor valida dimensiones automaticamente."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("Subtitle")
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(14)
        root.addLayout(content, 1)

        # Panel izquierdo
        left = QVBoxLayout()
        left.setSpacing(10)
        content.addLayout(left, 1)
        left.addWidget(self._build_matrix_card())
        left.addWidget(self._build_vector_card())
        left.addWidget(self._build_scalar_card())
        left.addWidget(self._build_objects_card(), 1)

        # Panel derecho
        right = QVBoxLayout()
        right.setSpacing(10)
        content.addLayout(right, 1)
        right.addWidget(self._build_expression_card())
        right.addWidget(self._build_result_card(), 1)

    def _open_settings(self):
        try:
            open_settings_dialog(self)
        except Exception:
            pass

    # ---------------- UI ----------------
    def _card(self, title: str):
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)
        lbl = QLabel(title)
        lbl.setObjectName("CardTitle")
        lay.addWidget(lbl)
        return card, lay

    def _build_matrix_card(self) -> QFrame:
        card, lay = self._card("Crear matriz")
        form = QHBoxLayout(); form.setSpacing(8)
        self.mat_name = QLineEdit("A"); self.mat_name.setFixedWidth(60)
        self.mat_rows = QLineEdit("2"); self.mat_rows.setFixedWidth(60); self.mat_rows.setAlignment(Qt.AlignCenter)
        self.mat_cols = QLineEdit("2"); self.mat_cols.setFixedWidth(60); self.mat_cols.setAlignment(Qt.AlignCenter)
        form.addWidget(QLabel("Nombre:")); form.addWidget(self.mat_name)
        form.addWidget(QLabel("Filas:")); form.addWidget(self.mat_rows)
        form.addWidget(QLabel("Columnas:")); form.addWidget(self.mat_cols)
        btn_grid = QPushButton("Crear tablero"); btn_grid.clicked.connect(self._crear_tablero_matriz)
        form.addWidget(btn_grid)
        lay.addLayout(form)

        self.matrix_grid_container = QFrame()
        self.matrix_grid = QGridLayout(self.matrix_grid_container)
        self.matrix_grid.setHorizontalSpacing(6); self.matrix_grid.setVerticalSpacing(6)
        lay.addWidget(self.matrix_grid_container)

        btn_save = QPushButton("Guardar matriz")
        btn_save.clicked.connect(self._guardar_matriz)
        lay.addWidget(btn_save, alignment=Qt.AlignRight)
        return card

    def _build_vector_card(self) -> QFrame:
        card, lay = self._card("Crear vector")
        form = QHBoxLayout(); form.setSpacing(8)
        self.vec_name = QLineEdit("u"); self.vec_name.setFixedWidth(60)
        self.vec_dim = QLineEdit("2"); self.vec_dim.setFixedWidth(60); self.vec_dim.setAlignment(Qt.AlignCenter)
        form.addWidget(QLabel("Nombre:")); form.addWidget(self.vec_name)
        form.addWidget(QLabel("Dimension:")); form.addWidget(self.vec_dim)
        btn_grid = QPushButton("Crear tablero"); btn_grid.clicked.connect(self._crear_tablero_vector)
        form.addWidget(btn_grid)
        lay.addLayout(form)

        self.vector_grid_container = QFrame()
        self.vector_grid = QVBoxLayout(self.vector_grid_container); self.vector_grid.setSpacing(6)
        lay.addWidget(self.vector_grid_container)

        btn_save = QPushButton("Guardar vector")
        btn_save.clicked.connect(self._guardar_vector)
        lay.addWidget(btn_save, alignment=Qt.AlignRight)
        return card

    def _build_scalar_card(self) -> QFrame:
        card, lay = self._card("Definir escalar")
        row = QHBoxLayout(); row.setSpacing(8)
        self.sca_name = QLineEdit("c"); self.sca_name.setFixedWidth(60)
        self.sca_val = QLineEdit("1"); self.sca_val.setFixedWidth(90); self.sca_val.setAlignment(Qt.AlignCenter)
        row.addWidget(QLabel("Nombre:")); row.addWidget(self.sca_name)
        row.addWidget(QLabel("Valor:")); row.addWidget(self.sca_val)
        btn = QPushButton("Guardar escalar"); btn.clicked.connect(self._guardar_escalar)
        row.addWidget(btn)
        lay.addLayout(row)
        return card

    def _build_objects_card(self) -> QFrame:
        card, lay = self._card("Objetos guardados")
        self.objects_list = QListWidget()
        self.objects_list.setSelectionMode(QListWidget.SingleSelection)
        bind_font_scale_stylesheet(self.objects_list, "font-family:Consolas,monospace;font-size:{body}px;", body=12)
        self.objects_list.setMinimumHeight(200)
        self.objects_list.itemSelectionChanged.connect(self._sync_object_actions)
        lay.addWidget(self.objects_list, 1)

        lay.addWidget(QLabel("Acciones sobre el objeto seleccionado en la lista:"))
        combo_row = QHBoxLayout(); combo_row.setSpacing(6)
        self.btn_edit_obj = QPushButton("Editar")
        self.btn_edit_obj.setFixedHeight(32)
        self.btn_edit_obj.clicked.connect(self._on_edit_obj)
        combo_row.addWidget(self.btn_edit_obj)
        self.btn_rename_obj = QPushButton("Renombrar")
        self.btn_rename_obj.setFixedHeight(32)
        self.btn_rename_obj.clicked.connect(self._on_rename_obj)
        combo_row.addWidget(self.btn_rename_obj)
        self.btn_delete_obj = QPushButton("Eliminar")
        self.btn_delete_obj.setFixedHeight(32)
        self.btn_delete_obj.clicked.connect(self._on_delete_obj)
        combo_row.addWidget(self.btn_delete_obj)
        combo_row.addStretch(1)
        lay.addLayout(combo_row)
        self._object_action_buttons = [self.btn_edit_obj, self.btn_rename_obj, self.btn_delete_obj]

        self._refresh_objects_view()
        return card

    def _build_expression_card(self) -> QFrame:
        card, lay = self._card("Expresion algebraica")
        info = QLabel("Ejemplos: A(u+v), Au + Av, 3A + 2B, A(Bu + Cv), M*(u - 3v). El motor valida dimensiones por ti.")
        info.setWordWrap(True)
        lay.addWidget(info)

        templates_row = QHBoxLayout(); templates_row.setSpacing(8)
        templates_row.addWidget(QLabel("Plantillas guiadas:"))
        for label, builder in self._template_buttons():
            btn = QPushButton(label)
            btn.setMinimumHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, fn=builder: self._apply_template(fn()))
            templates_row.addWidget(btn)
        templates_row.addStretch(1)
        lay.addLayout(templates_row)

        ops_row = QHBoxLayout(); ops_row.setSpacing(6)
        ops_row.addWidget(QLabel("Atajos de simbolos:"))
        for sym in ["+", "-", "*", "(", ")"]:
            b = QPushButton(sym)
            b.setFixedWidth(54)
            b.setMinimumHeight(32)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, t=sym: self._insert_text(t))
            ops_row.addWidget(b)
        ops_row.addStretch(1)
        lay.addLayout(ops_row)

        lay.addWidget(QLabel("Objetos guardados (click para desplegar e insertar en la expresion):"))
        self.shortcuts_list = _ClickCombo()
        self.shortcuts_list.activated.connect(self._on_combo_selected)
        lay.addWidget(self.shortcuts_list)

        self.expr_edit = QTextEdit()
        self.expr_edit.setPlaceholderText("Escribe aqui la expresion...")
        self.expr_edit.setFixedHeight(90)
        lay.addWidget(self.expr_edit)
        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Limpiar"); btn_clear.clicked.connect(self._limpiar_pantalla)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch(1)
        btn = QPushButton("Calcular"); btn.clicked.connect(self._calcular_expresion)
        btn_row.addWidget(btn)
        lay.addLayout(btn_row)
        self._refresh_shortcuts()
        return card

    def _build_result_card(self) -> QFrame:
        card, lay = self._card("Resultado")
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        clear_btn = QPushButton("Limpiar pantalla"); clear_btn.clicked.connect(self._limpiar_pantalla)
        save_btn = QPushButton("Guardar resultado"); save_btn.clicked.connect(self._guardar_resultado)
        show_btn = QPushButton("Mostrar guardados"); show_btn.clicked.connect(self._mostrar_guardados)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(show_btn)
        btn_row.addStretch(1)
        lay.addLayout(btn_row)

        self.result_box = QTextEdit(); self.result_box.setReadOnly(True)
        bind_font_scale_stylesheet(self.result_box, "font-family:Consolas,monospace;font-size:{body}px;", body=12)
        lay.addWidget(self.result_box, 1)
        return card

    # ---------------- Tableros ----------------
    def _clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setParent(None)
            else:
                layout.removeItem(item)

    def _crear_tablero_matriz(self):
        try:
            m = int(self.mat_rows.text()); n = int(self.mat_cols.text())
            if m <= 0 or n <= 0:
                raise ValueError
        except Exception:
            QMessageBox.warning(self, "Aviso", "Dimensiones de matriz no validas.")
            return
        self._clear_layout(self.matrix_grid)
        self.matrix_entries = []
        for i in range(m):
            row = []
            for j in range(n):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.matrix_grid.addWidget(e, i, j)
                row.append(e)
            self.matrix_entries.append(row)

    def _crear_tablero_vector(self):
        try:
            n = int(self.vec_dim.text())
            if n <= 0:
                raise ValueError
        except Exception:
            QMessageBox.warning(self, "Aviso", "Dimension de vector no valida.")
            return
        self._clear_layout(self.vector_grid)
        self.vector_entries = []
        for _ in range(n):
            e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
            self.vector_grid.addWidget(e)
            self.vector_entries.append(e)

    # ---------------- Guardar objetos ----------------
    def _guardar_matriz(self):
        nombre = (self.mat_name.text() or "").strip()
        if not (nombre.isalpha() and len(nombre) == 1):
            QMessageBox.warning(self, "Aviso", "Usa un nombre de matriz de una sola letra (ej: A, B, M).")
            return
        if nombre in self.objects:
            QMessageBox.warning(self, "Aviso", "Ese nombre ya existe. Usa otra letra.")
            return
        if not self.matrix_entries:
            self._crear_tablero_matriz()
        try:
            m = len(self.matrix_entries); n = len(self.matrix_entries[0])
            A = []
            for i in range(m):
                fila = [_parse_fraction(self.matrix_entries[i][j].text()) for j in range(n)]
                A.append(fila)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Error en datos de la matriz: {exc}")
            return
        final_name = self._unique_name(nombre)
        self.objects[final_name] = {"type": "matrix", "value": A}
        self._refresh_objects_view()

    def _guardar_vector(self):
        nombre = (self.vec_name.text() or "").strip()
        if not (nombre.isalpha() and len(nombre) == 1):
            QMessageBox.warning(self, "Aviso", "Usa un nombre de vector de una sola letra (ej: u, v, w).")
            return
        if nombre in self.objects:
            QMessageBox.warning(self, "Aviso", "Ese nombre ya existe. Usa otra letra.")
            return
        if not self.vector_entries:
            self._crear_tablero_vector()
        try:
            vec = [_parse_fraction(e.text()) for e in self.vector_entries]
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Error en datos del vector: {exc}")
            return
        final_name = self._unique_name(nombre)
        self.objects[final_name] = {"type": "vector", "value": vec}
        self._refresh_objects_view()

    def _guardar_escalar(self):
        nombre = (self.sca_name.text() or "").strip()
        if not (nombre.isalpha() and len(nombre) == 1):
            QMessageBox.warning(self, "Aviso", "Usa un nombre de escalar de una sola letra (ej: a, b, c).")
            return
        if nombre in self.objects:
            QMessageBox.warning(self, "Aviso", "Ese nombre ya existe. Usa otra letra.")
            return
        try:
            val = _parse_fraction(self.sca_val.text())
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Valor invalido: {exc}")
            return
        final_name = self._unique_name(nombre)
        self.objects[final_name] = {"type": "scalar", "value": val}
        self._refresh_objects_view()

    def _unique_name(self, base):
        return base

    def _refresh_objects_view(self):
        self.objects_list.clear()
        for k in sorted(self.objects.keys()):
            obj = self.objects[k]
            if obj["type"] == "scalar":
                label = f"{k}: escalar = {_fmt(obj['value'])}"
            elif obj["type"] == "vector":
                label = f"{k}: vector dim {len(obj['value'])} -> [{', '.join(_fmt(x) for x in obj['value'])}]"
            else:
                m = len(obj["value"]); n = len(obj["value"][0]) if m else 0
                label = f"{k}: matriz {m}x{n}"
            self.objects_list.addItem(label)
        has_objs = self.objects_list.count() > 0
        for b in getattr(self, "_object_action_buttons", []):
            b.setEnabled(has_objs and self._selected_object_name() is not None)
        if hasattr(self, "shortcuts_list"):
            self._refresh_shortcuts()
        self._sync_object_actions()

    def _refresh_shortcuts(self):
        self.shortcuts_list.clear()
        names = sorted(self.objects.keys())
        if not names:
            self.shortcuts_list.addItem("Guarda matrices, vectores o escalares...")
            self.shortcuts_list.setEnabled(False)
            for b in getattr(self, "_object_action_buttons", []):
                b.setEnabled(False)
            return
        self.shortcuts_list.setEnabled(True)
        for b in getattr(self, "_object_action_buttons", []):
            b.setEnabled(True)
        self.shortcuts_list.addItem("Selecciona y se insertara...")
        for name in names:
            self.shortcuts_list.addItem(name)
        self.shortcuts_list.setCurrentIndex(0)
        # Mantener seleccion en lista de objetos si coincide
        if self.objects_list.count() > 0:
            self.objects_list.setCurrentRow(0)

    def _insert_text(self, text: str):
        cursor = self.expr_edit.textCursor()
        cursor.insertText(text)
        self.expr_edit.setTextCursor(cursor)
        self.expr_edit.setFocus()

    def _on_combo_selected(self, index: int):
        if index <= 0:
            return
        text = self.shortcuts_list.itemText(index)
        self._insert_text(text)
        self.shortcuts_list.setCurrentIndex(0)
        # sincroniza botones con seleccion de lista si coincide
        items = self.objects_list.findItems(f"{text}:", Qt.MatchStartsWith)
        if items:
            self.objects_list.setCurrentItem(items[0])
        self._sync_object_actions()

    def _selected_object_name(self):
        sel = self.objects_list.currentItem()
        if sel is None:
            return None
        text = sel.text()
        name = text.split(":", 1)[0].strip()
        return name if name in self.objects else None

    def _on_delete_obj(self):
        name = self._selected_object_name()
        if not name:
            QMessageBox.information(self, "Selecciona objeto", "Primero elige un objeto para eliminar.")
            return
        confirm = QMessageBox.question(self, "Confirmar", f"¿Eliminar '{name}'?")
        if confirm != QMessageBox.Yes:
            return
        try:
            self.objects.pop(name, None)
            self._refresh_objects_view()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo eliminar: {exc}")
        self._sync_object_actions()

    def _on_rename_obj(self):
        name = self._selected_object_name()
        if not name:
            QMessageBox.information(self, "Selecciona objeto", "Primero elige un objeto para renombrar.")
            return
        new, ok = QInputDialog.getText(self, "Renombrar objeto", "Nuevo nombre:", text=name)
        if not ok:
            return
        new = (new or "").strip()
        if not new.isalpha():
            QMessageBox.warning(self, "Aviso", "Usa solo letras para el nombre.")
            return
        if new in self.objects and new != name:
            QMessageBox.warning(self, "Aviso", "Ya existe un objeto con ese nombre.")
            return
        try:
            self.objects[new] = self.objects.pop(name)
            self._refresh_objects_view()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo renombrar: {exc}")
        self._sync_object_actions()

    def _on_edit_obj(self):
        name = self._selected_object_name()
        if not name:
            QMessageBox.information(self, "Selecciona objeto", "Primero elige un objeto para editar.")
            return
        obj = self.objects.get(name)
        if not obj:
            return
        tip = obj["type"]
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Editar {name}")
        lay = QVBoxLayout(dlg)
        hint = QLabel(self._edit_hint(tip))
        hint.setWordWrap(True)
        lay.addWidget(hint)
        editor = QTextEditWidget()
        editor.setMinimumHeight(140)
        editor.setText(self._edit_prefill(obj))
        lay.addWidget(editor)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        if dlg.exec() != QDialog.Accepted:
            return
        try:
            new_obj = self._parse_edit_content(tip, editor.toPlainText())
            self.objects[name] = new_obj
            self._refresh_objects_view()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {exc}")
        self._sync_object_actions()

    def _edit_hint(self, tip: str) -> str:
        if tip == "scalar":
            return "Escalar: escribe un numero (fraccion opcional, ej. 3/2)."
        if tip == "vector":
            return "Vector: un valor por linea."
        return "Matriz: separa filas por lineas y valores por espacios o comas."

    def _edit_prefill(self, obj):
        if obj["type"] == "scalar":
            return _fmt(obj["value"])
        if obj["type"] == "vector":
            return "\n".join(_fmt(x) for x in obj["value"])
        if obj["type"] == "matrix":
            return "\n".join(" ".join(_fmt(x) for x in row) for row in obj["value"])
        return ""

    def _parse_edit_content(self, tip: str, text: str):
        text = (text or "").strip()
        if tip == "scalar":
            return {"type": "scalar", "value": _parse_fraction(text or "0")}
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() != ""]
        if tip == "vector":
            vals = [_parse_fraction(x) for x in lines] if lines else [Fraction(0)]
            return {"type": "vector", "value": vals}
        # matrix
        rows = []
        for ln in lines:
            parts = [p for p in ln.replace(",", " ").split() if p]
            rows.append([_parse_fraction(p) for p in parts])
        if not rows:
            rows = [[Fraction(0)]]
        # ensure rectangular
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            raise ValueError("Todas las filas deben tener la misma cantidad de columnas.")
        return {"type": "matrix", "value": rows}

    def _sync_object_actions(self):
        selected = self._selected_object_name()
        enabled = selected is not None
        for b in getattr(self, "_object_action_buttons", []):
            b.setEnabled(enabled)

    def _apply_template(self, text: str):
        self.expr_edit.setPlainText(text)
        cursor = self.expr_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.expr_edit.setTextCursor(cursor)
        self.expr_edit.setFocus()

    def _template_buttons(self):
        def first_of_type(t, fallback):
            obj = self.objects.get(fallback)
            if obj and obj.get("type") == t:
                return fallback
            return fallback

        def second_matrix(primary):
            return "B" if primary != "B" else "C"

        def template_av():
            A = first_of_type("matrix", "A")
            u = first_of_type("vector", "u")
            v = "v" if u != "v" else "w"
            return f"{A}({u}+{v})"

        def template_distrib():
            A = first_of_type("matrix", "A")
            u = first_of_type("vector", "u")
            v = "v" if u != "v" else "w"
            return f"{A}{u} + {A}{v}"

        def template_lineal_combo():
            A = first_of_type("matrix", "A")
            B = second_matrix(A)
            return f"3{A} + 2{B}"

        def template_nested():
            A = first_of_type("matrix", "A")
            B = second_matrix(A)
            u = first_of_type("vector", "u")
            c = first_of_type("scalar", "c")
            v = "v" if u != "v" else "w"
            return f"{A}({B}{u} + {c}{v})"

        def template_mix():
            A = first_of_type("matrix", "A")
            u = first_of_type("vector", "u")
            v = "v" if u != "v" else "w"
            return f"{A}*({u} - 3{v})"

        return [
            ("A(u+v)", template_av),
            ("Au + Av", template_distrib),
            ("3A + 2B", template_lineal_combo),
            ("A(Bu+Cv)", template_nested),
            ("A*(u-3v)", template_mix),
        ]

    # ---------------- Algebra ----------------
    def _add(self, a, b):
        ta, tb = a["type"], b["type"]
        if ta == 'identity_pending' or tb == 'identity_pending':
            a, b = self._coerce_identity_for_sum(a, b)
            ta, tb = a["type"], b["type"]
        if ta != tb:
            raise ValueError("Solo se pueden sumar objetos del mismo tipo.")
        if ta == "scalar":
            return {"type": "scalar", "value": a["value"] + b["value"]}
        if ta == "vector":
            if len(a["value"]) != len(b["value"]):
                raise ValueError("Los vectores deben tener la misma dimension.")
            return {"type": "vector", "value": [a["value"][i] + b["value"][i] for i in range(len(a['value']))]}
        ma = len(a["value"]); na = len(a["value"][0]) if ma else 0
        mb = len(b["value"]); nb = len(b["value"][0]) if mb else 0
        if ma != mb or na != nb:
            raise ValueError("Las matrices deben tener la misma dimension.")
        res = [[a["value"][i][j] + b["value"][i][j] for j in range(na)] for i in range(ma)]
        return {"type": "matrix", "value": res}

    def _sub(self, a, b):
        return self._add(a, self._mul({"type": "scalar", "value": Fraction(-1)}, b))

    def _mul(self, a, b):
        ta, tb = a["type"], b["type"]
        if ta == 'identity_pending' or tb == 'identity_pending':
            a, b = self._coerce_identity_for_mul(a, b)
            ta, tb = a["type"], b["type"]
        if ta == "scalar":
            val = a["value"]
            if tb == "scalar":
                return {"type": "scalar", "value": val * b["value"]}
            if tb == "vector":
                return {"type": "vector", "value": [val * x for x in b["value"]]}
            if tb == "matrix":
                return {"type": "matrix", "value": [[val * x for x in row] for row in b["value"]]}
        if tb == "scalar":
            return self._mul(b, a)
        if ta == "vector":
            raise ValueError("Solo se permite matriz * vector, no vector * matriz.")
        if ta == "matrix" and tb == "vector":
            A = a["value"]; v = b["value"]
            m = len(A); n = len(A[0]) if m else 0
            if len(v) != n:
                raise ValueError("Dimensiones incompatibles para A * v.")
            return {"type": "vector", "value": [sum(A[i][j] * v[j] for j in range(n)) for i in range(m)]}
        if ta == "matrix" and tb == "matrix":
            A, B = a["value"], b["value"]
            m = len(A); n = len(A[0]) if m else 0
            n2 = len(B); p = len(B[0]) if n2 else 0
            if n != n2:
                raise ValueError("Dimensiones incompatibles para A * B.")
            res = []
            for i in range(m):
                fila = []
                for j in range(p):
                    fila.append(sum(A[i][k] * B[k][j] for k in range(n)))
                res.append(fila)
            return {"type": "matrix", "value": res}
        raise ValueError("Operacion no soportada.")

    # ---------------- Parser ----------------
    def _tokenize(self, expr: str):
        expr = expr.replace(" ", "")
        tokens = []
        i = 0
        while i < len(expr):
            ch = expr[i]
            if ch in "+-*()":
                tokens.append(ch); i += 1; continue
            if ch == '^':
                # Soporta ^T, ^{-1} y ^(-1)
                if expr[i:i+2] == '^T':
                    tokens.append('^T'); i += 2; continue
                if expr[i:i+5] == '^{-1}':
                    tokens.append('^{-1}'); i += 5; continue
                if expr[i:i+5] == '^(-1)':
                    tokens.append('^{-1}'); i += 5; continue
                raise ValueError(f"Operador desconocido: {expr[i:i+5]}")
            if expr[i:i+4] == 'det(':  # det(A)
                tokens.append('det'); i += 3; continue
            if ch.isdigit():
                j = i
                while j < len(expr) and (expr[j].isdigit() or expr[j] == "/"):
                    j += 1
                tokens.append(expr[i:j]); i = j; continue
            if ch.isalpha():
                tokens.append(ch); i += 1; continue
            raise ValueError(f"Caracter invalido: {ch}")
        out = []
        def is_value(t):
            return t not in {'+', '-', '*', '(', ')', '^T', '^{-1}', 'det'}
        for idx, tok in enumerate(tokens):
            out.append(tok)
            if idx + 1 < len(tokens):
                a, b = tok, tokens[idx + 1]
                if (is_value(a) or a == ")") and (is_value(b) or b == "("):
                    out.append("*")
        return out

    def _parse(self, tokens):
        self._pos = 0
        self._tokens = tokens
        return self._parse_expr()

    def _peek(self):
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _eat(self, tok=None):
        cur = self._peek()
        if tok is not None and cur != tok:
            raise ValueError(f"Se esperaba '{tok}'")
        self._pos += 1
        return cur

    def _parse_expr(self):
        node = self._parse_term()
        while self._peek() in ("+", "-"):
            op = self._eat()
            rhs = self._parse_term()
            node = ("op", op, node, rhs)
        return node

    def _parse_term(self):
        node = self._parse_factor()
        while self._peek() == "*":
            self._eat("*")
            rhs = self._parse_factor()
            node = ("op", "*", node, rhs)
        return node

    def _parse_factor(self):
        tok = self._peek()
        if tok == "+":
            self._eat("+"); return self._parse_factor()
        if tok == "-":
            self._eat("-"); return ("op", "*", ("scalar", Fraction(-1)), self._parse_factor())
        if tok == "(":
            self._eat("(")
            node = self._parse_expr()
            if self._peek() != ")":
                raise ValueError("Falta cerrar parentesis")
            self._eat(")")
            # Soporta operadores postfijos ^T y ^{-1}
            if self._peek() in ["^T", "^{-1}"]:
                op = self._eat()
                return (op, node)
            return node
        if tok == "det":
            self._eat("det")
            if self._peek() != "(":
                raise ValueError("Se esperaba '('")
            self._eat("(")
            node = self._parse_expr()
            if self._peek() != ")":
                raise ValueError("Falta cerrar parentesis en det")
            self._eat(")")
            return ("det", node)
        if tok is None:
            raise ValueError("Expresion incompleta")
        self._eat()
        if tok.replace("/", "").isdigit():
            return ("scalar", _parse_fraction(tok))
        if tok.isalpha():
            if tok not in self.objects:
                if tok == "I":
                    self.objects['I'] = {'type': 'identity_pending'}
                else:
                    raise ValueError(f"Objeto '{tok}' no definido.")
            # Soporta operadores postfijos ^T y ^{-1}
            node = ("id", tok)
            if self._peek() in ["^T", "^{-1}"]:
                op = self._eat()
                return (op, node)
            return node
        raise ValueError(f"Token inesperado: {tok}")

    # ---------------- Evaluacion ----------------
    def _eval(self, node):
        kind = node[0]
        if kind == "scalar":
            return {"type": "scalar", "value": node[1]}
        if kind == "id":
            return self.objects[node[1]]
        if kind == "op":
            op, left, right = node[1], node[2], node[3]
            a = self._eval(left); b = self._eval(right)
            if op == "+":
                return self._add(a, b)
            if op == "-":
                return self._sub(a, b)
            if op == "*":
                return self._mul(a, b)
        if kind == "^T":
            val = self._eval(node[1])
            if val["type"] == "matrix":
                A = val["value"]
                m = len(A); n = len(A[0]) if m else 0
                T = [[A[j][i] for j in range(m)] for i in range(n)]
                return {"type": "matrix", "value": T}
            if val["type"] == "vector":
                v = val["value"]
                return {"type": "vector", "value": v}  # Vector columna, transpuesta es igual
            raise ValueError("Solo se puede transponer matrices o vectores.")
        if kind == "^{-1}":
            val = self._eval(node[1])
            if val["type"] != "matrix":
                raise ValueError("Solo se puede invertir matrices.")
            A = val["value"]
            return {"type": "matrix", "value": self._mat_inv(A)}
        if kind == "det":
            val = self._eval(node[1])
            if val["type"] != "matrix":
                raise ValueError("Solo se puede calcular el determinante de matrices.")
            A = val["value"]
            return {"type": "scalar", "value": self._mat_det(A)}
        raise ValueError("Nodo invalido.")
    def _mat_det(self, A):
        # Determinante por recursión (Laplace)
        m = len(A)
        n = len(A[0]) if m else 0
        if m != n:
            raise ValueError("La matriz no es cuadrada.")
        if m == 1:
            return A[0][0]
        if m == 2:
            return A[0][0]*A[1][1] - A[0][1]*A[1][0]
        det = Fraction(0)
        for j in range(n):
            minor = [[A[i][k] for k in range(n) if k != j] for i in range(1, m)]
            det += ((-1)**j) * A[0][j] * self._mat_det(minor)
        return det

    def _mat_inv(self, A):
        # Inversa por Gauss-Jordan
        m = len(A)
        n = len(A[0]) if m else 0
        if m != n:
            raise ValueError("La matriz no es cuadrada.")
        # Construir matriz aumentada [A | I]
        M = [[A[i][j] for j in range(n)] + [Fraction(int(i==j)) for j in range(n)] for i in range(n)]
        # Gauss-Jordan
        for i in range(n):
            # Buscar pivote
            if M[i][i] == 0:
                for k in range(i+1, n):
                    if M[k][i] != 0:
                        M[i], M[k] = M[k], M[i]
                        break
                else:
                    raise ValueError("La matriz no es invertible.")
            piv = M[i][i]
            for j in range(2*n):
                M[i][j] /= piv
            for k in range(n):
                if k != i:
                    fac = M[k][i]
                    for j in range(2*n):
                        M[k][j] -= fac * M[i][j]
        # Extraer inversa
        inv = [row[n:] for row in M]
        return inv

    # ---------- Helpers con pasos detallados ----------
    def _ensure_identity(self, n=None):
        if n is not None:
            if n <= 0:
                raise ValueError("Dimension de identidad invalida.")
            I = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]
            self.objects['I'] = {'type': 'matrix', 'value': I}
            return self.objects['I']
        if 'I' in self.objects and self.objects['I'].get('type') == 'matrix':
            return self.objects['I']
        # Busca la primera matriz cuadrada guardada para inferir dimension
        for name in sorted(self.objects.keys()):
            obj = self.objects[name]
            if obj.get('type') == 'matrix':
                m = len(obj['value']); p = len(obj['value'][0]) if m else 0
                if m == p and m > 0:
                    I = [[Fraction(1 if i == j else 0) for j in range(m)] for i in range(m)]
                    self.objects['I'] = {'type': 'matrix', 'value': I}
                    return self.objects['I']
        raise ValueError("No se puede inferir la matriz identidad: guarda antes una matriz cuadrada.")

    def _transpose_with_steps(self, A):
        m = len(A); n = len(A[0]) if m else 0
        steps = [f"Dimensiones: {m}x{n}. Se intercambian filas por columnas."]
        T = [[A[j][i] for j in range(m)] for i in range(n)]
        for i in range(n):
            col_vals = [_fmt(A[j][i]) for j in range(m)]
            row_vals = [_fmt(T[i][k]) for k in range(len(T[i]))]
            steps.append(f"Fila {i+1} de A^T se forma con columna {i+1} de A: ({', '.join(col_vals)}) -> [{', '.join(row_vals)}]")
        return T, steps

    def _det_with_steps(self, A):
        det, steps = determinante_con_pasos(A)
        return det, [s.replace("—", "-") for s in steps]

    def _inv_with_steps(self, A):
        n = len(A)
        if n == 0 or len(A[0]) != n:
            raise ValueError("La matriz no es cuadrada.")
        # Matriz aumentada
        I = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]
        M = [A[i][:] + I[i][:] for i in range(n)]
        steps = ["Construir matriz aumentada [A|I]:"]
        steps.extend(self._format_aug_lines(M, n))

        for col in range(n):
            # buscar pivote
            pivot = None
            for r in range(col, n):
                if M[r][col] != 0:
                    pivot = r; break
            if pivot is None:
                raise ValueError("La matriz no es invertible.")
            if pivot != col:
                M[col], M[pivot] = M[pivot], M[col]
                steps.append(f"Intercambiar R{col+1} con R{pivot+1} (pivote a la posicion {col+1}).")
                steps.extend(self._format_aug_lines(M, n))
            piv = M[col][col]
            if piv == 0:
                raise ValueError("La matriz no es invertible.")
            if piv != 1:
                M[col] = [x / piv for x in M[col]]
                steps.append(f"Normalizar R{col+1} dividiendo por {_fmt(piv)} para hacer pivote = 1.")
                steps.extend(self._format_aug_lines(M, n))
            for r in range(n):
                if r == col:
                    continue
                factor = M[r][col]
                if factor == 0:
                    continue
                M[r] = [M[r][c] - factor * M[col][c] for c in range(2*n)]
                steps.append(f"R{r+1} = R{r+1} - ({_fmt(factor)})·R{col+1} para anular columna {col+1}.")
                steps.extend(self._format_aug_lines(M, n))
        inv = [row[n:] for row in M]
        steps.append("Resultado: [I|A^{-1}] obtenido. Extraemos la parte derecha.")
        steps.extend(self._format_aug_lines(M, n))
        return inv, steps

    def _format_aug_lines(self, M, n):
        lines = []
        if not M:
            return lines
        left_cols = n
        maxw = max(len(_fmt(v)) for row in M for v in row)
        for row in M:
            left = " ".join(_fmt(v).rjust(maxw) for v in row[:left_cols])
            right = " ".join(_fmt(v).rjust(maxw) for v in row[left_cols:])
            lines.append(f"  {left} | {right}")
        return lines

    # ---------- Identidad dinámica ----------
    def _coerce_identity_for_sum(self, a, b):
        # Para suma/resta: ambos deben ser matrices mismas dimensiones
        if a['type'] == 'identity_pending' and b['type'] == 'matrix':
            m = len(b['value']); n = len(b['value'][0]) if m else 0
            if m != n:
                raise ValueError("La identidad debe ser cuadrada y del mismo tamaño que la otra matriz.")
            a = self._ensure_identity(m)
        if b['type'] == 'identity_pending' and a['type'] == 'matrix':
            m = len(a['value']); n = len(a['value'][0]) if m else 0
            if m != n:
                raise ValueError("La identidad debe ser cuadrada y del mismo tamaño que la otra matriz.")
            b = self._ensure_identity(m)
        return a, b

    def _coerce_identity_for_mul(self, a, b):
        # I * A  -> n = filas de A
        # A * I  -> n = columnas de A
        if a['type'] == 'identity_pending':
            if b['type'] != 'matrix':
                raise ValueError("La identidad solo puede multiplicarse con matrices.")
            n = len(b['value'])
            a = self._ensure_identity(n)
        if b['type'] == 'identity_pending':
            if a['type'] != 'matrix':
                raise ValueError("La identidad solo puede multiplicarse con matrices.")
            n = len(a['value'][0]) if len(a['value']) else 0
            b = self._ensure_identity(n)
        return a, b

    def _eval_with_log(self, node, log):
        kind = node[0]
        if kind == "scalar":
            return {"type": "scalar", "value": node[1]}, _fmt(node[1])
        if kind == "id":
            return self.objects[node[1]], node[1]
        if kind == "op":
            op, left, right = node[1], node[2], node[3]
            a, a_label = self._eval_with_log(left, log)
            b, b_label = self._eval_with_log(right, log)
            # compute result
            if op == "+":
                res = self._add(a, b)
                log.append(f"{a_label} + {b_label} -> {self._describe_obj(res)}")
                # Detallar elemento a elemento
                if res["type"] == "scalar":
                    log.append(f"  {_fmt(a['value'])} + {_fmt(b['value'])} = {_fmt(res['value'])}")
                elif res["type"] == "vector":
                    for i in range(len(res['value'])):
                        log.append(f"  v[{i+1}]: {_fmt(a['value'][i])} + {_fmt(b['value'][i])} = {_fmt(res['value'][i])}")
                elif res["type"] == "matrix":
                    m = len(res['value']); n = len(res['value'][0]) if m else 0
                    for i in range(m):
                        parts = []
                        for j in range(n):
                            parts.append(f"({_fmt(a['value'][i][j])} + {_fmt(b['value'][i][j])})={_fmt(res['value'][i][j])}")
                        log.append(f"  fila {i+1}: " + ", ".join(parts))
                return res, f"({a_label}+{b_label})"
            if op == "-":
                res = self._sub(a, b)
                log.append(f"{a_label} - {b_label} -> {self._describe_obj(res)}")
                if res["type"] == "scalar":
                    log.append(f"  {_fmt(a['value'])} - {_fmt(b['value'])} = {_fmt(res['value'])}")
                elif res["type"] == "vector":
                    for i in range(len(res['value'])):
                        log.append(f"  v[{i+1}]: {_fmt(a['value'][i])} - {_fmt(b['value'][i])} = {_fmt(res['value'][i])}")
                elif res["type"] == "matrix":
                    m = len(res['value']); n = len(res['value'][0]) if m else 0
                    for i in range(m):
                        parts = []
                        for j in range(n):
                            parts.append(f"({_fmt(a['value'][i][j])} - {_fmt(b['value'][i][j])})={_fmt(res['value'][i][j])}")
                        log.append(f"  fila {i+1}: " + ", ".join(parts))
                return res, f"({a_label}-{b_label})"
            if op == "*":
                res = self._mul(a, b)
                log.append(f"{a_label} * {b_label} -> {self._describe_obj(res)}")
                # Detallar segun tipos
                if a['type'] == 'scalar' and b['type'] == 'scalar':
                    log.append(f"  {_fmt(a['value'])} * {_fmt(b['value'])} = {_fmt(res['value'])}")
                elif a['type'] == 'scalar' and b['type'] == 'vector':
                    for i, val in enumerate(res['value']):
                        log.append(f"  v[{i+1}]: {_fmt(a['value'])} * {_fmt(b['value'][i])} = {_fmt(val)}")
                elif a['type'] == 'scalar' and b['type'] == 'matrix':
                    m = len(res['value']); n = len(res['value'][0]) if m else 0
                    for i in range(m):
                        parts = []
                        for j in range(n):
                            parts.append(f"{_fmt(a['value'])}*{_fmt(b['value'][i][j])}={_fmt(res['value'][i][j])}")
                        log.append(f"  fila {i+1}: " + ", ".join(parts))
                elif a['type'] == 'matrix' and b['type'] == 'vector':
                    A = a['value']; v = b['value']
                    for i in range(len(res['value'])):
                        parts = [f"{_fmt(A[i][j])}*{_fmt(v[j])}" for j in range(len(v))]
                        summ = " + ".join(parts)
                        log.append(f"  fila {i+1}: {summ} = {_fmt(res['value'][i])}")
                elif a['type'] == 'matrix' and b['type'] == 'matrix':
                    A = a['value']; B = b['value']
                    m = len(res['value']); p = len(res['value'][0]) if m else 0
                    for i in range(m):
                        for j in range(p):
                            parts = [f"{_fmt(A[i][k])}*{_fmt(B[k][j])}" for k in range(len(B))]
                            summ = " + ".join(parts)
                            log.append(f"  fila {i+1},col {j+1}: {summ} = {_fmt(res['value'][i][j])}")
                elif a['type'] == 'matrix' and b['type'] == 'scalar':
                    m = len(res['value']); n = len(res['value'][0]) if m else 0
                    for i in range(m):
                        parts = []
                        for j in range(n):
                            parts.append(f"{_fmt(a['value'][i][j])}*{_fmt(b['value'])}={_fmt(res['value'][i][j])}")
                        log.append(f"  fila {i+1}: " + ", ".join(parts))
                elif a['type'] == 'vector' and b['type'] == 'scalar':
                    for i, val in enumerate(res['value']):
                        log.append(f"  v[{i+1}]: {_fmt(a['value'][i])} * {_fmt(b['value'])} = {_fmt(val)}")
                return res, f"{a_label}*{b_label}"
        if kind == "^T":
            val, val_label = self._eval_with_log(node[1], log)
            if val["type"] == "matrix":
                A = val["value"]
                T, pasos = self._transpose_with_steps(A)
                log.append(f"Operacion: Transpuesta de {val_label}")
                log.extend([f"  {p}" for p in pasos])
                return {"type": "matrix", "value": T}, f"({val_label})^T"
            if val["type"] == "vector":
                v = val["value"]
                log.append(f"Operacion: Transpuesta de vector {val_label} (se mantiene como columna)")
                return {"type": "vector", "value": v}, f"({val_label})^T"
            raise ValueError("Solo se puede transponer matrices o vectores.")
        if kind == "^{-1}":
            val, val_label = self._eval_with_log(node[1], log)
            if val["type"] != "matrix":
                raise ValueError("Solo se puede invertir matrices.")
            A = val["value"]
            inv, pasos = self._inv_with_steps(A)
            log.append(f"Operacion: Inversa de {val_label} usando Gauss-Jordan")
            log.extend([f"  {p}" for p in pasos])
            return {"type": "matrix", "value": inv}, f"({val_label})^{{-1}}"
        if kind == "det":
            val, val_label = self._eval_with_log(node[1], log)
            if val["type"] != "matrix":
                raise ValueError("Solo se puede calcular el determinante de matrices.")
            A = val["value"]
            det, pasos = self._det_with_steps(A)
            log.append(f"Operacion: Determinante de {val_label}")
            log.extend([f"  {p}" for p in pasos])
            return {"type": "scalar", "value": det}, f"det({val_label})"
        raise ValueError("Nodo invalido.")

    def _describe_obj(self, obj):
        if obj["type"] == "scalar":
            return "escalar"
        if obj["type"] == "vector":
            return f"vector dim {len(obj['value'])}"
        if obj["type"] == "matrix":
            m = len(obj["value"]); n = len(obj["value"][0]) if m else 0
            return f"matriz {m}x{n}"
        return "objeto"

    def _ast_lines(self, node, depth=0):
        pad = "  " * depth
        if node[0] == "scalar":
            return [f"{pad}scalar {_fmt(node[1])}"]
        if node[0] == "id":
            return [f"{pad}id {node[1]}"]
        if node[0] == "op":
            op = node[1]
            lines = [f"{pad}{op}"]
            lines.extend(self._ast_lines(node[2], depth + 1))
            lines.extend(self._ast_lines(node[3], depth + 1))
            return lines
        return [f"{pad}{node}"]

    # ---------------- Formato y acciones ----------------
    def _format_value(self, obj):
        if obj["type"] == "scalar":
            return _fmt(obj["value"])
        if obj["type"] == "vector":
            vals = [_fmt(x) for x in obj["value"]]
            w = max((len(s) for s in vals), default=1)
            return "\n".join("[ " + s.rjust(w) + " ]" for s in vals)
        if obj["type"] == "matrix":
            A = obj["value"]
            if not A:
                return "[ ]"
            m = len(A); n = len(A[0])
            col_w = [0] * n
            for j in range(n):
                col_w[j] = max(len(_fmt(A[i][j])) for i in range(m))
            lines = []
            for i in range(m):
                row = " ".join(_fmt(A[i][j]).rjust(col_w[j]) for j in range(n))
                lines.append("[ " + row + " ]")
            return "\n".join(lines)
        return ""

    # ---------------- Heuristica de regla ----------------
    def _node_type(self, node):
        if node[0] == "scalar":
            return "scalar"
        if node[0] == "id":
            return self.objects.get(node[1], {}).get("type", "desconocido")
        if node[0] == "op":
            try:
                return self._eval(node)["type"]
            except Exception:
                return "expr"
        return "expr"

    def _rule_from_ast(self, ast):
        if ast[0] != "op":
            return "Operacion directa (un solo termino)."
        op = ast[1]
        tL = self._node_type(ast[2])
        tR = self._node_type(ast[3])

        def describe_sum(node):
            if node[0] == "op" and node[1] in ("+", "-"):
                t_a = self._node_type(node[2]); t_b = self._node_type(node[3])
                nombre = "suma" if node[1] == "+" else "resta"
                if t_a == t_b == "matrix":
                    return f" (la matriz proviene de una {nombre} de matrices antes de este producto)"
                if t_a == t_b == "vector":
                    return f" (el vector proviene de una {nombre} de vectores antes de este producto)"
            return ""

        if op in ("+", "-"):
            nombre = "Suma" if op == "+" else "Resta"
            if tL == tR == "scalar":
                return f"{nombre} de escalares."
            if tL == tR == "vector":
                return f"{nombre} de vectores (componente a componente)."
            if tL == tR == "matrix":
                return f"{nombre} de matrices (elemento a elemento)."
            return f"{nombre} de expresiones (se evalúan los términos y luego se combinan)."
        if op == "*":
            if "scalar" in (tL, tR) and "vector" in (tL, tR):
                other = ast[3] if tL == "scalar" else ast[2]
                return "Producto escalar por vector (escala cada componente)" + describe_sum(other) + "."
            if "scalar" in (tL, tR) and "matrix" in (tL, tR):
                other = ast[3] if tL == "scalar" else ast[2]
                return "Producto escalar por matriz (escala cada elemento)" + describe_sum(other) + "."
            if tL == "matrix" and tR == "vector":
                return "Producto matriz por vector (filas por columnas)."
            if tL == "matrix" and tR == "matrix":
                return "Producto de matrices (filas por columnas)."
            return "Producto de expresiones (aplica reglas por termino)."
        return "Operacion compuesta (se muestran los pasos detallados)."

    def _calcular_expresion(self):
        expr = self.expr_edit.toPlainText().strip()
        if not expr:
            QMessageBox.information(self, "Aviso", "Escribe una expresion.")
            return
        try:
            tokens = self._tokenize(expr)
            ast = self._parse(tokens)
            pasos = []
            res, _ = self._eval_with_log(ast, pasos)

            # Valores guardados (lista con representacion y tamano)
            saved_lines = []
            for name in sorted(self.objects.keys()):
                obj = self.objects[name]
                if obj["type"] == "matrix":
                    m = len(obj["value"]); n = len(obj["value"][0]) if m else 0
                    saved_lines.append(f"{name}: matriz {m}×{n}")
                    saved_lines.append(self._format_value(obj))
                elif obj["type"] == "vector":
                    n = len(obj["value"])
                    saved_lines.append(f"{name}: vector {n}×1")
                    saved_lines.append(self._format_value(obj))
                else:
                    saved_lines.append(f"{name}: escalar = {_fmt(obj['value'])}")

            # Identificacion de tipos para nodos principales (si corresponde)
            def node_ident(n):
                if n[0] == 'id':
                    nm = n[1]
                    obj = self.objects.get(nm)
                    if not obj:
                        return f"{nm}: (no definido)"
                    if obj['type'] == 'matrix':
                        m = len(obj['value']); p = len(obj['value'][0]) if m else 0
                        return f"{nm}: matriz {m}×{p}"
                    if obj['type'] == 'vector':
                        return f"{nm}: vector {len(obj['value'])}×1"
                    return f"{nm}: escalar"
                if n[0] == 'scalar':
                    return f"constante: escalar {_fmt(n[1])}"
                return "expresion compuesta"

            types_lines = []
            if ast[0] == 'op':
                left = ast[2]; right = ast[3]
                types_lines.append(node_ident(left))
                types_lines.append(node_ident(right))

            # Regla aplicada (simple heuristica sobre el nodo raiz)
            rule = self._rule_from_ast(ast)

            # Procedimiento: usar pasos generados por _eval_with_log
            proc = []
            proc.append(f"Operacion: {expr}")
            proc.append('Valores guardados:')
            proc.extend(saved_lines if saved_lines else ['(No hay objetos guardados)'])
            proc.append('')
            proc.append('Identificación de tipos:')
            proc.extend(types_lines if types_lines else ['(No aplicable)'])
            proc.append('')
            proc.append('Regla aplicada:')
            proc.append(rule)
            proc.append('')
            proc.append('Procedimiento paso a paso:')
            if pasos:
                for line in pasos:
                    proc.append(line)
            else:
                proc.append('Pasos no disponibles para esta expresion.')

            html = []
            html.append(f"<b>Operacion</b>")
            html.append(self._pre(expr))
            html.append('<b>Valores guardados</b>')
            if saved_lines:
                html.append(self._pre('\n'.join(saved_lines)))
            else:
                html.append(self._pre('(No hay objetos guardados)'))
            html.append('<b>Identificación de tipos</b>')
            html.append(self._pre('\n'.join(types_lines) if types_lines else '(No aplicable)'))
            html.append('<b>Regla aplicada</b>')
            html.append(self._pre(rule))
            html.append('<b>Procedimiento paso a paso</b>')
            html.append(self._pre('\n'.join(pasos) if pasos else 'Pasos no disponibles para esta expresion.'))
            html.append('<b>Resultado final</b>')
            html.append(self._pre(self._format_value(res)))
            self.result_box.setHtml("\n".join(html))
            self.result_box.moveCursor(QTextCursor.End)

            # Guarda data del ultimo calculo para botones de guardado
            self._last_eval = {
                "expr": expr,
                "proc_text": "\n".join(proc),
                "steps_text": "\n".join(pasos) if pasos else "Pasos no disponibles para esta expresion.",
                "result_text": self._format_value(res),
            }
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo evaluar: {exc}")

    def _limpiar_pantalla(self):
        self.result_box.clear()
        self.expr_edit.clear()

    def _pre(self, text):
        return "<pre style='padding:10px;'>" + text + "</pre>"

    # ---------------- Guardar y mostrar resultados ----------------
    def _guardar_resultado(self):
        if not self._last_eval:
            QMessageBox.information(self, "Aviso", "Primero calcula una expresion para guardar su resultado.")
            return
        default_name = self._last_eval.get("expr", "resultado")[:40]
        name, ok = QInputDialog.getText(self, "Guardar resultado", "Nombre:", text=default_name)
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Ingresa un nombre valido.")
            return
        entry = {
            "name": name,
            "expr": self._last_eval.get("expr", ""),
            "proc": self._last_eval.get("proc_text", ""),
            "result": self._last_eval.get("result_text", ""),
        }
        self.saved_results.append(entry)
        QMessageBox.information(self, "Guardado", f"Se guardo el resultado como '{name}'.")

    def _mostrar_guardados(self):
        if not self.saved_results:
            QMessageBox.information(self, "Guardados", "No hay resultados guardados todavia.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Resultados guardados")
        lay = QVBoxLayout(dlg)

        combo = QComboBox()
        for item in self.saved_results:
            combo.addItem(item["name"])
        lay.addWidget(combo)

        tabs = QTabWidget()
        proc_view = QTextEdit(); proc_view.setReadOnly(True)
        res_view = QTextEdit(); res_view.setReadOnly(True)
        tabs.addTab(proc_view, "Procedimiento")
        tabs.addTab(res_view, "Resultado")
        lay.addWidget(tabs, 1)

        def load(idx):
            if idx < 0 or idx >= len(self.saved_results):
                return
            item = self.saved_results[idx]
            proc_view.setPlainText(item.get("proc", ""))
            res_view.setPlainText(item.get("result", ""))

        combo.currentIndexChanged.connect(load)
        load(0)
        dlg.resize(640, 480)
        dlg.exec()


# Modo directo
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = OperacionesMatricesWindow()
    w.show()
    sys.exit(app.exec())
