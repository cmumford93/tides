"""
Tides of Remembrance – Text Adventure
-------------------------------------

A text-based adventure set in the world of *Tides of Remembrance*.

Gemini acts as the game master, narrating your journey as the Waker:
an engineer-hero exploring a drowned kingdom, navigating time loops,
and uncovering the fate of lost spirits.

Each run is a new loop with different details, choices, and consequences.
"""

import os
import sys
from google import genai
from google.genai import types

# ----------------------------------------------------------
# 1. CONFIGURE THE GEMINI CLIENT
# ----------------------------------------------------------

# Assumes your API key is already configured (e.g., in env vars) and
# that this works in your environment:
#   from google import genai
#   client = genai.Client()
#
# If you ever want to pass the key explicitly, you can do:
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
#client = genai.Client()

# You can swap models here if you want to experiment.
MODEL_NAME = "gemini-2.0-flash"


# ----------------------------------------------------------
# 2. SYSTEM PROMPT – TIDES OF REMEMBRANCE LORE
# ----------------------------------------------------------

SYSTEM_PROMPT = """
You are the game engine and narrator for an interactive story set in the
original game world *Tides of Remembrance*.

ROLE:
- You are NOT the player.
- You are the world, the NPCs, and the storyteller.
- You must follow consistent lore and treat previous messages as canon.

WORLD LORE (TIDES OF REMEMBRANCE):
- The setting is a once-great coastal kingdom, now partially drowned.
- Flooded ruins, half-sunken towers, quiet coves, and underwater tunnels
  connect different regions.
- Much of the old kingdom lies beneath the waves, filled with abandoned
  technology, strange machinery, and sealed spirit vials.
- Spirits of missing villagers are extracted and stored in vials; the
  spirits are conscious but cannot speak while trapped.
- The protagonist is called the Waker.
    - He is both a hero and a gifted engineer.
    - He can repair devices, analyze old mechanisms, and improvise tools.
- Important themes:
    - Memory, loss, grief, and responsibility.
    - Hope, rebuilding, and unexpected kindness.
    - Time loops and second chances.
- Time loops:
    - When the Waker dies, the loop resets, but he retains faint echoes:
      vague impressions, déjà vu, or partial memories.
    - The world may subtly change between loops.
- Travel & exploration:
    - The Waker can sail between islands and coastal ruins.
    - There is an underwater tunnel network that gradually opens as he
      finds or crafts better breathing equipment and lights.
- NPCs:
    - Arielle: a central love interest; empathetic, brave, tied to the sea.
    - Other NPCs can include lighthouse keepers, tinkers, scholars, sailors,
      and villagers with their own quiet struggles.
    - NPCs may react differently in later loops, or hint that something
      is “off” about time.

GAME STYLE:
- You always narrate in second person ("you").
- Mood: thoughtful, atmospheric, gently haunting but not pure horror.
- Each response should keep the story moving: something new learned,
  a new location revealed, a decision made, or a consequence resolved.

RESPONSE FORMAT (STRICT):
Respond EXACTLY in this structure (no extra headings, no reorder):

LOCATION:
<short description of where the Waker is right now>

SCENE:
<immersive description of what is happening, in 3–8 short paragraphs>

OPTIONS:
- <option 1, concise and actionable>
- <option 2, concise and actionable>
- <option 3, concise and actionable>
(You may occasionally include a 4th option, but never more than 4 total.)

STATS:
- Health: <number between 0 and 100>
- Inventory: <comma-separated list of items, or 'Empty'>
- Notable Traits: <short list of emotional/physical/mental traits, e.g.
  'Thoughtful, waterlogged, slightly wounded'>

RULES FOR GAME LOGIC:
- Treat the conversation history as the single source of truth.
- Track the Waker's injuries, items, and key events consistently.
- If the Waker takes dangerous actions, you may reduce Health.
- If Health reaches 0:
    - Narrate his final moments in that loop.
    - Clearly present an option to begin a NEW LOOP in the same world.
    - The new loop should have altered details, but still respect the core
      lore and previous runs as faint echoes.
- Use the Inventory section to track important tools:
    - Simple weapons (blade, spear, etc.).
    - Engineering tools (wrenches, coils, salvaged parts).
    - Sailing or underwater gear (breathing masks, spirit flasks, lights).
    - Spirit vials, keys, notes, relics, etc.
- When the player types an action:
    - Interpret it with some flexibility and map it to the closest option.
    - If it doesn't match any options but is reasonable, improvise an outcome.

UNIQUENESS ACROSS RUNS:
- A fresh run (new loop) should not be a carbon copy of a previous one.
- Change at least some of:
    - Starting location.
    - NPCs introduced early.
    - Secrets discovered.
- However, keep thematic anchors:
    - Flooded kingdom, spirits in vials, time loops, engineering, sailing,
      underwater tunnels, and the Waker’s connection to Arielle.
"""


