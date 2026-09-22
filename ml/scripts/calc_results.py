import requests

res = requests.post('http://localhost:8000/api/v1/auth/login', json={'email':'admin@example.com', 'password':'changeme123'})
token = res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

jobs = requests.get('http://localhost:8000/api/v1/jobs', headers=headers).json()
# Find the specific job created for the test
job = next(j for j in jobs if j['title'] == 'Senior Data Scientist')
print(f"Job: {job['title']} (ID: {job['id']})")

res_results = requests.get(f"http://localhost:8000/api/v1/screening/{job['public_id']}/results", headers=headers)
if res_results.status_code != 200:
    print(f"Error fetching results: {res_results.status_code} - {res_results.text}")
    exit(1)

results = res_results.json()
print(f"Total candidates matched: {len(results)}")

scores = [r.get('relevance_score', 0) for r in results]
print(f"Max score: {max(scores) if scores else 0}")
print(f"Non-zero scores: {len([s for s in scores if s > 0])}")
selected = [r for r in results if r.get('relevance_score', 0) >= 60.0]
print(f"Selected candidates (score >= 60.0): {len(selected)}")
print(f"Selection Rate: {len(selected) / len(results) * 100:.1f}%" if results else "0%")
