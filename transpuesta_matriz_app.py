import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction


class TranspuestaMatrizApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        # ventana
        self.root.title("Transpuesta de Matriz")
        self.root.geometry("900x600")
        self.root.configure(bg="#ffe4e6")
        self.root.resizable(True, True)

        # estilos
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", font=("Segoe UI", 12), background="#ffe4e6", foreground="#b91c1c")
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=8,
            background="#fbb6ce",
            foreground="white",
        )
        style.map(
            "Primary.TButton",
            background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
            foreground=[("!disabled", "white"), ("active", "white")],
        )
        style.configure(
            "Back.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=6,
            background="#fecaca",
            foreground="#b91c1c",
        )
        style.map(
            "Back.TButton",
            background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
            foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")],
        )

        self.bg = "#ffe4e6"
        self.entry_bg = "#fff0f5"

        # contenedores principales
        container = tk.Frame(self.root, bg=self.bg)
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # encabezado
        tk.Label(
            container,
            text="Transpuesta de Matriz",
            font=("Segoe UI", 26, "bold"),
            bg=self.bg,
            fg="#b91c1c",
        ).pack(pady=(10, 6))

        # configuraciÃ³n dimensiones
        cfg = tk.Frame(container, bg=self.bg)
        cfg.pack(pady=(6, 10))

        tk.Label(cfg, text="Filas:", bg=self.bg).grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.var_filas = tk.StringVar(value="2")
        tk.Spinbox(
            cfg,
            from_=1,
            to=50,
            increment=1,
            width=6,
            textvariable=self.var_filas,
            justify="center",
            bg=self.entry_bg
        ).grid(row=0, column=1, padx=6, pady=6)

        tk.Label(cfg, text="Columnas:", bg=self.bg).grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.var_cols = tk.StringVar(value="2")
        tk.Spinbox(
            cfg,
            from_=1,
            to=50,
            increment=1,
            width=6,
            textvariable=self.var_cols,
            justify="center",
            bg=self.entry_bg
        ).grid(row=0, column=3, padx=6, pady=6)

        ttk.Button(cfg, text="Crear matriz", style="Primary.TButton", command=self._crear_cuadricula).grid(
            row=0, column=4, padx=12, pady=6
        )

        # Opciones para modo avanzado: crear matriz B y vector x
        tk.Label(cfg, text=" ", bg=self.bg).grid(row=1, column=0)
        tk.Label(cfg, text="Matriz B filas:", bg=self.bg).grid(row=2, column=0, padx=6, pady=6, sticky="e")
        self.var_b_filas = tk.StringVar(value="2")
        tk.Spinbox(
            cfg,
            from_=1,
            to=50,
            increment=1,
            width=6,
            textvariable=self.var_b_filas,
            justify="center",
            bg=self.entry_bg
        ).grid(row=2, column=1, padx=6, pady=6)

        tk.Label(cfg, text="Matriz B cols:", bg=self.bg).grid(row=2, column=2, padx=6, pady=6, sticky="e")
        self.var_b_cols = tk.StringVar(value="2")
        tk.Spinbox(
            cfg,
            from_=1,
            to=50,
            increment=1,
            width=6,
            textvariable=self.var_b_cols,
            justify="center",
            bg=self.entry_bg
        ).grid(row=2, column=3, padx=6, pady=6)

        ttk.Button(cfg, text="Crear matriz B", style="Primary.TButton", command=self._crear_cuadricula_B).grid(
            row=2, column=4, padx=12, pady=6
        )

        tk.Label(cfg, text="Vector x filas:", bg=self.bg).grid(row=3, column=0, padx=6, pady=6, sticky="e")
        self.var_x_rows = tk.StringVar(value="2")
        tk.Spinbox(
            cfg,
            from_=1,
            to=50,
            increment=1,
            width=6,
            textvariable=self.var_x_rows,
            justify="center",
            bg=self.entry_bg
        ).grid(row=3, column=1, padx=6, pady=6)
        ttk.Button(cfg, text="Crear vector x", style="Primary.TButton", command=self._crear_vector_x).grid(
            row=3, column=4, padx=12, pady=6
        )

        # zona de ingreso de matriz
        self.ingreso_frame = tk.Frame(container, bg=self.bg)
        self.ingreso_frame.pack(pady=(8, 6))
        self.entries_grid = None
        self.dim = (0, 0)

        # acciones
        actions = tk.Frame(container, bg=self.bg)
        actions.pack(pady=(4, 8), fill="x")

        self.var_animar = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            actions,
            text="Animar paso a paso",
            variable=self.var_animar
        ).pack(side="left", padx=8)

        self.btn_calcular = ttk.Button(
            actions, text="Calcular transpuesta", style="Primary.TButton", command=self._calcular_transpuesta
        )
        self.btn_calcular.pack(side="left", padx=8)
        self.btn_calcular.state(["disabled"])  # hasta que exista la cuadricula

        ttk.Button(actions, text="Volver al inicio", style="Back.TButton", command=self._volver_al_inicio).pack(
            side="right", padx=8
        )

        # Modo avanzado: entrada de expresiones y evaluador
        adv = tk.Frame(container, bg=self.bg)
        adv.pack(pady=(6, 8), fill="x")
        tk.Label(adv, text="Operaciones avanzadas:", bg=self.bg, font=("Segoe UI", 12, "bold"), fg="#7f1d1d").pack(
            anchor="w", padx=6
        )
        expr_row = tk.Frame(adv, bg=self.bg)
        expr_row.pack(fill="x", padx=6, pady=4)
        tk.Label(expr_row, text="ExpresiÃ³n:", bg=self.bg).pack(side="left")
        self.expr_entry = tk.Entry(expr_row, width=60, bg="white")
        self.expr_entry.pack(side="left", padx=8)
        ttk.Button(expr_row, text="Evaluar expresiÃ³n", style="Primary.TButton", command=self._evaluar_expresion).pack(
            side="left", padx=8
        )

        # resultados
        self.result_frame = tk.Frame(container, bg=self.bg)
        self.result_frame.pack(pady=(10, 6), fill="both", expand=True)

    # utilidades
    def _parse_fraction(self, s: str) -> Fraction:
        s = (s or "").strip()
        if s == "":
            return Fraction(0)
        s = s.replace(",", ".")
        return Fraction(s)

    def _crear_cuadricula(self):
        # limpiar grillas previas
        for w in self.ingreso_frame.winfo_children():
            w.destroy()
        for w in self.result_frame.winfo_children():
            w.destroy()

        try:
            f = int(self.var_filas.get())
            c = int(self.var_cols.get())
            if f <= 0 or c <= 0:
                raise ValueError
            # lÃ­mite razonable para UI
            if f > 12 or c > 12:
                messagebox.showwarning(
                    "Aviso",
                    "Dimensiones grandes pueden dificultar la visualizaciÃ³n (mÃ¡ximo 12x12).",
                )
        except Exception:
            messagebox.showerror("Error", "Ingrese dimensiones vÃ¡lidas (enteros positivos).")
            return

        self.dim = (f, c)

        grid = tk.Frame(self.ingreso_frame, bg=self.bg)
        grid.pack()
        self.entries_grid = []
        for i in range(f):
            row_entries = []
            for j in range(c):
                e = tk.Entry(
                    grid,
                    width=8,
                    justify="center",
                    font=("Segoe UI", 11),
                    bg=self.entry_bg
                )
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.entries_grid.append(row_entries)

        # habilitar calcular
        try:
            self.btn_calcular.state(["!disabled"])
        except Exception:
            pass

    def _leer_matriz(self):
        if not self.entries_grid:
            raise ValueError("Primero cree la matriz.")
        f, c = self.dim
        mat = []
        for i in range(f):
            row = []
            for j in range(c):
                txt = self.entries_grid[i][j].get()
                val = self._parse_fraction(txt)
                row.append(val)
            mat.append(row)
        return mat

    def _calcular_transpuesta(self):
        for w in self.result_frame.winfo_children():
            w.destroy()
        try:
            A = self._leer_matriz()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        f = len(A)
        c = len(A[0]) if f else 0

        # T tendrÃ¡ tamaÃ±o c x f
        res_title = tk.Label(
            self.result_frame,
            text="Resultado (Transpuesta)",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg,
            fg="#b91c1c",
        )
        res_title.pack(pady=(4, 6))

        grid = tk.Frame(self.result_frame, bg=self.bg)
        grid.pack()

        # preparar grilla de etiquetas para el resultado
        self.result_labels = []
        for i in range(c):
            row_lbls = []
            for j in range(f):
                lbl = tk.Label(
                    grid,
                    text="",
                    bg=self.bg,
                    fg="#111",
                    font=("Segoe UI", 11),
                    relief="groove",
                    width=10,
                    anchor="center",
                )
                lbl.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")
                row_lbls.append(lbl)
            self.result_labels.append(row_lbls)

        # secciÃ³n de pasos
        pasos_title = tk.Label(
            self.result_frame,
            text="Pasos detallados",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg,
            fg="#b91c1c",
        )
        pasos_title.pack(pady=(10, 4))

        pasos_frame = tk.Frame(self.result_frame, bg=self.bg)
        pasos_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(pasos_frame)
        scrollbar.pack(side="right", fill="y")
        self.pasos_text = tk.Text(pasos_frame, height=10, yscrollcommand=scrollbar.set, bg="white")
        self.pasos_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.pasos_text.yview)

        # ejecutar modo animado o directo
        if self.var_animar.get():
            self._iniciar_animacion(A)
        else:
            self._mostrar_directo(A)

    def _mostrar_directo(self, A):
        f = len(A)
        c = len(A[0]) if f else 0
        pasos = []
        for i in range(f):
            for j in range(c):
                val = A[i][j]
                # T[j][i] = A[i][j]
                self.result_labels[j][i].config(text=str(val))
                pasos.append(f"Paso {len(pasos)+1}: A[{i+1},{j+1}] -> T[{j+1},{i+1}] = {val}")
        self.pasos_text.insert("1.0", "\n".join(pasos))

    def _iniciar_animacion(self, A):
        # crear lista de pares (i,j) en orden fila-por-fila
        f = len(A)
        c = len(A[0]) if f else 0
        self._anim_pairs = [(i, j) for i in range(f) for j in range(c)]
        self._anim_index = 0
        self._A_anim = A
        self._animar_siguiente()

    def _animar_siguiente(self):
        if self._anim_index >= len(self._anim_pairs):
            return
        i, j = self._anim_pairs[self._anim_index]
        val = self._A_anim[i][j]
        # T[j][i] = val
        self.result_labels[j][i].config(text=str(val))
        paso_txt = f"Paso {self._anim_index+1}: A[{i+1},{j+1}] -> T[{j+1},{i+1}] = {val}\n"
        self.pasos_text.insert("end", paso_txt)
        self.pasos_text.see("end")
        self._anim_index += 1
        # programar siguiente paso
        self.root.after(300, self._animar_siguiente)

    # --- Funciones y UI para modo avanzado ---
    def _crear_cuadricula_B(self):
        # limpiar area B si existe
        if not hasattr(self, 'ingreso_frame_B'):
            self.ingreso_frame_B = tk.Frame(self.root, bg=self.bg)
            # lo colocamos debajo del ingreso principal
            self.ingreso_frame_B.pack(padx=16, pady=(0, 8))
        for w in getattr(self, 'ingreso_frame_B').winfo_children():
            w.destroy()
        try:
            f = int(self.var_b_filas.get())
            c = int(self.var_b_cols.get())
            if f <= 0 or c <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Ingrese dimensiones vÃ¡lidas para B.")
            return
        self.dim_B = (f, c)
        grid = tk.Frame(self.ingreso_frame_B, bg=self.bg)
        grid.pack()
        self.entries_grid_B = []
        for i in range(f):
            row_entries = []
            for j in range(c):
                e = tk.Entry(
                    grid,
                    width=8,
                    justify="center",
                    font=("Segoe UI", 11),
                    bg=self.entry_bg
                )
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.entries_grid_B.append(row_entries)

    def _crear_vector_x(self):
        if not hasattr(self, 'ingreso_frame_x'):
            self.ingreso_frame_x = tk.Frame(self.root, bg=self.bg)
            self.ingreso_frame_x.pack(padx=16, pady=(0, 8))
        for w in getattr(self, 'ingreso_frame_x').winfo_children():
            w.destroy()
        try:
            f = int(self.var_x_rows.get())
            if f <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Ingrese dimensiones vÃ¡lidas para x.")
            return
        self.dim_x = (f, 1)
        grid = tk.Frame(self.ingreso_frame_x, bg=self.bg)
        grid.pack()
        self.entries_vector_x = []
        for i in range(f):
            e = tk.Entry(
                grid,
                width=10,
                justify="center",
                font=("Segoe UI", 11),
                bg=self.entry_bg
            )
            e.grid(row=i, column=0, padx=6, pady=6)
            self.entries_vector_x.append(e)

    def _leer_matriz_B(self):
        if not hasattr(self, 'entries_grid_B') or not self.entries_grid_B:
            return None
        f, c = self.dim_B
        mat = []
        for i in range(f):
            row = []
            for j in range(c):
                txt = self.entries_grid_B[i][j].get()
                val = self._parse_fraction(txt)
                row.append(val)
            mat.append(row)
        return mat

    def _leer_vector_x(self):
        if not hasattr(self, 'entries_vector_x') or not self.entries_vector_x:
            return None
        n = len(self.entries_vector_x)
        mat = []
        for i in range(n):
            txt = self.entries_vector_x[i].get()
            val = self._parse_fraction(txt)
            mat.append([val])
        return mat

    # funciones matriciales con Fraction
    def _mat_transpose(self, M):
        if M is None:
            return None
        r = len(M)
        c = len(M[0]) if r else 0
        return [[M[i][j] for i in range(r)] for j in range(c)]

    def _mat_add(self, A, B):
        if A is None or B is None:
            raise ValueError("OperaciÃ³n requiere dos matrices.")
        ra = len(A); ca = len(A[0]) if ra else 0
        rb = len(B); cb = len(B[0]) if rb else 0
        if ra != rb or ca != cb:
            raise ValueError("OperaciÃ³n no definida: dimensiones incompatibles para suma.")
        return [[A[i][j] + B[i][j] for j in range(ca)] for i in range(ra)]

    def _mat_sub(self, A, B):
        if A is None or B is None:
            raise ValueError("OperaciÃ³n requiere dos matrices.")
        ra = len(A); ca = len(A[0]) if ra else 0
        rb = len(B); cb = len(B[0]) if rb else 0
        if ra != rb or ca != cb:
            raise ValueError("OperaciÃ³n no definida: dimensiones incompatibles para resta.")
        return [[A[i][j] - B[i][j] for j in range(ca)] for i in range(ra)]

    def _mat_mul(self, A, B):
        if A is None or B is None:
            raise ValueError("OperaciÃ³n requiere dos operandos.")
        ra = len(A); ca = len(A[0]) if ra else 0
        rb = len(B); cb = len(B[0]) if rb else 0
        if ca != rb:
            raise ValueError(f"OperaciÃ³n no definida: columnas de la izquierda ({ca}) != filas de la derecha ({rb}).")
        # resultado ra x cb
        C = [[Fraction(0) for _ in range(cb)] for __ in range(ra)]
        for i in range(ra):
            for j in range(cb):
                s = Fraction(0)
                for k in range(ca):
                    s += A[i][k] * B[k][j]
                C[i][j] = s
        return C

    def _mat_to_str(self, M):
        if M is None:
            return ""
        return "\n".join(["\t".join([str(v) for v in row]) for row in M])

    # parser simple de expresiones con A, B, x y ^T
    def _preprocess_expr(self, s: str) -> str:
        # insertar '*' para multiplicaciÃ³n implÃ­cita entre A,B,x, ')'
        s = s.replace(' ', '')
        out = ''
        prev = ''
        for ch in s:
            if prev and ((prev in 'ABx)' ) and (ch in 'ABx(')):
                out += '*'
            out += ch
            prev = ch
        return out

    def _tokenize(self, s: str):
        tokens = []
        i = 0
        while i < len(s):
            if s[i].isalpha():
                # A, B, x
                if s[i] in ('A','B','x'):
                    # check for ^T after
                    if i+2 <= len(s)-1 and s[i+1] == '^' and s[i+2] == 'T':
                        tokens.append(s[i])
                        tokens.append('^T')
                        i += 3
                        continue
                    tokens.append(s[i])
                    i += 1
                    continue
                else:
                    raise ValueError('Token desconocido: '+s[i])
            if s.startswith('^T', i):
                tokens.append('^T'); i += 2; continue
            if s[i] in '+-*()':
                tokens.append(s[i]); i += 1; continue
            # parentesis cerrado
            # salto si hay espacios
            if s[i].isspace():
                i += 1; continue
            raise ValueError('Caracter invalido en expresiÃ³n: '+s[i])
        return tokens

    def _to_postfix(self, tokens):
        # shunting-yard: operators +,- (prec1 left), * (prec2 left), ^T (postfix, treat as func)
        out = []
        ops = []
        prec = {'+':1,'-':1,'*':2}
        for t in tokens:
            if t in ('A','B','x'):
                out.append(t)
            elif t == '^T':
                # postfix operator: directly add to output to be applied
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
                if not ops:
                    raise ValueError('ParÃ©ntesis desbalanceados')
                ops.pop()
            else:
                raise ValueError('Token inesperado: '+str(t))
        while ops:
            if ops[-1] in '()':
                raise ValueError('ParÃ©ntesis desbalanceados')
            out.append(ops.pop())
        return out

    def _eval_postfix(self, postfix, A, B, x):
        # Generate human-friendly step descriptions with intermediate results
        stack = []  # items are (name, matrix)
        pasos = []
        temp_idx = 1

        def mat_lines(M):
            return [" ".join(str(v) for v in row) for row in M]

        for t in postfix:
            if t == 'A':
                stack.append(('A', A))
            elif t == 'B':
                if B is None:
                    raise ValueError('B no definida pero usada en expresiÃ³n')
                stack.append(('B', B))
            elif t == 'x':
                if x is None:
                    raise ValueError('x no definido pero usado en expresiÃ³n')
                stack.append(('x', x))
            elif t == '^T':
                if not stack:
                    raise ValueError('Operador ^T sin operando')
                name, mat = stack.pop()
                R = self._mat_transpose(mat)
                new_name = f"C{temp_idx}"
                temp_idx += 1
                pasos.append(f"Paso: Transponer {name} -> {new_name}")
                pasos.append("La transpuesta intercambia filas por columnas.")
                pasos.extend(mat_lines(R))
                stack.append((new_name, R))
            elif t in ('+','-','*'):
                if len(stack) < 2:
                    raise ValueError('Operandos insuficientes para operador '+t)
                right_name, right = stack.pop()
                left_name, left = stack.pop()
                new_name = f"C{temp_idx}"
                temp_idx += 1
                if t == '+':
                    R = self._mat_add(left, right)
                    pasos.append(f"Paso: Suma {left_name} + {right_name} -> {new_name}")
                    pasos.append("Suma elemento a elemento:")
                    for i in range(len(R)):
                        row_expr = "   ".join(f"{left[i][j]}+{right[i][j]}" for j in range(len(R[0])))
                        pasos.append(row_expr)
                    pasos.append("Resultado intermedio {} =:" .format(new_name))
                    pasos.extend(mat_lines(R))
                elif t == '-':
                    R = self._mat_sub(left, right)
                    pasos.append(f"Paso: Resta {left_name} - {right_name} -> {new_name}")
                    pasos.append("Resta elemento a elemento:")
                    for i in range(len(R)):
                        row_expr = "   ".join(f"{left[i][j]}-{right[i][j]}" for j in range(len(R[0])))
                        pasos.append(row_expr)
                    pasos.append("Resultado intermedio {} =:" .format(new_name))
                    pasos.extend(mat_lines(R))
                else:
                    R = self._mat_mul(left, right)
                    pasos.append(f"Paso: Multiplicación {left_name} · {right_name} -> {new_name}")
                    pasos.append("Calcular entradas como suma de productos:")
                    for i in range(len(R)):
                        for j in range(len(R[0])):
                            terms = [f"{left[i][k]}·{right[k][j]}" for k in range(len(left[0]))]
                            pasos.append(f"R[{i+1},{j+1}] = " + " + ".join(terms) + f" = {R[i][j]}")
                stack.append((new_name, R))
            else:
                raise ValueError('Token desconocido en postfijo: '+str(t))
        if len(stack) != 1:
            raise ValueError('ExpresiÃ³n invalida, pila final: '+str(len(stack)))
        final_name, final_mat = stack[0]
        return final_mat, pasos

    def _evaluar_expresion(self):
        for w in self.result_frame.winfo_children():
            w.destroy()
        expr_raw = (self.expr_entry.get() or '').strip()
        if not expr_raw:
            messagebox.showerror('Error', 'Ingrese una expresiÃ³n para evaluar.')
            return
        try:
            A = self._leer_matriz()
        except Exception as e:
            messagebox.showerror('Error', 'Error leyendo A: '+str(e))
            return
        B = None
        x = None
        try:
            B = self._leer_matriz_B()
        except Exception as e:
            messagebox.showerror('Error', 'Error leyendo B: '+str(e))
            return
        try:
            x = self._leer_vector_x()
        except Exception as e:
            messagebox.showerror('Error', 'Error leyendo x: '+str(e))
            return

        try:
            s = self._preprocess_expr(expr_raw)
            tokens = self._tokenize(s)
            postfix = self._to_postfix(tokens)
            R, pasos = self._eval_postfix(postfix, A, B, x)
        except Exception as e:
            messagebox.showerror('Error', str(e))
            return

        # mostrar resultado
        r = len(R)
        c = len(R[0]) if r else 0
        res_title = tk.Label(
            self.result_frame,
            text=f"Resultado (ExpresiÃ³n: {expr_raw})",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg,
            fg="#b91c1c",
        )
        res_title.pack(pady=(4, 6))
        grid = tk.Frame(self.result_frame, bg=self.bg)
        grid.pack()
        self.result_labels = []
        for i in range(r):
            row_lbls = []
            for j in range(c):
                lbl = tk.Label(
                    grid,
                    text=str(R[i][j]),
                    bg=self.bg,
                    fg="#111",
                    font=("Segoe UI", 11),
                    relief="groove",
                    width=12,
                    anchor="center",
                )
                lbl.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")
                row_lbls.append(lbl)
            self.result_labels.append(row_lbls)

        pasos_title = tk.Label(
            self.result_frame,
            text="Pasos (resumen)",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg,
            fg="#b91c1c",
        )
        pasos_title.pack(pady=(10, 4))
        pasos_frame = tk.Frame(self.result_frame, bg=self.bg)
        pasos_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(pasos_frame)
        scrollbar.pack(side="right", fill="y")
        self.pasos_text = tk.Text(pasos_frame, height=8, yscrollcommand=scrollbar.set, bg="white")
        self.pasos_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.pasos_text.yview)
        self.pasos_text.insert('1.0', '\n'.join(pasos))

    def _volver_al_inicio(self):
        try:
            # cerrar esta ventana Toplevel y delegar al callback recibido
            self.root.destroy()
        finally:
            try:
                if callable(self.volver_callback):
                    self.volver_callback()
            except Exception:
                pass


