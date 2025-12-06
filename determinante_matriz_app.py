import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction
import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction
from typing import List, Tuple


_SUBSCRIPT_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _fmt(value: Fraction) -> str:
    # Formato ASCII para evitar símbolos raros en distintas codificaciones
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def _fmt_ascii(value: Fraction) -> str:
    """Formato simple ASCII para mostrar números en los procedimientos (sin caracteres unicode)."""
    if isinstance(value, Fraction):
        if value.denominator == 1:
            text = str(value.numerator)
        else:
            text = f"{value.numerator}/{value.denominator}"
    else:
        text = str(value)
    return text  # usa '-' normal si es negativo


def _sub(num: int) -> str:
    return str(num).translate(_SUBSCRIPT_MAP)


def _label(prefix: str, row: int, col: int) -> str:
    return f"{prefix}{_sub(row)}{_sub(col)}"


def _sign_factor_text(value: Fraction) -> str:
    return f"(+{_fmt(value)})" if value >= 0 else f"({_fmt(value)})"


def _fmt_factor(value: Fraction) -> str:
    return _fmt(value) if value >= 0 else f"({_fmt(value)})"


def _matrix_lines(matrix: List[List[Fraction]], indent: str = "") -> List[str]:
    lines = []
    for row in matrix:
        line = indent + "[ " + "  ".join(_fmt(col) for col in row) + " ]"
        lines.append(line)
    return lines


def _is_upper_triangular(matrix: List[List[Fraction]]) -> bool:
    n = len(matrix)
    for i in range(1, n):
        for j in range(0, i):
            if matrix[i][j] != 0:
                return False
    return True


def _is_lower_triangular(matrix: List[List[Fraction]]) -> bool:
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] != 0:
                return False
    return True


def _minor(matrix: List[List[Fraction]], row: int, col: int) -> List[List[Fraction]]:
    return [
        [matrix[i][j] for j in range(len(matrix)) if j != col]
        for i in range(len(matrix))
        if i != row
    ]


