from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QLineEdit, QTextEdit, QMessageBox, QTabWidget, QSpinBox,
    QToolButton, QMenu
)
from PySide6.QtCore import Qt, QSize
from fractions import Fraction
from .theme import (
    bind_font_scale_stylesheet,
    bind_theme_icon,
    make_overflow_icon,
    gear_icon_preferred,
    help_icon_preferred,
)
from .settings_qt import open_settings_dialog


def _fmt(x: Fraction) -> str:
    return f"{x.numerator}" if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _parse(s: str) -> Fraction:
    s = (s or "").strip().replace(",", ".")
    if s == "":
        return Fraction(0)
    return Fraction(s)


def _matmul(A, x):
    m = len(A)
    n = len(A[0]) if m else 0
    if len(x) != n:
        raise ValueError("Dimensiones incompatibles entre A y x")
    return [sum(A[i][j] * x[j] for j in range(n)) for i in range(m)]


def _format_symbolic_explicit(A):
    m = len(A)
    n = len(A[0]) if m else 0
    xnames = [f"x{j+1}" for j in range(n)]
    lines = []
    lines.append("")
    lines.append("Representación como combinación lineal de las columnas:")
    lines += _format_linear_combination(A)
    lines.append("")
    lines.append("Forma explícita (por componentes):")
    fila_expr = []
    for i in range(m):
        terms = []
        for j in range(n):
            a = _fmt(A[i][j])
            xj = xnames[j]
            if a == "0":
                continue
            if a == "1":
                terms.append(xj)
            elif a == "-1":
                terms.append(f"- {xj}")
            else:
                if a.startswith("-"):
                    terms.append(f"- {a[1:]}{xj}")
                else:
                    terms.append(f"{a}{xj}")
        if not terms:
            fila_expr.append("0")
        else:
            expr = terms[0]
            for t in terms[1:]:
                expr = expr + (" + " + t if not t.strip().startswith("-") else " - " + t.strip()[2:])
            fila_expr.append(expr)
    lines.append("T([" + ", ".join(xnames) + "]^T) = [")
    for expr in fila_expr:
        lines.append("  " + expr)
    lines.append("]^T")
    return lines


def _format_linear_combination(A):
    m = len(A)
    n = len(A[0]) if m else 0
    xnames = [f"x{j+1}" for j in range(n)]
    col_w = [0]*n
    for j in range(n):
        col_w[j] = max(len(_fmt(A[i][j])) for i in range(m)) if m else 1
    xw = [len(s) for s in xnames]

    # expresiones por fila del resultado
    fila_expr = []
    for i in range(m):
        terms = []
        for j in range(n):
            a = _fmt(A[i][j])
            if a == "0":
                continue
            if a == "1":
                terms.append(f"x{j+1}")
            elif a == "-1":
                terms.append(f"-x{j+1}")
            else:
                terms.append(f"{a}x{j+1}")
        if not terms:
            fila_expr.append("0")
        else:
            expr = terms[0]
            for t in terms[1:]:
                expr += (" + " + t) if not t.startswith("-") else (" - " + t[1:])
            fila_expr.append(expr)

    # Construir bloques por filas con ancho fijo y alinear la columna del resultado
    left_parts = []
    for i in range(m):
        pieces = []
        for j in range(n):
            scalar = xnames[j] if i == 0 else (" " * xw[j])
            val = _fmt(A[i][j]).rjust(col_w[j])
            pieces.append(f"{scalar} [ {val} ]")
        left_parts.append("  +  ".join(pieces))

    max_left = max(len(s) for s in left_parts) if left_parts else 0
    lines = []
    for i in range(m):
        left = left_parts[i].ljust(max_left)
        if i == 0:
            lines.append(f"= {left} = [ {fila_expr[i]} ]")
        else:
            lines.append(f"  {left}   [ {fila_expr[i]} ]")
    return lines


