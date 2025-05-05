import re
from pdf_reader import PDFReader
from xls_generator import Register, XLSGenerator
from converters.xls_converter_interface import XLSConverterInterface

month_dict = {
    'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06', 
    'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
}
863163
class Inter2FaturaXLSConverter(XLSConverterInterface):
    def __init__(self, pdf_path: str, xls_path: str, pdf_password: str = None):
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("The provided file is not a PDF file.")
        
        self.pdf_reader = PDFReader(pdf_path, pdf_password, skip_page_start = 1, skip_page_end = 3)
        self.xls_generator = XLSGenerator(xls_path)

    def _find_monetary(self, text):
        pattern = r'^\+?\s*R\$ \d{1,3}(?:\.\d{3})*,\d{2}$'
        return re.match(pattern, text)

    def _find_date(self, text):
        return re.search(r"\b\d{1,2}(?: de)? [a-z]{3}\. \d{4}\b", text)

    def _find_parcela(self, text):
        return re.search(r'\(Parcela (\d+) de (\d+)\)', text)
    
    def _find_unwanted(self, text: str):
        return text.lower() in ['Pagamento On Line'.lower(), 'Pagamento De Fatura'.lower()]

    def _convert_date(self, text):
        day, month, year = re.search(r"(\d{1,2})(?: de)? ([a-z]{3})\. (\d{4})", text).groups()
        month = month_dict[month]
        return f'{day}/{month}/{year}'
    
    def _remove_parcela(self, text):
        return re.sub(r'\(Parcela \d+ de \d+\)', '', text).strip()

    def convert(self):
        print('[LOG] Starting conversion...')
        
        register = None

        for page in self.pdf_reader.next_page():
            for text in page.next():
                if text in ["-"]:
                    continue
                
                if self._find_unwanted(text):
                    register = None
                    continue
                
                if self._find_date(text):
                    date = self._convert_date(text)
                    register = Register(date=date)
                    continue
                
                if self._find_monetary(text) and register:                    
                    filtered_text = re.sub(r'[^0-9,]', '', text)
                    value = float(filtered_text.replace(',', '.').replace(' ', ''))
                    
                    if not '+' in text:
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
                    
                    register.description = text
                    continue
                    
        return self.xls_generator.generate()