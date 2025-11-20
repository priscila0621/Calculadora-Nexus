from fractions import Fraction
import determinante_matriz_app as m
obj=m.DeterminanteMatrizApp.__new__(m.DeterminanteMatrizApp)
mat=[[Fraction(1),Fraction(5),Fraction(0)],[Fraction(2),Fraction(4),Fraction(-1)],[Fraction(0),Fraction(-2),Fraction(0)]]
text,det=m.DeterminanteMatrizApp._formato_procedimiento_ejemplo(obj,mat)
print('DET=',det)
print(text)
