import subprocess
from google.oauth2 import credentials
from google.cloud import datastore
from datetime import datetime

def migrate_proposals():
    try:
        # Obtener token de acceso de gcloud
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        kinds = ["Proposal", "LongProposal"]
        
        print(f"Iniciando migración de fechas para: {kinds}\n")
        
        for kind in kinds:
            query = client.query(kind=kind)
            entities = list(query.fetch())
            
            updates = []
            count = 0
            
            for entity in entities:
                changed = False
                
                # Si existe 'created' pero no 'created_at', o queremos unificar
                if 'created' in entity:
                    created_val = entity.pop('created')
                    # Solo actualizamos si 'created_at' no existe o si queremos forzar la unificación
                    entity['created_at'] = created_val
                    changed = True
                
                if changed:
                    updates.append(entity)
                    count += 1
            
            if updates:
                # Procesar en bloques de 500 (límite de Datastore para put_multi)
                for i in range(0, len(updates), 500):
                    batch = updates[i:i + 500]
                    client.put_multi(batch)
                print(f"Kind {kind:12}: Migradas {count} entidades.")
            else:
                print(f"Kind {kind:12}: No se encontraron entidades con el campo 'created'.")

        print("\nMigración completada con éxito.")

    except Exception as e:
        print(f"Error durante la migración: {e}")

if __name__ == "__main__":
    migrate_proposals()
