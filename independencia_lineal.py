
# independencia_lineal.py


import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction
from math import gcd
from determinante_matriz_app import determinante_con_pasos




def es_vector_cero(v):
    return all(x == 0 for x in v)




def son_multiplos(v1, v2):
    """Devuelve (es_multiplo, k, pasos, conclusion)."""

    def toF(x):
        return Fraction(x).limit_denominator()

    def fmt(q: Fraction):
        q = toF(q)
        return f"{q.numerator}" if q.denominator == 1 else f"{q.numerator}/{q.denominator}"

    ratio = None
    pasos = ["Buscamos un escalar k tal que v₁ = k·v₂ (comparamos componente a componente):"]

    for idx, (a, b) in enumerate(zip(v1, v2), start=1):
        fa, fb = toF(a), toF(b)

        if fb == 0 and fa == 0:
            pasos.append(f"  • Componente {idx}: 0 = k·0 → no fija k (cualquier k funciona en esta componente).")
            continue

        if fb == 0:
            pasos.append(f"  • Componente {idx}: v₂_{idx} = 0 pero v₁_{idx} = {fmt(fa)} → no existe un mismo k que satisfaga todas las componentes.")
            return False, None, pasos, ""

        k_local = Fraction(0) if fa == 0 else (fa / fb).limit_denominator()
        pasos.append(f"  • Componente {idx}: {fmt(fa)} = {fmt(k_local)}·{fmt(fb)}")

        if ratio is None:
            ratio = k_local
            continue

        if k_local != ratio:
            pasos.append(f"  × El valor de k cambió (antes {fmt(ratio)}, ahora {fmt(k_local)}) → no son múltiplos.")
            return False, None, pasos, ""

    # Si nunca se fijó ratio (ambos vectores eran 0 en todas las entradas), tomamos k = 0.
    if ratio is None:
        ratio = Fraction(0)

    conclusion = f"Se verifica que v₁ = {fmt(ratio)}·v₂"
    if ratio != 0:
        inv = (Fraction(1) / ratio).limit_denominator()
        conclusion += f" (equivalentemente, v₂ = {fmt(inv)}·v₁)."
    else:
        conclusion += " (v₁ es el vector cero y por tanto múltiplo trivial de v₂)."

    pasos.append(f"  ✓ Todas las componentes son consistentes con k = {fmt(ratio)}.")
    return True, ratio, pasos, conclusion




