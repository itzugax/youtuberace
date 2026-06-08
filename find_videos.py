import json

data = json.load(open('ytdata.json', encoding='utf-8'))

def traverse(obj, path=""):
    if isinstance(obj, dict):
        if 'videoId' in obj and 'title' in obj:
            if isinstance(obj['title'], dict) and 'simpleText' in obj['title']:
                print(f"Found video at {path}: {obj['videoId']} - {obj['title']['simpleText']}")
            elif isinstance(obj['title'], dict) and 'runs' in obj['title']:
                print(f"Found video at {path}: {obj['videoId']} - {obj['title']['runs'][0]['text']}")
            else:
                print(f"Found video at {path}: {obj['videoId']}")
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                traverse(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                traverse(v, f"{path}[{i}]")

traverse(data)
