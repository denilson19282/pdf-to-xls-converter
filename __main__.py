import os
import tkinter as tk
import traceback
import pandas as pd

from enum import Enum
from tkinter import filedialog, messagebox, ttk

from converters.mercado_pago_extrato_xls_converter import MercadoPagoExtratoXLSConverter
from converters.mercado_pago_fatura_xls_converter import MercadoPagoFaturaXLSConverter
from converters.inter_1_fatura_xls_converter import Inter1FaturaXLSConverter
from converters.inter_2_fatura_xls_converter import Inter2FaturaXLSConverter
from converters.nubank_1_fatura_xls_converter import Nubank1FaturaXLSConverter
from converters.nubank_2_fatura_xls_converter import Nubank2FaturaXLSConverter
from converters.bradesco_fatura_xls_converter import BradescoFaturaXLSConverter

class ConverterType(Enum):
    MERCADO_PAGO_FATURA = 'Mercado Pago Fatura (PDF)'
    MERCADO_PAGO_EXTRATO = 'Mercado Pago Extrato (PDF)'
    INTER_FATURA_1 = 'Inter Fatura 1 (PDF)'
    INTER_FATURA_2 = 'Inter Fatura 2 (PDF)'
    NUBANK_FATURA_1 = 'Nubank Fatura 1 (PDF)'
    NUBANK_FATURA_2 = 'Nubank Fatura 2 (PDF)'
    BRADESCO_FATURA = 'Bradesco Fatura (CSV)'

class PDFtoXLSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XLS Converter")
        self.root.minsize(500, 150)

        self.file_path = tk.StringVar()
        self.password = tk.StringVar()
        self.due_year = tk.StringVar()
        self.due_month = tk.StringVar()
        self.converter_type = tk.StringVar(value=ConverterType.MERCADO_PAGO_FATURA.value)
        
        default_file_path = os.path.join(os.getcwd(), 'input/mercado_pago/Fatura_MP_20240110.pdf')
        self.file_path.set(default_file_path)

        self.due_year.set('2025')
        self.due_month.set('03')

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Select File:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        tk.Button(self.root, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=10, pady=10, sticky="w")

        tk.Label(self.root, text="PDF Password:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.password, show="*", width=50).grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        tk.Label(self.root, text="Converter Type:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.converter_type_combobox = ttk.Combobox(self.root, textvariable=self.converter_type, values=[ct.value for ct in ConverterType])
        self.converter_type_combobox.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.converter_type_combobox.bind("<<ComboboxSelected>>", self.on_converter_type_change)

        tk.Button(self.root, text="Convert", command=self.generate_xls).grid(row=4, column=1, padx=10, pady=10)

        self.table_frame = tk.Frame(self.root)
        self.table_frame.grid(row=5, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")
        
        self.total_sum_label = tk.Label(self.root, text="Total Sum: 0")
        self.total_sum_label.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        self.total_sum_label.grid_remove()
        
        self.save_button = tk.Button(self.root, text="Save Table", command=self.save_xls)
        self.save_button.grid(row=6, column=3, padx=10, pady=10, sticky="e")
        self.save_button.grid_remove() 
        
        self.root.grid_rowconfigure(5, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_columnconfigure(4, weight=1)
        self.root.grid_columnconfigure(5, weight=1)

        self.due_year_label = tk.Label(self.root, text="Due Year:")
        self.due_year_entry = tk.Entry(self.root, textvariable=self.due_year,  width=10)
        self.due_month_label = tk.Label(self.root, text="Due Month:")
        self.due_month_entry = tk.Entry(self.root, textvariable=self.due_month, width=10)
    
    def on_converter_type_change(self, event):
        selected_converter = self.converter_type.get()
        if selected_converter == ConverterType.BRADESCO_FATURA.value:
            self.due_year_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            self.due_year_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
            self.due_month_label.grid(row=3, column=2, padx=10, pady=10, sticky="w")
            self.due_month_entry.grid(row=3, column=3, padx=10, pady=10, sticky="w")
        else:
            self.due_year_label.grid_remove()
            self.due_year_entry.grid_remove()
            self.due_month_label.grid_remove()
            self.due_month_entry.grid_remove()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF and CSV files", "*.pdf *.csv")])
        if file_path:
            self.file_path.set(file_path)

    def generate_xls(self):
        file_path = self.file_path.get()
        password = self.password.get()
        due_year = self.due_year_entry.get()
        due_month = self.due_month_entry.get()
        
        origin_file_name = os.path.basename(file_path)
        xls_file_name = os.path.splitext(origin_file_name)[0] + '.xls'
        xls_path = os.path.join('output', xls_file_name)

        if not file_path:
            messagebox.showerror("Error", "Please select a file path.")
            return

        try:
            selected_converter = ConverterType(self.converter_type.get())
            if selected_converter == ConverterType.MERCADO_PAGO_FATURA:
                converter = MercadoPagoFaturaXLSConverter(file_path, xls_path, password)
            elif selected_converter == ConverterType.MERCADO_PAGO_EXTRATO:
                converter = MercadoPagoExtratoXLSConverter(file_path, xls_path, password)
            elif selected_converter == ConverterType.INTER_FATURA_1:
                converter = Inter1FaturaXLSConverter(file_path, xls_path, password)
            elif selected_converter == ConverterType.INTER_FATURA_2:
                converter = Inter2FaturaXLSConverter(file_path, xls_path, password)
            elif selected_converter == ConverterType.NUBANK_FATURA_1:
                converter = Nubank1FaturaXLSConverter(file_path, xls_path)
            elif selected_converter == ConverterType.NUBANK_FATURA_2:
                converter = Nubank2FaturaXLSConverter(file_path, xls_path)
            elif selected_converter == ConverterType.BRADESCO_FATURA:
                converter = BradescoFaturaXLSConverter(file_path, xls_path, due_year, due_month)
            else:
                raise Exception("Converter not found")

            self.xls_file = converter.convert()
            
            registers = self.xls_file.registers
            total_sum = sum([r.value for r in registers])
            
            self.total_sum_label.config(text=f"Total Sum: {total_sum}")
            self.total_sum_label.grid()
            self.save_button.grid()
            
            self.display_xls()
        except Exception as e:
            print(e)
            traceback.print_exc()
            messagebox.showerror("Error", f"An error occurred: {e}")

    def display_xls(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        output = self.xls_file.save_to_memory()
        df = pd.read_excel(output)
        cols = list(df.columns)
        tree = ttk.Treeview(self.table_frame, columns=cols, show='headings', height=5)
        
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        column_width = {
            'Data': 70,
            'Descrição': 240,
            'Categoria': 70,
            'Valor': 70,
            'Situação': 70,
            'Parcela': 70,
        }
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=column_width.get(col, 100))

        for index, row in df.iterrows():
            tree.insert("", "end", values=list(row))

        tree.pack(fill='both', expand=True)

    
    def save_xls(self):
        if not self.xls_file:
            messagebox.showerror("Error", "No XLS file generated.")
            return
        
        self.xls_file.save_to_files()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFtoXLSApp(root)
    root.mainloop()