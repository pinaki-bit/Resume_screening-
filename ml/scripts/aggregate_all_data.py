import os
import json
import zipfile
import pandas as pd
import io
import time
from PyPDF2 import PdfReader

DOWNLOADS_DIR = r"C:\Users\pinak\Downloads"
OUTPUT_FILE = r"C:\Users\pinak\Desktop\RESUME_SCREENIG\ml\data\raw\master_combined.csv"

def extract_pdf_text_from_bytes(pdf_bytes):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + " "
        return text.strip()
    except Exception:
        return ""

def process_archive_1(zip_path):
    print(f"Processing {zip_path} (Raw PDFs)... This will take a while.")
    records = []
    if not os.path.exists(zip_path):
        print(f"  Skipping: {zip_path} not found.")
        return pd.DataFrame()
        
    with zipfile.ZipFile(zip_path, 'r') as z:
        pdf_files = [f for f in z.namelist() if f.lower().endswith('.pdf')]
        print(f"  Found {len(pdf_files)} PDFs in {zip_path}")
        
        for i, pdf_file in enumerate(pdf_files):
            if i > 0 and i % 100 == 0:
                print(f"    Processed {i}/{len(pdf_files)} PDFs...")
            # Folder name is category: "Resumes PDF/Accountant resumes/Image_10.pdf"
            parts = pdf_file.split('/')
            if len(parts) >= 2:
                category_folder = parts[-2]
                category = category_folder.replace(" resumes", "").replace(" Resumes", "").strip()
                
                try:
                    pdf_bytes = z.read(pdf_file)
                    text = extract_pdf_text_from_bytes(pdf_bytes)
                    if len(text) > 50:  # Valid text found
                        records.append({"Category": category, "Text": text})
                except Exception as e:
                    pass
    
    df = pd.DataFrame(records)
    print(f"  Extracted {len(df)} valid records from {zip_path}")
    return df

def process_csv_zip(zip_path, target_csv_name, category_col, text_col):
    print(f"Processing {zip_path} looking for {target_csv_name}...")
    if not os.path.exists(zip_path):
        print(f"  Skipping: {zip_path} not found.")
        return pd.DataFrame()
        
    with zipfile.ZipFile(zip_path, 'r') as z:
        csv_files = [f for f in z.namelist() if target_csv_name.lower() in f.lower()]
        if not csv_files:
            print(f"  Target CSV not found in {zip_path}")
            return pd.DataFrame()
            
        csv_file = csv_files[0]
        try:
            with z.open(csv_file) as f:
                df = pd.read_csv(f)
                
                # Try to find columns
                found_cat = None
                found_text = None
                
                for col in df.columns:
                    if category_col.lower() in col.lower():
                        found_cat = col
                    if text_col.lower() in col.lower() and "html" not in col.lower():
                        found_text = col
                        
                if found_cat and found_text:
                    df = df[[found_cat, found_text]].rename(columns={found_cat: "Category", found_text: "Text"})
                    # Drop NAs
                    df = df.dropna(subset=["Text", "Category"])
                    print(f"  Extracted {len(df)} records from {zip_path}")
                    return df
                else:
                    print(f"  Could not find matching columns in {csv_file}")
        except Exception as e:
            print(f"  Error reading {csv_file}: {e}")
            
    return pd.DataFrame()

def process_train_csv():
    path = os.path.join(DOWNLOADS_DIR, "train.csv")
    print(f"Processing {path}...")
    if not os.path.exists(path):
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    if "Category" in df.columns and "Text" in df.columns:
        df = df[["Category", "Text"]]
        print(f"  Extracted {len(df)} records from train.csv")
        return df
    return pd.DataFrame()

def main():
    start_time = time.time()
    all_dfs = []
    
    # 1. train.csv
    all_dfs.append(process_train_csv())
    
    # 2. archive (3).zip -> Resume/Resume.csv
    all_dfs.append(process_csv_zip(os.path.join(DOWNLOADS_DIR, "archive (3).zip"), "resume.csv", "Category", "Resume_str"))
    
    # 3. archive (5).zip -> Resume dataset.csv
    all_dfs.append(process_csv_zip(os.path.join(DOWNLOADS_DIR, "archive (5).zip"), "resume dataset.csv", "category", "Text"))
    
    # 4. archive (1).zip -> 2GB of Raw PDFs
    # NOTE: Skipped because inspection revealed these are scanned image PDFs (Image_10.pdf, etc)
    # PyPDF2 cannot extract text from images without Tesseract OCR.
    # all_dfs.append(process_archive_1(os.path.join(DOWNLOADS_DIR, "archive (1).zip")))
    
    # Combine everything
    master_df = pd.concat(all_dfs, ignore_index=True)
    initial_len = len(master_df)
    print(f"\nTotal combined rows: {initial_len}")
    
    # Clean up and drop exact duplicates
    master_df["Text"] = master_df["Text"].astype(str).str.strip()
    master_df = master_df[master_df["Text"].str.len() > 50]  # Filter junk
    master_df = master_df.drop_duplicates(subset=["Text"])
    
    final_len = len(master_df)
    print(f"Total valid unique rows after deduplication: {final_len} (Dropped {initial_len - final_len} duplicates/junk)")
    
    # Save to disk
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    master_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved master combined dataset to {OUTPUT_FILE}")
    print(f"Total time: {(time.time() - start_time)/60:.1f} minutes.")

if __name__ == "__main__":
    main()