# ---------- Función de independencia ----------
def son_linealmente_independientes(vectores, metodo="gauss"):
    # ---------- utilidades ----------
    def toF(x):
        return Fraction(x).limit_denominator()

    def lcm(a, b):
        return abs(a*b) // gcd(a, b) if a and b else 0

    def lcm_list(nums):
        cur = 1
        for d in nums:
            cur = lcm(cur, d) if cur else d
        return cur if cur else 1

    def fmt_frac(q: Fraction):
        return f"{q.numerator}" if q.denominator == 1 else f"{q.numerator}/{q.denominator}"

    def formato_matriz(M):
        filas_txt = []
        for fila in M:
            izq = "  ".join(f"{fmt_frac(x):>7}" for x in fila[:-1])
            der = f"{fmt_frac(fila[-1]):>7}"
            filas_txt.append("[ " + izq + "  |  " + der + " ]")
        return "\n".join(filas_txt)

    # Normaliza método pedido
    metodo = (metodo or "gauss").lower()

    # ---------- datos base ----------
    n = len(vectores[0])     # dimensión
    p = len(vectores)        # nº de vectores = nº de variables c1..cp

    resultado = ""
    reglas_aplicadas = []
    detalle_multiplos = ""

    # ---------- reglas básicas ----------
    for idx, v in enumerate(vectores):
        if es_vector_cero(v):
            reglas_aplicadas.append(f"• El conjunto contiene el vector cero (v{idx+1} = {v}), por lo que es linealmente dependiente.")
    if p > n:
        reglas_aplicadas.append(f"• El conjunto tiene más vectores ({p}) que dimensiones ({n}), por lo que es linealmente dependiente.")
    if p == 1:
        if not es_vector_cero(vectores[0]):
            reglas_aplicadas.append("• Un conjunto que solo tiene un vector v es linealmente independiente si y solo si v no es el vector cero.")
        else:
            reglas_aplicadas.append("• El único vector es el vector cero, por lo que el conjunto es linealmente dependiente.")
    if p == 2:
        es_mult, k_mult, pasos_mult, conclusion_mult = son_multiplos(vectores[0], vectores[1])
        if es_mult:
            reglas_aplicadas.append("• Un conjunto de dos vectores {v₁, v₂} es linealmente dependiente si al menos uno de los vectores es un múltiplo del otro.")
            pasos_mult.append(f"Conclusión: {conclusion_mult}")
            detalle_multiplos = "🧮 Comprobación de múltiplos para {v₁, v₂}:\n" + "\n".join(pasos_mult) + "\n"
        else:
            reglas_aplicadas.append("• Un conjunto de dos vectores {v₁, v₂} es linealmente independiente si y solo si ninguno de los vectores es un múltiplo del otro.")

    if p <= 2 and reglas_aplicadas and not (metodo == "determinante" and p == n):
        resultado += "📘 Reglas aplicadas:\n" + "\n".join(reglas_aplicadas) + "\n\n"
        if any("es linealmente dependiente" in r for r in reglas_aplicadas):
            if detalle_multiplos:
                resultado += detalle_multiplos
            resultado += "❌ El conjunto es linealmente DEPENDIENTE.\n"
            return False, resultado
        else:
            resultado += "✅ El conjunto es linealmente INDEPENDIENTE.\n"
            return True, resultado

    # ---------- método por determinante (opcional) ----------
    if metodo == "determinante":
        if p != n:
            reglas_aplicadas.append("• El método del determinante solo aplica cuando la matriz es cuadrada. Se usará Gauss-Jordan automáticamente.")
            metodo = "gauss"
        else:
            reglas_actuales = list(reglas_aplicadas)
            matriz_det = [[toF(vectores[j][i]) for j in range(p)] for i in range(n)]
            det_val, pasos_det = determinante_con_pasos(matriz_det)

            resultado = ""
            if reglas_actuales:
                resultado += "📘 Reglas aplicadas:\n" + "\n".join(reglas_actuales) + "\n\n"
            resultado += "📗 Procedimiento por determinante (columnas = vectores):\n\n"
            resultado += "\n".join(pasos_det) + "\n\n"
            resultado += f"det(A) = {fmt_frac(det_val)}\n\n"
            if det_val != 0:
                resultado += "Como det(A) != 0, el conjunto es linealmente INDEPENDIENTE.\n"
                return True, resultado
            resultado += "Como det(A) = 0, el conjunto es linealmente DEPENDIENTE.\n"
            return False, resultado

    # ---------- núcleo: SIEMPRE columnas = vectores ----------
    V = [[toF(vectores[j][i]) for j in range(p)] for i in range(n)]  # n x p
    A = [row + [Fraction(0)] for row in V]  # [V | 0]

    pasos = ["📗 Procedimiento paso a paso (Gauss-Jordan sobre c1..cₚ, columnas=vectores):\n\n"]

    piv_fila = 0
    pos_piv_col = [-1] * n

    # Gauss–Jordan (solo columnas de variables: 0..p-1)
    for col in range(p):
        fila_pivote = None
        for f in range(piv_fila, n):
            if A[f][col] != 0:
                fila_pivote = f
                break
        if fila_pivote is None:
            continue
        if fila_pivote != piv_fila:
            A[piv_fila], A[fila_pivote] = A[fila_pivote], A[piv_fila]
            pasos.append(f"↔ Se intercambian filas F{piv_fila+1} ↔ F{fila_pivote+1}\n")
            pasos.append(formato_matriz(A) + "\n\n")
        factor = A[piv_fila][col]
        if factor != 0:
            A[piv_fila] = [x / factor for x in A[piv_fila]]
            pasos.append(f"F{piv_fila+1} → F{piv_fila+1} / {fmt_frac(factor)}\n")
            pasos.append(formato_matriz(A) + "\n\n")
        for f in range(n):
            if f != piv_fila and A[f][col] != 0:
                fac = A[f][col]
                A[f] = [a - fac*b for a, b in zip(A[f], A[piv_fila])]
                pasos.append(f"F{f+1} → F{f+1} - ({fmt_frac(fac)})·F{piv_fila+1}\n")
                pasos.append(formato_matriz(A) + "\n\n")
        pos_piv_col[piv_fila] = col
        piv_fila += 1
        if piv_fila == n:
            break

    # columnas pivote y libres (sobre variables 0..p-1)
    piv_cols = set(c for c in pos_piv_col if c != -1)
    libres = [j for j in range(p) if j not in piv_cols]

    # vector solución c (tamaño p)
    c = [Fraction(0)] * p

    # ------------ helpers para despeje robusto (evita IndexError) ------------
    def despeje_vk_desde_Cint(Cint, prefer_libres=None):
        """Devuelve (k, rhs_str). Elige k con RHS no vacío; si no hay, v_k = 0."""
        prefer_libres = set(prefer_libres or [])
        candidatos = list(range(p))

        def prioridad(idx):
            Ci = Cint[idx]
            if Ci == -1: return (0, idx)
            if abs(Ci) == 1: return (1, idx)
            if idx in prefer_libres: return (2, idx)
            return (3, idx)

        candidatos.sort(key=prioridad)

        for cand in candidatos:
            Ck = Cint[cand]
            if Ck == 0:
                continue
            tmp_terms = []
            for i, Ci in enumerate(Cint):
                if i == cand or Ci == 0:
                    continue
                frac = Fraction(-Ci, Ck).limit_denominator()
                s = "-" if frac < 0 else ""
                aval = -frac if frac < 0 else frac
                coef_txt = fmt_frac(aval)
                tmp_terms.append(f"{s}{coef_txt}·v{i+1}")
            if tmp_terms:
                rhs = tmp_terms[0]
                for t in tmp_terms[1:]:
                    rhs += (" + " + t) if not t.startswith("-") else (" - " + t[1:])
                return cand, rhs

        # Caso extremo: sin RHS → v_k = 0
        k_fallback = candidatos[0] if candidatos else 0
        return k_fallback, "0   (columna nula)"

    # -------------------------------------------------------------------------

    if libres:
        # DEPENDIENTE — presentación didáctica (una o varias libres)
        reglas_aplicadas.append("• Es linealmente dependiente si existen coeficientes no todos cero tales que c₁v₁ + c₂v₂ + ⋯ + cₚvₚ = 0, es decir, al menos uno de los vectores puede escribirse como combinación lineal de los demás.")
        resultado += "📘 Reglas aplicadas:\n" + "\n".join(reglas_aplicadas) + "\n\n"
        resultado += "".join(pasos)

        # ---- 1) UNA libre: formato especial que pediste ----
        if len(libres) == 1:
            j = libres[0]               # índice de la variable libre
            tname = "t"
            # c_i en función de c_j (c_col = -A[i][j] c_j)
            coef_en_j = [Fraction(0)] * p
            coef_en_j[j] = Fraction(1)
            for i in reversed(range(n)):
                if pos_piv_col[i] == -1:
                    continue
                col = pos_piv_col[i]
                coef_en_j[col] = (-A[i][j]).limit_denominator()

            # Relaciones "c1 = 2c3, c2 = -c3, c3 libre (sea c3 = t)"
            rel_lineas = []
            for i in range(p):
                if i == j:
                    continue
                a = coef_en_j[i]
                if a == 0:
                    rel_lineas.append(f"c{i+1} = 0")
                else:
                    pref = "-" if a < 0 else ""
                    aval = -a if a < 0 else a
                    coef_txt = fmt_frac(aval)
                    rel_lineas.append(f"c{i+1} = {pref}{coef_txt}c{j+1}")
            rel_lineas.append(f"c{j+1} libre (sea c{j+1} = {tname})")

            resultado += "Relaciones entre coeficientes:\n" + ", ".join(rel_lineas) + "\n\n"
            resultado += f"Variables libres: c{j+1} libre (sea c{j+1} = {tname})\n\n"

            # Solución general y particular
            dir_vec = [coef_en_j[i] for i in range(p)]
            dir_vec[j] = Fraction(1)  # el libre vale 1 en el vector dirección
            vec_txt = "(" + ", ".join(fmt_frac(x) for x in dir_vec) + ")"
            resultado += f"Solución general: c = {tname}{vec_txt}\n"
            resultado += f"Tomando {tname} = 1 → c = {vec_txt}\n"

            # Construir Σ C_i v_i = 0 (entero)
            L = lcm_list([x.denominator for x in dir_vec])
            Cint = [int(x * L) for x in dir_vec]
            # "Es decir: ..." bonito
            suma_str = []
            for i, Ci in enumerate(Cint):
                if Ci == 0:
                    continue
                term = f"{abs(Ci)}v{i+1}"
                if not suma_str:
                    suma_str.append(("-" if Ci < 0 else "") + term)
                else:
                    suma_str.append((" - " if Ci < 0 else " + ") + term)
            resultado += "Es decir: " + "".join(suma_str) + " = 0"

            # Despejar v_k con RHS no vacío (preferir libre)
            k, rhs = despeje_vk_desde_Cint(Cint, prefer_libres=[j])
            resultado += f"  ⇔  v{k+1} = {rhs}\n\n"

            # Relación entera final
            relacion = " + ".join([f"{Cint[i]}·v{i+1}" for i in range(p)])
            resultado += f"🔢 Versión entera equivalente: {relacion} = 0\n"
            resultado += "❌ El conjunto es **linealmente DEPENDIENTE**.\n"
            return False, resultado

        # ---- 2) Varias libres: formato paramétrico t1, t2, ... ----
        else:
            # Relaciones c_pivote = sum_j (-A[i][j]) c_j
            relaciones = []
            for i in reversed(range(n)):
                if pos_piv_col[i] == -1:
                    continue
                col = pos_piv_col[i]
                terminos = []
                for j in range(col+1, p):
                    if j in libres and A[i][j] != 0:
                        coef = (-A[i][j]).limit_denominator()
                        s = "-" if coef < 0 else ""
                        aval = -coef if coef < 0 else coef
                        terminos.append(f"{s}{fmt_frac(aval)}c{j+1}")
                if terminos:
                    expr = terminos[0]
                    for t in terminos[1:]:
                        expr += (" + " + t) if not t.startswith("-") else (" - " + t[1:])
                    relaciones.append(f"c{col+1} = {expr}")
                else:
                    relaciones.append(f"c{col+1} = 0")

            param_name = {j: f"t{k+1}" for k, j in enumerate(libres)}
            for j in libres:
                relaciones.append(f"c{j+1} libre (pongamos c{j+1} = {param_name[j]})")

            resultado += "Relaciones entre coeficientes:\n" + "\n".join(relaciones) + "\n\n"
            resultado += "Variables libres: " + ", ".join([f"c{j+1} (sea c{j+1} = {param_name[j]})" for j in libres]) + "\n\n"

            # Base del núcleo y solución general
            base_nucleo = []
            for jlib in libres:
                c_basis = [Fraction(0)] * p
                c_basis[jlib] = Fraction(1)
                for i in reversed(range(n)):
                    if pos_piv_col[i] == -1:
                        continue
                    col = pos_piv_col[i]
                    suma = sum(A[i][k] * c_basis[k] for k in range(col+1, p))
                    c_basis[col] = -suma
                base_nucleo.append(c_basis)

            partes = []
            for k0, vdir in enumerate(base_nucleo):
                vec_txt = "(" + ", ".join(fmt_frac(x) for x in vdir) + ")"
                partes.append(f"t{k0+1}{vec_txt}")
            resultado += "Solución general: c = " + " + ".join(partes) + "\n"

            # Particular clara: t1=1, resto 0
            c = base_nucleo[0][:]
            vec_txt = "(" + ", ".join(fmt_frac(x) for x in c) + ")"
            fija = [f"t1 = 1"] + [f"t{k0+1} = 0" for k0 in range(1, len(libres))]
            resultado += "Tomando " + ", ".join(fija) + f" → c = {vec_txt}\n"

            # Relación entera y despeje robusto (preferir libres)
            denoms = [ci.denominator for ci in c]
            M = lcm_list(denoms)
            Cint = [int(ci * M) for ci in c]

            k, rhs = despeje_vk_desde_Cint(Cint, prefer_libres=libres)
            resultado += f"\n🧮 Despejando un vector:\n"
            resultado += f"v{k+1} = {rhs}\n"

            relacion = " + ".join([f"{Cint[i]}·v{i+1}" for i in range(p)])
            resultado += f"🔢 Versión entera equivalente: {relacion} = 0\n"
            resultado += "❌ El conjunto es **linealmente DEPENDIENTE**.\n"
            return False, resultado

    else:
        # INDEPENDIENTE (con procedimiento)
        reglas_aplicadas.append("• Se dice que un conjunto de vectores {v₁,…,vₚ} en ℝⁿ es linealmente independiente si la ecuación c₁v₁ + c₂v₂ + ⋯ + cₚvₚ = 0 solo tiene la solución trivial.")
        resultado += "📘 Reglas aplicadas:\n" + "\n".join(reglas_aplicadas) + "\n\n"
        pasos.append("Matriz reducida (RREF):\n")
        pasos.append(formato_matriz(A) + "\n\n")
        pasos.append(f"Columnas pivote (sobre c1..c{p}): {sorted(list(piv_cols))}\n")
        pasos.append(f"Rango de V: {len(piv_cols)}\n")
        pasos.append("Variables libres: ninguna\n\n")
        resultado += "".join(pasos)
        resultado += "Solución trivial: " + ", ".join([f"c{i+1}=0" for i in range(p)]) + "\n\n"
        resultado += "✅ El conjunto es **linealmente INDEPENDIENTE**.\n"
        return True, resultado



