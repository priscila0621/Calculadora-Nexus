import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction
from copy import deepcopy


class LeontiefApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        self.bg = "#ffe4e6"
        self.entry_bg = "#fff0f5"
        self.panel_bg = "#fdf7fb"
        self.card_bg = "#fff7fb"
        self.card_border = "#fbcfe8"
        self.mono_font = ("Consolas", 11)
        self.n = 0
        self.entries_c = []
        self.entries_d = []
        self.grid_c_frame = None
        self.grid_d_frame = None
        self.pasos_guardados = []
        self.matriz_final = None

        self.root.title("Modelo de Leontief - Sistema de insumo-producto")
        self.root.geometry("1280x900")
        self.root.configure(bg=self.bg)
        try:
            self.root.minsize(960, 720)
        except Exception:
            pass

        self._setup_styles()
        self._build_layout()

    # ---------------------------------------------------------
    # Estilos base
    # ---------------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", font=("Segoe UI", 11), background=self.bg, foreground="#b91c1c")
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=6,
                        background="#fbb6ce", foreground="white")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])
        style.configure("Back.TButton", font=("Segoe UI", 11, "bold"), padding=6,
                        background="#fecaca", foreground="#b91c1c")
        style.map("Back.TButton",
                  background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])
        style.configure("Ghost.TButton", font=("Segoe UI", 10, "bold"), padding=4,
                        background=self.bg, foreground="#b91c1c", borderwidth=0)
        style.map("Ghost.TButton",
                  background=[("!disabled", self.bg), ("active", "#ffe4e6")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])

    # ---------------------------------------------------------
    # Construccion de la interfaz
    # ---------------------------------------------------------
    def _build_layout(self):
        outer = tk.Frame(self.root, bg=self.bg)
        outer.pack(fill="both", expand=True, padx=14, pady=12)

        header = tk.Frame(outer, bg=self.bg)
        header.pack(fill="x", pady=(0, 8))
        tk.Label(header, text="Modelo de Leontief", font=("Segoe UI", 24, "bold"),
                 bg=self.bg, fg="#b91c1c").pack(anchor="w")
        tk.Label(
            header,
            text="Resuelve (I - C) * X = D construyendo la identidad y aplicando Gauss-Jordan.",
            font=("Segoe UI", 11),
            bg=self.bg,
            fg="#6b4557",
            wraplength=1100,
            justify="left",
        ).pack(anchor="w")

        controls = tk.Frame(outer, bg=self.bg)
        controls.pack(fill="x", pady=(4, 12))
        tk.Label(controls, text="Tamano del modelo (n x n):", bg=self.bg,
                 fg="#b91c1c", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.var_n = tk.IntVar(value=3)
        tk.Spinbox(controls, from_=1, to=10, textvariable=self.var_n, width=6, font=("Segoe UI", 12),
                   justify="center", bg=self.entry_bg).grid(row=0, column=1, padx=4, pady=6)

        ttk.Button(controls, text="Crear tablas", style="Primary.TButton",
                   command=self.crear_tablas).grid(row=0, column=2, padx=8, pady=6)

        self.btn_resolver = ttk.Button(controls, text="Resolver modelo",
                                       style="Primary.TButton", command=self.resolver_modelo)
        self.btn_resolver.grid(row=0, column=3, padx=8, pady=6)
        try:
            self.btn_resolver.state(["disabled"])
        except Exception:
            pass

        ttk.Button(controls, text="Limpiar", style="Primary.TButton",
                   command=self.limpiar).grid(row=0, column=4, padx=8, pady=6)
        ttk.Button(controls, text="Volver al inicio", style="Back.TButton",
                   command=self.volver_callback).grid(row=0, column=5, padx=8, pady=6)

        info = tk.Frame(outer, bg="#ffffff", highlightbackground="#f3c7d5", highlightthickness=1)
        info.pack(fill="x", pady=(0, 12))
        tk.Label(info, text="Como funciona:", font=("Segoe UI", 11, "bold"),
                 bg="#ffffff", fg="#b91c1c").pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(
            info,
            text=("1) Ingresa la matriz de consumo C y el vector de demanda final D.\n"
                  "2) El sistema arma la identidad I, calcula (I - C) y la matriz aumentada (I - C | D).\n"
                  "3) Se aplica Gauss-Jordan (mismo metodo del modulo de sistemas) y se muestra X, la produccion total."),
            bg="#ffffff",
            fg="#6b4557",
            justify="left",
            wraplength=1100,
        ).pack(anchor="w", padx=12, pady=(0, 10))

        body = tk.Frame(outer, bg=self.bg)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        left = tk.Frame(body, bg=self.bg)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = tk.Frame(body, bg=self.bg)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.frame_c = ttk.LabelFrame(left, text="Matriz de consumo C", padding=10, labelanchor="n")
        self.frame_c.pack(fill="x", pady=(0, 8))

        self.frame_d = ttk.LabelFrame(left, text="Vector de demanda final D", padding=10, labelanchor="n")
        self.frame_d.pack(fill="x", pady=(0, 8))

        result_frame = ttk.LabelFrame(right, text="Procedimiento y resultados", padding=4, labelanchor="n")
        result_frame.pack(fill="both", expand=True)
        result_wrapper = tk.Frame(result_frame, bg=self.panel_bg)
        result_wrapper.pack(fill="both", expand=True, padx=6, pady=6)
        self.result_canvas = tk.Canvas(result_wrapper, bg=self.panel_bg, highlightthickness=0)
        self.result_canvas.pack(side="left", fill="both", expand=True)
        scroll_y = ttk.Scrollbar(result_wrapper, orient="vertical", command=self.result_canvas.yview)
        scroll_y.pack(side="right", fill="y")
        self.result_canvas.configure(yscrollcommand=scroll_y.set)
        self.result_container = tk.Frame(self.result_canvas, bg=self.panel_bg)
        self.result_window = self.result_canvas.create_window((0, 0), window=self.result_container, anchor="nw")
        self.result_container.bind(
            "<Configure>",
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all"))
        )
        self.result_canvas.bind(
            "<Configure>",
            lambda e: self.result_canvas.itemconfigure(self.result_window, width=e.width)
        )

    # ---------------------------------------------------------
    # Helpers UI
    # ---------------------------------------------------------
    def limpiar(self):
        self.n = 0
        self.entries_c = []
        self.entries_d = []
        if self.grid_c_frame:
            self.grid_c_frame.destroy()
            self.grid_c_frame = None
        if self.grid_d_frame:
            self.grid_d_frame.destroy()
            self.grid_d_frame = None

        self._clear_result_panel()
        try:
            self.btn_resolver.state(["disabled"])
        except Exception:
            pass

    def crear_tablas(self):
        try:
            n = int(self.var_n.get())
            if n <= 0:
                raise ValueError
            if n > 10:
                messagebox.showwarning("Aviso", "Tamanos mayores a 10 pueden ser dificiles de visualizar.")
        except Exception:
            messagebox.showerror("Error", "Ingrese un tamano valido (entero positivo).")
            return

        self.n = n
        self.entries_c = []
        self.entries_d = []

        if self.grid_c_frame:
            self.grid_c_frame.destroy()
        if self.grid_d_frame:
            self.grid_d_frame.destroy()

        self.grid_c_frame = tk.Frame(self.frame_c, bg=self.bg)
        self.grid_c_frame.pack(pady=4)
        for i in range(n):
            row_entries = []
            for j in range(n):
                e = tk.Entry(self.grid_c_frame, width=8, justify="center", font=("Segoe UI", 11), bg=self.entry_bg)
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.entries_c.append(row_entries)

        self.grid_d_frame = tk.Frame(self.frame_d, bg=self.bg)
        self.grid_d_frame.pack(pady=4)
        for i in range(n):
            tk.Label(self.grid_d_frame, text=f"d{i+1}", bg=self.bg, fg="#b91c1c").grid(row=i, column=0, padx=4, pady=4)
            e = tk.Entry(self.grid_d_frame, width=10, justify="center", font=("Segoe UI", 11), bg=self.entry_bg)
            e.grid(row=i, column=1, padx=6, pady=4)
            self.entries_d.append(e)

        self._clear_result_panel()
        try:
            self.btn_resolver.state(["!disabled"])
        except Exception:
            pass

    def _clear_result_panel(self):
        if getattr(self, "result_container", None):
            for child in self.result_container.winfo_children():
                child.destroy()
        if getattr(self, "result_canvas", None):
            try:
                self.result_canvas.yview_moveto(0)
            except Exception:
                pass

    # ---------------------------------------------------------
    # Lectura y validacion
    # ---------------------------------------------------------
    def _parse_fraction(self, s: str) -> Fraction:
        s = (s or "").strip()
        if s == "":
            return Fraction(0)
        s = s.replace(",", ".")
        return Fraction(s)

    def _leer_datos(self):
        if not self.entries_c or not self.entries_d:
            raise ValueError("Primero cree las tablas de datos.")
        n = self.n
        C = []
        for i in range(n):
            fila = []
            for j in range(n):
                fila.append(self._parse_fraction(self.entries_c[i][j].get()))
            C.append(fila)

        D = []
        for i in range(n):
            D.append(self._parse_fraction(self.entries_d[i].get()))
        return C, D

    # ---------------------------------------------------------
    # Resolver modelo
    # ---------------------------------------------------------
    def resolver_modelo(self):
        try:
            C, D = self._leer_datos()
        except Exception as exc:
            messagebox.showerror("Error", f"Verifica los datos: {exc}")
            return

        n = self.n
        I = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]
        I_minus_C = [[I[i][j] - C[i][j] for j in range(n)] for i in range(n)]
        A_aug = [row + [D[i]] for i, row in enumerate(deepcopy(I_minus_C))]
        A_inicial = deepcopy(A_aug)

        pasos, matriz_final = self._gauss_jordan(A_aug)
        soluciones, tipo = self._extraer_soluciones(matriz_final)
        self.pasos_guardados = pasos
        self.matriz_final = matriz_final

        self._mostrar_resultado(C, D, I, I_minus_C, A_inicial, pasos, soluciones, tipo)

    # ---------------------------------------------------------
    # Gauss-Jordan con trazas
    # ---------------------------------------------------------
    def _gauss_jordan(self, A):
        n = len(A)
        m = len(A[0]) if A else 0
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
                    "titulo": f"F{fila_pivote+1} \u2194 F{pivote+1}",
                    "comentario": f"Intercambio de filas para ubicar el pivote en la columna {col+1}",
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
                    "titulo": f"F{fila_pivote+1} \u2192 F{fila_pivote+1}/{divisor}",
                    "comentario": f"Normalizacion del pivote en la columna {col+1}",
                    "oper_lines": [],
                    "matriz_lines": self._format_matriz_lines(A)
                })

            for f in range(n):
                if f != fila_pivote and A[f][col] != 0:
                    factor = A[f][col]
                    original_fila = A[f][:]
                    A[f] = [original_fila[j] - factor * A[fila_pivote][j] for j in range(m)]
                    oper_lines = self._format_operacion_vertical_lines(
                        A[fila_pivote], original_fila, factor, A[f], fila_pivote + 1, f + 1
                    )
                    pasos.append({
                        "titulo": f"F{f+1} \u2192 F{f+1} - ({factor})F{fila_pivote+1}",
                        "comentario": f"Se anula el elemento en la columna {col+1}",
                        "oper_lines": oper_lines,
                        "matriz_lines": self._format_matriz_lines(A)
                    })

            fila_pivote += 1
            if fila_pivote >= n:
                break

        return pasos, A

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

    # ---------------------------------------------------------
    # Soluciones
    # ---------------------------------------------------------
    def _extraer_soluciones(self, A):
        n = len(A)
        if n == 0:
            return [], "indeterminado"
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

    # ---------------------------------------------------------
    # Presentacion de resultados
    # ---------------------------------------------------------
    def _matrix_to_lines(self, M):
        if not M:
            return []
        ancho = max(len(str(x)) for fila in M for x in fila)
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

    def _vector_to_lines(self, vec):
        if vec is None:
            return []
        ancho = max(len(str(x)) for x in vec) if vec else 1
        lines = []
        for i, val in enumerate(vec):
            valstr = str(val).rjust(ancho)
            if i == 0:
                lines.append(f"\u23A1 {valstr} \u23A4")
            elif i == len(vec) - 1:
                lines.append(f"\u23A3 {valstr} \u23A6")
            else:
                lines.append(f"\u23A2 {valstr} \u23A5")
        return lines

    def _create_card(self, title, subtitle=None):
        card = tk.Frame(
            self.result_container,
            bg=self.card_bg,
            highlightbackground=self.card_border,
            highlightthickness=1,
            bd=0
        )
        card.pack(fill="x", pady=6)
        header = tk.Frame(card, bg=self.card_bg)
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(header, text=title, font=("Segoe UI", 13, "bold"),
                 bg=self.card_bg, fg="#b91c1c").pack(anchor="w")
        if subtitle:
            tk.Label(
                header,
                text=subtitle,
                font=("Segoe UI", 10),
                bg=self.card_bg,
                fg="#6b4557",
                wraplength=900,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))
        body = tk.Frame(card, bg=self.card_bg)
        body.pack(fill="x", padx=14, pady=(0, 12))
        return card, body

    def _render_lines_block(self, parent, lines, title=None):
        box = tk.Frame(parent, bg="#ffffff", highlightbackground="#f3d1df", highlightthickness=1, bd=0)
        box.pack(fill="x", pady=4)
        if title:
            tk.Label(box, text=title, font=("Segoe UI", 10, "bold"),
                     bg="#ffffff", fg="#b91c1c").pack(anchor="w", padx=10, pady=(8, 2))
        contenido = "\n".join(lines) if lines else "--"
        tk.Label(
            box,
            text=contenido,
            font=self.mono_font,
            bg="#ffffff",
            fg="#40263c",
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 10))
        return box

    def _create_badge(self, parent, text, danger=False):
        bg = "#ffe4e6" if danger else "#fce7f3"
        fg = "#7f1d1d" if danger else "#b91c1c"
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                       bg=bg, fg=fg, padx=10, pady=4)
        lbl.pack(side="left", padx=(0, 6), pady=(0, 4))
        return lbl

    def _render_step(self, parent, idx, step):
        step_frame = tk.Frame(parent, bg="#ffffff", highlightbackground="#f3d1df", highlightthickness=1, bd=0)
        step_frame.pack(fill="x", pady=6)
        header = tk.Frame(step_frame, bg="#ffffff")
        header.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(header, text=f"Paso {idx}: {step['titulo']}", font=("Segoe UI", 11, "bold"),
                 bg="#ffffff", fg="#b91c1c").pack(anchor="w")
        if step.get("comentario"):
            tk.Label(header, text=step["comentario"], font=("Segoe UI", 10),
                     bg="#ffffff", fg="#6b4557").pack(anchor="w", pady=(2, 0))

        content = tk.Frame(step_frame, bg="#ffffff")
        content.pack(fill="x", padx=10, pady=(0, 10))

        if step["oper_lines"]:
            left = tk.Frame(content, bg="#fffafc", highlightbackground="#f5d9e8", highlightthickness=1, bd=0)
            left.pack(side="left", fill="both", expand=True, padx=(0, 8))
            tk.Label(left, text="Operaciones", font=("Segoe UI", 9, "bold"),
                     bg="#fffafc", fg="#7f1d1d").pack(anchor="w", padx=8, pady=(8, 2))
            tk.Label(
                left,
                text="\n".join(step["oper_lines"]),
                font=("Consolas", 10),
                bg="#fffafc",
                fg="#40263c",
                justify="left",
                anchor="nw"
            ).pack(fill="both", padx=8, pady=(0, 8))

        right = tk.Frame(content, bg="#fffafc", highlightbackground="#f5d9e8", highlightthickness=1, bd=0)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Matriz", font=("Segoe UI", 9, "bold"),
                 bg="#fffafc", fg="#7f1d1d").pack(anchor="w", padx=8, pady=(8, 2))
        tk.Label(
            right,
            text="\n".join(step["matriz_lines"]),
            font=self.mono_font,
            bg="#fffafc",
            fg="#40263c",
            justify="left",
            anchor="nw"
        ).pack(fill="both", padx=8, pady=(0, 8))

    def _build_grid_card(self, grid, row, col, title, lines, subtitle=None,
                         button_text=None, button_textvar=None, button_command=None, colspan=1):
        card = tk.Frame(
            grid,
            bg=self.card_bg,
            highlightbackground=self.card_border,
            highlightthickness=1,
            bd=0
        )
        card.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=6, pady=6)
        header = tk.Frame(card, bg=self.card_bg)
        header.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(header, text=title, font=("Segoe UI", 12, "bold"),
                 bg=self.card_bg, fg="#b91c1c").pack(side="left", anchor="w")
        btn = None
        if button_text or button_textvar:
            btn = ttk.Button(
                header,
                text=button_text,
                textvariable=button_textvar,
                style="Ghost.TButton",
                command=button_command
            )
            btn.pack(side="right", anchor="e")
        if subtitle:
            tk.Label(
                card,
                text=subtitle,
                font=("Segoe UI", 9),
                bg=self.card_bg,
                fg="#6b4557",
                wraplength=420,
                justify="left"
            ).pack(fill="x", padx=12, pady=(0, 6))
        body = tk.Frame(card, bg=self.card_bg)
        body.pack(fill="x", padx=12, pady=(0, 10))
        self._render_lines_block(body, lines)
        return card, body, btn

    def _mostrar_resultado(self, C, D, I, I_minus_C, A_inicial, pasos, soluciones, tipo):
        self._clear_result_panel()

        hero_card, hero_body = self._create_card(
            "Modelo de Leontief",
            "Tablero en grid con cada matriz importante y botones para ver procedimientos."
        )
        badges = tk.Frame(hero_body, bg=self.card_bg)
        badges.pack(fill="x")
        self._create_badge(badges, f"n = {self.n} x {self.n}")
        self._create_badge(badges, f"Pasos Gauss-Jordan: {len(pasos)}")
        estado_texto = {
            "determinado": "Sistema determinado",
            "indeterminado": "Sistema con variables libres",
            "incompatible": "Sistema incompatible"
        }.get(tipo, "Estado del sistema")
        self._create_badge(badges, estado_texto, danger=(tipo == "incompatible"))

        grid_wrap = tk.Frame(self.result_container, bg=self.panel_bg)
        grid_wrap.pack(fill="x", pady=(4, 10))
        columns = 2
        for c in range(columns):
            grid_wrap.columnconfigure(c, weight=1)

        self._build_grid_card(
            grid_wrap, 0, 0,
            "Matriz de consumo C",
            self._matrix_to_lines(C),
            "Valores ingresados para C."
        )
        self._build_grid_card(
            grid_wrap, 0, 1,
            "Demanda final D",
            self._vector_to_lines(D),
            "Vector ingresado para D."
        )
        self._build_grid_card(
            grid_wrap, 1, 0,
            "Identidad I",
            self._matrix_to_lines(I),
            "Base para calcular (I - C)."
        )

        toggle_text = tk.StringVar(value="Procedimiento")
        ic_card, ic_body, ic_btn = self._build_grid_card(
            grid_wrap, 1, 1,
            "Resultado (I - C)",
            self._matrix_to_lines(I_minus_C),
            "Resta elemento a elemento entre I y C.",
            button_textvar=toggle_text
        )
        detalle_ic = tk.Frame(ic_body, bg=self.card_bg)
        detalle_ic.pack_forget()

        def toggle_ic():
            if detalle_ic.winfo_manager():
                detalle_ic.pack_forget()
                toggle_text.set("Procedimiento")
            else:
                detalle_ic.pack(fill="x", pady=(10, 0))
                toggle_text.set("Ocultar")

        if ic_btn:
            ic_btn.configure(command=toggle_ic)

        tk.Label(
            detalle_ic,
            text="Detalle de la resta I - C (mismas dimensiones, elemento a elemento).",
            font=("Segoe UI", 10),
            bg=self.card_bg,
            fg="#6b4557",
            wraplength=420,
            justify="left"
        ).pack(anchor="w", pady=(0, 6))
        det_grid = tk.Frame(detalle_ic, bg=self.card_bg)
        det_grid.pack(fill="x", pady=(0, 6))
        det_grid.columnconfigure(0, weight=1)
        det_grid.columnconfigure(1, weight=1)
        left_i = tk.Frame(det_grid, bg=self.card_bg)
        left_i.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right_c = tk.Frame(det_grid, bg=self.card_bg)
        right_c.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._render_lines_block(left_i, self._matrix_to_lines(I), title="Identidad I")
        self._render_lines_block(right_c, self._matrix_to_lines(C), title="Consumo C")
        self._render_lines_block(detalle_ic, self._matrix_to_lines(I_minus_C), title="Resultado (I - C)")

        self._build_grid_card(
            grid_wrap, 2, 0,
            "Matriz aumentada (I - C | D)",
            self._format_matriz_lines(A_inicial),
            "Punto de partida para Gauss-Jordan."
        )
        self._build_grid_card(
            grid_wrap, 2, 1,
            "Matriz reducida (I - C | X)",
            self._format_matriz_lines(self.matriz_final),
            "Resultado final despues de Gauss-Jordan."
        )

        sol_card, sol_body, _ = self._build_grid_card(
            grid_wrap, 3, 0,
            "Vector de produccion total X",
            self._vector_to_lines(soluciones) if soluciones else ["--"],
            "Solucion del sistema (o forma parametrica).",
            colspan=2
        )
        if tipo == "incompatible" or soluciones is None:
            for child in sol_body.winfo_children():
                child.destroy()
            tk.Label(
                sol_body,
                text="El sistema es incompatible: no existe produccion que cumpla con D.",
                font=("Segoe UI", 11, "bold"),
                bg=self.card_bg,
                fg="#b91c1c",
                wraplength=420,
                justify="left"
            ).pack(anchor="w", pady=(0, 6))
        elif tipo == "indeterminado":
            tk.Label(
                sol_body,
                text="El sistema tiene infinitas soluciones; se muestra una forma parametrica.",
                font=("Segoe UI", 9, "bold"),
                bg=self.card_bg,
                fg="#7f1d1d",
                wraplength=420,
                justify="left"
            ).pack(anchor="w", pady=(0, 6))

        if pasos:
            steps_card, steps_body = self._create_card(
                "Procedimiento Gauss-Jordan",
                "Despliega los pasos si quieres ver el detalle completo."
            )
            steps_container = tk.Frame(steps_body, bg=self.card_bg)
            steps_container.pack_forget()
            toggle_steps_text = tk.StringVar(value="Ver pasos")

            def toggle_steps():
                if steps_container.winfo_manager():
                    steps_container.pack_forget()
                    toggle_steps_text.set("Ver pasos")
                else:
                    steps_container.pack(fill="x", pady=(4, 0))
                    toggle_steps_text.set("Ocultar pasos")

            ttk.Button(
                steps_body,
                textvariable=toggle_steps_text,
                style="Ghost.TButton",
                command=toggle_steps
            ).pack(anchor="w", pady=(0, 6))

            for idx, step in enumerate(pasos, start=1):
                self._render_step(steps_container, idx, step)
