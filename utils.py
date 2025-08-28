import json

def extract_json(text):
    try:
        json_start = text.find('{')
        json_end = text.rfind('}')
        json_str = text[json_start:json_end+1]
        return json.loads(json_str)
    except Exception as e:
        return None
