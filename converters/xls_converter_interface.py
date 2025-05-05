from abc import ABC, abstractmethod

from xls_generator import XLSFile

class XLSConverterInterface(ABC):
    @abstractmethod
    def convert(self) -> XLSFile:
        pass
    
    def _find_category(self, text):
        if not text:
            return None
        
        # Category for credit card transactions
        if 'IFD*'.lower() in text.lower():
            return 'iFood'
        if 'ifood'.lower() in text.lower():
            return 'iFood'
        if 'UBER'.lower() in text.lower():
            return 'Transporte'
        if '99APP'.lower() in text.lower():
            return 'Transporte'
        if 'GITHUB INC. S'.lower() in text.lower():
            return 'Assinaturas e Serviços'
        if 'NETFLIX.COM'.lower() in text.lower():
            return 'Assinaturas e Serviços'
        if 'MP *HBOMAXASSIN'.lower() in text.lower():
            return 'Assinaturas e Serviços'
        if 'Invoice2go'.lower() in text.lower():
            return 'Assinaturas e Serviços'
        if 'Mobills'.lower() in text.lower():
            return 'Assinaturas e Serviços'
        if 'Claro Pgto'.lower() in text.lower():
            return 'Casa'
        if 'Steam'.lower() in text.lower():
            return 'Lazer e Hobbies'
        if 'CENTERPLEXCINEMAS'.lower() in text.lower():
            return 'Lazer e Hobbies'
        if '286MATEUS'.lower() in text.lower():
            return 'Mercado'
        if 'ATAKAREJO'.lower() in text.lower():
            return 'Mercado'
        if 'PAGUE MENOS'.lower() in text.lower():
            return 'Saúde'
        if 'ORTHODONTIC'.lower() in text.lower():
            return 'Saúde'
        
        # Category for bank transactions
        if 'Rendimentos' in text:
            return 'Rendimentos'
        if 'Pagamento de contas' in text:
            return 'Casa'
       
        return None