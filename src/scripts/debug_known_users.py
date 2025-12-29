from models.user import User, InlineUser
import subprocess
from google.oauth2 import credentials
from google.cloud import datastore

def debug_users():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        # Load all potential users from DB
        users = list(client.query(kind='User').fetch())
        inline_users = list(client.query(kind='InlineUser').fetch())

        print(f"Total User entities: {len(users)}")
        print(f"Total InlineUser entities: {len(inline_users)}")

        unique_users = {}
        for u in users:
            if not u.get('is_group'):
                unique_users[u.key.id_or_name] = u.get('name')
        for iu in inline_users:
            unique_users[iu.get('user_id')] = iu.get('name')

        print(f"Unique users mapped: {len(unique_users)}")
        for uid, name in list(unique_users.items())[:5]:
            print(f"  - {uid}: {name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_users()
