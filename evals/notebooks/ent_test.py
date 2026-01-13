import requests
def call_classification_api(text, mode="all", anonymize=False):
    """
    Call the Pebblo classification API
    
    Args:
        text (str): The text to classify
        mode (str): Classification mode - "all", "entity", or "topic"
        anonymize (bool): Whether to anonymize the results
    
    Returns:
        dict: The classification response
    """
    url = "http://localhost:8000/api/v1/classify"
    
    # Prepare the request payload without llm_config
    payload = {
        "text": text,
        "anonymize": anonymize,
        "country_list": ["US"]
    }
    
    try:
        #print("payload", payload)
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    

text = """Veteran Service Number: A12345678.
"""
response = call_classification_api(text)
print(response)