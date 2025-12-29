import subprocess
from google.oauth2 import credentials
from google.cloud import datastore
from fuzzywuzzy import fuzz
from datetime import datetime

def link_orphans():
    try:
        # Autenticación mediante gcloud
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project='cunhaobot')
        
        print("Cargando datos de Datastore...")
        
        # Cargar todas las propuestas
        all_proposals = list(client.query(kind='Proposal').fetch())
        all_long_proposals = list(client.query(kind='LongProposal').fetch())
        
        # Cargar frases huérfanas
        query_phrases = client.query(kind='Phrase')
        orphan_phrases = [e for e in query_phrases.fetch() if not e.get('proposal_id')]
        
        query_long_phrases = client.query(kind='LongPhrase')
        orphan_long_phrases = [e for e in query_long_phrases.fetch() if not e.get('proposal_id')]
        
        print(f"Huérfanas encontradas: {len(orphan_phrases)} cortas, {len(orphan_long_phrases)} largas.")
        print(f"Propuestas disponibles: {len(all_proposals)} cortas, {len(all_long_proposals)} largas.")

        def find_best_match(phrase_text, proposal_list):
            best_score = -1
            best_proposal = None
            
            for prop in proposal_list:
                # Usamos token_set_ratio para ser más flexibles con variaciones menores
                score = fuzz.token_set_ratio(phrase_text, prop['text'])
                if score > best_score:
                    best_score = score
                    best_proposal = prop
            
            return best_proposal, best_score

        def process_linking(phrases, proposals, kind_label):
            linked = 0
            updates = []
            
            for phrase in phrases:
                best_prop, score = find_best_match(phrase['text'], proposals)
                
                # Umbral de 90% para asegurar que es "factible"
                if best_prop and score >= 90:
                    phrase['proposal_id'] = best_prop.key.name
                    updates.append(phrase)
                    linked += 1
                    # print(f"[{kind_label}] Vinculado: '{phrase['text']}' -> '{best_prop['text']}' (Score: {score})")

            if updates:
                for i in range(0, len(updates), 500):
                    client.put_multi(updates[i:i+500])
            
            print(f"[{kind_label}] Vinculadas exitosamente: {linked}")
            return linked

        print("\nIniciando proceso de búsqueda difusa...")
        total_linked = 0
        total_linked += process_linking(orphan_phrases, all_proposals, "Phrase")
        total_linked += process_linking(orphan_long_phrases, all_long_proposals, "LongPhrase")
        
        print(f"\n--- PROCESO FINALIZADO ---")
        print(f"Total frases vinculadas por Levenshtein: {total_linked}")

    except Exception as e:
        print(f"Error durante la vinculación: {e}")

if __name__ == "__main__":
    link_orphans()
