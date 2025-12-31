import logging
import sys
import os
from google.cloud import datastore

# Añade 'src' al path para poder importar modelos y utilidades
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.user import User

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def unify_users(dry_run: bool = True):
    client = datastore.Client()
    
    if dry_run:
        logger.info("MODO DRY RUN - No se guardarán ni borrarán cambios")

    # 1. Cargar todas las entidades
    logger.info("Obteniendo todas las entidades User e InlineUser...")
    user_entities = list(client.query(kind="User").fetch())
    inline_user_entities = list(client.query(kind="InlineUser").fetch())
    
    logger.info(f"Encontradas {len(user_entities)} entidades User y {len(inline_user_entities)} entidades InlineUser")

    # 2. Agrupar por ID
    unified_data = {}

    def process_entity(entity, source_kind):
        data = dict(entity)
        # Extraer ID (chat_id o user_id en el formato antiguo, id en el nuevo)
        uid = data.get("id") or data.get("chat_id") or data.get("user_id")
        if uid is None:
            # Intentar obtener de la clave si no está en las propiedades
            uid = entity.key.id or entity.key.name
            
        if uid is None:
            logger.warning(f"No se pudo determinar el ID para la entidad {entity.key}")
            return

        uid = int(uid)
        
        if uid not in unified_data:
            unified_data[uid] = {
                "id": uid,
                "name": data.get("name", ""),
                "username": data.get("username"),
                "is_group": data.get("is_group", False),
                "gdpr": data.get("gdpr", False),
                "usages": data.get("usages", 0),
                "points": data.get("points", 0),
                "created_at": data.get("created_at"),
                "source_kinds": {source_kind},
                "old_keys": [entity.key]
            }
        else:
            entry = unified_data[uid]
            # Fusionar propiedades
            if not entry["name"] and data.get("name"):
                entry["name"] = data["name"]
            if not entry["username"] and data.get("username"):
                entry["username"] = data["username"]
            
            if data.get("is_group"):
                entry["is_group"] = True
                
            if data.get("gdpr"):
                entry["gdpr"] = True
                
            # Sumar estadísticas
            entry["usages"] += data.get("usages", 0)
            entry["points"] += data.get("points", 0)
            
            # Mantener la fecha de creación más antigua
            if data.get("created_at"):
                if not entry["created_at"] or data["created_at"] < entry["created_at"]:
                    entry["created_at"] = data["created_at"]
            
            entry["source_kinds"].add(source_kind)
            entry["old_keys"].append(entity.key)

    for entity in user_entities:
        process_entity(entity, "User")
    
    for entity in inline_user_entities:
        process_entity(entity, "InlineUser")

    logger.info(f"Usuarios únicos identificados: {len(unified_data)}")

    # 3. Guardar y limpiar
    for uid, data in unified_data.items():
        source_kinds = data.pop("source_kinds")
        old_keys = data.pop("old_keys")
        
        # Asegurar que el nombre sea un string
        if data["name"] is None:
            data["name"] = f"User {uid}"
            
        user = User(**data)
        
        logger.info(f"Unificando usuario {uid} ({user.name}): puntos={user.points}, usos={user.usages}, fuentes={source_kinds}")
        
        if not dry_run:
            # Guardar nueva entidad (usando Kind='User', KeyID=uid)
            new_key = client.key("User", uid)
            new_entity = datastore.Entity(key=new_key)
            new_entity.update(user.model_dump())
            client.put(new_entity)
            
            # Borrar claves antiguas que sean diferentes a la nueva
            # (evita borrar la entidad que acabamos de guardar si ya era correcta)
            keys_to_delete = [k for k in old_keys if k.kind != "User" or k.id != uid or k.name is not None]
            if keys_to_delete:
                client.delete_multi(keys_to_delete)
                logger.info(f"  -> Eliminadas {len(keys_to_delete)} entidades legacy")

    logger.info("Unificación completada.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Unificar datos de User e InlineUser en Datastore")
    parser.add_argument("--run", action="store_true", help="Ejecutar la migración (por defecto es dry-run)")
    args = parser.parse_args()
    
    unify_users(dry_run=not args.run)