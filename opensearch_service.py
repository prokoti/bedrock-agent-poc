import boto3
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")
SERVICE = "aoss"
HOST = os.getenv("OPENSEARCH_URL", "").replace("https://", "")

def get_opensearch_client():
    """Returns a signed OpenSearch Serverless client."""
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, REGION, SERVICE)
    
    client = OpenSearch(
        hosts=[{'host': HOST, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20
    )
    return client
