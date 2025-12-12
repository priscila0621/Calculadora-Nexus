from fractions import Fraction
from math import gcd
from typing import List, Optional, Sequence, Tuple

from determinante_matriz_app import determinante_con_pasos


def _to_fraction(x) -> Fraction:
    return Fraction(x).limit_denominator()


def _fmt_frac(q: Fraction) -> str:
    return f"{q.numerator}" if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def es_vector_cero(v: Sequence) -> bool:
    return all(_to_fraction(x) == 0 for x in v)


def son_multiplos(v1: Sequence, v2: Sequence) -> Tuple[bool, Optional[Fraction], List[str], str]:
    """Devuelve (son_multiplos, k, pasos, conclusion) para v1 = k*v2."""
    ratio = None
    pasos = ["Buscamos un escalar k tal que v' = k * v'' (componente a componente):"]

    for idx, (a, b) in enumerate(zip(v1, v2), start=1):
        fa, fb = _to_fraction(a), _to_fraction(b)

        if fb == 0 and fa == 0:
            pasos.append(f"  - Componente {idx}: 0 = k*0 (no fija k).")
            continue

        if fb == 0:
            conclusion = "No existe un escalar común: una componente de v'' es 0 y la correspondiente de v' no."
            pasos.append(f"  - Componente {idx}: v''_{idx} = 0 pero v'_{idx} = {_fmt_frac(fa)}.")
            pasos.append(f"Conclusión: {conclusion}")
            return False, None, pasos, conclusion

        k_local = Fraction(0) if fa == 0 else (fa / fb).limit_denominator()
        pasos.append(f"  - Componente {idx}: {_fmt_frac(fa)} = {_fmt_frac(k_local)} * {_fmt_frac(fb)}")

        if ratio is None:
            ratio = k_local
            continue

        if k_local != ratio:
            conclusion = "No existe un único k que iguale todas las componentes; no son múltiplos."
            pasos.append(f"  - El valor de k cambió (antes {_fmt_frac(ratio)}, ahora {_fmt_frac(k_local)}).")
            pasos.append(f"Conclusión: {conclusion}")
            return False, None, pasos, conclusion

    if ratio is None:
        ratio = Fraction(0)

    conclusion = f"Se verifica que v' = {_fmt_frac(ratio)} * v''"
    if ratio != 0:
        inv = (Fraction(1) / ratio).limit_denominator()
        conclusion += f" (equivalente: v'' = {_fmt_frac(inv)} * v')."
    else:
        conclusion += " (v' es el vector cero)."

    pasos.append(f"  - Todas las componentes son consistentes con k = {_fmt_frac(ratio)}.")
    return True, ratio, pasos, conclusion


