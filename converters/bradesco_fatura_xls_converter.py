import re
from pdf_reader import PDFReader
from xls_generator import Register, XLSGenerator
from converters.xls_converter_interface import XLSConverterInterface

class BradescoFaturaXLSConverter(XLSConverterInterface):
    def __init__(self, csv_path: str, xls_path: str, due_year: str, due_month: str):
        if not csv_path.lower().endswith('.csv'):
            raise ValueError("The provided file is not a CSV file.")

        self.due_year = due_year
        self.due_month = due_month
        self.csv_path = csv_path
        self.xls_generator = XLSGenerator(xls_path)

    def _find_parcela(self, text):
        return re.search(r'(\d+)/(\d+)', text)
    
    def _remove_parcela(self, text):
        return re.sub(r'(\d+)/(\d+)', '', text).strip()

    def convert(self):
        print('[LOG] Starting conversion...')
        
        register = None
        is_data_section = False

        with open(self.csv_path, 'r') as csv_file:
            for line in csv_file:
                line = line.strip()

                print(f'[LOG] Processing line ({is_data_section}): {line}')

                if not line:
                    is_data_section = False
                    continue
                
                if line.startswith("Data;Hist"):
                    is_data_section = True
                    continue

                if is_data_section:
                    columns = line.split(';')
                    if len(columns) != 4:
                        continue

                    date, description, _, value = columns

                    unwanted_entries = ['SALDO ANTERIOR', 'PAGTO. POR DEB EM C/C', 'PAG BOLETO BANCARIO']
                    if any(entry in description for entry in unwanted_entries):
                        continue

                    date = f"{date}/{self.due_year}"
                    value = float(value.replace('.', '').replace(',', '.').replace(' ', ''))
                    category = self._find_category(description)
                    installment = None
                    installments = None

                    if self._find_parcela(description):
                        match = self._find_parcela(description)
                        installment, installments = match.groups()
                        description = self._remove_parcela(description)

                    register = Register()
                    register.installment = installment
                    register.installments = installments
                    register.description = description
                    register.date = date
                    register.value = value
                    register.category = category

                    self.xls_generator.add_register(register)
                    
        return self.xls_generator.generate()