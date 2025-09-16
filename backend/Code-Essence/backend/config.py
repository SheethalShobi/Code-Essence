import boto3

REGION = "us-east-1"

# Bedrock client
session = boto3.Session(region_name=REGION)
bedrock_client = session.client("bedrock-runtime")
