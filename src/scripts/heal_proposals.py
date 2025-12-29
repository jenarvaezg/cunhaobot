import subprocess
from google.oauth2 import credentials
from google.cloud import datastore
from datetime import datetime

def heal_proposals():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        kinds = ["Proposal", "LongProposal"]
        default_date = datetime(2024, 1, 1) # Fecha base para registros antiguos
        
        print(f"Iniciando curación de propuestas para: {kinds}\n")
        
        for kind in kinds:
            query = client.query(kind=kind)
            entities = list(query.fetch())
            
            updates = []
            count = 0
            
            for entity in entities:
                changed = False
                
                # Caso 1: Tiene 'created' (limpieza final por si acaso)
                if 'created' in entity:
                    entity['created_at'] = entity.pop('created')
                    changed = True
                
                # Caso 2: No tiene 'created_at' ni tenía 'created'
                if 'created_at' not in entity:
                    entity['created_at'] = default_date
                    changed = True
                
                if changed:
                    updates.append(entity)
                    count += 1
            
            if updates:
                for i in range(0, len(updates), 500):
                    batch = updates[i:i + 500]
                    client.put_multi(batch)
                print(f"Kind {kind:12}: Curadas {count} entidades.")
            else:
                print(f"Kind {kind:12}: Todas las entidades tienen fecha.")

        print("\nCuración completada.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    heal_proposals()