# Wrap system prompt as a Content object.
SYSTEM_CONTENT = types.Content(
    parts=[types.Part.from_text(text=SYSTEM_PROMPT)]
)


# ----------------------------------------------------------
# 3. GEMINI CALLS & HELPERS
# ----------------------------------------------------------

def generate_game_response(history, player_input):
    """
    Send the player input + history to Gemini and get back a new game step.

    Parameters
    ----------
    history : list[types.Content]
        All previous user + model messages in this run.
    player_input : str
        What the player just typed (decision, action, or command).

    Returns
    -------
    reply_text : str
        The model's text output (narration + options + stats).
    new_history : list[types.Content]
        Updated history including this turn's user and model messages.
    """
    # Wrap the latest player action in a Content object as 'user'.
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=player_input)]
    )

    # Combine history with the new message we’re sending.
    contents = history + [user_message]

    # Configuration for generation: includes our system prompt
    # and some creativity controls.
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_CONTENT,
        temperature=0.9,          # Higher = more creative/varied
        top_p=0.95,
        max_output_tokens=512,
    )

    # Ask the model to continue the story.
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=config,
    )

    # The SDK usually exposes a convenient .text attr that concatenates parts.
    reply_text = response.text

    # Record the model's reply in the conversation history.
    model_message = types.Content(
        role="model",
        parts=[types.Part.from_text(text=reply_text)]
    )

    # New history now includes both the player's message and the model response.
    new_history = history + [user_message, model_message]

    return reply_text, new_history


def print_divider():
    """Visual separator between turns in the console."""
    print("\n" + "=" * 70 + "\n")


# ----------------------------------------------------------
# 4. MAIN GAME LOOP
# ----------------------------------------------------------

def main():
    """
    Main entry point for the Tides of Remembrance text adventure.

    Controls
    --------
    - Type normal English actions/choices to play.
    - Type '/restart' to begin a new loop (fresh run).
    - Type '/quit' or 'exit' to leave the game.
    """
    print_divider()
    print("Tides of Remembrance – Text Adventure (Gemini-powered)")
    print("You are the Waker, an engineer-hero in a drowned kingdom.")
    print("Type your actions, or '/quit' to exit, '/restart' for a new loop.\n")

    # Each "history" represents the current time loop.
    history = []

    # Initial prompt to start the first loop.
    intro_prompt = (
        "Start a fresh loop of *Tides of Remembrance*. "
        "Introduce the Waker (he/him) waking near the sea or coastal ruins, "
        "hint at his engineering skill, the flooded kingdom, and the mystery "
        "of spirits stored in vials. Present the first situation plus options "
        "following the required LOCATION/SCENE/OPTIONS/STATS format."
    )

    # Ask Gemini to begin the story.
    reply_text, history = generate_game_response(history, intro_prompt)
    print(reply_text)

    # Turn-based input loop.
    while True:
        print_divider()
        try:
            player_input = input("Your action> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThe tide recedes, and the echoes grow quiet. Goodbye.\n")
            break

        # Handle special commands locally.
        lower = player_input.lower()

        if lower in {"/quit", "quit", "exit"}:
            print("\nYou set your tools down and let the tide carry the memories away.\n")
            break

        if lower in {"/restart", "new loop", "new run", "new game"}:
            print("\n--- The current loop fractures. A NEW LOOP begins... ---\n")
            history = []
            intro_prompt = (
                "Begin a completely new loop in *Tides of Remembrance*. "
                "Keep the core lore, but change early details: starting spot, "
                "NPCs introduced, and early events. The Waker faintly remembers "
                "having done this before, but only as vague déjà vu. "
                "Follow the LOCATION/SCENE/OPTIONS/STATS format."
            )
            reply_text, history = generate_game_response(history, intro_prompt)
            print(reply_text)
            continue

        if not player_input:
            print("(If you feel stuck, describe what you want to do or type '/restart'.)")
            continue

        # Normal gameplay: send the action to Gemini.
        reply_text, history = generate_game_response(history, player_input)
        print(reply_text)


# ----------------------------------------------------------
# 5. SCRIPT ENTRY POINT
# ----------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_divider()
        print("Something went wrong while running the game:")
        print(e)
        print("\nCheck your API key, network connection, and model name.")
        sys.exit(1)