def determinante_con_pasos(matrix: List[List[Fraction]], level: int = 0, matrix_name: str = "A") -> Tuple[Fraction, List[str]]:
    n = len(matrix)
    indent = "    " * level
    steps: List[str] = []
    separator = indent + ("—" * 70)
    det_label = f"det({matrix_name})"

    if n == 1:
        value = matrix[0][0]
        steps.append(f"{indent}Caso base 1x1: {det_label} = {_fmt(value)}")
        return value, steps

    if n == 2:
        a11, a12 = matrix[0]
        a21, a22 = matrix[1]
        prod1 = a11 * a22
        prod2 = a12 * a21
        det = prod1 - prod2
        steps.append(f"{indent}Caso base 2x2:")
        steps.extend(_matrix_lines(matrix, indent + "    "))
        steps.append(
            f"{indent}{det_label} = ({_fmt(a11)} · {_fmt(a22)}) − ({_fmt(a12)} · {_fmt(a21)}) = {_fmt(prod1)} − {_fmt(prod2)} = {_fmt(det)}"
        )
        return det, steps

    es_superior = _is_upper_triangular(matrix)
    es_inferior = _is_lower_triangular(matrix)
    if es_superior or es_inferior:
        tipo = "superior" if es_superior else "inferior"
        diag = [matrix[i][i] for i in range(n)]
        det = Fraction(1)
        for value in diag:
            det *= value
        diag_product = " · ".join(_fmt(value) for value in diag)
        steps.append(f"{indent}La matriz {matrix_name} es triangular {tipo}.")
        steps.append(f"{indent}Producto de la diagonal principal: {diag_product} = {_fmt(det)}")
        return det, steps

    steps.append(f"{indent}Expansion por cofactores a lo largo de la primera fila")
    formula = " + ".join(f"{_label('a', 1, j + 1)}{_label('C', 1, j + 1)}" for j in range(n))
    steps.append(f"{indent}{det_label} = {formula}")

    contributions: List[Fraction] = []
    summary_values: List[Fraction] = []
    for j in range(n):
        elemento = matrix[0][j]
        idx_label = _label("a", 1, j + 1)
        sign_factor = Fraction(1 if j % 2 == 0 else -1)
        sign_symbol = "+" if sign_factor >= 0 else "−"

        steps.append(separator)
        steps.append(f"{indent}Elemento {idx_label} = {_fmt(elemento)} (signo {sign_symbol})")
        if elemento == 0:
            steps.append(f"{indent}Como {idx_label} = 0, su contribucion es nula y se omite.")
            contributions.append(Fraction(0))
            summary_values.append(Fraction(0))
            continue

        cofactor_label = _label("C", 1, j + 1)
        minor_label = _label("M", 1, j + 1)
        steps.append(f"{indent}Cofactor: {cofactor_label} = (−1)^(1+{j+1}) · det({minor_label})")

        submatriz = _minor(matrix, 0, j)
        steps.append(f"{indent}Submatriz {minor_label} (eliminando fila 1 y columna {j+1}):")
        steps.extend(_matrix_lines(submatriz, indent + "    "))

        sub_det, sub_steps = determinante_con_pasos(submatriz, level + 1, minor_label)
        steps.extend(sub_steps)
        steps.append(f"{indent}det({minor_label}) = {_fmt(sub_det)}")

        cofactor_value = sign_factor * sub_det
        steps.append(
            f"{indent}{cofactor_label} = {_sign_factor_text(sign_factor)} · {_fmt_factor(sub_det)} = {_fmt(cofactor_value)}"
        )

        contribucion = elemento * cofactor_value
        steps.append(
            f"{indent}Contribucion parcial: {_fmt_factor(elemento)} · {_fmt_factor(cofactor_value)} = {_fmt(contribucion)}"
        )
        contributions.append(contribucion)
        summary_values.append(contribucion)

    steps.append(separator)
    total = sum(contributions, Fraction(0))
    partes = " + ".join(_fmt_factor(valor) for valor in summary_values)
    steps.append(f"{indent}Suma total de contribuciones: {det_label} = {partes} = {_fmt(total)}")
    return total, steps


class DeterminanteMatrizApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        self.root.title("Determinante de Matriz")
        self.root.geometry("1020x740")
        self.root.configure(bg="#ffe4e6")

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

        self.n_var = tk.StringVar(value="3")
        self.entries: List[List[tk.Entry]] = []

        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        header = ttk.Label(container, text="Determinante de una Matriz Cuadrada",
                           font=("Segoe UI", 22, "bold"))
        header.grid(row=0, column=0, pady=(0, 16))

        config_frame = ttk.LabelFrame(container, text="Configuración", padding=12)
        config_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        config_frame.columnconfigure(2, weight=1)

        ttk.Label(config_frame, text="Orden (n×n):").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.spin_n = tk.Spinbox(config_frame, from_=1, to=8, width=5, justify="center",
                                 textvariable=self.n_var, font=("Segoe UI", 12), bg="#fff0f5")
        self.spin_n.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Button(config_frame, text="Generar cuadrícula", style="Primary.TButton",
                   command=self._generar_cuadricula).grid(row=0, column=2, padx=6, pady=6, sticky="w")

        self.matriz_frame = ttk.LabelFrame(container, text="Matriz A", padding=12)
        self.matriz_frame.grid(row=2, column=0, sticky="ew")

        acciones = ttk.Frame(container)
        acciones.grid(row=3, column=0, sticky="ew", pady=(16, 10))
        acciones.columnconfigure(0, weight=1)

        botones = ttk.Frame(acciones)
        botones.grid(row=0, column=0, sticky="w")
        ttk.Button(botones, text="Calcular determinante", style="Primary.TButton",
                   command=self._calcular).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(botones, text="Limpiar entradas", command=self._limpiar).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(botones, text="Ver reglas", command=self._mostrar_reglas).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(botones, text="Mostrar procedimiento", command=self._mostrar_procedimiento).grid(row=0, column=3, padx=6, pady=4)

        resultado_frame = ttk.Frame(container)
        resultado_frame.grid(row=4, column=0, sticky="nsew")
        container.rowconfigure(4, weight=1)
        resultado_frame.columnconfigure(1, weight=1)
        resultado_frame.rowconfigure(1, weight=1)

        self.resumen_label = ttk.Label(resultado_frame, text="Determinante pendiente de cálculo",
                                       font=("Segoe UI", 14, "bold"))
        self.resumen_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Recuadro destacado para mostrar el determinante separado y visible
        det_frame = ttk.LabelFrame(resultado_frame, text="Determinante", padding=8)
        det_frame.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.det_value = tk.Label(det_frame, text="det(A) = —", font=("Segoe UI", 18, "bold"),
                                  bg="#fff0f5", fg="#b91c1c", width=18, anchor="center", relief="flat")
        self.det_value.pack()

        self.matriz_preview = ttk.Frame(resultado_frame, padding=8)
        self.matriz_preview.grid(row=1, column=0, sticky="nw")
        self.matriz_preview.columnconfigure(0, weight=1)

        pasos_container = ttk.Frame(resultado_frame)
        pasos_container.grid(row=1, column=1, sticky="nsew")
        pasos_container.columnconfigure(0, weight=1)
        pasos_container.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(pasos_container, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.pasos_text = tk.Text(pasos_container, wrap="word", height=16, width=90,
                                  bg="#fff0f5", font=("Segoe UI", 11))
        self.pasos_text.grid(row=0, column=0, sticky="nsew")
        self.pasos_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.pasos_text.yview)
        self.pasos_text.config(state="disabled")

        self._generar_cuadricula()

    def _generar_cuadricula(self):
        for widget in self.matriz_frame.winfo_children():
            widget.destroy()
        self.entries.clear()

        try:
            n = int(self.n_var.get())
            if n <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Valor inválido", "Introduce un entero positivo para n.")
            return

        grid_frame = ttk.Frame(self.matriz_frame)
        grid_frame.pack()
        for i in range(n):
            fila_entries: List[tk.Entry] = []
            for j in range(n):
                entry = tk.Entry(grid_frame, width=8, justify="center", font=("Segoe UI", 12), bg="#fff0f5")
                entry.grid(row=i, column=j, padx=4, pady=4)
                fila_entries.append(entry)
            self.entries.append(fila_entries)

    def _leer_matriz(self) -> List[List[Fraction]]:
        matriz: List[List[Fraction]] = []
        for fila_entries in self.entries:
            fila: List[Fraction] = []
            for entry in fila_entries:
                valor = entry.get().strip()
                if valor == "":
                    raise ValueError("Hay casillas vacías en la matriz.")
                valor = valor.replace(",", ".")
                fila.append(Fraction(valor))
            matriz.append(fila)
        return matriz

    def _calcular(self):
        self.pasos_text.config(state="normal")
        self.pasos_text.delete("1.0", "end")
        self.pasos_text.config(state="disabled")
        for widget in self.matriz_preview.winfo_children():
            widget.destroy()
        self.resumen_label.config(text="Determinante pendiente de cálculo")

        try:
            matriz = self._leer_matriz()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        filas = len(matriz)
        if filas == 0:
            messagebox.showerror("Error", "Genera la matriz primero.")
            return
        columnas = len(matriz[0])
        if filas != columnas:
            messagebox.showwarning("Matriz no cuadrada", "Solo se pueden calcular determinantes de matrices cuadradas.")
            return

        texto_detallado, det = self._formato_procedimiento_ejemplo(matriz)
        # Mostrar determinante de forma distintiva
        self.resumen_label.config(text="Determinante calculado")
        self.det_value.config(text=f"det(A) = {_fmt(det)}")

        self._mostrar_matriz_preview(matriz)
        self._mostrar_pasos(texto_detallado)

    def _mostrar_matriz_preview(self, matriz: List[List[Fraction]]):
        grid = ttk.LabelFrame(self.matriz_preview, text="Matriz ingresada", padding=8)
        grid.grid(row=0, column=0, sticky="w")
        for i, fila in enumerate(matriz):
            for j, valor in enumerate(fila):
                label = tk.Label(
                    grid,
                    text=_fmt(valor),
                    width=8,
                    font=("Segoe UI", 12),
                    bg="#fff0f5",
                    relief="solid",
                )
                label.grid(row=i, column=j, padx=4, pady=4)

    def _mostrar_pasos(self, pasos):
        """Muestra el procedimiento en el panel principal (acepta lista o cadena)."""
        self.pasos_text.config(state="normal")
        self.pasos_text.delete("1.0", "end")
        if isinstance(pasos, str):
            texto = pasos if pasos.endswith("\n") else pasos + "\n"
            self.pasos_text.insert("end", texto)
        else:
            for linea in pasos:
                self.pasos_text.insert("end", linea + "\n")
        self.pasos_text.config(state="disabled")
        self.pasos_text.see("1.0")

    def _limpiar(self):
        for fila_entries in self.entries:
            for entry in fila_entries:
                entry.delete(0, "end")
        self.resumen_label.config(text="Determinante pendiente de cálculo")
        self.det_value.config(text="det(A) = —")
        self.pasos_text.config(state="normal")
        self.pasos_text.delete("1.0", "end")
        self.pasos_text.config(state="disabled")
        for widget in self.matriz_preview.winfo_children():
            widget.destroy()

    def _mostrar_reglas(self):
        """Abrir una ventana con las reglas para calcular determinantes, bien formateadas."""
        ventana = tk.Toplevel(self.root)
        ventana.title("Reglas para calcular determinantes")
        ventana.geometry("820x520")
        ventana.configure(bg="#fffaf0")

        texto = tk.Text(ventana, wrap="word", bg="#fffaf0", font=("Segoe UI", 11), padx=12, pady=12)
        texto.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        contenido = (
            "Reglas para calcular determinantes:\n\n"
            "1) Determinante de una matriz 2x2:\n"
            "   Si A = [aij] es 2x2, entonces\n"
            "   det(A) = a11*a22 - a12*a21\n\n"
            "   Ejemplo:\n"
            "   A = [ a11  a12 ]\n"
            "       [ a21  a22 ]\n"
            "   det(A) = a11*a22 - a12*a21\n\n"
            "2) Expansion por cofactores (filas/columnas):\n"
            "   Para n >= 2, el determinante de una matriz cuadrada A = [aij] de orden n\n"
            "   es la suma de n terminos de la forma +/- a1j * det(A1j),\n"
            "   donde A1j es la submatriz que resulta al eliminar la fila 1 y la columna j.\n"
            "   Usando la primera fila:\n"
            "   det(A) = a11*det(A11) - a12*det(A12) + a13*det(A13) - ... + (-1)^(1+n) a1n*det(A1n)\n\n"
            "3) Cofactor y menor:\n"
            "   - Menor (minor) Mij: determinante de la submatriz que se obtiene al eliminar\n"
            "     la fila i y la columna j.\n"
            "   - Cofactor Cij = (-1)^(i+j) * det(Mij). El signo depende solo de i+j.\n\n"
            "4) Matrices triangulares:\n"
            "   Si A es triangular (superior o inferior), entonces det(A) es el producto de\n"
            "   las entradas de la diagonal principal.\n\n"
            "Nota: La calculadora usa expansion por cofactores repetidamente hasta llegar\n"
            "a menores 2x2 y aplica det([[a,b],[c,d]]) = a*d - b*c.\n"
        )

        texto.insert("1.0", contenido)
        texto.config(state="disabled")

    def _formato_procedimiento_ejemplo(self, matrix: List[List[Fraction]]) -> Tuple[str, Fraction]:
        """Genera un texto con el procedimiento detallado en el formato de referencia."""
        n = len(matrix)
        lines: List[str] = []
        sep = "-" * 60

        def _fmt_sum_term(value: Fraction) -> str:
            text = _fmt_ascii(value)
            return f"({text})" if value < 0 else text

        if n == 0:
            return "", Fraction(0)

        if n == 1:
            valor = matrix[0][0]
            lines.append(sep)
            lines.append(" PROCEDIMIENTO DETALLADO: CASO BASE 1X1")
            lines.append(sep)
            lines.append("")
            lines.append("Matriz 1x1:")
            lines.append(f"    [ {_fmt_ascii(valor)} ]")
            lines.append("")
            lines.append("Calculo:")
            lines.append(f"    det(A) = {_fmt_ascii(valor)}")
            lines.append("")
            # Comprobación por cofactores (fila 1)
            lines.append("Comprobacion por cofactores (fila 1):")
            lines.append(f"    det(A) = a11*C11 + a12*C12")
            lines.append(f"    C11 = (+1)*det([{_fmt_ascii(a22)}]) = {_fmt_ascii(a22)}")
            lines.append(f"    C12 = (-1)*det([{_fmt_ascii(a21)}]) = -{_fmt_ascii(a21)}")
            lines.append(f"    a11*C11 + a12*C12 = {_fmt_ascii(a11)}*{_fmt_ascii(a22)} + {_fmt_ascii(a12)}*(-{_fmt_ascii(a21)}) = {_fmt_ascii(det_total)}")
            lines.append("")
            lines.append(sep)
            lines.append(f"DETERMINANTE FINAL:  {_fmt_ascii(valor)}")
            lines.append(sep)
            return "\n".join(lines), valor

        if n == 2:
            a11, a12 = matrix[0]
            a21, a22 = matrix[1]
            prod1 = a11 * a22
            prod2 = a12 * a21
            det_total = prod1 - prod2

            max_len_col1 = max(len(_fmt_ascii(a11)), len(_fmt_ascii(a21)))
            max_len_col2 = max(len(_fmt_ascii(a12)), len(_fmt_ascii(a22)))

            lines.append(sep)
            lines.append(" PROCEDIMIENTO DETALLADO: CASO BASE 2X2")
            lines.append(sep)
            lines.append("")
            lines.append("Matriz 2x2:")
            lines.append(
                "    [  "
                + _fmt_ascii(a11).rjust(max_len_col1)
                + "   "
                + _fmt_ascii(a12).rjust(max_len_col2)
                + " ]"
            )
            lines.append(
                "    [  "
                + _fmt_ascii(a21).rjust(max_len_col1)
                + "   "
                + _fmt_ascii(a22).rjust(max_len_col2)
                + " ]"
            )
            lines.append("")
            lines.append("Calculo:")
            lines.append(f"    det(A) = ({_fmt_ascii(a11)}*{_fmt_ascii(a22)}) - ({_fmt_ascii(a12)}*{_fmt_ascii(a21)})")
            lines.append(f"              = {_fmt_ascii(prod1)} - {_fmt_ascii(prod2)}")
            lines.append(f"              = {_fmt_ascii(det_total)}")
            lines.append("")
            lines.append(sep)
            lines.append(f"DETERMINANTE FINAL:  {_fmt_ascii(det_total)}")
            lines.append(sep)
            return "\n".join(lines), det_total

        # Estilo compacto para matrices n>=3 (como el ejemplo solicitado)
        if n >= 3:
            def _inline(m):
                return "[ " + "; ".join(" ".join(_fmt_ascii(x) for x in row) for row in m) + " ]"
            def _inline_bars(m):
                inner = "; ".join(" ".join(_fmt_ascii(x) for x in row) for row in m)
                return "| " + inner + " |"

            terms_text = []
            numeric_terms_text = []
            contribs: List[Fraction] = []
            bars_terms_text = []

            for j in range(n):
                a = matrix[0][j]
                sub = _minor(matrix, 0, j)
                sign = 1 if (j % 2 == 0) else -1
                op = "" if j == 0 else (" + " if sign > 0 else " - ")

                # Primera línea: a1j * det([submatriz])
                terms_text.append(f"{op}{_fmt_ascii(a)}*det{_inline(sub)}")
                bars_terms_text.append(f"{op}{_fmt_ascii(a)} {_inline_bars(sub)}")

                # Determinante del menor: si es 2x2 mostramos (ad-bc), si es mayor usamos su valor
                if len(sub) == 2:
                    a11, a12 = sub[0]
                    a21, a22 = sub[1]
                    p1 = a11 * a22
                    p2 = a12 * a21
                    det_sub = p1 - p2
                    numeric_terms_text.append(f"{op}{_fmt_ascii(a)}({_fmt_ascii(p1)} - {_fmt_ascii(p2)})")
                else:
                    det_sub, _ = determinante_con_pasos(sub)
                    numeric_terms_text.append(f"{op}{_fmt_ascii(a)}({_fmt_ascii(det_sub)})")

                contribs.append(Fraction(sign) * a * det_sub)

            total = sum(contribs, Fraction(0))

            lines.append("det(A) = " + "".join(terms_text))
            lines.append("= " + "".join(numeric_terms_text) + f" = {_fmt_ascii(total)}")
            lines.append("det(A) = " + "".join(bars_terms_text) + " = ... = " + _fmt_ascii(total))
            return "\n".join(lines), total

        lines.append(sep)
        lines.append(" PROCEDIMIENTO DETALLADO: EXPANSION POR COFACTORES (FILA 1)")
        lines.append(sep)
        lines.append("")

        formula = " + ".join(f"a1{j+1}*C1{j+1}" for j in range(n))
        lines.append(f"det(A) = {formula}")
        lines.append("")

        contrib_values: List[Fraction] = []

        for j in range(n):
            a = matrix[0][j]
            idx = f"a1{j+1}"
            sign_factor = Fraction(1 if j % 2 == 0 else -1)
            sign_symbol = "+" if sign_factor > 0 else "-"

            lines.append(sep)
            lines.append("")
            lines.append(f"Elemento {idx} = {_fmt_ascii(a)}   (signo {sign_symbol})")
            lines.append("")

            if a == 0:
                lines.append(f"    Como {idx} = 0, su contribucion es nula y se omite.")
                lines.append("")
                contrib_values.append(Fraction(0))
                continue

            sub = _minor(matrix, 0, j)
            col_widths = [0] * len(sub[0]) if sub else []
            for fila in sub:
                for col_index, val in enumerate(fila):
                    text = _fmt_ascii(val)
                    col_widths[col_index] = max(col_widths[col_index], len(text))

            lines.append(f"Submatriz M1{j+1} (eliminando fila 1 y columna {j+1}):")
            for fila in sub:
                partes = [_fmt_ascii(val).rjust(col_widths[col_index]) for col_index, val in enumerate(fila)]
                lines.append("    [  " + "   ".join(partes) + " ]")
            lines.append("")

            if len(sub) == 2:
                a11, a12 = sub[0]
                a21, a22 = sub[1]
                prod1 = a11 * a22
                prod2 = a12 * a21
                det_sub = prod1 - prod2

                lines.append("Caso base 2x2:")
                lines.append(
                    "    [  "
                    + _fmt_ascii(a11).rjust(col_widths[0])
                    + "   "
                    + _fmt_ascii(a12).rjust(col_widths[1])
                    + " ]"
                )
                lines.append(
                    "    [  "
                    + _fmt_ascii(a21).rjust(col_widths[0])
                    + "   "
                    + _fmt_ascii(a22).rjust(col_widths[1])
                    + " ]"
                )
                lines.append("")
                lines.append("Calculo:")
                lines.append(
                    f"    det(M1{j+1}) = ({_fmt_ascii(a11)}*{_fmt_ascii(a22)}) - ({_fmt_ascii(a12)}*{_fmt_ascii(a21)})"
                )
                lines.append(f"              = {_fmt_ascii(prod1)} - {_fmt_ascii(prod2)}")
                lines.append(f"              = {_fmt_ascii(det_sub)}")
                lines.append("")
            else:
                det_sub, _ = determinante_con_pasos(sub)
                lines.append("Calculo:")
                lines.append(f"    det(M1{j+1}) = {_fmt_ascii(det_sub)}")
                lines.append("")

            cofactor = sign_factor * det_sub
            contrib = a * cofactor

            lines.append(f"    C1{j+1} = ({'+' if sign_factor > 0 else '-'}1)*({_fmt_ascii(det_sub)}) = {_fmt_ascii(cofactor)}")
            lines.append(f"    Contribucion parcial: {_fmt_ascii(a)} * {_fmt_ascii(cofactor)} = {_fmt_ascii(contrib)}")
            lines.append("")

            contrib_values.append(contrib)

        lines.append(sep)
        lines.append("")

        total = sum(contrib_values, Fraction(0))
        partes = " + ".join(_fmt_sum_term(valor) for valor in contrib_values)

        lines.append("Suma total de contribuciones:")
        lines.append("")
        lines.append(f"    det(A) = {partes}")
        lines.append(f"    det(A) = {_fmt_ascii(total)}")
        lines.append("")
        lines.append(sep)
        lines.append(f"DETERMINANTE FINAL:  {_fmt_ascii(total)}")
        lines.append(sep)

        return "\n".join(lines), total

    def _mostrar_procedimiento(self):
        """Muestra en una ventana el procedimiento detallado para la matriz actual."""
        try:
            matriz = self._leer_matriz()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        texto, det = self._formato_procedimiento_ejemplo(matriz)

        ventana = tk.Toplevel(self.root)
        ventana.title("Procedimiento detallado: determinante")
        ventana.geometry("1000x700")
        ventana.configure(bg="#fffaf0")

        # dividir ventana en dos columnas: procedimiento (izq) y recuadro determinante (der)
        left = ttk.Frame(ventana, padding=8)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(ventana, padding=8)
        right.pack(side="right", fill="y")

        # scrollbars
        vscroll = ttk.Scrollbar(left, orient='vertical')
        hscroll = ttk.Scrollbar(left, orient='horizontal')

        # usar fuente monoespaciada para alineacion exacta
        font_name = "Consolas"
        try:
            text_widget = tk.Text(left, wrap="none", bg="#fffaf0", font=(font_name, 11), padx=12, pady=12,
                                  xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        except Exception:
            # fallback
            text_widget = tk.Text(left, wrap="none", bg="#fffaf0", font=("Courier", 11), padx=12, pady=12,
                                  xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)

        vscroll.config(command=text_widget.yview)
        hscroll.config(command=text_widget.xview)
        vscroll.pack(side='right', fill='y')
        hscroll.pack(side='bottom', fill='x')
        text_widget.pack(fill="both", expand=True)

        text_widget.config(state="normal")
        text_widget.insert("1.0", texto)
        text_widget.config(state="disabled")

        det_frame = ttk.LabelFrame(right, text="Determinante", padding=12)
        det_frame.pack(fill="both", expand=False, padx=8, pady=8)
        det_label = tk.Label(det_frame, text=f"det(A) = {_fmt_ascii(det)}", font=("Consolas", 16, "bold"), bg="#fffaf0")
        det_label.pack(padx=12, pady=12)

        cerrar = ttk.Button(right, text="Cerrar", command=ventana.destroy)
        cerrar.pack(pady=8)

    def _volver_al_inicio(self):
        try:
            self.root.destroy()
        finally:
            try:
                if callable(self.volver_callback):
                    self.volver_callback()
            except Exception:
                pass

