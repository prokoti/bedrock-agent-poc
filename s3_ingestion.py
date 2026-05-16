import boto3
import os
import io
import PyPDF2
from dotenv import load_dotenv
from lambda_ingestion import ingest_document

load_dotenv()

# Configuration
REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client("s3", region_name=REGION)

def extract_text_from_pdf(file_content):
    """Extracts text from a PDF file byte stream."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        return ""

def chunk_text(text, chunk_size=2000, overlap=200):
    """Splits long text into smaller overlapping chunks."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def process_s3_documents():
    """
    Iterates through S3 bucket and ingests documents.
    Convention: s3://bucket/tenant_id/org_id/filename.ext
    """
    if not S3_BUCKET:
        print("Error: S3_BUCKET_NAME not set in .env")
        return

    print(f"\n--- [S3 Ingestion] Scanning Bucket: {S3_BUCKET} ---")
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET):
            if 'Contents' not in page:
                print("Bucket is empty.")
                continue

            for obj in page['Contents']:
                key = obj['Key']
                
                if key.endswith('/'): continue

                print(f"Processing: {key}")
                
                # Extract Tenant and Org from Path
                parts = key.split('/')
                if len(parts) < 3:
                    print(f"Skipping {key}: Does not follow /tenant/org/file convention.")
                    continue
                
                tenant_id = parts[0].strip()
                org_id = parts[1].strip()
                filename = parts[-1]

                # Get Object & Extract Text
                response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                content = response['Body'].read()

                if key.lower().endswith('.pdf'):
                    raw_text = extract_text_from_pdf(content)
                elif key.lower().endswith('.txt'):
                    raw_text = content.decode('utf-8')
                else: continue

                if not raw_text.strip(): continue

                # NEW: Split into chunks to avoid Bedrock Length Limits
                text_chunks = chunk_text(raw_text)
                print(f" -> Splitting into {len(text_chunks)} chunks for {tenant_id}/{org_id}")

                for i, chunk in enumerate(text_chunks):
                    metadata = {
                        "tenant_id": tenant_id,
                        "org_id": org_id,
                        "filename": filename,
                        "chunk_id": i,
                        "data_type": "s3_document"
                    }
                    ingest_document(chunk, metadata, source=f"s3://{S3_BUCKET}/{key}")
                
                print(f" ✅ Finished ingesting {filename}")

        print("\n--- S3 Ingestion Complete ---")

    except Exception as e:
        print(f"Error during S3 ingestion: {str(e)}")

if __name__ == "__main__":
    process_s3_documents()
