import httpx
import uuid

BASE_URL = "http://localhost:8000/api"

def test_pipeline():
    client = httpx.Client(timeout=30.0)
    
    # 1. Register a new user
    uid = str(uuid.uuid4())[:8]
    email = f"test_{uid}@example.com"
    username = f"test_{uid}"
    password = "SecurePassword123!"
    
    print(f"Registering user: {email} ...")
    resp = client.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Test User",
        "password": password
    })
    
    if resp.status_code not in [200, 201]:
        print("Registration failed:", resp.status_code, resp.text)
        return
    
    print("Registration successful!")
    tokens = resp.json()
    access_token = tokens["access_token"]
    
    # 2. Login
    print("Logging in ...")
    resp = client.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    if resp.status_code != 200:
        print("Login failed:", resp.status_code, resp.text)
        return
    print("Login successful!")
    
    # Authenticated client headers
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 3. Get profile
    print("Fetching profile ...")
    resp = client.get(f"{BASE_URL}/users/me/profile", headers=headers)
    if resp.status_code != 200:
        print("Fetch profile failed:", resp.status_code, resp.text)
        return
    print("Profile data:", resp.json())
    
    # 4. Trigger crawl for gsoc
    print("Triggering crawl for gsoc ...")
    resp = client.post(f"{BASE_URL}/ai/trigger-crawl?platform=gsoc", headers=headers)
    if resp.status_code != 200:
        print("Trigger crawl failed:", resp.status_code, resp.text)
        return
    print("Trigger crawl message:", resp.json())
    
    print("\nAll pipeline tests completed successfully!")

if __name__ == "__main__":
    test_pipeline()
