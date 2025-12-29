import subprocess
from google.oauth2 import credentials
from google.cloud import datastore

def inspect_proposals():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        search_texts = ["Mastuerzo", "poseidon"]
        kinds = ["Proposal", "LongProposal"]
        
        for kind in kinds:
            for text in search_texts:
                query = client.query(kind=kind)
                query.add_filter('text', '=', text)
                entities = list(query.fetch())
                
                for entity in entities:
                    print(f"Kind: {kind} | Text: {entity.get('text')} | ID: {entity.key.name}")
                    print(f"  Fields: {list(entity.keys())}")
                    print(f"  created: {entity.get('created')}")
                    print(f"  created_at: {entity.get('created_at')}")
                    print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_proposals()
