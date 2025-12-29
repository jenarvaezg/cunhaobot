import subprocess
from google.oauth2 import credentials
from google.cloud import datastore


def analyze_datastore():
    try:
        # Get access token from gcloud
        token = (
            subprocess.check_output(["gcloud", "auth", "print-access-token"])
            .decode("utf-8")
            .strip()
        )
        creds = credentials.Credentials(token)
        client = datastore.Client(credentials=creds, project="cunhaobot")

        kinds = [
            "Phrase",
            "LongPhrase",
            "User",
            "InlineUser",
            "Proposal",
            "LongProposal",
        ]

        stats = {}

        print("Iniciando análisis para el proyecto: cunhaobot\n")

        for kind in kinds:
            query = client.query(kind=kind)
            entities = list(
                query.fetch(limit=1000)
            )  # Limit to avoid huge memory usage if data is massive
            stats[kind] = {"count": len(entities), "entities": entities}
            print(f"Kind: {kind:15} | Total: {len(entities)}")

        print("\n" + "=" * 50)
        print("--- ANÁLISIS DE FRASES ---")
        print("=" * 50)
        for phrase_kind in ["Phrase", "LongPhrase"]:
            entities = stats[phrase_kind]["entities"]
            if not entities:
                print(f"\nSin datos para {phrase_kind}")
                continue

            total_usages = sum(e.get("usages", 0) for e in entities)
            avg_usages = total_usages / len(entities) if entities else 0

            # Sort by usages
            sorted_phrases = sorted(
                entities, key=lambda x: x.get("usages", 0), reverse=True
            )

            print(f"\nEstadísticas para {phrase_kind}:")
            print(f"Total de usos acumulados: {total_usages}")
            print(f"Promedio de usos por frase: {avg_usages:.2f}")

            print("\nTop 5 frases más usadas:")
            for e in sorted_phrases[:5]:
                print(f"- {e.get('text')} ({e.get('usages', 0)} usos)")

        print("\n" + "=" * 50)
        print("--- ANÁLISIS DE USUARIOS ---")
        print("=" * 50)
        user_entities = stats["User"]["entities"]
        if user_entities:
            groups = [e for e in user_entities if e.get("is_group") == True]
            private = [e for e in user_entities if e.get("is_group") == False]
            gdpr_count = sum(1 for e in user_entities if e.get("gdpr") == True)
            print(f"Usuarios privados: {len(private)}")
            print(f"Grupos:           {len(groups)}")
            print(f"GDPR activos:     {gdpr_count}")
        else:
            print("No se encontraron usuarios registrados.")

        print("\n" + "=" * 50)
        print("--- ANÁLISIS DE PROPUESTAS PENDIENTES ---")
        print("=" * 50)
        for prop_kind in ["Proposal", "LongProposal"]:
            entities = stats[prop_kind]["entities"]
            if not entities:
                print(f"No hay propuestas pendientes para {prop_kind}.")
                continue

            print(f"Propuestas {prop_kind:12} | Pendientes: {len(entities)}")

            def get_total_votes(e):
                return len(e.get("liked_by", [])) + len(e.get("disliked_by", []))

            if entities:
                most_voted = max(entities, key=get_total_votes)
                print(
                    f"Más votada: '{most_voted.get('text')}' con {get_total_votes(most_voted)} votos."
                )

    except Exception as e:
        print(f"Error durante el análisis: {e}")


if __name__ == "__main__":
    analyze_datastore()
