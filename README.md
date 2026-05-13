# Prokoti Multi-Tenant RAG (POOLED Architecture)

This repository contains a production-grade **Multi-Tenant Retrieval-Augmented Generation (RAG)** system built using Amazon Bedrock, OpenSearch Serverless, and PostgreSQL.

## 🛡️ Key Features

- **POOLED Data Architecture**: All tenant data is stored in a single OpenSearch index, isolated by a "Hard Security Wall" at the query level.
- **Production-Grade Identity Enrichment**: User permissions are fetched live from a PostgreSQL **User Registry**, ensuring real-time authorization (ABAC).
- **Metadata Filter Walls**: Prevents cross-tenant data leakage by enforcing mandatory `tenant_id` and `classification` filters on every retrieval request.
- **Dynamic Ingestion Pipeline**: Automatically redacts PII, generates Titan embeddings, and tags data with classification levels (Public, Internal, Confidential, Restricted).
- **Streamlit Dashboard**: A premium UI to test identity-driven access and visualize "Permission Envelopes."

## 🏗️ Architecture

1.  **PostgreSQL**: Source of truth for employee records and user permissions.
2.  **Amazon Titan Embeddings**: Converts text into 1024-dimension vectors.
3.  **Amazon OpenSearch Serverless (AOSS)**: Vector database for fast, filtered retrieval.
4.  **Claude 3.5 Sonnet**: The core LLM agent that generates secure, context-aware responses.

## 🚀 Getting Started

### 1. Prerequisites
- AWS Account with Bedrock & OpenSearch Serverless access.
- PostgreSQL local or RDS instance.
- Python 3.10+

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Setup
1.  **Configure Environment**: Update `.env` with your AWS and DB credentials.
2.  **Initialize Database**:
    ```bash
    python update_sql_schema.py
    python seed_large_db.py
    ```
3.  **Setup OpenSearch**:
    ```bash
    python opensearch_setup.py
    ```
4.  **Ingest Data**:
    ```bash
    python lambda_ingestion.py
    ```

### 4. Running the App
```bash
streamlit run app.py
```

## 🧪 Testing Multi-Tenancy

In the Streamlit Sidebar, enter different User IDs to see how the access wall changes:
- `acme_sales_0`: Can only see Sales data for Acme.
- `umbrella_research_5`: Can see Restricted Research data for Umbrella.
- `hooli_capital_10`: Blocked from seeing any data from other tenants.

## 📂 Project Structure

- `app.py`: Streamlit Frontend.
- `agent_runtime.py`: Core RAG orchestration logic.
- `lambda_retrieval.py`: Identity enrichment & security filter construction.
- `lambda_ingestion.py`: Data processing & vectorization pipeline.
- `seed_large_db.py`: Scalable multi-tenant data generator.
