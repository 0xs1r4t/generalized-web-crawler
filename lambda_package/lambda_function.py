import json
import requests

def lambda_handler(event, context):
    url = event.get("queryStringParameters", {}).get("url", None)
    
    if not url:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "URL parameter is required"})
        }
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)

        return {
            "statusCode": response.status_code,
            "body": response.text
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error fetching URL: {str(e)}"})
        }

