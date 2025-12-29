import subprocess
from google.oauth2 import credentials
from google.cloud import datastore
from collections import Counter

def check_voting_ended():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        kinds = ["Proposal", "LongProposal"]
        
        for kind in kinds:
            print(f"\n--- Analizando {kind} ---")
            query = client.query(kind=kind)
            entities = list(query.fetch())
            
            stats = []
            for entity in entities:
                val = entity.get('voting_ended')
                type_name = type(val).__name__
                stats.append((type_name, str(val)))
            
            counts = Counter(stats)
            for (t, v), count in counts.items():
                print(f"Tipo: {t:10} | Valor: {v:10} | Cantidad: {count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_voting_ended()
