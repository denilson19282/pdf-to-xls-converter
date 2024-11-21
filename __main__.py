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


class ConverterType(Enum):
    MERCADO_PAGO_FATURA = 'Mercado Pago Fatura'
    MERCADO_PAGO_EXTRATO = 'Mercado Pago Extrato'
    INTER_FATURA_1 = 'Inter Fatura 1'
    INTER_FATURA_2 = 'Inter Fatura 2'
    NUBANK_FATURA_1 = 'Nubank Fatura 1'
    NUBANK_FATURA_2 = 'Nubank Fatura 2'

class PDFtoXLSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to XLS Converter")
        self.root.minsize(500, 150)

        self.pdf_path = tk.StringVar()
        self.password = tk.StringVar()
        self.converter_type = tk.StringVar(value=ConverterType.MERCADO_PAGO_FATURA.value)
        
        default_pdf_path = os.path.join(os.getcwd(), 'input/mercado_pago/Fatura_MP_20240110.pdf')
        self.pdf_path.set(default_pdf_path)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Select PDF File:").grid(row=0, column=0, padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.pdf_path, width=50).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.root, text="PDF Password:").grid(row=1, column=0, padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.password, show="*", width=50).grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(self.root, text="Converter Type:").grid(row=2, column=0, padx=10, pady=10)
        self.converter_type_combobox = ttk.Combobox(self.root, textvariable=self.converter_type, values=[ct.value for ct in ConverterType])
        self.converter_type_combobox.grid(row=2, column=1, padx=10, pady=10)

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
        
    def browse_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_path.set(file_path)

    def generate_xls(self):
        pdf_path = self.pdf_path.get()
        password = self.password.get()
        
        pdf_file_name = os.path.basename(pdf_path)
        xls_file_name = os.path.splitext(pdf_file_name)[0] + '.xls'
        xls_path = os.path.join('output', xls_file_name)

        if not pdf_path:
            messagebox.showerror("Error", "Please select a PDF file path.")
            return

        try:
            selected_converter = ConverterType(self.converter_type.get())
            if selected_converter == ConverterType.MERCADO_PAGO_FATURA:
                converter = MercadoPagoFaturaXLSConverter(pdf_path, xls_path, password)
            elif selected_converter == ConverterType.MERCADO_PAGO_EXTRATO:
                converter = MercadoPagoExtratoXLSConverter(pdf_path, xls_path, password)
            elif selected_converter == ConverterType.INTER_FATURA_1:
                converter = Inter1FaturaXLSConverter(pdf_path, xls_path, password)
            elif selected_converter == ConverterType.INTER_FATURA_2:
                converter = Inter2FaturaXLSConverter(pdf_path, xls_path, password)
            elif selected_converter == ConverterType.NUBANK_FATURA_1:
                converter = Nubank1FaturaXLSConverter(pdf_path, xls_path)
            elif selected_converter == ConverterType.NUBANK_FATURA_2:
                converter = Nubank2FaturaXLSConverter(pdf_path, xls_path)
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