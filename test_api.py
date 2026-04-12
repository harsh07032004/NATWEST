import urllib.request
import json

url = "http://localhost:5000/api/query"
data = {
    "query": "show sales and why did they drop",
    "dataset_ref": "data/Superstore.csv"
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'))
req.add_header('Content-Type', 'application/json')

try:
    response = urllib.request.urlopen(req)
    result = response.read().decode('utf-8')
    print("SUCCESS")
    print(json.dumps(json.loads(result), indent=2))
except Exception as e:
    print("FAILED")
    print(e)
