import os
import zipfile
import pandas as pd
import fitz  # PyMuPDF
import easyocr
import io
from PIL import Image
import numpy as np
import time

DOWNLOADS_DIR = r"C:\Users\pinak\Downloads"
ZIP_PATH = os.path.join(DOWNLOADS_DIR, "archive (1).zip")
OUTPUT_CSV = r"C:\Users\pinak\Desktop\RESUME_SCREENIG\ml\data\raw\ocr_results.csv"

def init_easyocr():
    # Load model into GPU memory
    print("Initializing EasyOCR on GPU (this may take a moment to load weights)...")
    reader = easyocr.Reader(['en'], gpu=True)
    return reader

def pdf_to_images(pdf_bytes, max_pages=3):
    """Convert the first few pages of a PDF to a list of numpy arrays for easyocr."""
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i in range(min(len(doc), max_pages)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(np.array(img))
    except Exception as e:
        print(f"Error rendering PDF: {e}")
    return images

def main():
    if not os.path.exists(ZIP_PATH):
        print(f"File not found: {ZIP_PATH}")
        return

    # Checkpoint system
    processed_files = set()
    if os.path.exists(OUTPUT_CSV):
        try:
            df_existing = pd.read_csv(OUTPUT_CSV)
            if 'Filename' in df_existing.columns:
                processed_files = set(df_existing['Filename'].tolist())
                print(f"Loaded {len(processed_files)} already processed files from checkpoint.")
        except Exception:
            pass

    # Open CSV in append mode
    file_exists = os.path.exists(OUTPUT_CSV)
    f_out = open(OUTPUT_CSV, "a", encoding="utf-8")
    if not file_exists:
        f_out.write("Filename,Category,Text\n")

    reader = init_easyocr()
    
    start_time = time.time()
    count = 0
    
    print(f"Opening {ZIP_PATH} for OCR processing...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        pdf_files = [f for f in z.namelist() if f.lower().endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDFs.")
        
        for i, pdf_file in enumerate(pdf_files):
            if pdf_file in processed_files:
                continue
                
            parts = pdf_file.split('/')
            if len(parts) >= 2:
                category_folder = parts[-2]
                category = category_folder.replace(" resumes", "").replace(" Resumes", "").strip()
                
                try:
                    pdf_bytes = z.read(pdf_file)
                    images = pdf_to_images(pdf_bytes, max_pages=2)
                    
                    text = ""
                    for img in images:
                        # detail=0 returns just a list of strings
                        results = reader.readtext(img, detail=0)
                        text += " ".join(results) + " "
                    
                    text = text.strip()
                    
                    if len(text) > 10:
                        # Escape quotes for CSV
                        clean_text = text.replace('"', '""').replace("\n", " ")
                        f_out.write(f'"{pdf_file}","{category}","{clean_text}"\n')
                        f_out.flush()
                        
                    count += 1
                    
                    if count % 10 == 0:
                        elapsed = time.time() - start_time
                        print(f"  Processed {count} files (Total progress: {i+1}/{len(pdf_files)}) - Elapsed: {elapsed/60:.1f} min")
                        
                except Exception as e:
                    print(f"Failed to process {pdf_file}: {e}")

    f_out.close()
    print("OCR Processing Complete.")

if __name__ == "__main__":
    main()
