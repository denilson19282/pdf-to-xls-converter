from dataclasses import dataclass
from io import BytesIO
import xlwt

@dataclass
class Register:
    date: str = None
    description: str = None
    category: str = None
    value: float = None
    situation: str = None
    installment: str = None
    installments: int = None
    
class XLSFile:
    def __init__(self, file_name: str, registers: list[Register] = []):
        self.file_name = file_name
        self.registers = registers
        
        self.workbook = xlwt.Workbook()
        self.sheet = self.workbook.add_sheet('Sheet1')
        
        self._add_header()
        self._add_registers()
        
    def save_to_files(self):
        print('[LOG] Saving to file ', self.file_name)
        self.workbook.save(self.file_name)
        
    def save_to_memory(self):
        output = BytesIO()
        self.workbook.save(output)
        output.seek(0)
        return output
    
    def _add_header(self):
        header = ['Data', 'Descrição', 'Categoria', 'Valor', 'Situação', 'Parcela']
        for col_num, header_title in enumerate(header):
            self.sheet.write(0, col_num, header_title)

    def _add_registers(self):
        for row_num, register in enumerate(self.registers, start=1):
            date = register.date or ''
            description = register.description or ''
            category = register.category or ''
            value = register.value or ''
            situation = register.situation or ''
            installment = register.installment or ''
            installments = register.installments or ''
            
            if installment and installments:
                description = f'{description} (Parcela {installment} de {installments})'
            
            self.sheet.write(row_num, 0, date)
            self.sheet.write(row_num, 1, description)
            self.sheet.write(row_num, 2, category)
            self.sheet.write(row_num, 3, value)
            self.sheet.write(row_num, 4, situation)
  
class XLSGenerator:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.registers : list[Register] = []

    def add_register(self, register: Register):
        self.registers.append(register)

    def generate(self):
        self._log_registers()
        return XLSFile(self.file_name, self.registers)
    
    def _log_registers(self):
        print('[LOG][REGISTERS]', len(self.registers), 'registers found')
        for register in self.registers:
            print('[LOG][REGISTER] ', register)
            
        print('[LOG] Total value: ', sum([r.value for r in self.registers]))