# -------------------- Interfaz Gráfica --------------------
class IndependenciaLinealApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback
        self.root.title("Independencia Lineal de Vectores")
        self.root.configure(bg="#ffe4e6")
        self._setup_styles()
        self._setup_widgets()


    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=8,
                        background="#fbb6ce", foreground="#fff")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])
        style.configure("Back.TButton", font=("Segoe UI", 11, "bold"), padding=6,
                        background="#fecaca", foreground="#b91c1c")
        style.map("Back.TButton",
                  background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])


    def _setup_widgets(self):
        frame = ttk.Frame(self.root, padding=10, style="TFrame")
        frame.pack(fill="both", expand=True)


        arriba = ttk.Frame(frame, style="TFrame")
        arriba.pack(pady=5)
        ttk.Label(arriba, text="Dimensión:", background="#ffe4e6", font=("Segoe UI", 11)).pack(side="left")
        self.dim_var = tk.IntVar(value=3)
        dim_spin = ttk.Spinbox(arriba, from_=1, to=10, width=3, textvariable=self.dim_var, font=("Segoe UI", 11))
        dim_spin.pack(side="left", padx=5)
        ttk.Label(arriba, text="Cantidad de vectores:", background="#ffe4e6", font=("Segoe UI", 11)).pack(side="left")
        self.cant_var = tk.IntVar(value=2)
        cant_spin = ttk.Spinbox(arriba, from_=1, to=10, width=3, textvariable=self.cant_var, font=("Segoe UI", 11))
        cant_spin.pack(side="left", padx=5)
        ttk.Button(arriba, text="Volver", style="Back.TButton", command=self.volver_callback).pack(side="left", padx=15)


        self.dim_var.trace_add("write", lambda *a: self._crear_entradas())
        self.cant_var.trace_add("write", lambda *a: self._crear_entradas())


        self.entradas_frame = ttk.Frame(frame, style="TFrame")
        self.entradas_frame.pack(pady=15)


        abajo = ttk.Frame(frame, style="TFrame")
        abajo.pack(pady=5)

        metodo_frame = ttk.LabelFrame(abajo, text="Método", padding=8)
        metodo_frame.pack(side="left", padx=10)
        self.metodo_var = tk.StringVar(value="gauss")
        ttk.Radiobutton(metodo_frame, text="Gauss-Jordan", variable=self.metodo_var,
                        value="gauss").pack(anchor="w", pady=1)
        ttk.Radiobutton(metodo_frame, text="Determinante (matriz cuadrada)", variable=self.metodo_var,
                        value="determinante").pack(anchor="w", pady=1)

        botones_frame = ttk.Frame(abajo, style="TFrame")
        botones_frame.pack(side="left", padx=10)
        ttk.Button(botones_frame, text="Vectores columna", style="Primary.TButton",
                   command=lambda: self.verificar("columna")).pack(fill="x", pady=2)
        ttk.Button(botones_frame, text="Vectores fila", style="Primary.TButton",
                   command=lambda: self.verificar("fila")).pack(fill="x", pady=2)
        self.resultado = tk.Text(abajo, width=70, height=20, state="disabled", font=("Consolas", 11),
                                 bg="#fff0f6", fg="black", wrap="word")
        self.resultado.pack(side="left", padx=10)


        self._crear_entradas()


    def _crear_entradas(self):
        for widget in self.entradas_frame.winfo_children():
            widget.destroy()
        dim = self.dim_var.get()
        cant = self.cant_var.get()
        self.entradas = []
        for j in range(cant):
            col = []
            col_frame = ttk.Frame(self.entradas_frame, style="TFrame")
            col_frame.pack(side="left", padx=12)
            ttk.Label(col_frame, text=f"v{j+1}", font=("Segoe UI", 11, "bold"),
                      background="#ffe4e6", foreground="#b91c1c").pack()
            for i in range(dim):
                e = ttk.Entry(col_frame, width=6, justify="center", font=("Segoe UI", 11))
                e.pack(pady=2)
                col.append(e)
            self.entradas.append(col)


    def verificar(self, orientacion="columna"):
        try:
            vectores = []
            for col in self.entradas:
                v = [float(e.get()) for e in col]
                vectores.append(v)
        except Exception:
            messagebox.showerror("Error", "Por favor, ingresa todos los valores numéricos.")
            return


        if not vectores:
            messagebox.showerror("Error", "Ingresa al menos un vector.")
            return

        if orientacion == "fila":
            # Tomamos cada fila ingresada como vector fila.
            vectores = [list(fila) for fila in zip(*vectores)]

        metodo_sel = self.metodo_var.get() if hasattr(self, "metodo_var") else "gauss"
        independiente, justificacion = son_linealmente_independientes(vectores, metodo=metodo_sel)


        self.resultado.configure(state="normal")
        self.resultado.delete("1.0", tk.END)
        if orientacion == "fila":
            self.resultado.insert(tk.END, "Modo: vectores fila (se toman las filas como vectores).\n")
        else:
            self.resultado.insert(tk.END, "Modo: vectores columna (se toman las columnas como vectores).\n")
        if metodo_sel == "determinante":
            self.resultado.insert(tk.END, "Método: determinante (usa det(A) con columnas = vectores).\n\n")
        else:
            self.resultado.insert(tk.END, "Método: Gauss-Jordan (sistema homogéneo c·v = 0).\n\n")
        self.resultado.insert(tk.END, justificacion)
        self.resultado.configure(state="disabled")



