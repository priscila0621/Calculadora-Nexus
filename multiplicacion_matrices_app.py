import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from fractions import Fraction


class MultiplicacionMatricesApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        self.root.title("Multiplicación de Matrices")
        self.root.geometry("1000x700")
        self.root.configure(bg="#ffe4e6")
        self.root.resizable(True, True)

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

        self.container = tk.Frame(self.root, bg=self.bg)
        self.container.pack(fill="both", expand=True, padx=16, pady=12)

        self.frames = {name: tk.Frame(self.container, bg=self.bg)
                       for name in ("bienvenida", "config", "ingreso", "resultados")}

        # datos
        self.num_matrices = 0
        self.dimensiones = []
        self.matrices = []
        self.scalar_used_per_matrix = []
        self.scalars_per_matrix = []
        self.current_index = 0
        self.entries_grid = None
        self.custom_op = None  # None | 'add' | 'sub'
        self.chain_scalar_use_var = None
        self.chain_scalar_val_var = None
        self.chain_scalar_frame = None
        self.chain_lock_first_matrix = False
        self._ultimo_titulo_resultado = "Resultado de la Multiplicación"

        self._crear_bienvenida()
        self._crear_configuracion()
        self._crear_ingreso()
        self._crear_resultados()
        self._mostrar_frame("bienvenida")

    # util
    def _mostrar_frame(self, name):
        for fr in self.frames.values():
            fr.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def _parse_fraction(self, s):
        s = (s or "").strip()
        if s == "":
            return Fraction(0)
        s = s.replace(",", ".")
        return Fraction(s)

    def _buscar_incompatibilidad_dimensiones(self, dims):
        """
        Retorna una tupla con informacion de la primera incompatibilidad encontrada.
        Formato: (indice_base, columnas_actual, filas_siguiente, dim_actual, dim_siguiente)
        Si no hay incompatibilidades devuelve None.
        """
        for idx in range(len(dims) - 1):
            columnas_actual = dims[idx][1]
            filas_siguiente = dims[idx + 1][0]
            if columnas_actual != filas_siguiente:
                return idx, columnas_actual, filas_siguiente, dims[idx], dims[idx + 1]
        return None

    def _matriz_coincide_dim(self, matriz, dim):
        """
        Verifica si la matriz proporcionada coincide con las dimensiones esperadas (filas x columnas).
        """
        if not matriz:
            return False
        filas, columnas = dim
        if len(matriz) != filas:
            return False
        try:
            return all(len(fila) == columnas for fila in matriz)
        except Exception:
            return False

    # Bienvenida
    def _crear_bienvenida(self):
        f = self.frames["bienvenida"]
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text="Multiplicación de Matrices", font=("Segoe UI", 26, "bold"),
                 bg=self.bg, fg="#b91c1c").pack(pady=(40, 6))
        tk.Label(f, text="Multiplicación de 2 o más matrices (A × B × …) con validación de dimensiones",
                 font=("Segoe UI", 12), bg=self.bg, fg="#7f1d1d").pack(pady=(0, 24))
        ttk.Button(f, text="Comenzar", style="Primary.TButton",
                   command=lambda: self._mostrar_frame("config")).pack(pady=10, ipadx=12, ipady=6)
        ttk.Button(f, text="Volver al inicio", style="Back.TButton",
                   command=self._volver_al_inicio).pack(side="bottom", pady=20)

    # Configuración
    def _crear_configuracion(self):
        f = self.frames["config"]
        for w in f.winfo_children():
            w.destroy()
        header = tk.Frame(f, bg=self.bg); header.pack(pady=(20, 10), fill="x")
        tk.Label(header, text="Configuración de dimensiones", font=("Segoe UI", 18, "bold"),
                 bg=self.bg, fg="#b91c1c").pack()
        mid = tk.Frame(f, bg=self.bg); mid.pack(pady=12)
        tk.Label(mid, text="¿Cuántas matrices deseas multiplicar?", bg=self.bg,
                 font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.input_num = tk.StringVar(value="2")
        tk.Entry(mid, textvariable=self.input_num, width=6, bg=self.entry_bg).grid(row=0, column=1, padx=6, pady=6)
        ttk.Button(mid, text="Generar campos", style="Primary.TButton",
                   command=self._generar_campos_dim).grid(row=0, column=2, padx=12, pady=6)
        self.frame_dims = tk.Frame(f, bg=self.bg); self.frame_dims.pack(pady=12)

        # Escalar opcional
        scalar_row = tk.Frame(f, bg=self.bg); scalar_row.pack(pady=(8, 0), fill="x")
        tk.Label(scalar_row, text="Escalar opcional (k):", bg=self.bg, font=("Segoe UI", 11)).pack(side="left", padx=(4, 6))
        self.scalar_use_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(scalar_row, text="Usar escalar", variable=self.scalar_use_var)
        chk.pack(side="left")
        self.scalar_val_var = tk.StringVar(value="1")
        self.scalar_entry = tk.Entry(scalar_row, width=10, bg=self.entry_bg, textvariable=self.scalar_val_var)
        self.scalar_entry.pack(side="left", padx=(8, 6))
        tk.Label(scalar_row, text="(si no se marca, no se aplica)", bg=self.bg, fg="#7f1d1d").pack(side="left")
        bottom = tk.Frame(f, bg=self.bg); bottom.pack(side="bottom", fill="x", pady=14)
        ttk.Button(bottom, text="Volver al inicio", style="Back.TButton",
                   command=self._volver_al_inicio).pack(side="left", padx=12)
        ttk.Button(bottom, text="Siguiente", style="Primary.TButton",
                   command=self._validar_dimensiones).pack(side="right", padx=12)

    def _generar_campos_dim(self):
        for w in self.frame_dims.winfo_children():
            w.destroy()
        try:
            n = int(self.input_num.get())
            if n < 2:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Ingrese un número entero ≥ 2.")
            return
        self.num_matrices = n
        self.dim_entries = []
        tk.Label(self.frame_dims, text="Ingrese dimensiones:", bg=self.bg, font=("Segoe UI", 12))\
            .pack(anchor="w", pady=(0, 6))
        tk.Label(
            self.frame_dims,
            text="Regla: si A es m x n y B es p x q, entonces n debe ser igual a p para poder multiplicar.",
            bg=self.bg,
            fg="#7f1d1d",
            font=("Segoe UI", 10),
            wraplength=760,
            justify="left"
        ).pack(anchor="w", pady=(0, 8))
        for i in range(n):
            rowf = tk.Frame(self.frame_dims, bg=self.bg); rowf.pack(anchor="w", pady=6)
            tk.Label(rowf, text=f"Matriz {i+1}:", bg=self.bg, width=10).pack(side="left", padx=6)
            ef = tk.Entry(rowf, width=6, bg=self.entry_bg)
            ec = tk.Entry(rowf, width=6, bg=self.entry_bg)
            ef.pack(side="left", padx=(0, 6)); tk.Label(rowf, text="x", bg=self.bg).pack(side="left"); ec.pack(side="left", padx=(6, 6))
            self.dim_entries.append((ef, ec))

    def _validar_dimensiones(self):
        try:
            dims = []
            for ef, ec in self.dim_entries:
                f = int(ef.get()); c = int(ec.get())
                if f <= 0 or c <= 0:
                    raise ValueError
                dims.append((f, c))
            incompatibilidad = self._buscar_incompatibilidad_dimensiones(dims)
            if incompatibilidad:
                idx, columnas, filas, dim_actual, dim_siguiente = incompatibilidad
                messagebox.showerror(
                    "Dimensiones incompatibles",
                    (
                        f"No se puede multiplicar Matriz {idx+1} ({dim_actual[0]}x{dim_actual[1]}) "
                        f"con Matriz {idx+2} ({dim_siguiente[0]}x{dim_siguiente[1]}).\n"
                        f"Las columnas de la primera ({columnas}) deben ser iguales "
                        f"a las filas de la segunda ({filas})."
                    ),
                )
                return
            prev_dims = getattr(self, "dimensiones", [])
            prev_matrices = getattr(self, "matrices", [])
            nuevas_matrices = []
            for idx, dim in enumerate(dims):
                if idx < len(prev_dims) and idx < len(prev_matrices):
                    matriz_existente = prev_matrices[idx]
                    if prev_dims[idx] == dim and self._matriz_coincide_dim(matriz_existente, dim):
                        nuevas_matrices.append(matriz_existente)
                        continue
                nuevas_matrices.append(None)
            self.dimensiones = dims
            self.matrices = nuevas_matrices
            # Inicializar escalares por matriz
            self.scalar_used_per_matrix = [False for _ in range(len(dims))]
            self.scalars_per_matrix = [Fraction(1) for _ in range(len(dims))]
            self.current_index = 0
            # Guardar configuración del escalar
            try:
                self.use_scalar = bool(self.scalar_use_var.get())
            except Exception:
                self.use_scalar = False
            try:
                self.scalar_k = self._parse_fraction(self.scalar_val_var.get()) if self.use_scalar else Fraction(1)
            except Exception:
                self.scalar_k = Fraction(1)
            self._mostrar_frame("ingreso")
            self._render_ingreso_actual()
        except Exception:
            messagebox.showerror("Error", "Verifica que las dimensiones sean correctas.")

    # Ingreso
    def _crear_ingreso(self):
        f = self.frames["ingreso"]
        for w in f.winfo_children():
            w.destroy()
        self.ing_header = tk.Frame(f, bg=self.bg); self.ing_header.pack(fill="x", pady=(18, 6))
        self.label_ing_title = tk.Label(self.ing_header, text="", font=("Segoe UI", 16, "bold"),
                                        bg=self.bg, fg="#b91c1c")
        self.label_ing_title.pack()
        self.chain_scalar_frame = tk.Frame(f, bg=self.bg)
        self.ing_table = tk.Frame(f, bg=self.bg); self.ing_table.pack(pady=8)
        self.ing_error = tk.Label(f, text="", fg="red", bg=self.bg); self.ing_error.pack()
        btns = tk.Frame(f, bg=self.bg); btns.pack(pady=12)
        self.btn_prev = ttk.Button(btns, text="Anterior", style="Back.TButton", command=self._ingresar_anterior)
        self.btn_prev.grid(row=0, column=0, padx=8)
        self.btn_confirm = ttk.Button(btns, text="Confirmar Matriz", style="Primary.TButton", command=self._confirmar_matriz)
        self.btn_confirm.grid(row=0, column=1, padx=8)
        ttk.Button(f, text="Volver al inicio", style="Back.TButton", command=self._volver_al_inicio)\
            .pack(side="bottom", pady=14)

    def _render_ingreso_actual(self):
        for w in self.ing_table.winfo_children():
            w.destroy()
        self.ing_error.config(text="")
        if self.custom_op in ("add", "sub"):
            self._render_chain_scalar_controls()
        elif self.chain_scalar_frame is not None:
            self.chain_scalar_frame.pack_forget()
        idx = self.current_index
        f, c = self.dimensiones[idx]
        if self.custom_op in ("add", "sub") and self.chain_lock_first_matrix and idx == 0:
            self.label_ing_title.config(text=f"Matriz resultado (solo lectura) ({f}x{c})")
        else:
            self.label_ing_title.config(text=f"Ingresa los valores de la Matriz {idx+1} ({f}x{c})")
        if hasattr(self.btn_prev, "state"):
            if idx == 0:
                self.btn_prev.state(["disabled"])
            else:
                self.btn_prev.state(["!disabled"])
        self.entries_grid = []
        grid = tk.Frame(self.ing_table, bg=self.bg); grid.pack()
        for i in range(f):
            row_entries = []
            for j in range(c):
                e = tk.Entry(grid, width=8, justify="center", font=("Segoe UI", 11), bg=self.entry_bg)
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.entries_grid.append(row_entries)
        matriz_guardada = self.matrices[idx] if idx < len(self.matrices) else None
        if self._matriz_coincide_dim(matriz_guardada, (f, c)):
            for i, fila in enumerate(self.entries_grid):
                for j, entrada in enumerate(fila):
                    entrada.delete(0, "end")
                    entrada.insert(0, str(matriz_guardada[i][j]))
                    if self.custom_op in ("add", "sub") and self.chain_lock_first_matrix and idx == 0:
                        entrada.config(state="readonly")

        # Escalar por matriz (opcional)
        row = tk.Frame(self.ing_table, bg=self.bg); row.pack(pady=(10, 0))
        self.scalar_chk_cur = tk.BooleanVar(value=self.scalar_used_per_matrix[idx] if idx < len(self.scalar_used_per_matrix) else False)
        self.scalar_val_cur = tk.StringVar(value=str(self.scalars_per_matrix[idx] if idx < len(self.scalars_per_matrix) else Fraction(1)))
        if self.custom_op in ("add", "sub"):
            letra = chr(ord("A") + idx) if idx < 26 else str(idx + 1)
            label_scalar = f"Usar escalar k{letra}"
        else:
            label_scalar = f"Usar escalar para Matriz {idx+1}"
        ttk.Checkbutton(row, text=label_scalar, variable=self.scalar_chk_cur).pack(side="left")
        tk.Entry(row, width=10, bg=self.entry_bg, textvariable=self.scalar_val_cur).pack(side="left", padx=6)

    def _ingresar_anterior(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._render_ingreso_actual()

    def _render_chain_scalar_controls(self):
        if self.chain_scalar_frame is None:
            return
        for w in self.chain_scalar_frame.winfo_children():
            w.destroy()
        self.chain_scalar_frame.pack(fill="x", pady=(0, 8))
        tk.Label(
            self.chain_scalar_frame,
            text="Aplicar escalar opcional al resultado final:",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg,
            fg="#7f1d1d",
        ).pack(anchor="w", padx=4)
        row = tk.Frame(self.chain_scalar_frame, bg=self.bg)
        row.pack(anchor="w", pady=(2, 0), padx=4)
        if self.chain_scalar_use_var is None:
            self.chain_scalar_use_var = tk.BooleanVar(value=getattr(self, "use_scalar", False))
        if self.chain_scalar_val_var is None:
            self.chain_scalar_val_var = tk.StringVar(value=str(getattr(self, "scalar_k", Fraction(1))))
        ttk.Checkbutton(row, text="Usar escalar k", variable=self.chain_scalar_use_var).pack(side="left")
        tk.Entry(row, width=10, bg=self.entry_bg, textvariable=self.chain_scalar_val_var).pack(side="left", padx=6)
        tk.Label(row, text="(se aplica tras sumar/restar)", bg=self.bg, fg="#7f1d1d").pack(side="left")

    def _actualizar_scalar_global_chain(self):
        if self.chain_scalar_use_var is None or self.chain_scalar_val_var is None:
            return True
        try:
            use_scalar = bool(self.chain_scalar_use_var.get())
        except Exception:
            use_scalar = False
        if use_scalar:
            try:
                scalar_val = self._parse_fraction(self.chain_scalar_val_var.get())
            except Exception:
                self.ing_error.config(text="Escalar global invalido.")
                return False
        else:
            scalar_val = Fraction(1)
        self.ing_error.config(text="")
        self.use_scalar = use_scalar
        self.scalar_k = scalar_val if use_scalar else Fraction(1)
        if hasattr(self, "scalar_use_var"):
            try:
                self.scalar_use_var.set(self.use_scalar)
            except Exception:
                pass
        if hasattr(self, "scalar_val_var"):
            try:
                self.scalar_val_var.set(str(self.scalar_k))
            except Exception:
                pass
        return True

    def _confirmar_matriz(self):
        try:
            f, c = self.dimensiones[self.current_index]
            mat = []
            for i in range(f):
                row = []
                for j in range(c):
                    row.append(self._parse_fraction(self.entries_grid[i][j].get()))
                mat.append(row)
            self.matrices[self.current_index] = mat
            # Guardar escalar de esta matriz
            try:
                usek = bool(self.scalar_chk_cur.get())
            except Exception:
                usek = False
            try:
                kval = self._parse_fraction(self.scalar_val_cur.get()) if usek else Fraction(1)
            except Exception:
                kval = Fraction(1)
            if self.current_index < len(self.scalar_used_per_matrix):
                self.scalar_used_per_matrix[self.current_index] = usek
                self.scalars_per_matrix[self.current_index] = kval
            if self.current_index + 1 < self.num_matrices:
                self.current_index += 1
                self._render_ingreso_actual()
            else:
                # Si venimos de suma/resta encadenada, calcular esa operación
                if self.custom_op in ("add", "sub"):
                    if not self._actualizar_scalar_global_chain():
                        return
                    self._calcular_suma_resta()
                else:
                    self._calcular_multiplicacion()
        except Exception as e:
            self.ing_error.config(text=f"Error en los datos: {e}")

    # Resultados
    def _crear_resultados(self):
        f = self.frames["resultados"]
        for w in f.winfo_children():
            w.destroy()
        self.result_container = tk.Frame(f, bg=self.bg)
        self.result_container.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(f, text="Volver al inicio", style="Back.TButton", command=self._volver_al_inicio)\
            .pack(side="bottom", pady=12)

    def _calcular_multiplicacion(self):
        try:
            dims_reales = []
            for idx, mat in enumerate(self.matrices, start=1):
                if not mat or not mat[0]:
                    messagebox.showerror("Error", f"Matriz {idx} no tiene datos suficientes.")
                    return
                dims_reales.append((len(mat), len(mat[0])))
            incompatibilidad = self._buscar_incompatibilidad_dimensiones(dims_reales)
            if incompatibilidad:
                idx_incomp, columnas, filas, dim_actual, dim_siguiente = incompatibilidad
                messagebox.showerror("Dimensiones incompatibles", (
                    f"No se puede multiplicar Matriz {idx_incomp+1} ({dim_actual[0]}x{dim_actual[1]}) "
                    f"con Matriz {idx_incomp+2} ({dim_siguiente[0]}x{dim_siguiente[1]}).\n"
                    f"Las columnas de la primera ({columnas}) deben ser iguales a las filas de la segunda ({filas})."
                ))
                return

            # Aplicar escalares por matriz antes de multiplicar
            mats_escaladas = []
            pasos_general = []
            for ix, M in enumerate(self.matrices):
                k = self.scalars_per_matrix[ix] if ix < len(self.scalars_per_matrix) else Fraction(1)
                usar = (ix < len(self.scalar_used_per_matrix) and self.scalar_used_per_matrix[ix])
                if usar:
                    filas = len(M); cols = len(M[0]) if filas else 0
                    Ms = [[Fraction(0) for _ in range(cols)] for _ in range(filas)]
                    pasos_general.append("")
                    pasos_general.append(f"Aplicando escalar k_{ix+1} = {k} a Matriz {ix+1}:")
                    for i in range(filas):
                        for j in range(cols):
                            Ms[i][j] = M[i][j] * k
                            pasos_general.append(f"a{i+1}{j+1} := {k}*{M[i][j]} = {Ms[i][j]}")
                    mats_escaladas.append(Ms)
                else:
                    mats_escaladas.append(M)
            parcial = mats_escaladas[0]
            for ix in range(1, len(self.matrices)):
                pasos_general.append("")
                pasos_general.append(f"Multiplicación {ix}: cálculo de c_ij de Matriz {ix} x Matriz {ix+1}")
                R, pasos = self._multiplicar_con_detalle(parcial, mats_escaladas[ix])
                pasos_general.extend(pasos)
                parcial = R
            # Escalar global (de la pantalla de configuración), si se activó
            if getattr(self, 'use_scalar', False) and getattr(self, 'scalar_k', Fraction(1)) != 1:
                parcial, pasos_k = self._aplicar_escalar(parcial, self.scalar_k)
                pasos_general.append("")
                pasos_general.append(f"Aplicando escalar k = {self.scalar_k} a toda la matriz resultante:")
                pasos_general.extend(pasos_k)
            self._mostrar_resultados(parcial, pasos_general)
            self._mostrar_frame("resultados")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrio un problema: {e}")

    def _multiplicar_con_detalle(self, A, B):
        fa, ca = len(A), len(A[0])
        fb, cb = len(B), len(B[0])
        if ca != fb:
            raise ValueError("Las columnas de A deben coincidir con las filas de B.")
        R = [[Fraction(0) for _ in range(cb)] for _ in range(fa)]
        pasos = []
        for i in range(fa):
            for j in range(cb):
                terms = []
                s = Fraction(0)
                for k in range(ca):
                    a = A[i][k]; b = B[k][j]
                    terms.append(f"{a}*{b}")
                    s += a * b
                R[i][j] = s
                pasos.append(f"c{i+1}{j+1} = " + " + ".join(terms) + f" = {s}")
        return R, pasos

    def _aplicar_escalar(self, M, k):
        filas = len(M); cols = len(M[0]) if filas else 0
        R = [[Fraction(0) for _ in range(cols)] for _ in range(filas)]
        pasos = []
        for i in range(filas):
            row_terms = []
            for j in range(cols):
                R[i][j] = M[i][j] * k
                row_terms.append(f"c{i+1}{j+1} = {k}*{M[i][j]} = {R[i][j]}")
            pasos.extend(row_terms)
        return R, pasos

    def _sumar_matrices(self, A, B):
        fa, ca = len(A), len(A[0])
        fb, cb = len(B), len(B[0])
        if fa != fb or ca != cb:
            raise ValueError("Para sumar, las matrices deben tener las mismas dimensiones.")
        R = [[Fraction(0) for _ in range(ca)] for _ in range(fa)]
        pasos = []
        for i in range(fa):
            for j in range(ca):
                R[i][j] = A[i][j] + B[i][j]
                pasos.append(f"c{i+1}{j+1} = {A[i][j]} + {B[i][j]} = {R[i][j]}")
        return R, pasos

    def _restar_matrices(self, A, B):
        fa, ca = len(A), len(A[0])
        fb, cb = len(B), len(B[0])
        if fa != fb or ca != cb:
            raise ValueError("Para restar, las matrices deben tener las mismas dimensiones.")
        R = [[Fraction(0) for _ in range(ca)] for _ in range(fa)]
        pasos = []
        for i in range(fa):
            for j in range(ca):
                R[i][j] = A[i][j] - B[i][j]
                pasos.append(f"c{i+1}{j+1} = {A[i][j]} - {B[i][j]} = {R[i][j]}")
        return R, pasos

    def _calcular_suma_resta(self):
        try:
            if len(self.matrices) < 2 or not self.matrices[0] or not self.matrices[1]:
                messagebox.showerror("Error", "Faltan matrices para operar.")
                return
            A = self.matrices[0]
            B = self.matrices[1]
            # aplicar escalares por matriz si marcados
            mats_escaladas = []
            pasos_general = []
            for ix, M in enumerate([A, B]):
                k = self.scalars_per_matrix[ix] if ix < len(self.scalars_per_matrix) else Fraction(1)
                usar = (ix < len(self.scalar_used_per_matrix) and self.scalar_used_per_matrix[ix])
                if usar:
                    filas = len(M); cols = len(M[0]) if filas else 0
                    Ms = [[Fraction(0) for _ in range(cols)] for _ in range(filas)]
                    pasos_general.append("")
                    if self.custom_op in ("add", "sub") and ix < 26:
                        nombre_escalar = f"k{chr(ord('A') + ix)}"
                    else:
                        nombre_escalar = f"k_{ix+1}"
                    pasos_general.append(f"Aplicando escalar {nombre_escalar} = {k} a Matriz {ix+1}:")
                    for i in range(filas):
                        for j in range(cols):
                            Ms[i][j] = M[i][j] * k
                            pasos_general.append(f"a{i+1}{j+1} := {k}*{M[i][j]} = {Ms[i][j]}")
                    mats_escaladas.append(Ms)
                else:
                    mats_escaladas.append(M)

            self.matrices = mats_escaladas
            A2, B2 = mats_escaladas[0], mats_escaladas[1]
            if self.custom_op == "add":
                titulo = "Resultado de la Suma"
                pasos_general.append("")
                pasos_general.append("Suma de matrices (A + B):")
                R, pasos = self._sumar_matrices(A2, B2)
            else:
                titulo = "Resultado de la Resta"
                pasos_general.append("")
                pasos_general.append("Resta de matrices (A - B):")
                R, pasos = self._restar_matrices(A2, B2)
            pasos_general.extend(pasos)

            # aplicar escalar global si fue configurado
            if getattr(self, 'use_scalar', False) and getattr(self, 'scalar_k', Fraction(1)) != 1:
                R, pasos_k = self._aplicar_escalar(R, self.scalar_k)
                pasos_general.append("")
                pasos_general.append(f"Aplicando escalar k = {self.scalar_k} a toda la matriz resultante:")
                pasos_general.extend(pasos_k)

            self._mostrar_resultados(R, pasos_general, titulo=titulo)
            self._mostrar_frame("resultados")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrio un problema: {e}")
        finally:
            self.custom_op = None
            self.chain_lock_first_matrix = False

    def _mostrar_resultados(self, resultado_final, pasos_general, titulo=None):
        for w in self.result_container.winfo_children():
            w.destroy()

        if titulo is None:
            titulo = "Resultado de la Multiplicaci�n"
        self._ultimo_titulo_resultado = titulo
        tk.Label(self.result_container, text=titulo,
                 font=("Segoe UI", 18, "bold"), bg=self.bg, fg="#b91c1c").pack(pady=(10, 10))

        # Mostrar matrices ingresadas y escalar si aplica
        matsf = tk.Frame(self.result_container, bg=self.bg); matsf.pack(pady=6)
        for idx, mat in enumerate(self.matrices, start=1):
            subf = tk.Frame(matsf, bg=self.bg); subf.pack(side="left", padx=12)
            tk.Label(subf, text=f"Matriz {idx}", font=("Segoe UI", 12, "bold"), bg=self.bg, fg="#7f1d1d").pack()
            grid = tk.Frame(subf, bg=self.bg); grid.pack()
            for i, row in enumerate(mat):
                for j, val in enumerate(row):
                    tk.Label(grid, text=str(val), width=8, bg=self.entry_bg, relief="solid")\
                        .grid(row=i, column=j, padx=4, pady=4)
        if getattr(self, 'use_scalar', False) and getattr(self, 'scalar_k', Fraction(1)) != 1:
            subf = tk.Frame(matsf, bg=self.bg); subf.pack(side="left", padx=12)
            tk.Label(subf, text="Escalar k", font=("Segoe UI", 12, "bold"), bg=self.bg, fg="#7f1d1d").pack()
            tk.Label(subf, text=str(self.scalar_k), font=("Segoe UI", 12), bg=self.bg, fg="#7f1d1d").pack()

        # Resultado con corchetes
        tk.Label(self.result_container, text="Matriz Resultante:",
                 font=("Segoe UI", 14, "bold"), bg=self.bg, fg="#b91c1c").pack(pady=(12, 6))
        matf = tk.Frame(self.result_container, bg=self.bg); matf.pack()
        rows = len(resultado_final); cols = len(resultado_final[0]) if rows else 0
        for i, row in enumerate(resultado_final):
            if i == 0:
                left, right = "⎡", "⎤"
            elif i == rows - 1:
                left, right = "⎣", "⎦"
            else:
                left, right = "⎢", "⎥"
            tk.Label(matf, text=left, font=("Consolas", 16), bg=self.bg).grid(row=i, column=0, padx=(2, 4))
            for j, val in enumerate(row):
                tk.Label(
                    matf,
                    text=str(val),
                    width=10,
                    bg="white",
                    fg="#000",
                    relief="solid",
                    font=("Segoe UI", 14, "bold"),
                ).grid(row=i, column=j+1, padx=6, pady=6)
            tk.Label(matf, text=right, font=("Consolas", 16), bg=self.bg).grid(row=i, column=cols+1, padx=(4, 2))

        # Encadenar nueva multiplicación: usar resultado como A
        def usar_resultado():
            p = simpledialog.askinteger("Nueva matriz B", "Número de columnas de B (p):",
                                        initialvalue=cols, minvalue=1, parent=self.root)
            if not p:
                return
            self.num_matrices = 2
            self.dimensiones = [(rows, cols), (cols, p)]
            self.matrices = [resultado_final, None]
            self.current_index = 1
            self.custom_op = None
            self._mostrar_frame("ingreso")
            self._render_ingreso_actual()

        ttk.Button(self.result_container, text="Usar resultado como A",
                   style="Primary.TButton", command=usar_resultado).pack(pady=(8, 0))

        # Encadenar suma/resta con otra matriz (mismas dimensiones)
        def sumar_resultado():
            self.num_matrices = 2
            self.dimensiones = [(rows, cols), (rows, cols)]
            self.matrices = [resultado_final, None]
            self.current_index = 0
            self.custom_op = "add"
            self.scalar_used_per_matrix = [False, False]
            self.scalars_per_matrix = [Fraction(1), Fraction(1)]
            self.chain_scalar_use_var = None
            self.chain_scalar_val_var = None
            self.chain_lock_first_matrix = True
            self._mostrar_frame("ingreso")
            self._render_ingreso_actual()

        def restar_resultado():
            self.num_matrices = 2
            self.dimensiones = [(rows, cols), (rows, cols)]
            self.matrices = [resultado_final, None]
            self.current_index = 0
            self.custom_op = "sub"
            self.scalar_used_per_matrix = [False, False]
            self.scalars_per_matrix = [Fraction(1), Fraction(1)]
            self.chain_scalar_use_var = None
            self.chain_scalar_val_var = None
            self.chain_lock_first_matrix = True
            self._mostrar_frame("ingreso")
            self._render_ingreso_actual()

        chain = tk.Frame(self.result_container, bg=self.bg)
        chain.pack(pady=(6, 8))
        ttk.Button(chain, text="Sumar resultado con otra matriz", style="Primary.TButton",
                   command=sumar_resultado).pack(side="left", padx=6)
        ttk.Button(chain, text="Restar otra matriz al resultado", style="Primary.TButton",
                   command=restar_resultado).pack(side="left", padx=6)

        # Procedimiento
        tk.Label(self.result_container, text="Procedimiento paso a paso:",
                 font=("Segoe UI", 13, "bold"), bg=self.bg, fg="#7f1d1d").pack(anchor="w", pady=(10, 4))
        proc = tk.Frame(self.result_container, bg=self.bg); proc.pack(fill="both", expand=True)
        text = tk.Text(proc, wrap="word", height=12, bg="#fff0f5", font=("Consolas", 12))
        text.pack(fill="both", expand=True)
        text.insert("1.0", "\n".join(pasos_general))
        text.config(state="disabled")

    def _volver_al_inicio(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        try:
            if self.volver_callback:
                self.volver_callback()
        except Exception:
            pass
