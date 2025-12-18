
import requests
import sys

# Try both standard ports
PORTS = [8000, 8002]

def test_login():
    url_path = "/api/auth/login"
    username = "admin@empresa.com"
    password = "admin123"
    
    for port in PORTS:
        base_url = f"http://localhost:{port}"
        full_url = f"{base_url}{url_path}"
        print(f"Testing login at: {full_url}")
        
        try:
            response = requests.post(
                full_url,
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                print(f"SUCCESS! Login worked on port {port}.")
                print(f"Token: {response.json().get('access_token')[:20]}...")
            else:
                print(f"FAILED on port {port}. Status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"Could not connect to port {port} (Server might be down or not listening here).")
        except Exception as e:
            print(f"Error on port {port}: {e}")
        print("-" * 30)

if __name__ == "__main__":
    test_login()
