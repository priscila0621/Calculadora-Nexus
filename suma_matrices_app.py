import tkinter as tk
from tkinter import ttk, messagebox
from fractions import Fraction


class SumaMatricesApp:
    def __init__(self, root, volver_callback):
        self.root = root
        self.volver_callback = volver_callback

        self.root.title("Suma de Matrices")
        self.root.geometry("900x700")
        self.root.configure(bg="#ffe4e6")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", font=("Segoe UI", 12), background="#ffe4e6", foreground="#b91c1c")
        style.configure("Primary.TButton", font=("Segoe UI", 12, "bold"), padding=8,
                        background="#fbb6ce", foreground="#fff")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])
        style.configure("Back.TButton", font=("Segoe UI", 12, "bold"), padding=6,
                        background="#fecaca", foreground="#b91c1c")
        style.map("Back.TButton",
                  background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])

        self.num_matrices = 0
        self.rows = 0
        self.cols = 0
        self.matrices = []
        self.current_matrix = 0
        self.entries = []

        self.main_frame = ttk.Frame(self.root, padding=12)
        self.main_frame.pack(fill="both", expand=True)

        self.error_label = None

        self.show_welcome()

    # ---------------- Helpers ----------------
    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def add_back_button(self, parent_frame=None):
        container = parent_frame if parent_frame is not None else self.main_frame
        back = ttk.Button(container, text="Volver al inicio", style="Back.TButton",
                          command=self._volver_al_inicio)
        back.pack(side="bottom", pady=8)

    def _volver_al_inicio(self):
        try:
            self.volver_callback()
        except Exception:
            pass
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass

    def _parse_fraction(self, s):
        s = s.strip()
        if s == "":
            raise ValueError("Vacío")
        s = s.replace(",", ".")
        return Fraction(s)

    # ---------------- Pantalla bienvenida ----------------
    def show_welcome(self):
        self.clear_main()
        ttk.Label(self.main_frame, text="Suma de Matrices", font=("Segoe UI", 18, "bold"),
                  background="#ffe4e6", foreground="#b91c1c").pack(pady=12)
        ttk.Label(self.main_frame, text="Suma hasta N matrices con las mismas dimensiones",
                  font=("Segoe UI", 12), background="#ffe4e6", foreground="#7f1d1d").pack(pady=6)

        start_btn = ttk.Button(self.main_frame, text="Comenzar", style="Primary.TButton",
                               command=self.ask_num_and_dimensions)
        start_btn.pack(pady=20)
        self.add_back_button(self.main_frame)

    # ---------------- Configuración ----------------
    def ask_num_and_dimensions(self):
        self.clear_main()
        ttk.Label(self.main_frame, text="Configuración - Cantidad y dimensiones", font=("Segoe UI", 14, "bold"),
                  background="#ffe4e6", foreground="#b91c1c").pack(pady=10)

        frame = ttk.Frame(self.main_frame, padding=8)
        frame.pack(pady=8)

        ttk.Label(frame, text="¿Cuántas matrices deseas sumar?", background="#ffe4e6").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.num_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.num_var, width=6, font=("Segoe UI", 12), bg="#fff0f5").grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(frame, text="Filas:", background="#ffe4e6").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.row_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.row_var, width=6, font=("Segoe UI", 12), bg="#fff0f5").grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(frame, text="Columnas:", background="#ffe4e6").grid(row=1, column=2, padx=6, pady=6, sticky="w")
        self.col_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.col_var, width=6, font=("Segoe UI", 12), bg="#fff0f5").grid(row=1, column=3, padx=6, pady=6)

        ttk.Button(self.main_frame, text="Siguiente", style="Primary.TButton",
                   command=self.save_num_and_dimensions).pack(pady=12)

        self.error_label = ttk.Label(self.main_frame, text="", foreground="red", background="#ffe4e6")
        self.error_label.pack()
        self.add_back_button(self.main_frame)

    def save_num_and_dimensions(self):
        try:
            n = int(self.num_var.get())
            r = int(self.row_var.get())
            c = int(self.col_var.get())
            if n < 2 or r <= 0 or c <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Ingresa números válidos (mínimo 2 matrices, dimensiones > 0)")
            return
        self.num_matrices, self.rows, self.cols = n, r, c
        self.matrices, self.current_matrix = [], 0
        self.ask_matrix_values()

    # ---------------- Ingreso de valores ----------------
    def ask_matrix_values(self):
        self.clear_main()
        ttk.Label(self.main_frame, text=f"Matriz {self.current_matrix+1} de {self.num_matrices}",
                  font=("Segoe UI", 14, "bold"), background="#ffe4e6", foreground="#b91c1c").pack(pady=8)

        grid_frame = ttk.Frame(self.main_frame)
        grid_frame.pack(pady=6)

        self.entries = []
        for i in range(self.rows):
            row_entries = []
            for j in range(self.cols):
                e = tk.Entry(grid_frame, width=8, justify="center", font=("Segoe UI", 12), bg="#fff0f5")
                e.grid(row=i, column=j, padx=4, pady=4)
                row_entries.append(e)
            self.entries.append(row_entries)

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        if self.current_matrix > 0:
            ttk.Button(btn_frame, text="Anterior", command=self.go_previous).grid(row=0, column=0, padx=6)

        ttk.Button(btn_frame, text="Confirmar Matriz", style="Primary.TButton",
                   command=self.save_matrix).grid(row=0, column=1, padx=6)

        self.error_label = ttk.Label(self.main_frame, text="", foreground="red", background="#ffe4e6")
        self.error_label.pack(pady=6)
        self.add_back_button(self.main_frame)

    def go_previous(self):
        self.current_matrix -= 1
        self.ask_matrix_values()

    def save_matrix(self):
        try:
            mat = []
            for i in range(self.rows):
                fila = []
                for j in range(self.cols):
                    val = self._parse_fraction(self.entries[i][j].get())
                    fila.append(val)
                mat.append(fila)
            if self.current_matrix < len(self.matrices):
                self.matrices[self.current_matrix] = mat
            else:
                self.matrices.append(mat)
        except Exception as e:
            self.error_label.config(text=f"Error en los datos: {e}")
            return

        if self.current_matrix + 1 < self.num_matrices:
            self.current_matrix += 1
            self.ask_matrix_values()
        else:
            self.show_result()

    # ---------------- Resultado ----------------
    def show_result(self):
        self.clear_main()
        ttk.Label(self.main_frame, text="Resumen de matrices ingresadas",
                  font=("Segoe UI", 16, "bold"),
                  background="#ffe4e6", foreground="#b91c1c").pack(pady=10)

        # Contenedor centrado para matrices
        center_frame = ttk.Frame(self.main_frame)
        center_frame.pack(pady=10)

        for idx, mat in enumerate(self.matrices, start=1):
            ttk.Label(center_frame, text=f"Matriz {idx}", font=("Segoe UI", 12, "bold"),
                      background="#ffe4e6", foreground="#7f1d1d").pack(pady=4)
            self._display_matrix(center_frame, mat)

        # Botones debajo
        btns = ttk.Frame(self.main_frame)
        btns.pack(pady=15)
        ttk.Button(btns, text="Calcular suma", style="Primary.TButton",
                   command=self.calculate_sum).grid(row=0, column=0, padx=8)
        ttk.Button(btns, text="Reiniciar", style="Back.TButton",
                   command=self.ask_num_and_dimensions).grid(row=0, column=1, padx=8)

        self.add_back_button(self.main_frame)

    def calculate_sum(self):
        result = [[sum(m[i][j] for m in self.matrices) for j in range(self.cols)] for i in range(self.rows)]

        ttk.Label(self.main_frame, text="Matriz resultante",
                  font=("Segoe UI", 14, "bold"),
                  background="#ffe4e6", foreground="#b91c1c").pack(pady=10)

        self._display_matrix(self.main_frame, result)

        ttk.Label(self.main_frame, text="Detalle de la suma por posición",
                  font=("Segoe UI", 13, "bold"),
                  background="#ffe4e6", foreground="#7f1d1d").pack(pady=8)

        self._display_sum_details(self.main_frame, result)

    def _display_matrix(self, parent, matrix):
        # Muestra una matriz delimitada con corchetes altos estilo libro
        frame = ttk.Frame(parent)
        frame.pack(pady=6)
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        for i, row in enumerate(matrix):
            # Corchete izquierdo por fila
            if i == 0:
                left, right = "⎡", "⎤"
            elif i == rows - 1:
                left, right = "⎣", "⎦"
            else:
                left, right = "⎢", "⎥"
            tk.Label(frame, text=left, font=("Consolas", 16), bg="#ffe4e6").grid(row=i, column=0, padx=(2, 4))
            for j, val in enumerate(row):
                tk.Label(frame, text=str(val), width=8, font=("Segoe UI", 12),
                         bg="#fff0f5", relief="solid").grid(row=i, column=j+1, padx=3, pady=3)
            tk.Label(frame, text=right, font=("Consolas", 16), bg="#ffe4e6").grid(row=i, column=cols+1, padx=(4, 2))

    def _display_sum_details(self, parent, result):
        container = ttk.Frame(parent)
        container.pack(pady=6, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(container, wrap="word", height=15, width=100,
                              font=("Segoe UI", 11), bg="#fff0f5")
        text_widget.pack(side="left", fill="both", expand=True)

        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        for i in range(self.rows):
            for j in range(self.cols):
                parts = " + ".join(str(m[i][j]) for m in self.matrices)
                expr = f"[{i+1},{j+1}]: {parts} = {result[i][j]}\n"
                text_widget.insert("end", expr)

        text_widget.config(state="disabled")
