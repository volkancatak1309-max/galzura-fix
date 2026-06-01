import os, json, requests
key = os.environ["PLACES_KEY"]
url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
r = requests.get(url, params={"query": "Skyimport Sulz", "key": key, "language": "tr"}, timeout=15)
print("STATUS:", r.status_code)
print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:2000])
