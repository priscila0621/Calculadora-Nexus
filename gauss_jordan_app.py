import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction
from copy import deepcopy



class GaussJordanApp:
    def __init__(self, root, volver_callback):
        # Callback para regresar al inicio
        self.volver_callback = volver_callback

        # ConfiguraciÃ³n de la ventana principal
        self.root = root
        self.root.title("MÃ©todo de EliminaciÃ³n de Gauss-Jordan")
        self.root.geometry("1250x900")
        self.root.configure(bg="#ffe4e6")  # Fondo rosita pastel

        # ConfiguraciÃ³n de estilos y widgets iniciales
        self._setup_styles()
        self._setup_widgets()

        # Variables internas
        self.pasos_guardados = []
        self.matriz_original = None
        self.matriz_final = None
        self.soluciones = None
        self.detalle_button = None
        self.mostrando_detalles = False

        # El botÃ³n "Volver" se crearÃ¡ dentro de frame_top (ahora junto al limpiar)
        self.boton_volver = None

    # ---------------------------------------------------------
    # ConfiguraciÃ³n de estilos visuales
    # ---------------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", font=("Segoe UI", 12), background="#ffe4e6", foreground="#b91c1c")
        style.configure("TEntry", font=("Segoe UI", 12))
        style.configure("Primary.TButton", font=("Segoe UI", 12, "bold"), padding=8,
                        background="#fbb6ce", foreground="#fff")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])

        # Estilo original para botones de volver (se mantiene para MenuMatrices)
        style.configure("Back.TButton", font=("Segoe UI", 12, "bold"), padding=8,
                        background="#fecaca", foreground="#b91c1c")
        style.map("Back.TButton",
                  background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])

    # ---------------------------------------------------------
    # CreaciÃ³n de los elementos grÃ¡ficos principales
    # ---------------------------------------------------------
    def _setup_widgets(self):
        frame_top = ttk.Frame(self.root, padding=20, style="TFrame")
        frame_top.pack(fill="x", pady=10)

        # Entrada para nÃºmero de ecuaciones (Spinbox)
        ttk.Label(frame_top, text="NÃºmero de ecuaciones:").grid(row=0, column=0, padx=8, pady=5, sticky="e")
        self.ecuaciones_var = tk.IntVar(value=2)
        tk.Spinbox(frame_top, from_=1, to=20, textvariable=self.ecuaciones_var, width=6, font=("Segoe UI", 12),
                   justify="center").grid(row=0, column=1, padx=8, pady=5)

        # Entrada para nÃºmero de incÃ³gnitas (Spinbox)
        ttk.Label(frame_top, text="NÃºmero de incÃ³gnitas:").grid(row=0, column=2, padx=8, pady=5, sticky="e")
        self.incognitas_var = tk.IntVar(value=2)
        tk.Spinbox(frame_top, from_=1, to=20, textvariable=self.incognitas_var, width=6, font=("Segoe UI", 12),
                   justify="center").grid(row=0, column=3, padx=8, pady=5)

        # BotÃ³n para crear la matriz
        ttk.Button(frame_top, text="Crear matriz", style="Primary.TButton", command=self.crear_matriz).grid(
            row=0, column=4, padx=10)

        # BotÃ³n para limpiar pantalla
        ttk.Button(frame_top, text="Limpiar pantalla", style="Primary.TButton", command=self.limpiar_pantalla).grid(
            row=0, column=5, padx=10)

        # BotÃ³n volver al inicio al lado del de limpiar
        self.boton_volver = ttk.Button(frame_top, text="Volver al inicio",
                                       style="Primary.TButton", command=self.volver_callback)
        self.boton_volver.grid(row=0, column=6, padx=10)

        # BotÃ³n para verificar independencia de columnas
        ttk.Button(frame_top, text="Verificar independencia",
                   style="Primary.TButton", command=self.verificar_independencia_columnas).grid(
            row=0, column=7, padx=10)

        # Contenedor de la matriz
        self.frame_matriz = ttk.Frame(self.root, padding=20)
        self.frame_matriz.pack()

        # Ãrea de resultados
        frame_result = ttk.LabelFrame(self.root, text="Resultados", padding=15, labelanchor="n")
        frame_result.pack(fill="both", expand=True, padx=15, pady=15)

        self.text_result = tk.Text(frame_result, height=35, wrap="none",
                                   font=("Consolas", 11), bg="#fff0f5", fg="#222",
                                   relief="solid", borderwidth=1)
        self.text_result.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(frame_result, orient="vertical", command=self.text_result.yview)
        scroll_y.pack(side="right", fill="y")
        self.text_result.configure(yscrollcommand=scroll_y.set, state="disabled")

        self.text_result.tag_configure("bold", font=("Consolas", 12, "bold"))
        self.text_result.tag_configure("comment", font=("Consolas", 10, "italic"), foreground="#555")

        # Eliminar botÃ³n "Verificar independencia" (ya no se requiere)
        try:
            for child in frame_top.winfo_children():
                try:
                    if isinstance(child, ttk.Button) and child.cget("text") == "Verificar independencia":
                        child.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    # ---------------------------------------------------------
    # Crear la matriz en pantalla
    # ---------------------------------------------------------
    def crear_matriz(self):
        for w in self.frame_matriz.winfo_children():
            w.destroy()

        filas = self.ecuaciones_var.get()
        columnas = self.incognitas_var.get()
        if filas <= 0 or columnas <= 0:
            messagebox.showerror("Error", "Ingrese dimensiones mayores que 0.")
            return

        self.filas = filas
        self.columnas = columnas + 1  # Ãºltima columna = tÃ©rminos independientes
        self.entries = []

        # Encabezados x1, x2, x3...
        for j in range(columnas):
            ttk.Label(self.frame_matriz, text=f"x{j + 1}", font=("Segoe UI", 12, "bold"), background="#ffe4e6",
                      foreground="#b91c1c").grid(row=0, column=j, padx=6, pady=6)
        ttk.Label(self.frame_matriz, text="b", font=("Segoe UI", 12, "bold"), background="#ffe4e6",
                  foreground="#b91c1c").grid(row=0, column=columnas, padx=6, pady=6)

        # Entradas de la matriz
        for i in range(filas):
            fila_entries = []
            for j in range(self.columnas):
                e = ttk.Entry(self.frame_matriz, width=8, justify="center")
                e.grid(row=i + 1, column=j, padx=6, pady=6)
                try:
                    e.bind("<KeyRelease>", lambda _ev=None: self._preview_sistema())
                except Exception:
                    pass
                fila_entries.append(e)
            self.entries.append(fila_entries)

        # BotÃ³n "Resolver"
        ttk.Button(self.frame_matriz, text="Resolver", style="Primary.TButton", command=self.resolver).grid(
            row=self.filas + 1, columnspan=self.columnas, pady=20)

        # Si existen detalles previos, limpiarlos
        if self.detalle_button:
            self.detalle_button.destroy()
            self.detalle_button = None
            self.mostrando_detalles = False

        # Vista previa inicial
        self._preview_sistema()

    # ---------------------------------------------------------
    # Nuevo: limpiar pantalla
    # ---------------------------------------------------------
    def limpiar_pantalla(self):
        # Limpia la matriz
        for w in self.frame_matriz.winfo_children():
            w.destroy()

        # Limpia resultados
        self.text_result.configure(state="normal")
        self.text_result.delete("1.0", tk.END)
        self.text_result.configure(state="disabled")

        # Limpia variables
        self.pasos_guardados = []
        self.matriz_original = None
        self.matriz_final = None
        self.soluciones = None
        self.detalle_button = None
        self.mostrando_detalles = False
        self.entries = []

    # ---------------------------------------------------------
    # Convertir datos y aplicar Gauss-Jordan
    # ---------------------------------------------------------
    def resolver(self):
        try:
            matriz_original = []
            for i in range(self.filas):
                fila = []
                for j in range(self.columnas):
                    val_str = self.entries[i][j].get().strip()
                    if val_str == "":
                        val_str = "0"
                    fila.append(Fraction(val_str))
                matriz_original.append(fila)

            self.matriz_original = deepcopy(matriz_original)
            A = deepcopy(matriz_original)
            pasos = self.gauss_jordan(A, self.filas, self.columnas)
            self.pasos_guardados = pasos
            self.matriz_final = A

            self.soluciones, _ = self._extraer_soluciones(A)
            self.mostrar_resumen()

            if self.detalle_button:
                self.detalle_button.destroy()
            self.mostrando_detalles = False

            # BotÃ³n de pasos detallados
            self.detalle_button = ttk.Button(self.frame_matriz, text="Ver pasos detallados",
                                            style="Primary.TButton", command=self.toggle_detalles)
            self.detalle_button.grid(row=self.filas + 2, columnspan=self.columnas, pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"OcurriÃ³ un error: {e}")

    # ---------------------------------------------------------
    # Extraer soluciones de la matriz reducida
    # ---------------------------------------------------------
    def _extraer_soluciones(self, A):
        n, m = self.filas, self.columnas
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
                    if A[i][-1] != 0:   # Solo agregar el tÃ©rmino independiente si no es 0
                        partes.append(str(A[i][-1]))
                    for j in libres:
                        coef = -A[i][j]
                        if coef != 0:
                            partes.append(f"({coef})*x{j+1}")
                    # Unir las partes con " + ", sin que empiece con 0 +
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
    # Mostrar resumen final (con forma vectorial extra)
    # ---------------------------------------------------------
    def mostrar_resumen(self):
        self.text_result.configure(state="normal")
        self.text_result.delete("1.0", tk.END)

        self.text_result.insert(tk.END, "===== SOLUCI\u00D3N FINAL =====\n\n", ("bold",))
        if self.matriz_final is None:
            self.text_result.insert(tk.END, "(no hay soluciones calculadas)\n")
            self.text_result.configure(state="disabled")
            return

        soluciones, tipo = self._extraer_soluciones(self.matriz_final)

        # Mostrar el sistema de ecuaciones formado (a partir de la matriz original)
        if self.matriz_original:
            try:
                self.text_result.insert(tk.END, "Sistema de ecuaciones ingresado:\n", ("bold",))
                for ln in self._formatear_sistema_ecuaciones(self.matriz_original):
                    self.text_result.insert(tk.END, ln + "\n")
                self.text_result.insert(tk.END, "\n")
            except Exception:
                pass

        if tipo == "incompatible":
            self.text_result.insert(tk.END, "El sistema es inconsistente: aparece una fila del tipo 0 = b con bâ‰ 0\n")
        elif tipo == "determinado":
            self.text_result.insert(tk.END, "El sistema tiene soluciÃ³n Ãºnica:\n\n")
            for i, val in enumerate(soluciones):
                self.text_result.insert(tk.END, f"x{i+1} = {val}\n")
        elif tipo == "indeterminado":
            self.text_result.insert(tk.END, "El sistema tiene infinitas soluciones:\n\n")
            # SoluciÃ³n en forma normal
            for i, val in enumerate(soluciones):
                self.text_result.insert(tk.END, f"x{i+1} = {val}\n")

            # --- Forma vectorial tipo libro de texto ---
            self.text_result.insert(tk.END, "\nConjunto soluciÃ³n:\n\n")
            num_vars = self.columnas - 1
            libres = []
            for i, val in enumerate(soluciones):
                if isinstance(val, str) and "variable libre" in val:
                    libres.append(i)

            # Determinar si el sistema es homogÃ©neo (todos los tÃ©rminos independientes son 0)
            es_homogeneo = all(self.matriz_original[i][-1] == 0 for i in range(self.filas))

            # Vector particular (todas libres en 0)
            particular = []
            for i in range(num_vars):
                if isinstance(soluciones[i], str) and "variable libre" in soluciones[i]:
                    particular.append("0")
                else:
                    expr = str(soluciones[i])
                    for l in libres:
                        expr = expr.replace(f"x{l+1}", "0")
                    try:
                        val = eval(expr)
                    except Exception:
                        val = expr
                    particular.append(str(val))

            # Vectores columna para cada variable libre
            vectores_libres = []
            for l in libres:
                vector = []
                for i in range(num_vars):
                    if i == l:
                        vector.append("1")
                    else:
                        expr = str(soluciones[i])
                        if f"x{l+1}" in expr:
                            import re
                            match = re.search(rf"\(([^)]+)\)\*x{l+1}", expr)
                            if match:
                                coef = match.group(1)
                            else:
                                match = re.search(rf"([-\d/]+)\*x{l+1}", expr)
                                coef = match.group(1) if match else "-1"
                            vector.append(coef)
                        else:
                            vector.append("0")
                vectores_libres.append(vector)

            # Imprimir en formato columna tipo libro de texto, con corchetes alineados
            def vector_columna_str(vector, ancho=6):
                # Calcula el ancho mÃ¡ximo para alinear los nÃºmeros
                maxlen = max(len(str(x)) for x in vector)
                lines = []
                for i, val in enumerate(vector):
                    valstr = str(val).rjust(maxlen)
                    if i == 0:
                        lines.append(f"\u23A1 {valstr} \u23A4")  # âŽ¡ âŽ¤
                    elif i == len(vector) - 1:
                        lines.append(f"\u23A3 {valstr} \u23A6")  # âŽ£ âŽ¦
                    else:
                        lines.append(f"\u23A2 {valstr} \u23A5")  # âŽ¢ âŽ¥
                return lines

            # Imprimir en formato columna tipo libro de texto, con corchetes alineados y x = centrado
            def imprimir_vectores_con_x_igual(lines):
                x_eq = "x ="
                # Buscar la posiciÃ³n del primer corchete de bloque
                primer_vector_inicio = lines[0].find("\u23A1")
                if primer_vector_inicio < 0:
                    primer_vector_inicio = 0
                x_eq_pos = primer_vector_inicio - len(x_eq) - 1
                if x_eq_pos < 0:
                    x_eq_pos = 0
                for i, l in enumerate(lines):
                    if i == 0:
                        self.text_result.insert(tk.END, " " * x_eq_pos + x_eq + " " + l + "\n")
                    else:
                        self.text_result.insert(tk.END, " " * (x_eq_pos + len(x_eq) + 1) + l + "\n")

            if not es_homogeneo:
                # --- Imprimir vector particular y libres alineados ---
                nombres = [" " * 2] + [f"x{libres[idx]+1}" for idx in range(len(libres))]
                vectores = [particular] + [vectores_libres[idx] for idx in range(len(libres))]
                lines = self.vectores_columna_lado_a_lado(vectores, nombres, espacio_entre_vectores=4)
                imprimir_vectores_con_x_igual(lines)
                self.text_result.insert(
                    tk.END,
                    "\nDonde " + ", ".join([f"x{l+1}" for l in libres]) + " \u2208 \u211D (parÃ¡metros libres).\n"
                )
            else:
                # Solo combinaciÃ³n lineal si es homogÃ©neo
                nombres = [f"x{libres[idx]+1}" for idx in range(len(libres))]
                vectores = [vectores_libres[idx] for idx in range(len(libres))]
                lines = self.vectores_columna_lado_a_lado(vectores, nombres, espacio_entre_vectores=4)
                imprimir_vectores_con_x_igual(lines)
                self.text_result.insert(
                    tk.END,
                    "\nDonde " + ", ".join([f"x{l+1}" for l in libres]) + " \u2208 \u211D (parÃ¡metros libres).\n"
                )

        self.text_result.configure(state="disabled")

    # ---------------------------------------------------------
    # Alternar entre resumen y pasos
    # ---------------------------------------------------------
    def toggle_detalles(self):
        if self.mostrando_detalles:
            self.mostrar_resumen()
            if self.detalle_button:
                self.detalle_button.config(text="Ver pasos detallados")
            self.mostrando_detalles = False
        else:
            self.mostrar_detalles()
            if self.detalle_button:
                self.detalle_button.config(text="Ocultar pasos detallados")
            self.mostrando_detalles = True

    # ---------------------------------------------------------
    # Mostrar pasos del mÃ©todo
    # ---------------------------------------------------------
    def mostrar_detalles(self):
        self.text_result.configure(state="normal")
        self.text_result.delete("1.0", tk.END)

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
                self.text_result.insert(tk.END, line_text)
            self.text_result.insert(tk.END, "\n" + "-" * 110 + "\n\n")

        self.text_result.insert(tk.END, "===== SOLUCI\u00D3N FINAL =====\n", ("bold",))
        soluciones, tipo = self._extraer_soluciones(self.matriz_final)
        for i, val in enumerate(soluciones):
            self.text_result.insert(tk.END, f"x{i+1} = {val}\n")
        self.text_result.configure(state="disabled")

    # ---------------------------------------------------------
    # Inserta un encabezado en el Ã¡rea de resultados
    # ---------------------------------------------------------
    def _insert_header(self, titulo, comentario=""):
        self.text_result.insert(tk.END, "OperaciÃ³n: ")
        start = self.text_result.index(tk.END)
        self.text_result.insert(tk.END, titulo)
        end = self.text_result.index(tk.END)
        self.text_result.tag_add("bold", start, end)
        if comentario:
            self.text_result.insert(tk.END, "  \u2014  ")
            c_start = self.text_result.index(tk.END)
            self.text_result.insert(tk.END, comentario)
            c_end = self.text_result.index(tk.END)
            self.text_result.tag_add("comment", c_start, c_end)
        self.text_result.insert(tk.END, "\n\n")

    # ---------------------------------------------------------
    # Algoritmo Gauss-Jordan
    # ---------------------------------------------------------
    def gauss_jordan(self, A, n, m):
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
                    "comentario": f"Intercambio de filas para poner un pivote no nulo en la columna {col+1}",
                    "oper_lines": [],
                    "matriz_lines": self.format_matriz_lines(A)
                })

            divisor = A[fila_pivote][col]
            if divisor == 0:
                fila_pivote += 1
                continue
            if divisor != 1:
                A[fila_pivote] = [val / divisor for val in A[fila_pivote]]
                pasos.append({
                    "titulo": f"F{fila_pivote+1} \u2192 F{fila_pivote+1}/{divisor}",
                    "comentario": f"NormalizaciÃ³n: se convierte en pivote a 1 en la columna {col+1}",
                    "oper_lines": [],
                    "matriz_lines": self.format_matriz_lines(A)
                })

            for f in range(n):
                if f != fila_pivote and A[f][col] != 0:
                    factor = A[f][col]
                    original_fila = A[f][:]
                    A[f] = [original_fila[j] - factor * A[fila_pivote][j] for j in range(m)]
                    oper_lines = self.format_operacion_vertical_lines(
                        A[fila_pivote], original_fila, factor, A[f], fila_pivote + 1, f + 1
                    )
                    pasos.append({
                        "titulo": f"F{f+1} \u2192 F{f+1} - ({factor})F{fila_pivote+1}",
                        "comentario": f"Se anula el elemento en la columna {col+1} usando la fila pivote",
                        "oper_lines": oper_lines,
                        "matriz_lines": self.format_matriz_lines(A)
                    })
            fila_pivote += 1
            if fila_pivote >= n:
                break
        return pasos

    # ---------------------------------------------------------
    # Funciones auxiliares
    # ---------------------------------------------------------
    def format_operacion_vertical_lines(self, fila_pivote, fila_actual, factor, fila_result, idx_piv, idx_obj):
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

    def format_matriz_lines(self, A):
        ancho = max((len(str(x)) for fila in A for x in fila), default=1)
        lines = []
        for fila in A:
            line = " ".join(str(x).rjust(ancho) for x in fila)
            lines.append(line)
        return lines

    # ---------------------------------------------------------
    # Construir representacion del sistema A|b como ecuaciones
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Vista previa del sistema mientras se ingresa la matriz
    # ---------------------------------------------------------
    def _preview_sistema(self):
        if getattr(self, "matriz_final", None) is not None:
            return
        try:
            if not getattr(self, "entries", None):
                # No hay cuadrícula: limpia el panel sin texto
                self.text_result.configure(state="normal")
                self.text_result.delete("1.0", tk.END)
                self.text_result.configure(state="disabled")
                return
            A_aug = []
            for i in range(getattr(self, "filas", 0)):
                fila = []
                for j in range(getattr(self, "columnas", 0)):
                    val_str = self.entries[i][j].get().strip() if self.entries and i < len(self.entries) and j < len(self.entries[i]) else "0"
                    if val_str == "":
                        val_str = "0"
                    fila.append(Fraction(val_str))
                A_aug.append(fila)
            lines = self._formatear_sistema_ecuaciones(A_aug)
        except Exception:
            lines = []
        try:
            self.text_result.configure(state="normal")
            self.text_result.delete("1.0", tk.END)
            if lines:
                self.text_result.insert(tk.END, "Sistema de ecuaciones ingresado:\n", ("bold",))
                for ln in lines:
                    self.text_result.insert(tk.END, ln + "\n")
            self.text_result.configure(state="disabled")
        except Exception:
            pass

    # ---------------------------------------------------------
    # Imprime varios vectores columna alineados y sumados
    # ---------------------------------------------------------
    def vectores_columna_lado_a_lado(self, vectores, nombres, espacio_entre_vectores=4):
        n = len(vectores[0])
        m = len(vectores)
        # Encabezados: x3, + x4, + x5, ...
        encabezados = [nombres[0]] + [f"+ {nombres[idx]}" for idx in range(1, m)]
        max_encabezado = max(len(e) for e in encabezados)
        max_num_len = max(len(str(v[fila])) for v in vectores for fila in range(n))
        bloque_ancho = max_encabezado + 3 + max_num_len + 2  # espacios y corchetes

        sep = " " * espacio_entre_vectores

        lines = []
        for fila in range(n):
            line = ""
            for idx, v in enumerate(vectores):
                valstr = str(v[fila]).rjust(max_num_len)
                # Corchetes segÃºn la fila
                if fila == 0:
                    corchete_izq = "\u23A1"  # âŽ¡
                    corchete_der = "\u23A4"  # âŽ¤
                elif fila == n - 1:
                    corchete_izq = "\u23A3"  # âŽ£
                    corchete_der = "\u23A6"  # âŽ¦
                else:
                    corchete_izq = "\u23A2"  # âŽ¢
                    corchete_der = "\u23A5"  # âŽ¥
                # Encabezado solo en la primera fila
                if fila == 0:
                    encabezado = encabezados[idx].rjust(max_encabezado)
                    bloque = f"{encabezado} {corchete_izq} {valstr} {corchete_der}"
                else:
                    bloque = " " * max_encabezado + f" {corchete_izq} {valstr} {corchete_der}"
                bloque = bloque.ljust(bloque_ancho)
                if idx < m - 1:
                    bloque += sep
                line += bloque
            lines.append(line.rstrip())
        return lines

    # ---------------------------------------------------------
    # Verificar independencia de columnas
    # ---------------------------------------------------------
# verificar_independencia_columnas removido a petición del usuario

    def verificar_independencia_columnas(self):
        """Método retirado. Stub de compatibilidad."""
        pass
