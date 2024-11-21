import re
from pdf_reader import PDFReader
from xls_generator import Register, XLSGenerator
from converters.pdf_xls_converter_interface import PDFXLSConverterInterface

month_dict = {
    'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06', 
    'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
}

class MercadoPagoExtratoXLSConverter(PDFXLSConverterInterface):
    def __init__(self, pdf_path: str, xls_path: str, pdf_password: str = None):
        self.pdf_reader = PDFReader(pdf_path, pdf_password)
        self.xls_generator = XLSGenerator(xls_path)

    def _find_table_start(self, text):
        return text == 'DETALHE DOS MOVIMENTOS'
    
    def _find_table_end(self, text):
        return False
      
    def _find_operation_id(self, text):
      pattern = r'^\d+$'
      return re.match(pattern, text)
    
    def _find_monetary(self, text):
        pattern = r'^R\$ -?\d{1,3}(?:\.\d{3})*,\d{2}$'
        return re.match(pattern, text)

    def _find_date(self, text):
        return re.search(r"\b\d{2}-\d{2}-\d{4}\b", text)

    def _convert_date(self, text):
        day, month, year = re.search(r"(\d{2})-(\d{2})-(\d{4})", text).groups()
        return f'{day}/{month}/{year}'
    
    def _remove_parcela(self, text):
        return re.sub(r'\(Parcela \d+ de \d+\)', '', text).strip()
    
    def _extract_description(self, text):
        match = re.search(r"(\d{2}-\d{2}-\d{4})(.*)", text)
        date, description = match.groups()
        return description.strip() if description else None

    def convert(self):
        print('[LOG] Starting conversion...')
        
        register = None
        is_table = False

        for page in self.pdf_reader.next_page():
            for text in page.next():
                if self._find_table_start(text):
                    is_table = True
                    continue
                
                if self._find_table_end(text):
                    is_table = False
                    continue
                  
                if self._find_operation_id(text):
                    continue
                
                if self._find_date(text) and is_table:
                    date = self._convert_date(text)
                    description = self._extract_description(text)
                    register = Register(date=date, description=description)
                    continue
                
                if self._find_monetary(text) and register:
                    filtered_text = re.sub(r'[^0-9,-]', '', text)
                    value = float(filtered_text.replace(',', '.').replace(' ', ''))
                    
                    register.value = value
                    register.category = self._find_category(register.description)
                    
                    self.xls_generator.add_register(register)
                    
                    register = None
                    continue
                
                if register:
                    register.description = text if not register.description else f'{register.description.strip()} {text}'
                    continue
                    
        return self.xls_generator.generate()