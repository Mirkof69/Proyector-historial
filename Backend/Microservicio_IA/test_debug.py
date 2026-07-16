import json
import os

import requests

url = 'http://localhost:5000/analyze'
img_dir = r'C:\Users\Miscar\Downloads\ecografias'
path = 'eco_gemelos.jpg'
full = os.path.join(img_dir, path)
with open(full, 'rb') as f:
    r = requests.post(url, files={'file': (path, f, 'image/jpeg')})
data = r.json()
print(json.dumps(data, indent=2, default=str)[:3000])
