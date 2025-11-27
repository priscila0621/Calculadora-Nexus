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
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextCursor
from fractions import Fraction
from .theme import bind_font_scale_stylesheet, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from .settings_qt import open_settings_dialog


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
        self.objects_view = QTextEdit(); self.objects_view.setReadOnly(True)
        bind_font_scale_stylesheet(self.objects_view, "font-family:Consolas,monospace;font-size:{body}px;", body=12)
        lay.addWidget(self.objects_view, 1)
        self._refresh_objects_view()
        return card

    def _build_expression_card(self) -> QFrame:
        card, lay = self._card("Expresion algebraica")
        info = QLabel("Ejemplos: A(u+v), Au + Av, 3A + 2B, A(Bu + Cv), M*(u - 3v)")
        info.setWordWrap(True)
        lay.addWidget(info)

        templates_row = QHBoxLayout(); templates_row.setSpacing(8)
        templates_row.addWidget(QLabel("Plantillas rapidas:"))
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
            b.setFixedWidth(42)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, t=sym: self._insert_text(t))
            ops_row.addWidget(b)
        ops_row.addStretch(1)
        lay.addLayout(ops_row)

        lay.addWidget(QLabel("Inserta objetos guardados con un toque:"))
        self.shortcuts_box = QFrame()
        self.shortcuts_layout = QGridLayout(self.shortcuts_box)
        self.shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        self.shortcuts_layout.setHorizontalSpacing(8)
        self.shortcuts_layout.setVerticalSpacing(8)
        lay.addWidget(self.shortcuts_box)

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
        self.result_box = QTextEdit(); self.result_box.setReadOnly(True)
        bind_font_scale_stylesheet(self.result_box, "font-family:Consolas,monospace;font-size:{body}px;", body=12)
        clear_btn = QPushButton("Limpiar pantalla"); clear_btn.clicked.connect(self._limpiar_pantalla)
        lay.addWidget(clear_btn, alignment=Qt.AlignRight)
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
        if not nombre.isalpha():
            QMessageBox.warning(self, "Aviso", "Usa un nombre de matriz con letras (ej: A, B, M).")
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
        if not nombre.isalpha():
            QMessageBox.warning(self, "Aviso", "Usa un nombre de vector con letras (ej: u, v, w).")
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
        if not nombre.isalpha():
            QMessageBox.warning(self, "Aviso", "Usa un nombre de escalar con letras (ej: a, b, c).")
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
        if base not in self.objects:
            return base
        idx = 2
        while f"{base}{idx}" in self.objects:
            idx += 1
        return f"{base}{idx}"

    def _refresh_objects_view(self):
        lines = []
        for k in sorted(self.objects.keys()):
            obj = self.objects[k]
            if obj["type"] == "scalar":
                lines.append(f"{k}: escalar = {_fmt(obj['value'])}")
            elif obj["type"] == "vector":
                lines.append(f"{k}: vector dim {len(obj['value'])} -> [{', '.join(_fmt(x) for x in obj['value'])}]")
            else:
                m = len(obj["value"]); n = len(obj["value"][0]) if m else 0
                lines.append(f"{k}: matriz {m}x{n}")
        self.objects_view.setPlainText("\n".join(lines))
        if hasattr(self, "shortcuts_layout"):
            self._refresh_shortcuts()

    def _refresh_shortcuts(self):
        self._clear_layout(self.shortcuts_layout)
        names = sorted(self.objects.keys())
        if not names:
            lbl = QLabel("Guarda matrices, vectores o escalares y tocalos aqui para insertarlos en la expresion.")
            lbl.setWordWrap(True)
            self.shortcuts_layout.addWidget(lbl, 0, 0)
            return
        cols = 4
        for idx, name in enumerate(names):
            btn = QPushButton(name)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, t=name: self._insert_text(t))
            row, col = divmod(idx, cols)
            self.shortcuts_layout.addWidget(btn, row, col)

    def _insert_text(self, text: str):
        cursor = self.expr_edit.textCursor()
        cursor.insertText(text)
        self.expr_edit.setTextCursor(cursor)
        self.expr_edit.setFocus()

    def _apply_template(self, text: str):
        self.expr_edit.setPlainText(text)
        cursor = self.expr_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.expr_edit.setTextCursor(cursor)
        self.expr_edit.setFocus()

    def _template_buttons(self):
        def first_of_type(t, fallback):
            for name, obj in self.objects.items():
                if obj.get("type") == t:
                    return name
            return fallback

        def second_matrix(primary):
            for name, obj in self.objects.items():
                if obj.get("type") == "matrix" and name != primary:
                    return name
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
            if ch.isdigit():
                j = i
                while j < len(expr) and (expr[j].isdigit() or expr[j] == "/"):
                    j += 1
                tokens.append(expr[i:j]); i = j; continue
            if ch.isalpha():
                j = i
                while j < len(expr) and expr[j].isalpha():
                    j += 1
                tokens.append(expr[i:j]); i = j; continue
            raise ValueError(f"Caracter invalido: {ch}")
        out = []
        for idx, tok in enumerate(tokens):
            out.append(tok)
            if idx + 1 < len(tokens):
                a, b = tok, tokens[idx + 1]
                if (a not in "+-*" and a != "(") and (b not in "+-*)" and b != ")"):
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
            return node
        if tok is None:
            raise ValueError("Expresion incompleta")
        self._eat()
        if tok.replace("/", "").isdigit():
            return ("scalar", _parse_fraction(tok))
        if tok.isalpha():
            if tok not in self.objects:
                raise ValueError(f"Objeto '{tok}' no definido.")
            return ("id", tok)
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
        raise ValueError("Nodo invalido.")

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
            if op == "+":
                res = self._add(a, b)
                log.append(f"{a_label} + {b_label} -> {self._describe_obj(res)}")
                return res, f"({a_label}+{b_label})"
            if op == "-":
                res = self._sub(a, b)
                log.append(f"{a_label} - {b_label} -> {self._describe_obj(res)}")
                return res, f"({a_label}-{b_label})"
            if op == "*":
                res = self._mul(a, b)
                log.append(f"{a_label} * {b_label} -> {self._describe_obj(res)}")
                return res, f"{a_label}*{b_label}"
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
            proc = []
            proc.append("Tokens: " + " ".join(tokens))
            proc.append("")
            proc.append("Arbol sintactico:")
            proc.extend(self._ast_lines(ast))
            proc.append("")
            proc.append("Operaciones:")
            if pasos:
                for idx, line in enumerate(pasos, 1):
                    proc.append(f"{idx}. {line}")
            else:
                proc.append("Sin operaciones registradas.")
            html = []
            html.append("<b>Expresion:</b> " + expr)
            html.append(self._pre("\n".join(proc)))
            html.append("<b>Resultado:</b>")
            html.append(self._pre(self._format_value(res)))
            self.result_box.setHtml("\n".join(html))
            self.result_box.moveCursor(QTextCursor.End)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo evaluar: {exc}")

    def _limpiar_pantalla(self):
        self.result_box.clear()
        self.expr_edit.clear()

    def _pre(self, text):
        return "<pre style='background:#fffaf5;padding:10px;border:1px solid #f5d0c5;border-radius:6px;'>" + text + "</pre>"


# Modo directo
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = OperacionesMatricesWindow()
    w.show()
    sys.exit(app.exec())
