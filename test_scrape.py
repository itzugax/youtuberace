import urllib.request
import json
import re

def dump():
    data = json.dumps({
        'context': {
            'client': {
                'clientName': 'WEB',
                'clientVersion': '2.20210721.00.00'
            }
        },
        'videoId': 'jNQXAC9IVRw'
    }).encode('utf-8')
    
    req = urllib.request.Request(
        'https://www.youtube.com/youtubei/v1/next', 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    s = json.dumps(res)
    print("Length:", len(s))
    
    # regex search for videoId
    matches = set(re.findall(r'"videoId":"([^"]+)"', s))
    print(f"Found {len(matches)} videoIds: {list(matches)[:5]}")
    
    # print the string around the first videoId to see its parent object
    if matches:
        vid = list(matches)[1]
        idx = s.find(f'"videoId":"{vid}"')
        print("Context:")
        print(s[max(0, idx-50):idx+150])

dump()
