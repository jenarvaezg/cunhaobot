# Game Design Document: El Cuñado - Arena de Tasca 🥊

**Concepto:** Un auto-battler asíncrono (estilo *El Bruto* o *MyBrute*) donde los usuarios gestionan a un "Luchador Cuñado" que pelea automáticamente contra otros usuarios de los grupos de Telegram/Slack.

**Objetivo:** Subir de nivel ganando debates (peleas) para desbloquear habilidades absurdas, armas de bar y mejorar estadísticas, convirtiéndose en el "Rey de la Barra".

---

## 1. Mecánicas Principales

### 1.1. Creación del Luchador
Todo usuario tiene un luchador vinculado a su cuenta.
*   **Nombre:** Se hereda del usuario (o se puede personalizar, ej: *"Paco 'El Grifo'"*).
*   **Apariencia:** (Fase 2) Generada proceduralmente o basada en la foto de perfil.

### 1.2. Estadísticas (Los 4 Pilares del Cuñadismo)
En lugar de Fuerza/Agilidad/Velocidad, usamos términos temáticos:

1.  **Vozarrón (Fuerza):** Determina el daño base de los "Zascas".
    *   *Lore:* "Quien más grita, más razón tiene."
2.  **Cintura (Agilidad):** Probabilidad de esquivar un argumento enemigo (Miss) o bloquearlo (Parry).
    *   *Lore:* "Habilidad para cambiar de tema cuando vas perdiendo."
3.  **Verborrea (Velocidad):** Determina quién ataca primero y la probabilidad de atacar varias veces seguidas (Combo).
    *   *Lore:* "No deja hablar a los demás."
4.  **Aguante (Vida/HP):** Puntos de vida.
    *   *Lore:* "Capacidad de aguantar alcohol y tonterías sin irse a casa."

### 1.3. El Combate
*   **Asíncrono:** No requiere que los dos usuarios estén conectados.
*   **Automático:** El servidor simula la pelea turno por turno basándose en stats, armas y habilidades.
*   **Resultado:** Se genera un "Battle Log" (texto enriquecido) o una repetición visual (HTML5).

### 1.4. Progresión (Sistema "El Bruto")
Al subir de nivel, el jugador **DEBE elegir entre dos opciones** (RNG ponderado):
*   Opción A: +3 Vozarrón.
*   Opción B: Nueva Habilidad "Golpe de Remo".

Esto crea "builds" únicos (el tanque que aguanta todo, el rápido que pega 10 veces, el que usa armas, etc.).

---

## 2. Inventario y Habilidades

### 2.1. Armas (Se equipan y usan aleatoriamente en combate)
Las armas tienen daño, rango de acierto y probabilidad de combo.

*   **El Palillo:** Daño bajo, muy rápido (Verborrea).
*   **La Servilleta (Sucia):** Daño nulo, pero baja la Cintura del rival (lo ciega).
*   **Copa de Soberano:** Daño alto, se rompe tras usarla.
*   **El Móvil (con meme):** Aturde al rival 1 turno.
*   **Llaves del Mercedes:** Daño crítico muy alto.
*   **La Cuenta:** Daño masivo, pero te quita vida a ti también.

### 2.2. Habilidades Pasivas y Activas
*   **"Y tú más":** Refleja el 30% del daño recibido.
*   **"Yo controlo":** +50% daño en el primer turno.
*   **"Cuñado de Guardia":** Sobrevive con 1 HP al primer golpe letal.
*   **"Ladrón de Chistes":** Roba el arma del rival.
*   **"Invocar Sobrino":** (Mascota) Aparece un "Sobrino Informático" que ataca por ti (poco daño, mucha distracción).
*   **"Grito al Cielo":** Asusta al rival (baja su Verborrea).

---

## 3. Flujo del Juego (User Journey)

1.  **Registro:** `/arena crear` (o automático al primera interacción).
2.  **Desafío:** `/duelo @usuario` o `/duelo random` (busca rival de nivel similar).
3.  **La Pelea:** El bot calcula el resultado instantáneamente.
    *   *Output:* Mensaje con resumen: "🥊 **Paco** ha destrozado a **Jose** con un *Zasca Legendario*".
    *   *Botón:* [Ver Repetición] (Abre WebApp).
4.  **Recompensa:** El ganador recibe XP. El perdedor recibe menos XP (pero siempre algo, para no frustrar).
5.  **Level Up:** El bot envía un mensaje privado: "¡Has subido a Nivel 2! Elige: [A: +3 Aguante] o [B: Arma: Palillo]".

---

## 4. Arquitectura Técnica

### 4.1. Base de Datos (Nuevas Entidades)

**Modelo `Fighter` (Luchador):**
```python
class Fighter(BaseModel):
    user_id: int  # Link al User principal
    level: int = 1
    xp: int = 0
    # Stats base
    vozarron: int = 5
    cintura: int = 5
    verborrea: int = 5
    aguante: int = 50
    # Inventario
    weapons: list[str] = []
    skills: list[str] = []
    # Estado
    fights_today: int = 0
    last_fight_at: datetime
```

**Modelo `Fight` (Histórico):**
```python
class Fight(BaseModel):
    id: str
    fighter_a_id: int
    fighter_b_id: int
    winner_id: int
    log: list[dict]  # JSON con cada turno { "actor": "A", "action": "attack", "dmg": 10 }
    created_at: datetime
```

### 4.2. Motor de Combate (Service)
Clase `ArenaService` que contiene la lógica pura:
*   `calculate_initiative(fighter_a, fighter_b)`
*   `simulate_turn(...)`
*   `resolve_fight(...)` -> Devuelve el objeto `Fight` con todo el log.

### 4.3. Visualización
*   **Fase 1 (Texto):** El bot edita el mensaje en tiempo real o manda un log estático.
    *   *Ejemplo:* "Paco saca [Palillo]... ¡Zas! (10 dmg). Jose intenta huir... ¡Falla!"
*   **Fase 2 (Web/Phaser):** Reutilizar el canvas de Phaser del "Tapas Runner".
    *   Dos sprites estáticos (avatares) que tiemblan al recibir daño.
    *   Texto flotante de daño.
    *   Iconos de armas apareciendo.

---

## 5. Monetización (Ficticia / Puntos del Bot)
*   Se pueden gastar puntos globales (del bot principal) para:
    *   Recuperar "fatiga" (pelear más veces al día).
    *   Sobornar al árbitro (pequeño buff temporal, riesgo de ser descubierto).
    *   Cambiar el nombre del luchador.

## 6. Roadmap de Implementación

1.  **Core Backend:** Modelos `Fighter` y `Fight`, lógica de subida de nivel.
2.  **Motor de Batalla:** Algoritmo simple de turnos y daño.
3.  **Integración CLI/Bot:** Comandos `/duelo` y sistema de notificaciones de Level Up.
4.  **Visualización Texto:** Logs divertidos generados por templates o IA.
5.  **Visualización Web:** Player simple en `/arena/replay/{fight_id}`.
