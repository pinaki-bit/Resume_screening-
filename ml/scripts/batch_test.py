import argparse
import json
import logging
import os
import random
import sys
import time
from tempfile import TemporaryDirectory
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/api/v1"

def authenticate(email, password):
    logger.info(f"Authenticating as {email}...")
    res = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password}
    )
    res.raise_for_status()
    token = res.json()["access_token"]
    logger.info("Authentication successful.")
    return token

def create_job(token, title, department, requirements):
    logger.info(f"Creating job: {title}")
    res = requests.post(
        f"{API_URL}/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "department": department,
            "requirements": requirements,
            "status": "open"
        }
    )
    res.raise_for_status()
    job = res.json()
    logger.info(f"Job created with ID: {job['id']}")
    return job

def create_pdf_from_text(text, filepath):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in text.split('\n'):
        # Just simple text layout for extraction
        line = line.strip()
        if not line:
            continue
        # Split very long lines roughly
        while len(line) > 100:
            c.drawString(50, y, line[:100])
            y -= 15
            line = line[100:]
            if y < 50:
                c.showPage()
                y = height - 50
        c.drawString(50, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()

def get_resumes_from_csv(csv_path, category, target_dir, num_resumes):
    logger.info(f"Loading {num_resumes} '{category}' resumes from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df[df['Category'] == category]
    
    if len(df) == 0:
        logger.error(f"No resumes found for category '{category}'!")
        sys.exit(1)
        
    df = df.sample(n=min(num_resumes, len(df)))
    
    extracted_paths = []
    for i, row in enumerate(df.itertuples()):
        text = str(row.Text)
        filename = f"{category.replace(' ', '_')}_{i}.pdf"
        filepath = os.path.join(target_dir, filename)
        create_pdf_from_text(text, filepath)
        extracted_paths.append(filepath)
        
    logger.info(f"Generated {len(extracted_paths)} text-based PDFs.")
    return extracted_paths

def upload_resume(token, file_path):
    with open(file_path, "rb") as f:
        res = requests.post(
            f"{API_URL}/resumes/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (os.path.basename(file_path), f, "application/pdf")}
        )
    if res.status_code == 201:
        return res.json()
    else:
        logger.error(f"Failed to upload {os.path.basename(file_path)}: {res.text}")
        return None

def match_resume(token, job_id, resume_public_id):
    res = requests.post(
        f"{API_URL}/screening/{job_id}/match/{resume_public_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if res.status_code == 200:
        return res.json()
    else:
        logger.error(f"Failed to match {resume_public_id}: {res.text}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=r"C:\Users\pinak\Downloads\train.csv")
    parser.add_argument("--num", type=int, default=100)
    parser.add_argument("--threshold", type=int, default=60)
    args = parser.parse_args()

    token = authenticate("admin@example.com", "changeme123")
    
    # Create the benchmark job
    job_reqs = [
        {"skill_name": "Machine Learning", "is_required": True},
        {"skill_name": "Deep Learning", "is_required": True},
        {"skill_name": "Data Analysis", "is_required": True},
        {"skill_name": "Computer Vision", "is_required": False},
        {"skill_name": "NLP", "is_required": False}
    ]
    job = create_job(token, "Senior Data Scientist", "Data Science", job_reqs)
    
    with TemporaryDirectory() as tmpdir:
        pdf_paths = get_resumes_from_csv(args.csv, "Data Science", tmpdir, args.num)
        
        results = []
        selected = 0
        failed = 0
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Processing {i}/{len(pdf_paths)}: {os.path.basename(pdf_path)}")
            resume = upload_resume(token, pdf_path)
            if not resume:
                failed += 1
                continue
                
            if resume["status"] == "failed":
                logger.warning(f"Resume {resume['public_id']} processing failed internally: {resume.get('error_message')}")
                failed += 1
                continue
                
            match_data = match_resume(token, job["public_id"], resume["public_id"])
            if not match_data:
                failed += 1
                continue
                
            score = match_data["relevance_score"]
            is_selected = score >= args.threshold
            if is_selected:
                selected += 1
                
            results.append({
                "filename": os.path.basename(pdf_path),
                "score": score,
                "is_selected": is_selected,
                "domain": resume["predicted_domain"]
            })
            
            # Short sleep to prevent completely overwhelming the local API
            time.sleep(0.5)

        logger.info("=" * 40)
        logger.info("BATCH TEST RESULTS")
        logger.info("=" * 40)
        logger.info(f"Total Attempted: {len(pdf_paths)}")
        logger.info(f"Failed to Process: {failed}")
        
        valid_count = len(results)
        logger.info(f"Successfully Screened: {valid_count}")
        
        if valid_count > 0:
            selection_rate = (selected / valid_count) * 100
            logger.info(f"Selected Candidates (Score >= {args.threshold}%): {selected} ({selection_rate:.1f}%)")
            
            # Save results
            out_file = "batch_test_results.json"
            with open(out_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Detailed results saved to {out_file}")

if __name__ == "__main__":
    main()
