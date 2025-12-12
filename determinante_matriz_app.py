from fractions import Fraction
from typing import List, Tuple


def _fmt(value: Fraction) -> str:
    """Representa fracciones en ASCII (a/b) o enteros cuando corresponde."""
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)


def _fmt_term(value: Fraction) -> str:
    text = _fmt(value)
    return text if value >= 0 else f"({text})"


def _matrix_lines(matrix: List[List[Fraction]], indent: str = "") -> List[str]:
    return [indent + "[ " + "  ".join(_fmt(col) for col in row) + " ]" for row in matrix]


def _is_upper_triangular(matrix: List[List[Fraction]]) -> bool:
    n = len(matrix)
    for i in range(1, n):
        for j in range(i):
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


def determinante_con_pasos(
    matrix: List[List[Fraction]], level: int = 0, matrix_name: str = "A"
) -> Tuple[Fraction, List[str]]:
    """
    Calcula el determinante por expansión de cofactores devolviendo el detalle.
    La función es independiente de cualquier interfaz gráfica.
    """
    if not matrix:
        return Fraction(0), ["Matriz vacía: det = 0"]

    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("La matriz debe ser cuadrada.")

    indent = "    " * level
    steps: List[str] = []
    det_label = f"det({matrix_name})"
    separator = indent + "-" * 70

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
            f"{indent}{det_label} = ({_fmt(a11)} * {_fmt(a22)}) - ({_fmt(a12)} * {_fmt(a21)}) = {_fmt(prod1)} - {_fmt(prod2)} = {_fmt(det)}"
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
        diag_product = " * ".join(_fmt(value) for value in diag)
        steps.append(f"{indent}La matriz {matrix_name} es triangular {tipo}.")
        steps.append(f"{indent}{det_label} = {diag_product} = {_fmt(det)}")
        return det, steps

    steps.append(f"{indent}Expansión por cofactores en la primera fila")
    formula = " + ".join(f"a1{j+1}C1{j+1}" for j in range(n))
    steps.append(f"{indent}{det_label} = {formula}")

    contributions: List[Fraction] = []
    summary_values: List[Fraction] = []
    for j in range(n):
        elemento = matrix[0][j]
        sign_factor = Fraction(1 if j % 2 == 0 else -1)
        sign_symbol = "+" if sign_factor >= 0 else "-"

        steps.append(separator)
        steps.append(f"{indent}Elemento a1{j+1} = {_fmt(elemento)} (signo {sign_symbol})")
        if elemento == 0:
            steps.append(f"{indent}Como a1{j+1} = 0, su contribución es nula.")
            contributions.append(Fraction(0))
            summary_values.append(Fraction(0))
            continue

        minor_label = f"M1{j+1}"
        steps.append(f"{indent}Cofactor C1{j+1} = (-1)^(1+{j+1}) * det({minor_label})")

        submatriz = _minor(matrix, 0, j)
        steps.append(f"{indent}Submatriz {minor_label} (eliminando fila 1 y columna {j+1}):")
        steps.extend(_matrix_lines(submatriz, indent + "    "))

        sub_det, sub_steps = determinante_con_pasos(submatriz, level + 1, minor_label)
        steps.extend(sub_steps)
        steps.append(f"{indent}det({minor_label}) = {_fmt(sub_det)}")

        cofactor_value = sign_factor * sub_det
        steps.append(f"{indent}C1{j+1} = ({sign_symbol}1) * {_fmt(sub_det)} = {_fmt(cofactor_value)}")

        contribucion = elemento * cofactor_value
        steps.append(f"{indent}Contribución parcial: {_fmt(elemento)} * {_fmt(cofactor_value)} = {_fmt(contribucion)}")
        contributions.append(contribucion)
        summary_values.append(contribucion)

    steps.append(separator)
    total = sum(contributions, Fraction(0))
    partes = " + ".join(_fmt_term(value) for value in summary_values)
    steps.append(f"{indent}Suma total de contribuciones: {det_label} = {partes} = {_fmt(total)}")
    return total, steps
