import re
from pdf_reader import PDFReader
from xls_generator import Register, XLSGenerator
from converters.pdf_xls_converter_interface import PDFXLSConverterInterface

month_dict = {
    'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06', 
    'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
}

class Nubank2FaturaXLSConverter(PDFXLSConverterInterface):
    def __init__(self, pdf_path: str, xls_path: str, pdf_password: str = None):
        self.pdf_reader = PDFReader(pdf_path, pdf_password, skip_page_start= 2)
        self.xls_generator = XLSGenerator(xls_path)

    def _find_monetary(self, text):
        pattern = r'^\d{1,3}(?:\.\d{3})*,\d{2}$'
        return re.match(pattern, text)

    def _find_date(self, text):
        return re.search(r"^\b\d{1,2} [a-zA-Z]{3}\b$", text, re.IGNORECASE)

    def _find_parcela(self, text):
        return re.search(r'Parcela (\d+)/(\d+)', text)
    
    def _find_due(self, text):
        pattern = r"FATURA \d{1,2} [A-Z]{3} \d{4}"
        return re.search(pattern, text)
    
    def _find_credit(self, text):
        pattern = r"(Estorno de|Pagamento em)"
        return re.search(pattern, text, re.IGNORECASE)
    
    def _apply_year(self, day: str, month: str, due_year: str, due_month: str):
        if int(due_month) == 1 and int(month) == 12:
            year = str(int(due_year) - 1)
        elif int(due_month) == 12 and int(month) == 1:
            year = str(int(due_year) + 1)
        else:
            year = due_year
            
        return f'{day}/{month}/{year}'

    def _convert_date(self, text, due_year, due_month):
        day, month = re.search(r"\b(\d{1,2}) ([A-Z]{3})\b", text, re.IGNORECASE).groups()
        month = month_dict[month.lower()]
        return self._apply_year(day, month, due_year, due_month)
    
    def _remove_parcela(self, text):
        return re.sub(r' - Parcela (\d+)/(\d+)', '', text).strip()

    def convert(self):
        print('[LOG] Starting conversion...')
        
        register = None
        due_year = None
        due_month = None
        
        for page in self.pdf_reader.next_page():
            for text in page.next():
                if self._find_due(text):
                    due_match = re.search(r"FATURA \d{1,2} ([A-Z]{3}) (\d{4})", text, re.IGNORECASE)
                    due_month, due_year = due_match.groups()
                    due_month = month_dict[due_month.lower()]
                    continue
                
                if self._find_date(text):
                    date = self._convert_date(text, due_year, due_month)
                    register = Register(date=date)
                    continue
                
                if register and self._find_monetary(text):
                    filtered_text = re.sub(r'[^0-9,]', '', text)
                    value = float(filtered_text.replace(',', '.').replace(' ', ''))
                    
                    if not self._find_credit(register.description):
                        value = -value
                    
                    register.value = value
                    register.category = self._find_category(register.description)
                    
                    self.xls_generator.add_register(register)
                    
                    register = None
                    continue
                
                if register:
                    if self._find_parcela(text):
                        match = self._find_parcela(text)
                        installment, installments = match.groups()
                        register.installment = installment
                        register.installments = installments
                        text = self._remove_parcela(text)
                    
                    register.description = text if not register.description else f'{register.description} {text}'
                    continue
                    
        return self.xls_generator.generate()