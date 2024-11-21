import fitz
import pytesseract
from PIL import Image
import numpy as np
import cv2

class PDFReader:
    def __init__(self, doc_name: str, password : str = None, dictionary: dict = None, skip_page_start: int = None, skip_page_end: int = None, use_ocr: bool = False):
        self.doc_name = doc_name
        self.password = password
        self.dictionary = dictionary
        self.skip_page_start = skip_page_start
        self.skip_page_end = skip_page_end
        self.use_ocr = use_ocr
    
    def _correct_text(self, text):
        if not self.dictionary:
            return text
          
        corrected_chars = []
        for char in text:
            corrected_chars.append(self.dictionary.get(char, char))
            
        return ''.join(corrected_chars)
    
    def _perform_ocr(self, page):
        pix = page.get_pixmap(matrix=fitz.Matrix(8, 8))
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert PIL image to OpenCV format
        open_cv_image = np.array(image)
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Apply dilation and erosion to remove noise
        kernel = np.ones((1, 1), np.uint8)
        img = cv2.dilate(thresh, kernel, iterations=1)
        img = cv2.erode(img, kernel, iterations=1)
        thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Remove horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40,1))
        remove_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        cnts = cv2.findContours(remove_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(img, [c], -1, (255,255,255), 5)
            
        # Remove vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,40))
        remove_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(img, [c], -1, (255,255,255), 5)
            
        # Convert back to PIL image
        image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        image.save(f'ocr_image_{page.number}.png')
        
        text = pytesseract.image_to_string(image, config='--psm 6')
        return self._correct_text(text)
    
    def next_page(self):
        doc = fitz.open(self.doc_name)
        if doc.is_encrypted:
            if self.password:
                doc.authenticate(self.password)
            else:
                raise Exception("Document is encrypted and no password was provided")
        
        skip_page_end = -self.skip_page_end if self.skip_page_end else None
        pages = list(doc.pages())[self.skip_page_start:skip_page_end]
        for page in pages:
            if self.use_ocr:
                text = self._perform_ocr(page)
            else:
                text = page.get_text("text")
            corrected_text = self._correct_text(text)
            yield Page(corrected_text)
            
class Page:
    def __init__(self, text: str):
        self.text = text
        self.tokens = text.split('\n')

    def next(self):
        for token in self.tokens:
            print('[LOG][TEXT]', token)
            yield token