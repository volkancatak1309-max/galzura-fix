import os, json
from data_collector import places_firma_bul
r = places_firma_bul("SKY IMPORT OG", "Vorarlberg", os.environ["PLACES_KEY"], domain="skyimport.eu")
print(json.dumps(r, ensure_ascii=False, indent=2))
