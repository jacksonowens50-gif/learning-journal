import os
import requests

token = os.environ["GITHUB_TOKEN"]

response = requests.get(
    "https://api.github.com/user/emails",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
)

print(response.status_code)
print(response.json())