import json
import requests


### Check connection (TEST)
# url = "https://search-deliver-me-kts7eem5abkhyvqvhvaq223pim.ap-southeast-2.es.amazonaws.com/"
# res = requests.get(url, auth=("dme", "Dme3571&*"))
# print(res.status_code)
# print(str(res.text))


### SEARCH (TEST)
# curl -XGET -u 'dme:Dme3571&*' 'https://search-deliver-me-kts7eem5abkhyvqvhvaq223pim.ap-southeast-2.es.amazonaws.com/movies/_search?q=mars&pretty=true'
# url = "https://search-deliver-me-kts7eem5abkhyvqvhvaq223pim.ap-southeast-2.es.amazonaws.com/movies/_search?q=a&pretty=true"
# res = requests.get(url, auth=("dme", "Dme3571&*"))
# print(res.status_code)
# print(str(res.text))


### PUT ONE (TEST)
# url = "https://search-deliver-me-kts7eem5abkhyvqvhvaq223pim.ap-southeast-2.es.amazonaws.com/movies/_doc/1"
# headers = {"Content-Type": "application/json"}
# data = '{"director": "Burton, Tim"}'
# res = requests.put(url, auth=("dme", "Dme3571&*"), data=data, headers=headers)
# print(res.status_code)
# print(str(res.text))


### PUT BULK (TEST)
# url = "https://search-deliver-me-kts7eem5abkhyvqvhvaq223pim.ap-southeast-2.es.amazonaws.com/_bulk?pretty&refresh"
# headers = {"Content-Type": "application/x-ndjson"}

# with open("movies.json", "rb") as f:
#     data = f.read()

# res = requests.post(url, auth=("dme", "Dme3571&*"), data=data, headers=headers)
# print(res.status_code)
# s0 = json.loads(res.content)
# print(json.dumps(s0, indent=2, sort_keys=True))

### PUT BULK (LIVE)
url = "https://search-deliver-me-kts7eem5abkhyvqvhvaq223pim.ap-southeast-2.es.amazonaws.com/_bulk?pretty&refresh"
headers = {"Content-Type": "application/x-ndjson"}

with open("addresses.json", "rb") as f:
    data = f.read()

res = requests.post(url, auth=("dme", "Dme3571&*"), data=data, headers=headers)
print(res.status_code)
s0 = json.loads(res.content)
print(json.dumps(s0, indent=2, sort_keys=True))