def _format_product(A, x, b=None):
    """Devuelve líneas de texto que muestran [A][x] = [b] con corchetes.
    x es vector columna. Soporta m != n.
    """
    m = len(A)
    n = len(A[0]) if m else 0
    # anchuras por columna de A
    col_w = [0]*n
    for j in range(n):
        col_w[j] = max(len(_fmt(A[i][j])) for i in range(m)) if m else 1
    x_w = max((len(_fmt(x[j])) for j in range(n)), default=1)
    b_w = max((len(_fmt(b[i])) for i in range(m)), default=1) if b is not None else 1

    lines = []
    rows = max(m, n)
    for i in range(rows):
        # bloque A
        if i < m:
            a_row = " ".join(_fmt(A[i][j]).rjust(col_w[j]) for j in range(n))
            left = "[ " + a_row + " ]"
        else:
            left = "  " + " "*(sum(col_w)+ (n-1)) + "  "
        # bloque x
        if i < n:
            x_txt = _fmt(x[i]).rjust(x_w)
            mid = "[ " + x_txt + " ]"
        else:
            mid = "  " + " "*(x_w+2)
        # bloque b
        if b is not None and i < m:
            b_txt = _fmt(b[i]).rjust(b_w)
            right = "[ " + b_txt + " ]"
        else:
            right = ""
        eq = " = " if (b is not None and i == 0) else ("   " if b is not None else "")
        times = "   " if i else "   "  # separación simple
        if i == 0 and b is not None:
            lines.append(f"{left}{times}{mid}{eq}{right}")
        else:
            lines.append(f"{left}{times}{mid}{('   '+right) if right else ''}")
    return lines


def _format_vector_column(vec):
    vals = [_fmt(v) for v in vec]
    w = max((len(s) for s in vals), default=1)
    return "\n".join("[ " + s.rjust(w) + " ]" for s in vals)


def _format_matrix(A):
    if not A:
        return "[ ]"
    m = len(A); n = len(A[0])
    col_w = [0]*n
    for j in range(n):
        col_w[j] = max(len(_fmt(A[i][j])) for i in range(m))
    lines = []
    for i in range(m):
        row = " ".join(_fmt(A[i][j]).rjust(col_w[j]) for j in range(n))
        lines.append("[ " + row + " ]")
    return "\n".join(lines)


def _dot_steps(A, x, b):
    m = len(A); n = len(A[0]) if A else 0
    steps = ["", "  Detalle por filas (producto punto):"]
    for i in range(m):
        mults = [f"({_fmt(A[i][j])})*({_fmt(x[j])})" for j in range(n)]
        prods = [A[i][j]*x[j] for j in range(n)]
        sums = " + ".join(_fmt(p) for p in prods)
        steps.append(f"  Fila {i+1}: " + " + ".join(mults) + f" = {sums} = {_fmt(b[i])}")
    return steps


def _format_scaled_sum(c, Tu, d, Tv, result):
    sc = _fmt(c); sd = _fmt(d)
    m = len(Tu)
    wt = max((len(_fmt(x)) for x in Tu), default=1)
    wv = max((len(_fmt(x)) for x in Tv), default=1)
    wr = max((len(_fmt(x)) for x in result), default=1)
    ws1 = len(sc); ws2 = len(sd)
    lines = []
    for i in range(m):
        coef1 = sc if i == 0 else " "*ws1
        coef2 = sd if i == 0 else " "*ws2
        t = _fmt(Tu[i]).rjust(wt)
        v = _fmt(Tv[i]).rjust(wv)
        r = _fmt(result[i]).rjust(wr)
        if i == 0:
            lines.append(f"= {coef1} [ {t} ]  +  {coef2} [ {v} ] = [ {r} ]")
        else:
            lines.append(f"  {coef1} [ {t} ]     {coef2} [ {v} ]   [ {r} ]")
    return lines

class TransformacionesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transformaciones lineales: T(x)=Ax")

        outer = QWidget(); self.setCentralWidget(outer)
        lay = QVBoxLayout(outer)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

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
        act_help = menu.addAction(help_icon_preferred(20), "Ayuda")
        act_help.triggered.connect(self._open_help)
        more_btn.setMenu(menu)
        topbar.addWidget(more_btn, 0, Qt.AlignRight)
        lay.addLayout(topbar)

        title = QLabel("Transformaciones lineales")
        title.setObjectName("Title")
        lay.addWidget(title)

        tabs = QTabWidget(); lay.addWidget(tabs, 1)

        # Tab 1
        self.tab_ax = QWidget(); tabs.addTab(self.tab_ax, "T(x)=Ax")
        self._build_tab_ax()

        # Tab 2
        self.tab_base = QWidget(); tabs.addTab(self.tab_base, "Matriz desde base")
        self._build_tab_base()

        # Tab 3
        self.tab_lin = QWidget(); tabs.addTab(self.tab_lin, "Comprobar linealidad")
        self._build_tab_linealidad()

        # Tab 4
        self.tab_axb = QWidget(); tabs.addTab(self.tab_axb, "Resolver Ax=b")
        self._build_tab_axb()

    # ------- Tab 1: T(x)=Ax -------
    def _build_tab_ax(self):
        lay = QVBoxLayout(self.tab_ax)
        cfg = QHBoxLayout(); lay.addLayout(cfg)
        cfg.addWidget(QLabel("m (filas):"))
        self.m1 = QSpinBox(); self.m1.setRange(1, 10); self.m1.setValue(2); cfg.addWidget(self.m1)
        cfg.addSpacing(8)
        cfg.addWidget(QLabel("n (columnas):"))
        self.n1 = QSpinBox(); self.n1.setRange(1, 10); self.n1.setValue(2); cfg.addWidget(self.n1)
        btn = QPushButton("Crear A y x"); btn.clicked.connect(self._crear_Ax); cfg.addWidget(btn)
        cfg.addStretch(1)

        self.gridA1 = QWidget(); self.gridA1_lay = QGridLayout(self.gridA1)
        self.gridA1_lay.setHorizontalSpacing(6); self.gridA1_lay.setVerticalSpacing(6)
        lay.addWidget(self.gridA1)

        self.out1 = QTextEdit(); self.out1.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.out1,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        lay.addWidget(self.out1, 1)

        self.m1.valueChanged.connect(self._crear_Ax)
        self.n1.valueChanged.connect(self._crear_Ax)
        self._crear_Ax()

    def _crear_Ax(self):
        for i in reversed(range(self.gridA1_lay.count())):
            w = self.gridA1_lay.itemAt(i).widget()
            if w: w.setParent(None)
        m, n = self.m1.value(), self.n1.value()
        self.A1 = [[QLineEdit() for j in range(n)] for i in range(m)]
        self.x1 = [QLineEdit() for _ in range(n)]
        for i in range(m):
            for j in range(n):
                e = self.A1[i][j]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.gridA1_lay.addWidget(e, i+1, j)
        self.gridA1_lay.addWidget(QLabel("x"), 0, n)
        for j in range(n):
            e = self.x1[j]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
            self.gridA1_lay.addWidget(e, j+1, n)
        calc = QPushButton("Calcular T(x)=Ax"); calc.clicked.connect(self._calc_ax)
        self.gridA1_lay.addWidget(calc, m+2, 0, 1, n+1)

    def _calc_ax(self):
        try:
            m, n = self.m1.value(), self.n1.value()
            A = [[_parse(self.A1[i][j].text()) for j in range(n)] for i in range(m)]
            x = [_parse(e.text()) for e in self.x1]
            b = _matmul(A, x)

            # Representación con corchetes alineados
            mat_lines = _format_product(A, x, b)

            # Paso a paso por filas (producto punto)
            steps = ["", "Paso a paso:"]
            for i in range(m):
                mults = [f"({_fmt(A[i][j])})*({_fmt(x[j])})" for j in range(n)]
                prods = [A[i][j]*x[j] for j in range(n)]
                sums = " + ".join(_fmt(p) for p in prods)
                steps.append(f"Fila {i+1}: " + " + ".join(mults) + f" = {sums} = {_fmt(b[i])}")

            self.out1.setPlainText("\n".join(mat_lines + steps))
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo calcular: {exc}")

    # ------- Tab 2: construir A desde T(e_j) -------
    def _build_tab_base(self):
        lay = QVBoxLayout(self.tab_base)
        cfg = QHBoxLayout(); lay.addLayout(cfg)
        cfg.addWidget(QLabel("m (filas):"))
        self.m2 = QSpinBox(); self.m2.setRange(1, 10); self.m2.setValue(2); cfg.addWidget(self.m2)
        cfg.addSpacing(8)
        cfg.addWidget(QLabel("n (columnas):"))
        self.n2 = QSpinBox(); self.n2.setRange(1, 10); self.n2.setValue(2); cfg.addWidget(self.n2)
        btn = QPushButton("Crear campos T(e_j)"); btn.clicked.connect(self._crear_base); cfg.addWidget(btn)
        cfg.addStretch(1)

        self.grid2 = QWidget(); self.grid2_lay = QGridLayout(self.grid2)
        self.grid2_lay.setHorizontalSpacing(6); self.grid2_lay.setVerticalSpacing(6)
        lay.addWidget(self.grid2)

        self.out2 = QTextEdit(); self.out2.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.out2,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        lay.addWidget(self.out2, 1)

        self.m2.valueChanged.connect(self._crear_base)
        self.n2.valueChanged.connect(self._crear_base)
        self._crear_base()

    def _crear_base(self):
        for i in reversed(range(self.grid2_lay.count())):
            w = self.grid2_lay.itemAt(i).widget()
            if w: w.setParent(None)
        m, n = self.m2.value(), self.n2.value()
        self.Tej = []
        for j in range(n):
            self.grid2_lay.addWidget(QLabel(f"T(e{j+1})"), 0, j)
            col = []
            for i in range(m):
                e = QLineEdit(); e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.grid2_lay.addWidget(e, i+1, j)
                col.append(e)
            self.Tej.append(col)
        btn = QPushButton("Construir A"); btn.clicked.connect(self._build_A_from_base)
        self.grid2_lay.addWidget(btn, m+2, 0, 1, n)

    def _build_A_from_base(self):
        try:
            m, n = self.m2.value(), self.n2.value()
            A = [[_parse(self.Tej[j][i].text()) for j in range(n)] for i in range(m)]

            lines = []
            # Paso 1: datos de entrada
            lines.append("Paso 1) Imágenes de la base canónica (por columnas):")
            for j in range(n):
                col = [_fmt(A[i][j]) for i in range(m)]
                lines.append(f"T(e{j+1}) = [ " + "  ".join(col) + " ]^T")

            # Paso 2: formar A
            lines.append("")
            lines.append("Paso 2) Formar la matriz A colocando T(ej) como columnas:")
            for i in range(m):
                row = "  ".join(_fmt(A[i][j]) for j in range(n))
                lines.append("A = [ " + row + " ]")

            # Paso 3: interpretación y fórmula
            lines.append("")
            lines.append(f"Interpretación: Sea T: R^{n} → R^{m} definida por T(x) = A x.")
            lines.append("La j-ésima columna de A es T(e_j). Para x = [x1, …, xn]^T se cumple:")
            lines.append("T(x) = x1·T(e1) + x2·T(e2) + ··· + xn·T(en).")

            # Paso 4: forma explícita por componentes
            lines += _format_symbolic_explicit(A)

            self.out2.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo construir A: {exc}")

    # ------- Tab 3: comprobar linealidad -------
    def _build_tab_linealidad(self):
        lay = QVBoxLayout(self.tab_lin)
        info = QLabel("Comprueba numéricamente T(cu+dv)=cT(u)+dT(v) para T(x)=Ax")
        lay.addWidget(info)

        cfg = QHBoxLayout(); lay.addLayout(cfg)
        cfg.addWidget(QLabel("m:")); self.m3 = QSpinBox(); self.m3.setRange(1, 10); self.m3.setValue(2); cfg.addWidget(self.m3)
        cfg.addWidget(QLabel("n:")); self.n3 = QSpinBox(); self.n3.setRange(1, 10); self.n3.setValue(2); cfg.addWidget(self.n3)
        b = QPushButton("Crear campos"); b.clicked.connect(self._crear_linealidad); cfg.addWidget(b); cfg.addStretch(1)

        self.grid3 = QWidget(); self.grid3_lay = QGridLayout(self.grid3)
        self.grid3_lay.setHorizontalSpacing(6); self.grid3_lay.setVerticalSpacing(6)
        lay.addWidget(self.grid3)

        self.out3 = QTextEdit(); self.out3.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.out3,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        lay.addWidget(self.out3, 1)

        self.m3.valueChanged.connect(self._crear_linealidad)
        self.n3.valueChanged.connect(self._crear_linealidad)
        self._crear_linealidad()

    # ------- Tab 4: Resolver Ax=b -------
    def _build_tab_axb(self):
        lay = QVBoxLayout(self.tab_axb)
        cfg = QHBoxLayout(); lay.addLayout(cfg)
        cfg.addWidget(QLabel("m (filas):"))
        self.m4 = QSpinBox(); self.m4.setRange(1, 10); self.m4.setValue(3); cfg.addWidget(self.m4)
        cfg.addWidget(QLabel("n (columnas):"))
        self.n4 = QSpinBox(); self.n4.setRange(1, 10); self.n4.setValue(2); cfg.addWidget(self.n4)
        btn = QPushButton("Crear A y b"); btn.clicked.connect(self._crear_axb); cfg.addWidget(btn); cfg.addStretch(1)

        self.grid4 = QWidget(); self.grid4_lay = QGridLayout(self.grid4)
        self.grid4_lay.setHorizontalSpacing(6); self.grid4_lay.setVerticalSpacing(6)
        lay.addWidget(self.grid4)

        self.out4 = QTextEdit(); self.out4.setReadOnly(True)
        bind_font_scale_stylesheet(
            self.out4,
            "font-family:Consolas,monospace;font-size:{body}px;",
            body=12,
        )
        lay.addWidget(self.out4, 1)

        self.m4.valueChanged.connect(self._crear_axb)
        self.n4.valueChanged.connect(self._crear_axb)
        self._crear_axb()

    def _crear_axb(self):
        for i in reversed(range(self.grid4_lay.count())):
            w = self.grid4_lay.itemAt(i).widget()
            if w: w.setParent(None)
        m, n = self.m4.value(), self.n4.value()
        self.A4 = [[QLineEdit() for j in range(n)] for i in range(m)]
        self.b4 = [QLineEdit() for _ in range(m)]
        self.grid4_lay.addWidget(QLabel("A (m×n)"), 0, 0)
        for i in range(m):
            for j in range(n):
                e = self.A4[i][j]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.grid4_lay.addWidget(e, i+1, j)
        self.grid4_lay.addWidget(QLabel("b"), 0, n)
        for i in range(m):
            e = self.b4[i]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
            self.grid4_lay.addWidget(e, i+1, n)
        solve = QPushButton("Resolver Ax=b"); solve.clicked.connect(self._resolver_axb)
        self.grid4_lay.addWidget(solve, m+2, 0, 1, n+1)

    def _format_aug(self, M):
        m = len(M); n = len(M[0])-1 if m else 0
        col_w = [0]*n
        for j in range(n):
            col_w[j] = max(len(_fmt(M[i][j])) for i in range(m)) if m else 1
        bw = max((len(_fmt(M[i][-1])) for i in range(m)), default=1)
        lines = []
        for i in range(m):
            left = " ".join(_fmt(M[i][j]).rjust(col_w[j]) for j in range(n))
            right = _fmt(M[i][-1]).rjust(bw)
            lines.append("[ " + left + "  |  " + right + " ]")
        return "\n".join(lines)

    def _resolver_axb(self):
        try:
            m, n = self.m4.value(), self.n4.value()
            A = [[_parse(self.A4[i][j].text()) for j in range(n)] for i in range(m)]
            b = [_parse(self.b4[i].text()) for i in range(m)]
            M = [row[:] + [b[i]] for i, row in enumerate(A)]
            pasos = ["Matriz aumentada [A | b]:\n" + self._format_aug(M) + "\n"]
            r = 0; piv_cols = []
            for c in range(n):
                p = None
                for i in range(r, m):
                    if M[i][c] != 0:
                        p = i; break
                if p is None:
                    continue
                if p != r:
                    M[r], M[p] = M[p], M[r]
                    pasos.append(f"Intercambio F{r+1} ↔ F{p+1}\n" + self._format_aug(M) + "\n")
                piv = M[r][c]
                if piv != 1:
                    M[r] = [x / piv for x in M[r]]
                    pasos.append(f"F{r+1} ← F{r+1} / {_fmt(piv)}\n" + self._format_aug(M) + "\n")
                for i in range(m):
                    if i != r and M[i][c] != 0:
                        fac = M[i][c]
                        M[i] = [M[i][k] - fac*M[r][k] for k in range(n+1)]
                        pasos.append(f"F{i+1} ← F{i+1} - ({_fmt(fac)})·F{r+1}\n" + self._format_aug(M) + "\n")
                piv_cols.append(c); r += 1
                if r == m: break

            for i in range(m):
                if all(M[i][j] == 0 for j in range(n)) and M[i][-1] != 0:
                    self.out4.setPlainText("Sistema inconsistente.\n\n" + "\n".join(pasos))
                    return
            if len(piv_cols) == n:
                x = [Fraction(0)]*n
                for i, c in enumerate(piv_cols):
                    x[c] = M[i][-1]
                vals_fmt = [_fmt(xi) for xi in x]
                linea_vars = ", ".join([f"x{j+1} = {vals_fmt[j]}" for j in range(n)])
                col_txt = _format_vector_column(x)
                fila_txt = "[ " + ", ".join(vals_fmt) + " ]^T"
                aprox = ", ".join([f"{float(xi):.6g}" for xi in x])
                out = [
                    "RREF de [A|b] y pasos:\n" + self._format_aug(M),
                    "\nSolución única:",
                    linea_vars,
                    "\nVector columna:",
                    col_txt,
                    "\nVector fila:",
                    fila_txt,
                    f"\nAproximado: ({aprox})^T",
                ]
                self.out4.setPlainText("\n".join(pasos) + "\n" + "\n".join(out))
            else:
                self.out4.setPlainText("Sistema con infinitas soluciones (parámetros libres).\n\n" + "\n".join(pasos) + "\nRREF:\n" + self._format_aug(M))
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo resolver Ax=b: {exc}")

    def _crear_linealidad(self):
        for i in reversed(range(self.grid3_lay.count())):
            w = self.grid3_lay.itemAt(i).widget()
            if w: w.setParent(None)
        m, n = self.m3.value(), self.n3.value()
        # A
        self.grid3_lay.addWidget(QLabel("A (m×n)"), 0, 0)
        self.A3 = [[QLineEdit() for j in range(n)] for i in range(m)]
        for i in range(m):
            for j in range(n):
                e = self.A3[i][j]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
                self.grid3_lay.addWidget(e, i+1, j)
        # u y v
        self.grid3_lay.addWidget(QLabel("u"), 0, n)
        self.u3 = [QLineEdit() for _ in range(n)]
        for j in range(n):
            e = self.u3[j]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
            self.grid3_lay.addWidget(e, j+1, n)
        self.grid3_lay.addWidget(QLabel("v"), 0, n+1)
        self.v3 = [QLineEdit() for _ in range(n)]
        for j in range(n):
            e = self.v3[j]; e.setAlignment(Qt.AlignCenter); e.setPlaceholderText("0")
            self.grid3_lay.addWidget(e, j+1, n+1)
        # escalares
        self.grid3_lay.addWidget(QLabel("c:"), 0, n+2)
        self.c3 = QLineEdit("1"); self.c3.setAlignment(Qt.AlignCenter)
        self.grid3_lay.addWidget(self.c3, 0, n+3)
        self.grid3_lay.addWidget(QLabel("d:"), 1, n+2)
        self.d3 = QLineEdit("1"); self.d3.setAlignment(Qt.AlignCenter)
        self.grid3_lay.addWidget(self.d3, 1, n+3)

        check = QPushButton("Comprobar"); check.clicked.connect(self._check_lin_steps)
        self.grid3_lay.addWidget(check, m+2, 0, 1, n+4)

    def _check_lin(self):
        try:
            m, n = self.m3.value(), self.n3.value()
            A = [[_parse(self.A3[i][j].text()) for j in range(n)] for i in range(m)]
            u = [_parse(e.text()) for e in self.u3]
            v = [_parse(e.text()) for e in self.v3]
            c = _parse(self.c3.text())
            d = _parse(self.d3.text())
            cu_dv = [c*ui + d*vi for ui, vi in zip(u, v)]
            Tu = _matmul(A, u)
            Tv = _matmul(A, v)
            Tcu_dv = _matmul(A, cu_dv)
            cTu_dTv = [c*Tu[i] + d*Tv[i] for i in range(len(Tu))]
            ok = all(Tcu_dv[i] == cTu_dTv[i] for i in range(len(Tu)))
            lines = ["Comprobación:", "T(cu+dv) vs cT(u)+dT(v)", "Iguales: SI" if ok else "Iguales: NO", ""]
            lines.append("T(u) = [" + ", ".join(_fmt(x) for x in Tu) + "]")
            lines.append("T(v) = [" + ", ".join(_fmt(x) for x in Tv) + "]")
            lines.append("T(cu+dv) = [" + ", ".join(_fmt(x) for x in Tcu_dv) + "]")
            lines.append("cT(u)+dT(v) = [" + ", ".join(_fmt(x) for x in cTu_dTv) + "]")
            self.out3.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo comprobar: {exc}")

    # Nuevo método con pasos detallados y alineados
    def _check_lin_steps(self):
        try:
            m, n = self.m3.value(), self.n3.value()
            A = [[_parse(self.A3[i][j].text()) for j in range(n)] for i in range(m)]
            u = [_parse(e.text()) for e in self.u3]
            v = [_parse(e.text()) for e in self.v3]
            c = _parse(self.c3.text())
            d = _parse(self.d3.text())
            cu_dv = [c*ui + d*vi for ui, vi in zip(u, v)]
            Tu = _matmul(A, u)
            Tv = _matmul(A, v)
            Tcu_dv = _matmul(A, cu_dv)
            cTu_dTv = [c*Tu[i] + d*Tv[i] for i in range(len(Tu))]
            ok = all(Tcu_dv[i] == cTu_dTv[i] for i in range(len(Tu)))

            lines = ["Comprobación de linealidad (paso a paso):", ""]
            lines.append("Paso 1) Datos:")
            lines.append("A = \n" + _format_matrix(A))
            lines.append("u = \n" + _format_vector_column(u))
            lines.append("v = \n" + _format_vector_column(v))
            lines.append(f"c = {_fmt(c)},   d = {_fmt(d)}")

            lines.append("")
            lines.append("Paso 2) Vector cu + dv (componente a componente):")
            for j in range(n):
                part1 = _fmt(c*u[j]); part2 = _fmt(d*v[j])
                lines.append(f"  comp {j+1}: {_fmt(c)}*{_fmt(u[j])} + {_fmt(d)}*{_fmt(v[j])} = {part1} + {part2} = {_fmt(cu_dv[j])}")
            lines.append("cu+dv =\n" + _format_vector_column(cu_dv))

            lines.append("")
            lines.append("Paso 3) T(u) = A·u:")
            lines += _format_product(A, u, Tu)
            lines += _dot_steps(A, u, Tu)

            lines.append("")
            lines.append("Paso 4) T(v) = A·v:")
            lines += _format_product(A, v, Tv)
            lines += _dot_steps(A, v, Tv)

            lines.append("")
            lines.append("Paso 5) T(cu+dv) = A·(cu+dv):")
            lines += _format_product(A, cu_dv, Tcu_dv)
            lines += _dot_steps(A, cu_dv, Tcu_dv)

            lines.append("")
            lines.append("Paso 6) cT(u) + dT(v):")
            lines += _format_scaled_sum(c, Tu, d, Tv, cTu_dTv)

            lines.append("")
            lines.append("Conclusión: T(cu+dv) y cT(u)+dT(v) son iguales" if ok else "Conclusión: No son iguales")
            self.out3.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"No se pudo comprobar: {exc}")

    def _open_settings(self):
        try:
            open_settings_dialog(self)
        except Exception:
            pass

    def _open_help(self):
        text = (
            "Transformaciones lineales T(x)=Ax:\n"
            "- Usa cada pestaña según el flujo: T(x)=Ax, matriz desde base, comprobar linealidad o resolver Ax=b.\n"
            "- Ajusta dimensiones con los controles superiores y presiona el botón de crear antes de llenar datos.\n"
            "- Los resultados y pasos detallados aparecen en los paneles inferiores de cada pestaña.\n\n"
            "El menú de tres puntos ofrece Configuración y esta Ayuda."
        )
        try:
            QMessageBox.information(self, "Ayuda", text)
        except Exception:
            pass
