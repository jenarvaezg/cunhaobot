import subprocess
from google.oauth2 import credentials
from google.cloud import datastore

def migrate_to_long():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        text = "Beber agua del grifo es como una vacuna, te fortalece las defensas"
        
        # 1. Obtener de Phrase
        old_key = client.key('Phrase', text)
        old_entity = client.get(old_key)
        
        if not old_entity:
            print("No se encontró la frase en 'Phrase'. Quizás ya fue migrada.")
            return

        # 2. Crear en LongPhrase
        new_key = client.key('LongPhrase', text)
        new_entity = datastore.Entity(key=new_key)
        new_entity.update(old_entity)
        
        # 3. Guardar nueva y borrar vieja
        client.put(new_entity)
        client.delete(old_key)
        
        print(f"Migración completada:")
        print(f"  - Creada en 'LongPhrase'")
        print(f"  - Borrada de 'Phrase'")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_to_long()
