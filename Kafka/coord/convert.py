import sys
sys.path.append("/opt")

import requests
import json

with open('/opt/Kafka/coord/district_HN.txt', 'r') as f:
    district_HNs = [line.strip().replace(',', '') for line in f]

with open('/opt/Kafka/coord/district_HCM.txt', 'r') as f:
    district_HCMs = [line.strip().replace(',', '') for line in f]

coord_list = []
for district_HN in district_HNs:
    response = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={district_HN},Hà Nội,VNM&appid=72dc1092f8152fcd1935938246615de4")
    data_HN = response.json()
    coord = {"lat": data_HN[0]["lat"], "lon": data_HN[0]["lon"], "distirct": district_HN, "city": "Hà Nội"}
    coord_list.append(coord)
for distric_HCM in district_HCMs:
    response = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={distric_HCM},Hồ Chí Minh,VNM&appid=72dc1092f8152fcd1935938246615de4")
    data_HCM = response.json()
    coord = {"lat": data_HCM[0]["lat"], "lon": data_HCM[0]["lon"], "distirct": distric_HCM, "city": "Hồ Chí Minh"}
    coord_list.append(coord)

with open('/opt/Kafka/coord/coordinate.json', 'w', encoding='utf-8') as f:
    json.dump(coord_list, f, ensure_ascii=False, indent=4)

print("Done")


