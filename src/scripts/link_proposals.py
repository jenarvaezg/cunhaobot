import subprocess
from google.oauth2 import credentials
from google.cloud import datastore
from datetime import datetime

def link_phrases_to_proposals():
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        # 1. Cargar todas las frases y propuestas en memoria (mapeadas por texto)
        # Nota: Usamos normalización básica para facilitar la coincidencia
        def get_all_by_text(kind):
            query = client.query(kind=kind)
            return {e['text'].strip(): e for e in query.fetch()}

        print("Cargando datos de Datastore...")
        phrases = list(client.query(kind='Phrase').fetch())
        long_phrases = list(client.query(kind='LongPhrase').fetch())
        
        proposals_by_text = get_all_by_text('Proposal')
        long_proposals_by_text = get_all_by_text('LongProposal')
        
        print(f"Total frases: {len(phrases)} cortas, {len(long_phrases)} largas")
        print(f"Total propuestas en DB: {len(proposals_by_text)} cortas, {len(long_proposals_by_text)} largas")

        def process_linking(phrase_list, proposal_map, kind_name):
            linked_count = 0
            updates_phrases = []
            updates_proposals = []
            
            for phrase in phrase_list:
                text = phrase['text'].strip()
                if text in proposal_map:
                    proposal = proposal_map[text]
                    
                    # Vincular frase a propuesta
                    if phrase.get('proposal_id') != proposal.key.name:
                        phrase['proposal_id'] = proposal.key.name
                        updates_phrases.append(phrase)
                        linked_count += 1
                    
                    # Asegurar que la propuesta está marcada como terminada
                    if not proposal.get('voting_ended'):
                        proposal['voting_ended'] = True
                        if not proposal.get('voting_ended_at'):
                            proposal['voting_ended_at'] = phrase.get('created_at', datetime.now())
                        updates_proposals.append(proposal)

            # Guardar cambios
            if updates_phrases:
                for i in range(0, len(updates_phrases), 500):
                    client.put_multi(updates_phrases[i:i+500])
            
            if updates_proposals:
                for i in range(0, len(updates_proposals), 500):
                    client.put_multi(updates_proposals[i:i+500])
                    
            print(f"[{kind_name}] Vinculadas: {linked_count} | Propuestas cerradas: {len(updates_proposals)}")
            return linked_count

        print("\nEjecutando vinculación...")
        linked_short = process_linking(phrases, proposals_by_text, "Phrase")
        linked_long = process_linking(long_phrases, long_proposals_by_text, "LongPhrase")
        
        linked_total = linked_short + linked_long
        total_phrases = len(phrases) + len(long_phrases)
        
        print(f"\n--- RESUMEN ---")
        print(f"Frases vinculadas: {linked_total}")
        print(f"Frases sin propuesta: {total_phrases - linked_total}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    link_phrases_to_proposals()
