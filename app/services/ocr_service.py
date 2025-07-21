# app/services/ocr_service.py
import pytesseract
import easyocr
import cv2
import numpy as np
from PIL import Image
import io

class OCRService:
    def __init__(self):
        self.easyocr_reader = easyocr.Reader(['en', 'it'])
    
    def preprocess_image_for_ocr(self, image_bytes: bytes) -> np.ndarray:
        """Preprocessa immagine per OCR ottimale"""
        # Converti in array numpy
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Converti in grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Applica denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Migliora contrasto
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Applica threshold adattivo
        threshold = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return threshold
    
    def extract_text_tesseract(self, image_bytes: bytes) -> str:
        """Estrae testo con Tesseract"""
        try:
            processed_img = self.preprocess_image_for_ocr(image_bytes)
            
            # Configurazione Tesseract per biglietti
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@.+()-_ '
            
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            return text.strip()
        except Exception as e:
            print(f"❌ Tesseract OCR error: {e}")
            return ""
    
    def extract_text_easyocr(self, image_bytes: bytes) -> str:
        """Estrae testo con EasyOCR"""
        try:
            processed_img = self.preprocess_image_for_ocr(image_bytes)
            results = self.easyocr_reader.readtext(processed_img)
            
            text_blocks = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Solo testo con confidence alta
                    text_blocks.append(text)
            
            return ' '.join(text_blocks)
        except Exception as e:
            print(f"❌ EasyOCR error: {e}")
