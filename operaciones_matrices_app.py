import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction


class OperacionesMatricesApp:
    """
    Módulo para practicar operaciones con una matriz A y vectores u, v (y w opcional).

    Permite:
    - Calcular y comparar A(u+v) con Au + Av (distributividad).
    - Calcular y comparar A(au + bv) con aAu + bAv para escalares a, b.
    - Aplicar A a un vector w personalizado.
    Las respuestas principales se resaltan dentro del cuadro de resultados.
    """

    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        self.root.title("Operaciones con matrices: A(u, v)")
        self.root.geometry("1120x820")
        self.root.configure(bg="#ffe4e6")

        self._setup_styles()
        self._build_ui()

    # ---------------- utilidades ----------------
    @staticmethod
    def _parse_fraction(s: str) -> Fraction:
        s = (s or "").strip().replace(",", ".")
        if s == "":
            return Fraction(0)
        return Fraction(s)

    @staticmethod
    def _fmt(x: Fraction) -> str:
        return f"{x.numerator}" if x.denominator == 1 else f"{x.numerator}/{x.denominator}"

    @staticmethod
    def _matmul(A, x):
        m = len(A)
        n = len(A[0]) if m else 0
        if len(x) != n:
            raise ValueError("El vector debe tener tantas entradas como columnas tiene A.")
        return [sum(A[i][j] * x[j] for j in range(n)) for i in range(m)]

    @staticmethod
    def _combine(u, v, a=1, b=1):
        if len(u) != len(v):
            raise ValueError("Los vectores u y v deben tener la misma longitud.")
        return [a * ui + b * vi for ui, vi in zip(u, v)]

    def _detalle_combinacion(self, u, v, a=1, b=1, nombre="u+v"):
        lines = []
        for idx, (ui, vi) in enumerate(zip(u, v), 1):
            parcial_u = a * ui
            parcial_v = b * vi
            total = parcial_u + parcial_v
            term_u = f"{self._fmt(a)}*{self._fmt(ui)}"
            term_v = f"{self._fmt(b)}*{self._fmt(vi)}"
            lines.append(f"{nombre}[{idx}] = {term_u} + {term_v} = {self._fmt(parcial_u)} + "
                         f"{self._fmt(parcial_v)} = {self._fmt(total)}")
        return lines

    def _detalle_mat_vec(self, A, x, nombre="A"):
        lines = []
        for i, fila in enumerate(A, 1):
            productos = [f"{self._fmt(fila[j])}*{self._fmt(x[j])}" for j in range(len(x))]
            total = sum(fila[j] * x[j] for j in range(len(x)))
            lines.append(f"{nombre}[fila {i}] = " + " + ".join(productos) + f" = {self._fmt(total)}")
        return lines

    # ---------------- estilos y UI ----------------
    def _setup_styles(self):
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

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Operaciones con matrices y vectores", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(header, text="Volver", style="Back.TButton", command=self._volver).pack(side="right")

        ttk.Label(self.root, text="Analiza expresiones como A(u+v) = Au + Av y extensiones con escalares.",
                  background="#ffe4e6", foreground="#7f1d1d").pack(pady=(0, 8))

        cfg = ttk.Frame(self.root, padding=10)
        cfg.pack(fill="x")
        ttk.Label(cfg, text="Filas (m):").grid(row=0, column=0, padx=6, sticky="e")
        ttk.Label(cfg, text="Columnas (n):").grid(row=0, column=2, padx=6, sticky="e")
        self.m_var = tk.IntVar(value=2)
        self.n_var = tk.IntVar(value=2)
        ttk.Spinbox(cfg, from_=1, to=8, textvariable=self.m_var, width=6, justify="center").grid(row=0, column=1)
        ttk.Spinbox(cfg, from_=1, to=8, textvariable=self.n_var, width=6, justify="center").grid(row=0, column=3)
        ttk.Button(cfg, text="Crear campos", style="Primary.TButton", command=self._crear_campos).grid(row=0, column=4, padx=10)
        ttk.Button(cfg, text="Cargar ejemplo de la imagen", style="Back.TButton",
                   command=self._cargar_ejemplo_imagen).grid(row=0, column=5, padx=10)

        self.campos_frame = ttk.Frame(self.root, padding=10)
        self.campos_frame.pack(fill="x")

        acciones = ttk.Frame(self.root, padding=10)
        acciones.pack(fill="x", pady=(0, 4))

        distrib = ttk.Frame(acciones)
        distrib.pack(fill="x", pady=4)
        ttk.Label(distrib, text="Distributividad:", foreground="#7f1d1d", background="#ffe4e6",
                  font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 8))
        ttk.Button(distrib, text="Calcular A(u+v) y Au + Av", style="Primary.TButton",
                   command=self._calcular_distrib).pack(side="left")

        combo = ttk.Frame(acciones)
        combo.pack(fill="x", pady=4)
        ttk.Label(combo, text="Linealidad con escalares  a·u + b·v:", background="#ffe4e6").pack(side="left", padx=(0, 6))
        ttk.Label(combo, text="a=", background="#ffe4e6").pack(side="left")
        self.a_var = tk.StringVar(value="1")
        ttk.Entry(combo, textvariable=self.a_var, width=6, justify="center").pack(side="left", padx=4)
        ttk.Label(combo, text="b=", background="#ffe4e6").pack(side="left")
        self.b_var = tk.StringVar(value="1")
        ttk.Entry(combo, textvariable=self.b_var, width=6, justify="center").pack(side="left", padx=4)
        ttk.Button(combo, text="Calcular A(au+bv) y aAu + bAv", style="Primary.TButton",
                   command=self._calcular_linealidad).pack(side="left", padx=8)

        wframe = ttk.Frame(acciones)
        wframe.pack(fill="x", pady=4)
        ttk.Label(wframe, text="Vector w opcional:", background="#ffe4e6").pack(side="left", padx=(0, 6))
        ttk.Button(wframe, text="Calcular A(w)", style="Primary.TButton", command=self._calcular_w).pack(side="left")
        ttk.Button(wframe, text="Limpiar resultados", style="Back.TButton", command=self._limpiar_resultados).pack(side="left", padx=8)

        self.resultado = tk.Text(self.root, height=20, font=("Consolas", 11), bg="#fff0f5")
        self.resultado.pack(fill="both", expand=True, padx=12, pady=8)
        self.resultado.tag_config("titulo", font=("Segoe UI", 12, "bold"), foreground="#b91c1c")
        self.resultado.tag_config("respuesta", font=("Consolas", 12, "bold"), foreground="#b91c1c",
                                  background="#fff", underline=0)
        self.resultado.config(state="disabled")

        self._crear_campos()

    def _volver(self):
        try:
            self.volver_callback()
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass

    # ---------------- creación de campos ----------------
    def _crear_campos(self):
        for w in self.campos_frame.winfo_children():
            w.destroy()
        m, n = self.m_var.get(), self.n_var.get()

        ttk.Label(self.campos_frame, text="Matriz A (m x n)").grid(row=0, column=0, padx=8, pady=4)
        self.entries_A = []
        gridA = ttk.Frame(self.campos_frame)
        gridA.grid(row=1, column=0, padx=8)
        for i in range(m):
            fila = []
            for j in range(n):
                e = ttk.Entry(gridA, width=8, justify="center")
                e.grid(row=i, column=j, padx=3, pady=3)
                fila.append(e)
            self.entries_A.append(fila)

        col_vectors = ttk.Frame(self.campos_frame)
        col_vectors.grid(row=1, column=1, padx=16)
        ttk.Label(self.campos_frame, text="Vector u").grid(row=0, column=1)
        self.entries_u = self._crear_vector_entries(col_vectors, n, col=0)
        ttk.Label(self.campos_frame, text="Vector v").grid(row=0, column=2)
        self.entries_v = self._crear_vector_entries(col_vectors, n, col=1)
        ttk.Label(self.campos_frame, text="Vector w").grid(row=0, column=3)
        self.entries_w = self._crear_vector_entries(col_vectors, n, col=2)

    def _crear_vector_entries(self, parent, n, col):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=col, padx=8)
        entries = []
        for i in range(n):
            e = ttk.Entry(frame, width=8, justify="center")
            e.grid(row=i, column=0, padx=3, pady=3)
            entries.append(e)
        return entries

    # ---------------- lectura y formato ----------------
    def _leer_matriz(self):
        m, n = self.m_var.get(), self.n_var.get()
        return [[self._parse_fraction(self.entries_A[i][j].get()) for j in range(n)] for i in range(m)]

    def _leer_vector(self, entries):
        return [self._parse_fraction(e.get()) for e in entries]

    def _format_matrix(self, A):
        if not A:
            return "[ ]"
        m = len(A); n = len(A[0])
        col_w = [0] * n
        for j in range(n):
            col_w[j] = max(len(self._fmt(A[i][j])) for i in range(m))
        lines = []
        for i in range(m):
            row = " ".join(self._fmt(A[i][j]).rjust(col_w[j]) for j in range(n))
            lines.append("[ " + row + " ]")
        return "\n".join(lines)

    def _format_vector(self, vec):
        vals = [self._fmt(v) for v in vec]
        w = max((len(s) for s in vals), default=1)
        return "\n".join("[ " + s.rjust(w) + " ]" for s in vals)

    def _write(self, text):
        self.resultado.configure(state="normal")
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert("1.0", text)
        self.resultado.configure(state="disabled")

    def _append(self, text, tag=None):
        self.resultado.configure(state="normal")
        start = self.resultado.index(tk.END)
        self.resultado.insert(tk.END, text + "\n")
        end = self.resultado.index(tk.END)
        if tag:
            self.resultado.tag_add(tag, start, end)
        self.resultado.configure(state="disabled")

    def _limpiar_resultados(self):
        self._write("")

    # ---------------- cálculos ----------------
    def _calcular_distrib(self):
        try:
            A = self._leer_matriz()
            u = self._leer_vector(self.entries_u)
            v = self._leer_vector(self.entries_v)
            u_mas_v = self._combine(u, v, 1, 1)
            Au = self._matmul(A, u)
            Av = self._matmul(A, v)
            A_u_mas_v = self._matmul(A, u_mas_v)
            Au_mas_Av = self._combine(Au, Av, 1, 1)
            iguales = Au_mas_Av == A_u_mas_v

            lines = []
            lines.append("== Distributividad: A(u+v) frente a Au + Av ==")
            lines.append("")
            lines.append("A =")
            lines.append(self._format_matrix(A))
            lines.append("u =")
            lines.append(self._format_vector(u))
            lines.append("v =")
            lines.append(self._format_vector(v))
            lines.append("")
            lines.append("Paso 1: vector u + v (entrada a entrada)")
            lines.append("u + v =")
            lines.append(self._format_vector(u_mas_v))
            lines.append("")
            lines.extend(self._detalle_combinacion(u, v, 1, 1, "u+v"))
            lines.append("")
            lines.append("Paso 2: aplicar A a (u+v) (producto fila x columna)")
            lines.append("A(u+v) =")
            lines.append(self._format_vector(A_u_mas_v))
            lines.append("")
            lines.extend(self._detalle_mat_vec(A, u_mas_v, "A(u+v)"))
            lines.append("")
            lines.append("Paso 3: calcular Au y Av por separado")
            lines.append("Au =")
            lines.append(self._format_vector(Au))
            lines.append("Av =")
            lines.append(self._format_vector(Av))
            lines.extend(self._detalle_mat_vec(A, u, "Au"))
            lines.extend(self._detalle_mat_vec(A, v, "Av"))
            lines.append("")
            lines.append("Paso 4: sumar Au + Av (entrada a entrada)")
            lines.append("Au + Av =")
            lines.append(self._format_vector(Au_mas_Av))
            lines.append("")
            lines.extend(self._detalle_combinacion(Au, Av, 1, 1, "Au+Av"))

            self._write("\n".join(lines) + "\n")
            self._append("Conclusión: A(u+v) y Au+Av " + ("COINCIDEN ✔" if iguales else "NO coinciden ✖"),
                         tag="respuesta")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo calcular la distributividad: {exc}")

    def _calcular_linealidad(self):
        try:
            A = self._leer_matriz()
            u = self._leer_vector(self.entries_u)
            v = self._leer_vector(self.entries_v)
            a = self._parse_fraction(self.a_var.get())
            b = self._parse_fraction(self.b_var.get())

            au_bv = self._combine(u, v, a, b)
            A_au_bv = self._matmul(A, au_bv)
            Au = self._matmul(A, u)
            Av = self._matmul(A, v)
            aAu_bAv = self._combine(Au, Av, a, b)
            iguales = A_au_bv == aAu_bAv

            lines = []
            lines.append("== Linealidad con escalares: A(au+bv) frente a aAu + bAv ==")
            lines.append(f"a = {self._fmt(a)},  b = {self._fmt(b)}")
            lines.append("")
            lines.append("Paso 1: combinación au + bv (entrada a entrada)")
            lines.append("au + bv =")
            lines.append(self._format_vector(au_bv))
            lines.append("")
            lines.extend(self._detalle_combinacion(u, v, a, b, "au+bv"))
            lines.append("")
            lines.append("Paso 2: aplicar A a (au+bv) (producto fila x columna)")
            lines.append("A(au+bv) =")
            lines.append(self._format_vector(A_au_bv))
            lines.append("")
            lines.extend(self._detalle_mat_vec(A, au_bv, "A(au+bv)"))
            lines.append("")
            lines.append("Paso 3: calcular Au y Av y luego combinarlos con a y b")
            lines.append("Au =")
            lines.append(self._format_vector(Au))
            lines.append("Av =")
            lines.append(self._format_vector(Av))
            lines.extend(self._detalle_mat_vec(A, u, "Au"))
            lines.extend(self._detalle_mat_vec(A, v, "Av"))
            lines.append("")
            lines.append("aAu + bAv =")
            lines.append(self._format_vector(aAu_bAv))
            lines.extend(self._detalle_combinacion(Au, Av, a, b, "aAu+bAv"))

            self._write("\n".join(lines) + "\n")
            self._append("Conclusión: A(au+bv) y aAu+bAv " + ("COINCIDEN ✔" if iguales else "NO coinciden ✖"),
                         tag="respuesta")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo calcular la combinación lineal: {exc}")

    def _calcular_w(self):
        try:
            A = self._leer_matriz()
            w = self._leer_vector(self.entries_w)
            Aw = self._matmul(A, w)
            lines = []
            lines.append("== Aplicar A a un vector w ==")
            lines.append("w =")
            lines.append(self._format_vector(w))
            lines.append("")
            lines.append("A w =")
            lines.append(self._format_vector(Aw))
            self._write("\n".join(lines) + "\n")
            self._append("Resultado A(w): " + "  ".join(self._fmt(x) for x in Aw), tag="respuesta")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo calcular A(w): {exc}")

    # ---------------- ejemplo ----------------
    def _cargar_ejemplo_imagen(self):
        self.m_var.set(2)
        self.n_var.set(2)
        self._crear_campos()
        ejemplo_A = [[2, 5], [3, 1]]
        ejemplo_u = [4, -1]
        ejemplo_v = [-3, 5]
        for i in range(2):
            for j in range(2):
                self.entries_A[i][j].insert(0, str(ejemplo_A[i][j]))
        for i, val in enumerate(ejemplo_u):
            self.entries_u[i].insert(0, str(val))
        for i, val in enumerate(ejemplo_v):
            self.entries_v[i].insert(0, str(val))
        for e in self.entries_w:
            e.delete(0, tk.END)
        self._write("Ejemplo cargado. Listo para calcular.")


# Modo directo (útil para pruebas rápidas)
if __name__ == "__main__":
    root = tk.Tk()
    app = OperacionesMatricesApp(root, root.destroy)
    root.mainloop()
