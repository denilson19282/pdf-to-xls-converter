import re
from pdf_reader import PDFReader
from xls_generator import Register, XLSGenerator
from converters.xls_converter_interface import XLSConverterInterface

class MercadoPagoFaturaXLSConverter(XLSConverterInterface):
    def __init__(self, pdf_path: str, xls_path: str, pdf_password: str = None):
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("The provided file is not a PDF file.")
        
        self.pdf_reader = PDFReader(pdf_path, pdf_password, skip_page_start = 1, skip_page_end = 3, use_ocr = True)
        self.xls_generator = XLSGenerator(xls_path)

    def _find_entry(self, text):
        pattern = r"^\d{2}/\d{2}.*[0-9]+,[0-9]{2}$"
        return re.match(pattern, text)
    
    def _find_unwanted_entry(self, text):
        unwanted_pattern = r"Pagamento da fatura de \w+/[0-9]{4}"
        return re.search(unwanted_pattern, text)
    
    def _find_credit_entry(self, text):
        if "Crédito concedido" in text:
            return True
        return False
    
    def _find_due(self, text):
        pattern = r"Vencimento: \d{2}/\d{2}/\d{4}"
        return re.search(pattern, text)
    
    def _apply_year(self, day: str, month: str, due_year: str, due_month: str):
        if int(due_month) == 1 and int(month) == 12:
            year = str(int(due_year) - 1)
        elif int(due_month) == 12 and int(month) == 1:
            year = str(int(due_year) + 1)
        else:
            year = due_year

        return f'{day}/{month}/{year}'
    
    def convert(self):
        print('[LOG] Starting conversion...')

        year_due = None
        month_due = None
        for page in self.pdf_reader.next_page():
            for text in page.next():
                if self._find_due(text):
                    year_due = text.split('/')[2]
                    month_due = text.split('/')[1]
                    continue
                
                if self._find_unwanted_entry(text):
                    continue
                
                if not self._find_entry(text):
                    continue
                
                is_credit = self._find_credit_entry(text)
                
                date_pattern = r"^\d{2}/\d{2}"
                parcela_pattern = r"Parcela (\d+) de (\d+)"
                value_pattern = r"R\$ [0-9.,]+,[0-9]{2}$"
                
                date_match = re.search(date_pattern, text)
                parcela_match = re.search(parcela_pattern, text)
                value_match = re.search(value_pattern, text)
                
                installment, installments = parcela_match.groups() if parcela_match else (None, None)
                value = value_match.group(0) if value_match else None
                
                if value:
                    filtered_value = re.sub(r'[^0-9,]', '', value)
                    value = float(filtered_value.replace(',', '.')) * (1 if is_credit else -1)
                
                if date_match:
                    day, month = date_match.group(0).split('/')
                    if installment:
                        month_expected = (int(month) + int(installment) - 1) % 12
                        month = str(month_expected if month_expected != 0 else 12)
                        month = month.zfill(2)
                
                date = self._apply_year(day, month, year_due, month_due)
                description_start = date_match.end() if date_match else 0
                description_end = parcela_match.start() if parcela_match else value_match.start() if value_match else len(text)
                description = text[description_start:description_end].strip()
                category = self._find_category(description)
                                
                register = Register()
                register.date = date
                register.description = description
                register.installment = installment
                register.installments = installments
                register.value = value
                register.category = category
                
                self.xls_generator.add_register(register)
                
        return self.xls_generator.generate()