def son_linealmente_independientes(vectores: List[Sequence], metodo: str = "gauss") -> Tuple[bool, str]:
    """
    Evalúa independencia lineal usando Gauss-Jordan o determinante.
    Retorna (independiente, explicación).
    """
    if not vectores:
        raise ValueError("Se requieren al menos un vector.")

    n = len(vectores[0])
    if any(len(v) != n for v in vectores):
        raise ValueError("Todos los vectores deben tener la misma dimensión.")

    metodo = (metodo or "gauss").lower()
    p = len(vectores)

    reglas_aplicadas: List[str] = []
    resultado: List[str] = []

    if any(es_vector_cero(v) for v in vectores):
        reglas_aplicadas.append("El conjunto contiene el vector cero, por lo que es linealmente dependiente.")
    if p > n:
        reglas_aplicadas.append(f"Hay más vectores ({p}) que dimensiones ({n}); el conjunto es dependiente.")
    if p == 1:
        if es_vector_cero(vectores[0]):
            reglas_aplicadas.append("El único vector es el vector cero, por lo que el conjunto es dependiente.")
        else:
            reglas_aplicadas.append("Un único vector no nulo siempre es independiente.")

    if p == 2:
        es_mult, k_mult, pasos_mult, conclusion_mult = son_multiplos(vectores[0], vectores[1])
        if es_mult:
            reglas_aplicadas.append("Dos vectores son dependientes si uno es múltiplo del otro.")
            pasos_mult.append(f"Conclusión: {conclusion_mult}")
            detalle_mult = "\n".join(pasos_mult)
        else:
            reglas_aplicadas.append("Dos vectores son independientes cuando ninguno es múltiplo del otro.")
            detalle_mult = "\n".join(pasos_mult)
    else:
        detalle_mult = ""

    if reglas_aplicadas:
        resultado.append("Reglas aplicadas:")
        resultado.extend(f"- {r}" for r in reglas_aplicadas)
        resultado.append("")
        if any("dependiente" in r.lower() for r in reglas_aplicadas) and not (
            metodo == "determinante" and p == n and p > 2
        ):
            if p == 2 and detalle_mult:
                resultado.append(detalle_mult)
                resultado.append("")
            conclusion = "El conjunto es LINEALMENTE DEPENDIENTE."
            resultado.append(conclusion)
            return False, "\n".join(resultado)
        if p == 1 and not es_vector_cero(vectores[0]):
            resultado.append("El conjunto es LINEALMENTE INDEPENDIENTE.")
            return True, "\n".join(resultado)

    # Método por determinante (solo si matriz cuadrada)
    if metodo == "determinante":
        if p != n:
            resultado.append("El método del determinante solo aplica con matriz cuadrada; se usa Gauss-Jordan.")
        else:
            matriz_det = [[_to_fraction(vectores[j][i]) for j in range(p)] for i in range(n)]
            det_val, pasos_det = determinante_con_pasos(matriz_det)
            resultado.append("Procedimiento por determinante (columnas = vectores):")
            resultado.append("")
            resultado.extend(pasos_det)
            resultado.append("")
            resultado.append(f"det(A) = {_fmt_frac(det_val)}")
            resultado.append("")
            if det_val != 0:
                resultado.append("Como det(A) != 0, el conjunto es LINEALMENTE INDEPENDIENTE.")
                return True, "\n".join(resultado)
            resultado.append("Como det(A) = 0, el conjunto es LINEALMENTE DEPENDIENTE.")
            return False, "\n".join(resultado)

    # Gauss-Jordan sobre [V | 0], columnas = vectores
    A = [[_to_fraction(vectores[j][i]) for j in range(p)] for i in range(n)]  # n x p
    pasos = ["Procedimiento Gauss-Jordan (columnas = vectores):", ""]

    def formato_matriz(M):
        if not M:
            return "[]"
        col_widths = [0] * len(M[0])
        for fila in M:
            for idx, val in enumerate(fila):
                col_widths[idx] = max(col_widths[idx], len(_fmt_frac(val)))
        lines = []
        for fila in M:
            parts = [_fmt_frac(val).rjust(col_widths[idx]) for idx, val in enumerate(fila)]
            lines.append("[ " + "  ".join(parts) + " ]")
        return "\n".join(lines)

    piv_row = 0
    pivot_cols: List[int] = []
    for col in range(p):
        pivot = None
        for r in range(piv_row, n):
            if A[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        if pivot != piv_row:
            A[piv_row], A[pivot] = A[pivot], A[piv_row]
            pasos.append(f"Intercambio F{piv_row+1} ↔ F{pivot+1}")
            pasos.append(formato_matriz(A))
            pasos.append("")
        piv = A[piv_row][col]
        if piv != 1:
            A[piv_row] = [x / piv for x in A[piv_row]]
            pasos.append(f"Normalizar F{piv_row+1} dividiendo por {_fmt_frac(piv)}")
            pasos.append(formato_matriz(A))
            pasos.append("")
        for r in range(n):
            if r == piv_row or A[r][col] == 0:
                continue
            factor = A[r][col]
            A[r] = [a - factor * b for a, b in zip(A[r], A[piv_row])]
            pasos.append(f"F{r+1} = F{r+1} - ({_fmt_frac(factor)})*F{piv_row+1}")
            pasos.append(formato_matriz(A))
            pasos.append("")
        pivot_cols.append(col)
        piv_row += 1
        if piv_row == n:
            break

    rango = len(pivot_cols)
    pasos.append(f"Columnas pivote: {[c+1 for c in pivot_cols]}")
    pasos.append(f"Rango de V: {rango}")
    pasos.append("")

    resultado.extend(pasos)

    if rango == p:
        resultado.append("No hay columnas libres; la única combinación es la trivial.")
        resultado.append("El conjunto es LINEALMENTE INDEPENDIENTE.")
        return True, "\n".join(resultado)

    # Intento de relación entera corta para mostrar dependencia
    free_cols = [c for c in range(p) if c not in pivot_cols]
    if free_cols:
        c_free = free_cols[0]
        pasos_relacion = ["Relación de dependencia construida a partir de la columna libre más simple:"]
        coef = [Fraction(0) for _ in range(p)]
        coef[c_free] = Fraction(1)
        for row, col in enumerate(pivot_cols):
            coef[col] = -A[row][c_free]
        den_lcm = 1
        for c in coef:
            den_lcm = abs(den_lcm * c.denominator) // gcd(den_lcm, c.denominator)
        coef_enteros = [int(c * den_lcm) for c in coef]
        partes = [f"{coef_enteros[i]}*v{i+1}" for i in range(p) if coef_enteros[i] != 0]
        pasos_relacion.append(" + ".join(partes) + " = 0")
        resultado.extend(pasos_relacion)
        resultado.append("")

    resultado.append("Hay columnas sin pivote (variables libres); existe una combinación no trivial.")
    resultado.append("El conjunto es LINEALMENTE DEPENDIENTE.")
    return False, "\n".join(resultado)
