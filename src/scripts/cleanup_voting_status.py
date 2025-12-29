import subprocess
from google.oauth2 import credentials
from google.cloud import datastore
from datetime import datetime

def cleanup_voting_status():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        kinds = ["Proposal", "LongProposal"]
        
        print(f"Iniciando limpieza de estados de votación para: {kinds}\n")
        
        for kind in kinds:
            query = client.query(kind=kind)
            entities = list(query.fetch())
            
            updates = []
            count_fixed_dates = 0
            count_fixed_nones = 0
            
            for entity in entities:
                val = entity.get('voting_ended')
                changed = False
                
                # Caso 1: Es una fecha (migración a voting_ended_at)
                if isinstance(val, datetime):
                    entity['voting_ended_at'] = val
                    entity['voting_ended'] = True
                    changed = True
                    count_fixed_dates += 1
                
                # Caso 2: Es None o no existe
                elif val is None:
                    entity['voting_ended'] = False
                    changed = True
                    count_fixed_nones += 1
                
                # Caso 3: Asegurar booleano si es cualquier otra cosa no booleana
                elif not isinstance(val, bool):
                    entity['voting_ended'] = bool(val)
                    changed = True
                
                if changed:
                    updates.append(entity)
            
            if updates:
                for i in range(0, len(updates), 500):
                    batch = updates[i:i + 500]
                    client.put_multi(batch)
                print(f"Kind {kind:12}: Corregidos {count_fixed_dates} fechas y {count_fixed_nones} nulos.")
            else:
                print(f"Kind {kind:12}: No se requirieron cambios.")

        print("\nLimpieza completada con éxito.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup_voting_status()
