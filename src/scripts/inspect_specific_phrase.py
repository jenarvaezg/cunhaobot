import subprocess
from google.oauth2 import credentials
from google.cloud import datastore

def inspect_phrase():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        text = "Beber agua del grifo es como una vacuna, te fortalece las defensas"
        
        # Buscar en Phrase
        key = client.key('Phrase', text)
        phrase = client.get(key)
        
        if phrase:
            print(f"Encontrada en Phrase:")
            for k, v in phrase.items():
                print(f"  {k}: {v}")
            print(f"  Proposal ID: {phrase.get('proposal_id')}")
        else:
            print("No se encontró en Phrase.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_phrase()
