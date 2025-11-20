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


