from litestar.testing import TestClient
from main import app
import json

def check_orphans_context():
    with TestClient(app=app) as client:
        # Simulate admin session
        # Use config to get the correct owner_id
        from main import config
        client.set_session_data({"user": {"id": config.owner_id, "first_name": "Admin"}})
        
        rv = client.get("/orphans")
        print(f"Status Code: {rv.status_code}")
        
        # Check if known_users is in context (if it was a template response we'd check rv.text or context)
        # Since it's a Template response, we can inspect the text for option tags
        options_count = rv.text.count("<option value=")
        print(f"Number of <option> tags in response: {options_count}")
        
        if options_count < 2: # At least one for the placeholder
            print("WARNING: Dropdown seems empty or only contains placeholder.")
            # Print a snippet of the dropdown area
            start = rv.text.find('<select name="creator_id"')
            end = rv.text.find('</select>', start) + 9
            print(f"Dropdown HTML: {rv.text[start:end]}")

if __name__ == "__main__":
    check_orphans_context()
