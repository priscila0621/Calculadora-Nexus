import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction


def _fmt(x: Fraction) -> str:
    try:
        return str(x)
    except Exception:
        return f"{x}"


class InversaMatrizApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        # ventana
        self.root.title("Inversa de Matriz")
        self.root.geometry("1000x720")
        self.root.configure(bg="#ffe4e6")
        self.root.resizable(True, True)

        # estilos
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", font=("Segoe UI", 12), background="#ffe4e6", foreground="#b91c1c")
        style.configure("Primary.TButton", font=("Segoe UI", 12, "bold"), padding=8,
                        background="#fbb6ce", foreground="white")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])
        style.configure("Back.TButton", font=("Segoe UI", 11, "bold"), padding=6,
                        background="#fecaca", foreground="#b91c1c")
        style.map("Back.TButton",
                  background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])

        self.bg = "#ffe4e6"
        self.entry_bg = "#fff0f5"

        # contenedor principal con scroll (toda la ventana desplazable)
        outer = tk.Frame(self.root, bg=self.bg)
        outer.pack(fill="both", expand=True, padx=16, pady=12)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(outer, bg=self.bg, highlightthickness=0)
        self.vscroll = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.hscroll = ttk.Scrollbar(outer, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vscroll.set, xscrollcommand=self.hscroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vscroll.grid(row=0, column=1, sticky="ns")
        self.hscroll.grid(row=1, column=0, sticky="ew")

        container = tk.Frame(self.canvas, bg=self.bg)
        self.container_window = self.canvas.create_window((0, 0), window=container, anchor="nw")

        def _update_scrollregion(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def _expand_width(event):
            # Hace que el contenido use todo el ancho visible
            self.canvas.itemconfigure(self.container_window, width=event.width)

        container.bind("<Configure>", _update_scrollregion)
        self.canvas.bind("<Configure>", _expand_width)

        # Desplazamiento con la rueda del mouse
        def _on_mousewheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
            except Exception:
                delta = -1
            self.canvas.yview_scroll(delta, "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # encabezado
        tk.Label(container, text="Inversa de Matriz", font=("Segoe UI", 26, "bold"),
                 bg=self.bg, fg="#b91c1c").pack(pady=(10, 6))

        # configuración
        cfg = tk.Frame(container, bg=self.bg)
        cfg.pack(pady=6)
        tk.Label(cfg, text="Tamaño (n x n):", bg=self.bg).grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.var_n = tk.StringVar(value="3")
        tk.Spinbox(cfg, from_=1, to=12, increment=1, width=6,
                   textvariable=self.var_n, justify="center", bg=self.entry_bg).grid(row=0, column=1, padx=6, pady=6)

        ttk.Button(cfg, text="Crear matriz", style="Primary.TButton", command=self._crear_cuadricula)\
            .grid(row=0, column=2, padx=12, pady=6)

        # ingreso matriz
        self.ingreso_frame = tk.Frame(container, bg=self.bg)
        self.ingreso_frame.pack(pady=(8, 6))
        self.entries_grid = None
        self.n = 0

        # acciones
        actions = tk.Frame(container, bg=self.bg)
        actions.pack(pady=(4, 8), fill="x")

        # selección de método
        self.metodo = tk.StringVar(value="adj")  # adj (n<=3) o gj
        ttk.Label(actions, text="Método:", background=self.bg).pack(side="left", padx=(0,4))
        ttk.Radiobutton(actions, text="Adjunta (n3)", variable=self.metodo, value="adj").pack(side="left", padx=4)
        ttk.Radiobutton(actions, text="Gauss-Jordan", variable=self.metodo, value="gj").pack(side="left", padx=4)

        self.var_animar = tk.BooleanVar(value=False)
        ttk.Checkbutton(actions, text="Animar paso a paso", variable=self.var_animar).pack(side="left", padx=12)

        self.btn_calcular = ttk.Button(actions, text="Calcular inversa", style="Primary.TButton",
                                       command=self._calcular_inversa)
        self.btn_calcular.pack(side="left", padx=8)
        self.btn_calcular.state(["disabled"])  # hasta crear la grilla

        ttk.Button(actions, text="Volver al inicio", style="Back.TButton", command=self._volver_al_inicio)\
            .pack(side="right", padx=8)

        # resultados
        self.result_frame = tk.Frame(container, bg=self.bg)
        self.result_frame.pack(fill="both", expand=True, pady=(6, 6))

    # helpers UI simples
    def _clear_result(self):
        for w in self.result_frame.winfo_children():
            w.destroy()

    def _render_matrix(self, parent, M):
        grid = tk.Frame(parent, bg=self.bg)
        grid.pack(pady=4)
        for i, fila in enumerate(M):
            for j, val in enumerate(fila):
                tk.Label(
                    grid, text=_fmt(val), bg=self.bg, fg="#111",
                    font=("Segoe UI", 11), relief="groove", width=10, anchor="center"
                ).grid(row=i, column=j, padx=4, pady=4, sticky="nsew")
        return grid

    # utilidades
    def _parse_fraction(self, s: str) -> Fraction:
        s = (s or "").strip()
        if s == "":
            return Fraction(0)
        s = s.replace(",", ".")
        return Fraction(s)

    def _crear_cuadricula(self):
        for w in self.ingreso_frame.winfo_children():
            w.destroy()
        self._clear_result()

        try:
            n = int(self.var_n.get())
            if n <= 0:
                raise ValueError
            if n > 12:
                messagebox.showwarning("Aviso", "Tamao grande puede ser difcil de visualizar (mx 12).")
        except Exception:
            messagebox.showerror("Error", "Ingrese n valido (entero positivo).")
            return

        self.n = n
        grid = tk.Frame(self.ingreso_frame, bg=self.bg)
        grid.pack()
        self.entries_grid = []
        for i in range(n):
            row_entries = []
            for j in range(n):
                e = tk.Entry(grid, width=8, justify="center", font=("Segoe UI", 11), bg=self.entry_bg)
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.entries_grid.append(row_entries)

        try:
            self.btn_calcular.state(["!disabled"])
        except Exception:
            pass

    def _leer_matriz(self):
        if not self.entries_grid:
            raise ValueError("Primero cree la matriz.")
        n = self.n
        A = []
        for i in range(n):
            fila = []
            for j in range(n):
                txt = self.entries_grid[i][j].get()
                fila.append(self._parse_fraction(txt))
            A.append(fila)
        return A

    # UI helpers para mostrar [A|I]
    def _build_augmented_view(self, n):
        wrapper = tk.Frame(self.result_frame, bg=self.bg)
        wrapper.pack(pady=6)

        left_col = tk.Frame(wrapper, bg=self.bg)
        left_col.pack(side="left", padx=(0, 10))
        right_col = tk.Frame(wrapper, bg=self.bg)
        right_col.pack(side="left", padx=(10, 0))

        tk.Label(left_col, text="A (trabajo)", font=("Segoe UI", 14, "bold"), bg=self.bg, fg="#b91c1c").pack()
        tk.Label(right_col, text="I / Inversa", font=("Segoe UI", 14, "bold"), bg=self.bg, fg="#b91c1c").pack()

        self.grid_A = tk.Frame(left_col, bg=self.bg)
        self.grid_A.pack(pady=6)
        self.grid_I = tk.Frame(right_col, bg=self.bg)
        self.grid_I.pack(pady=6)

        self.lbl_A = []
        self.lbl_I = []
        for i in range(n):
            ra = []
            ri = []
            for j in range(n):
                la = tk.Label(self.grid_A, text="", bg=self.bg, fg="#111", font=("Segoe UI", 11),
                              relief="groove", width=10, anchor="center")
                la.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")
                li = tk.Label(self.grid_I, text="", bg=self.bg, fg="#111", font=("Segoe UI", 11),
                              relief="groove", width=10, anchor="center")
                li.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")
                ra.append(la)
                ri.append(li)
            self.lbl_A.append(ra)
            self.lbl_I.append(ri)

        # área de pasos
        pasos_title = tk.Label(self.result_frame, text="Pasos detallados", font=("Segoe UI", 14, "bold"),
                               bg=self.bg, fg="#b91c1c")
        pasos_title.pack(pady=(10, 4))
        pasos_frame = tk.Frame(self.result_frame, bg=self.bg)
        pasos_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(pasos_frame)
        scrollbar.pack(side="right", fill="y")
        self.pasos_text = tk.Text(pasos_frame, height=10, wrap="none", yscrollcommand=scrollbar.set, bg="white")
        self.pasos_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.pasos_text.yview)
        # scroll horizontal para pasos (cuando hay líneas largas)
        scrollbar_x = ttk.Scrollbar(pasos_frame, orient="horizontal", command=self.pasos_text.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        self.pasos_text.configure(xscrollcommand=scrollbar_x.set)
        # estilos para encabezados/comentarios en pasos detallados
        try:
            self.pasos_text.tag_configure("bold", font=("Consolas", 12, "bold"))
            self.pasos_text.tag_configure("comment", font=("Consolas", 10, "italic"), foreground="#555")
        except Exception:
            pass

    def _render_augmented(self, A, I):
        # Si no hay grillas construidas (caso no invertible), no hacer nada
        if not hasattr(self, 'lbl_A') or not self.lbl_A or not hasattr(self, 'lbl_I') or not self.lbl_I:
            return
        n = self.n
        for i in range(n):
            for j in range(n):
                self.lbl_A[i][j].config(text=_fmt(A[i][j]))
                self.lbl_I[i][j].config(text=_fmt(I[i][j]))

    # -----------------------------
    # Comprobación c), d), e) vía RREF
    # -----------------------------
    def _rref_info(self, A):
        """Devuelve (RREF, columnas_pivote, columnas_libres) usando Fraction.

        Construye una copia de A y aplica GaussJordan completo.
        """
        n = len(A)
        if n == 0:
            return [], [], []
        m = len(A[0])
        M = [row[:] for row in A]
        row = 0
        piv_cols = []
        for col in range(m):
            if row >= n:
                break
            # buscar pivote no nulo en o debajo de 'row'
            piv = None
            for r in range(row, n):
                if M[r][col] != 0:
                    piv = r
                    break
            if piv is None:
                continue
            if piv != row:
                M[row], M[piv] = M[piv], M[row]
            a = M[row][col]
            if a != 1:
                M[row] = [v / a for v in M[row]]
            for r in range(n):
                if r == row:
                    continue
                f = M[r][col]
                if f != 0:
                    M[r] = [M[r][j] - f * M[row][j] for j in range(m)]
            piv_cols.append(col)
            row += 1
        free_cols = [j for j in range(m) if j not in piv_cols]
        return M, piv_cols, free_cols

    def _explain_failure_cde(self, A, text_widget):
        """Escribe en el text_widget la justificación usando c), d) y e)."""
        R, piv_cols, free_cols = self._rref_info(A)
        n = len(A)
        # helper insert
        def ins(s=""):
            try:
                text_widget.insert("end", s + "\n")
            except Exception:
                pass
        ins("Comprobacion de invertibilidad (c, d, e)")
        ins("")
        ins("RREF de A:")
        # formato sencillo
        if R:
            maxw = max(len(str(v)) for fila in R for v in fila)
            for fila in R:
                ins(" ".join(str(v).rjust(maxw) for v in fila))
        ins("")
        if len(piv_cols) != n:
            ins(f"- (c) No tiene n posiciones pivote: {len(piv_cols)} de {n}.")
        else:
            ins(f"- (c) Tiene n posiciones pivote: {len(piv_cols)} de {n}.")
        # (d) Construir una solución no trivial si hay libres
        if free_cols:
            j0 = free_cols[0]
            x = [Fraction(0) for _ in range(n)]
            x[j0] = Fraction(1)
            for r, pc in enumerate(piv_cols):
                if j0 < len(R[0]):
                    x[pc] = -R[r][j0]
            ins("")
            ins("- (d) Existe solucion no trivial para Ax = 0. Ejemplo:")
            ins("x = [ " + ", ".join(str(v) for v in x) + " ]^t")
            ins("")
            ins("- (e) Por consiguiente, las columnas de A son linealmente dependientes (no LI).")
        else:
            ins("")
            ins("- (d) Ax=0 solo tiene la solucion trivial.")
    def _calcular_inversa(self):
        for w in self.result_frame.winfo_children():
            w.destroy()
        try:
            A = self._leer_matriz()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        n = self.n

        metodo = self.metodo.get()
        if metodo == "adj" and n <= 3:
            self._calcular_inversa_adjunta(A)
        else:
            # identidad
            I = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]

                        # Verificar invertibilidad antes de construir las grillas A/I
            ok, _ = self._gauss_jordan_steps(A, I, collect_only=True)

            if self.var_animar.get():
                if not ok:
                    pasos_title = tk.Label(self.result_frame, text="Pasos detallados", font=("Segoe UI", 14, "bold"),
                                           bg=self.bg, fg="#b91c1c")
                    pasos_title.pack(pady=(10, 4))
                    pasos_frame = tk.Frame(self.result_frame, bg=self.bg)
                    pasos_frame.pack(fill="both", expand=True)
                    scrollbar = ttk.Scrollbar(pasos_frame)
                    scrollbar.pack(side="right", fill="y")
                    self.pasos_text = tk.Text(pasos_frame, height=10, wrap="none", yscrollcommand=scrollbar.set, bg="white")
                    self.pasos_text.pack(side="left", fill="both", expand=True)
                    scrollbar.config(command=self.pasos_text.yview)
                    # scroll horizontal para pasos (cuando hay lineas largas)
                    scrollbar_x = ttk.Scrollbar(pasos_frame, orient="horizontal", command=self.pasos_text.xview)
                    scrollbar_x.pack(side="bottom", fill="x")
                    self.pasos_text.configure(xscrollcommand=scrollbar_x.set)
                    # estilos para encabezados/comentarios en pasos detallados
                    try:
                        self.pasos_text.tag_configure("bold", font=("Consolas", 12, "bold"))
                        self.pasos_text.tag_configure("comment", font=("Consolas", 10, "italic"), foreground="#555")
                    except Exception:
                        pass
                    self._render_detailed_gauss_jordan(A, I)
                    return
                self._build_augmented_view(n)
                self._render_augmented(A, I)
                self._start_animation(A, I)
            else:
                if not ok:
                    pasos_title = tk.Label(self.result_frame, text="Pasos detallados", font=("Segoe UI", 14, "bold"),
                                           bg=self.bg, fg="#b91c1c")
                    pasos_title.pack(pady=(10, 4))
                    pasos_frame = tk.Frame(self.result_frame, bg=self.bg)
                    pasos_frame.pack(fill="both", expand=True)
                    scrollbar = ttk.Scrollbar(pasos_frame)
                    scrollbar.pack(side="right", fill="y")
                    self.pasos_text = tk.Text(pasos_frame, height=10, wrap="none", yscrollcommand=scrollbar.set, bg="white")
                    self.pasos_text.pack(side="left", fill="both", expand=True)
                    scrollbar.config(command=self.pasos_text.yview)
                    # scroll horizontal para pasos (cuando hay lineas largas)
                    scrollbar_x = ttk.Scrollbar(pasos_frame, orient="horizontal", command=self.pasos_text.xview)
                    scrollbar_x.pack(side="bottom", fill="x")
                    self.pasos_text.configure(xscrollcommand=scrollbar_x.set)
                    # estilos para encabezados/comentarios en pasos detallados
                    try:
                        self.pasos_text.tag_configure("bold", font=("Consolas", 12, "bold"))
                        self.pasos_text.tag_configure("comment", font=("Consolas", 10, "italic"), foreground="#555")
                    except Exception:
                        pass
                    self._render_detailed_gauss_jordan(A, I)
                    return
                self._build_augmented_view(n)
                self._render_augmented(A, I)
                self._render_detailed_gauss_jordan(A, I)

    # --------- Método de la adjunta (n<=3) con pasos detallados ----------
    def _calcular_inversa_adjunta(self, A):
        n = self.n

        # layout superior con dos columnas (como en la imagen)
        top = tk.Frame(self.result_frame, bg=self.bg)
        top.pack(fill="x", pady=(4, 8))
        left = tk.Frame(top, bg=self.bg)
        left.pack(side="left", expand=True, padx=(0, 10))
        right = tk.Frame(top, bg=self.bg)
        right.pack(side="left", expand=True, padx=(10, 0))

        # columna izquierda: A (no mostramos A^t para evitar confusiones)
        tk.Label(left, text="A =", font=("Segoe UI", 16, "bold"), bg=self.bg, fg="#b91c1c").pack()
        self._render_matrix(left, A)

        # columna derecha: |A| paso a paso y Adj(A)
        tk.Label(right, text="|A|", font=("Segoe UI", 16, "bold"), bg=self.bg, fg="#b91c1c").pack()
        pasos_frame = tk.Frame(right, bg=self.bg)
        pasos_frame.pack(fill="both", expand=True)
        scrollbar_y = ttk.Scrollbar(pasos_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        pasos_text = tk.Text(
            pasos_frame, height=10, wrap="none",
            yscrollcommand=scrollbar_y.set, bg="white"
        )
        pasos_text.pack(side="left", fill="both", expand=True)
        scrollbar_y.config(command=pasos_text.yview)
        scrollbar_x = ttk.Scrollbar(pasos_frame, orient="horizontal", command=pasos_text.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        pasos_text.configure(xscrollcommand=scrollbar_x.set)

        pasos_text.insert("end", "1) Cálculo del determinante\n")
        if n == 1:
            det = A[0][0]
            pasos_text.insert("end", f"|A| = {det}\n")
        elif n == 2:
            a,b = A[0]
            c,d = A[1]
            det = a*d - b*c
            pasos_text.insert("end", f"|A| = a11·a22 - a12·a21\n")
            pasos_text.insert("end", f"= ({a})·({d}) - ({b})·({c})\n")
            pasos_text.insert("end", f"= {det}\n")
        elif n == 3:
            a11,a12,a13 = A[0]
            a21,a22,a23 = A[1]
            a31,a32,a33 = A[2]
            pasos_text.insert("end", "Expansion por cofactores en la primera fila:\n")
            # Menores 2x2 y cofactores
            M11 = a22*a33 - a23*a32
            M12 = a21*a33 - a23*a31
            M13 = a21*a32 - a22*a31
            C11 = M11
            C12 = -M12
            C13 = M13
            pasos_text.insert("end", f"M11 = det([[{a22}, {a23}], [{a32}, {a33}]]) = {M11};  C11 = (+)·M11 = {C11}\n")
            pasos_text.insert("end", f"M12 = det([[{a21}, {a23}], [{a31}, {a33}]]) = {M12};  C12 = (-)·M12 = {C12}\n")
            pasos_text.insert("end", f"M13 = det([[{a21}, {a22}], [{a31}, {a32}]]) = {M13};  C13 = (+)·M13 = {C13}\n")
            det = a11*C11 + a12*C12 + a13*C13
            pasos_text.insert("end", f"|A| = a11·C11 + a12·C12 + a13·C13 = ({a11})·({C11}) + ({a12})·({C12}) + ({a13})·({C13}) = {det}\n")
        else:
            messagebox.showerror("Método adjunta", "Solo disponible para n  3.")
            return

        if det == 0:
            messagebox.showerror("Sin inversa", "La matriz no es invertible (determinante 0).")
            return

        tk.Label(right, text="Adj(A) =", font=("Segoe UI", 16, "bold"), bg=self.bg, fg="#b91c1c").pack(pady=(10, 0))
        pasos_text.insert("end", "\n2) Matriz de cofactores de A\n")

        def sign(i,j):
            return Fraction(1) if (i+j)%2==0 else Fraction(-1)

        if n == 1:
            C = [[Fraction(1)]]
            pasos_text.insert("end", "C[1,1] = (+)·det([]) = 1\n")
        elif n == 2:
            # cofactores calculados directamente desde A
            a,b = A[0]
            c,d = A[1]
            # menores de 1x1 (el valor restante)
            m11, m12, m21, m22 = d, c, b, a
            c11 = sign(0,0)*m11
            c12 = sign(0,1)*m12
            c21 = sign(1,0)*m21
            c22 = sign(1,1)*m22
            pasos_text.insert("end", f"C[1,1] = (+)·{m11} = {c11}\n")
            pasos_text.insert("end", f"C[1,2] = (-)·{m12} = {c12}\n")
            pasos_text.insert("end", f"C[2,1] = (-)·{m21} = {c21}\n")
            pasos_text.insert("end", f"C[2,2] = (+)·{m22} = {c22}\n")
            C = [[c11, c12], [c21, c22]]
        else:  # n == 3
            C = [[Fraction(0) for _ in range(3)] for _ in range(3)]
            for i in range(3):
                for j in range(3):
                    rows = [r for r in range(3) if r != i]
                    cols = [c for c in range(3) if c != j]
                    m = [
                        [A[rows[0]][cols[0]], A[rows[0]][cols[1]]],
                        [A[rows[1]][cols[0]], A[rows[1]][cols[1]]],
                    ]
                    mdet = m[0][0]*m[1][1] - m[0][1]*m[1][0]
                    s = sign(i,j)
                    C[i][j] = s*mdet
                    pasos_text.insert(
                        "end",
                        f"M[{i+1},{j+1}] = det([[{m[0][0]}, {m[0][1]}],[{m[1][0]}, {m[1][1]}]]) = {mdet}; "
                        f"C[{i+1},{j+1}] = ({'+' if s>0 else '-'})·{mdet} = {C[i][j]}\n",
                    )

        # 3) Adj(A) = (Cof(A))^t (traspuesta de la matriz de cofactores)
        pasos_text.insert("end", "\n3) Adj(A) = (Cof(A))^t (traspuesta de la matriz de cofactores)\n")
        Adj_A = [list(row) for row in zip(*C)]
        adj_frame = tk.Frame(right, bg=self.bg)
        adj_frame.pack()
        self._render_matrix(adj_frame, Adj_A)

        # sección final: A^{-1} = (1/|A|)·Adj(A)
        bottom = tk.Frame(self.result_frame, bg=self.bg)
        bottom.pack(fill="x", pady=(10, 4))
        tk.Label(bottom, text="A^{-1} = (1/|A|)·Adj(A)", font=("Segoe UI", 14, "bold"), bg=self.bg, fg="#b91c1c").pack()

        inv = [[Adj_A[i][j] / det for j in range(n)] for i in range(n)]
        self._render_matrix(self.result_frame, inv)
        pasos_text.insert("end", "\n3) Adj(A) = (Cof(A))^t\n")
        pasos_text.insert("end", f"4) Como |A| = {det}, A^{-1} = (1/{det})·Adj(A)\n")
        pasos_text.insert("end", f"\nAdj(A) = (Cof(A))^t\n")
        pasos_text.insert("end", f"A^{-1} = (1/{det})·Adj(A)\n")

    # Construye la lista de pasos (descriptores) para Gauss-Jordan
    def _gauss_jordan_steps(self, A, I, collect_only=False):
        n = self.n
        pasos = []

        def find_pivot_row(k):
            best = None
            best_abs = Fraction(0)
            for r in range(k, n):
                val = A[r][k]
                if val != 0 and abs(val) >= best_abs:
                    best = r
                    best_abs = abs(val)
            return best

        # Usamos descriptores de pasos genéricos; los valores exactos (pivote/factor)
        # se calculan al aplicar el paso, para que funcionen con animación.
        for k in range(n):
            pasos.append(("pivot", k))
            pasos.append(("scale", k))
            for i in range(n):
                if i != k:
                    pasos.append(("elim", i, k))

        if collect_only:
            # Validación mínima: intentamos simular para detectar singularidad
            Atest = [row[:] for row in A]
            Itest = [row[:] for row in I]
            ok = self._apply_steps(Atest, Itest, pasos, log_to_text=False, simulate=True)
            return ok, pasos
        return True, pasos

    # ---------------------------------------------------------
    # Formato: operación vertical tipo libro y matriz aumentada
    # ---------------------------------------------------------
    def _format_operacion_vertical_lines(self, fila_pivote, fila_actual, factor, fila_result, idx_piv, idx_obj):
        # Alinear etiquetas y celdas considerando todas las filas involucradas
        todos = fila_pivote + fila_actual + fila_result
        ancho = max((len(str(x)) for x in todos), default=1)

        def fmt_with_bar(lst):
            # Inserta una barra entre A e I y alinea cada celda
            n2 = len(lst) // 2 if len(lst) % 2 == 0 else len(lst)
            left = " ".join(str(x).rjust(ancho) for x in lst[:n2])
            right = " ".join(str(x).rjust(ancho) for x in lst[n2:])
            if right:
                return f"{left}   |   {right}"
            return left

        escala = [(-factor) * val for val in fila_pivote]
        factor_str = f"+{abs(factor)}" if factor < 0 else f"-{factor}"

        lab1 = f"{factor_str}R{idx_piv} : "
        lab2 = f"+R{idx_obj} : "
        lab3 = f"=R{idx_obj} : "
        lab_w = max(len(l) for l in (lab1, lab2, lab3))

        body1 = fmt_with_bar(escala)
        body2 = fmt_with_bar(fila_actual)
        body3 = fmt_with_bar(fila_result)
        dash = "-" * len(body3)

        lines = [
            lab1.ljust(lab_w) + body1,
            lab2.ljust(lab_w) + body2,
            " " * lab_w + dash,
            lab3.ljust(lab_w) + body3,
        ]
        return lines

    def _format_augmented_lines(self, A, I):
        # A e I son n x n
        n = len(A)
        if n == 0:
            return []
        maxw = 1
        for i in range(n):
            for v in A[i] + I[i]:
                maxw = max(maxw, len(str(v)))
        lines = []
        for i in range(n):
            left = " ".join(str(x).rjust(maxw) for x in A[i])
            right = " ".join(str(x).rjust(maxw) for x in I[i])
            lines.append(f"{left}   |   {right}")
        return lines

    def _insert_header_to_text(self, titulo, comentario=""):
        # Inserta encabezado en self.pasos_text con estilos
        self.pasos_text.insert("end", "Operación: ")
        start = self.pasos_text.index("end")
        self.pasos_text.insert("end", titulo)
        end = self.pasos_text.index("end")
        try:
            self.pasos_text.tag_add("bold", start, end)
        except Exception:
            pass
        if comentario:
            self.pasos_text.insert("end", "    ")
            c_start = self.pasos_text.index("end")
            self.pasos_text.insert("end", comentario)
            c_end = self.pasos_text.index("end")
            try:
                self.pasos_text.tag_add("comment", c_start, c_end)
            except Exception:
                pass
        self.pasos_text.insert("end", "\n\n")

    # ---------------------------------------------------------
    # Genera y muestra pasos detallados Gauss-Jordan para [A|I]
    # ---------------------------------------------------------
    def _render_detailed_gauss_jordan(self, A, I):
        n = self.n
        # copias de trabajo
        Aw = [row[:] for row in A]
        Iw = [row[:] for row in I]

        # limpiar área de pasos
        self.pasos_text.delete("1.0", "end")

        fila_pivote = 0
        columnas_pivote = []
        for col in range(n):
            # buscar pivote no nulo
            piv = None
            for r in range(fila_pivote, n):
                if Aw[r][col] != 0:
                    piv = r
                    break
            if piv is None:
                continue

            # Intercambio si es necesario
            if piv != fila_pivote:
                Aw[fila_pivote], Aw[piv] = Aw[piv], Aw[fila_pivote]
                Iw[fila_pivote], Iw[piv] = Iw[piv], Iw[fila_pivote]
                self._insert_header_to_text(
                    f"R{fila_pivote+1}  R{piv+1}",
                    f"Intercambio de filas para poner pivote  0 en columna {col+1}"
                )
                for line in self._format_augmented_lines(Aw, Iw):
                    self.pasos_text.insert("end", line + "\n")
                self.pasos_text.insert("end", "\n" + "-" * 110 + "\n\n")

            # Normalizar fila pivote
            a = Aw[fila_pivote][col]
            if a == 0:
                fila_pivote += 1
                if fila_pivote >= n:
                    break
                continue
            if a != 1:
                Aw[fila_pivote] = [val / a for val in Aw[fila_pivote]]
                Iw[fila_pivote] = [val / a for val in Iw[fila_pivote]]
                self._insert_header_to_text(
                    f"R{fila_pivote+1}  R{fila_pivote+1}/{_fmt(a)}",
                    f"Normalización: pivote 1 en columna {col+1}"
                )
                for line in self._format_augmented_lines(Aw, Iw):
                    self.pasos_text.insert("end", line + "\n")
                self.pasos_text.insert("end", "\n" + "-" * 110 + "\n\n")

            # Eliminar en otras filas
            for r in range(n):
                if r == fila_pivote:
                    continue
                f = Aw[r][col]
                if f == 0:
                    continue
                fila_orig_A = Aw[r][:]
                fila_orig_I = Iw[r][:]
                fila_piv_A = Aw[fila_pivote][:]
                fila_piv_I = Iw[fila_pivote][:]
                # resultado
                Aw[r] = [fila_orig_A[j] - f * fila_piv_A[j] for j in range(n)]
                Iw[r] = [fila_orig_I[j] - f * fila_piv_I[j] for j in range(n)]
                # formateo operación vertical sobre fila completa (A|I)
                fila_piv_full = fila_piv_A + fila_piv_I
                fila_orig_full = fila_orig_A + fila_orig_I
                fila_res_full = Aw[r] + Iw[r]
                oper_lines = self._format_operacion_vertical_lines(
                    fila_piv_full, fila_orig_full, f, fila_res_full, fila_pivote + 1, r + 1
                )
                self._insert_header_to_text(
                    f"R{r+1}  R{r+1} - ({_fmt(f)})R{fila_pivote+1}",
                    f"Anular elemento en columna {col+1} usando la fila pivote"
                )
                # ensamblar lado a lado: oper_lines (izq) y matriz (der)
                matriz_lines = self._format_augmented_lines(Aw, Iw)
                max_left = max((len(s) for s in oper_lines), default=0)
                sep = "   |   "
                max_len = max(len(oper_lines), len(matriz_lines))
                for i in range(max_len):
                    left = oper_lines[i] if i < len(oper_lines) else ""
                    right = matriz_lines[i] if i < len(matriz_lines) else ""
                    line_text = left.ljust(max_left) + (sep if right else "") + right + "\n"
                    self.pasos_text.insert("end", line_text)
                self.pasos_text.insert("end", "\n" + "-" * 110 + "\n\n")

            columnas_pivote.append(col)
            fila_pivote += 1
            if fila_pivote >= n:
                break

        # render final en las grillas superiores
        self._render_augmented(Aw, Iw)

        # Comprobación por propiedades (c), (d) y (e)
        if len(columnas_pivote) != n:
            try:
                self.pasos_text.insert("end", "Comprobacion de invertibilidad (c, d, e)\n", ("bold",))
            except Exception:
                self.pasos_text.insert("end", "Comprobacion de invertibilidad (c, d, e)\n")

            self.pasos_text.insert("end", f"- (c) No tiene n posiciones pivote: {len(columnas_pivote)} de {n}.\n")
            libres = [j for j in range(n) if j not in columnas_pivote]
            if libres:
                j0 = libres[0]
                x = [Fraction(0) for _ in range(n)]
                x[j0] = Fraction(1)
                fila = 0
                for pc in columnas_pivote:
                    x[pc] = -Aw[fila][j0]
                    fila += 1
                self.pasos_text.insert("end", "- (d) Existe solucion no trivial para Ax = 0. Ejemplo:\n")
                self.pasos_text.insert("end", "x = [ " + ", ".join(str(v) for v in x) + " ]^t\n")
                self.pasos_text.insert("end", "- (e) Por consiguiente, las columnas de A son linealmente dependientes (no LI).\n")
            else:
                self.pasos_text.insert("end", "- (d) Ax=0 solo tiene la solucion trivial; sin embargo, al no tener n pivotes (c), A no es invertible.\n")

            messagebox.showerror(
                "Sin inversa",
                "No tiene n posiciones pivote (c). Entonces Ax=0 tiene solucion no trivial (d) y las columnas de A son dependientes (e)."
            )
            return
    def _apply_steps(self, A, I, pasos, log_to_text=True, simulate=False):
        n = self.n
        for step in pasos:
            if step[0] == "pivot":
                _, k = step
                # seleccionar mejor pivote y/o intercambiar
                p = None
                best_abs = Fraction(0)
                for r in range(k, n):
                    v = A[r][k]
                    if v != 0 and abs(v) >= best_abs:
                        best_abs = abs(v)
                        p = r
                if p is None or A[p][k] == 0:
                    # singular
                    return False
                if p != k:
                    A[k], A[p] = A[p], A[k]
                    I[k], I[p] = I[p], I[k]
                    if log_to_text:
                        self.pasos_text.insert("end", f"Intercambiar R{k+1} -> R{p+1}\n")
                else:
                    if log_to_text:
                        self.pasos_text.insert("end", f"Pivote en R{k+1} ya adecuado\n")
            elif step[0] == "scale":
                _, k = step
                a = A[k][k]
                if a == 0:
                    return False
                if a != 1:
                    for j in range(n):
                        A[k][j] /= a
                        I[k][j] /= a
                    if log_to_text:
                        self.pasos_text.insert("end", f"R{k+1} := R{k+1} / {a}\n")
                else:
                    if log_to_text:
                        self.pasos_text.insert("end", f"Pivote R{k+1} ya es 1\n")
            elif step[0] == "elim":
                _, i, k = step
                if i == k:
                    continue
                f = A[i][k]
                if f != 0:
                    for j in range(n):
                        A[i][j] -= f * A[k][j]
                        I[i][j] -= f * I[k][j]
                    if log_to_text:
                        self.pasos_text.insert("end", f"R{i+1} := R{i+1} - ({_fmt(f)})*R{k+1}\n")
                else:
                    if log_to_text:
                        self.pasos_text.insert("end", f"Columna {k+1}: R{i+1} ya tiene 0\n")

            if not simulate:
                self._render_augmented(A, I)
        return True

    def _start_animation(self, A, I):
        ok, pasos = self._gauss_jordan_steps(A, I, collect_only=True)
        if not ok:
            # No animamos; explicamos inmediatamente por (c), (d) y (e)
            self.pasos_text.delete("1.0", "end")
            self._explain_failure_cde(A, self.pasos_text)
            messagebox.showerror("Sin inversa", "No tiene n posiciones pivote (c). Entonces Ax=0 tiene solucion no trivial (d) y las columnas de A son dependientes (e).")
            return
        # Copias mutables para animación
        self.A_anim = [row[:] for row in A]
        self.I_anim = [row[:] for row in I]
        self.steps = pasos
        self.step_index = 0
        # limpiar pasos
        self.pasos_text.delete("1.0", "end")
        self._render_augmented(self.A_anim, self.I_anim)
        self._animate_next()

    def _animate_next(self):
        if self.step_index >= len(self.steps):
            # Animación terminada: confirmar (c), (d) y (e) si A quedó en identidad
            try:
                n = self.n
                A = self.A_anim
                is_I = True
                for i in range(n):
                    for j in range(n):
                        if A[i][j] != (1 if i == j else 0):
                            is_I = False
                            break
                    if not is_I:
                        break
                if is_I:
                    try:
                        self.pasos_text.insert("end", "Comprobación de invertibilidad (c, d, e)\n", ("bold",))
                    except Exception:
                        self.pasos_text.insert("end", "Comprobación de invertibilidad (c, d, e)\n")
                    self.pasos_text.insert("end", f"(c) Pivotes encontrados: {n} de n = {n}  OK.\n")
                    self.pasos_text.insert("end", "(d) Ax = 0 solo tiene la solución trivial.\n")
                    self.pasos_text.insert("end", "(e) Las columnas de A forman un conjunto linealmente independiente.\n")
            finally:
                return
        # aplicar un paso
        step = [self.steps[self.step_index]]
        ok = self._apply_steps(self.A_anim, self.I_anim, step, log_to_text=True, simulate=False)
        if not ok:
            self.pasos_text.insert("end", "\nSe detecta que no hay n pivotes.\n")
            self._explain_failure_cde(self.A_anim, self.pasos_text)
            messagebox.showerror("Sin inversa", "No tiene n posiciones pivote (c). Entonces Ax=0 tiene solucion no trivial (d) y las columnas de A son dependientes (e).")
            return
        self.step_index += 1
        self.pasos_text.see("end")
        self.root.after(350, self._animate_next)

    def _volver_al_inicio(self):
        try:
            self.root.destroy()
        finally:
            try:
                if callable(self.volver_callback):
                    self.volver_callback()
            except Exception:
                pass