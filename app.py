import streamlit as st
import sqlite3
from datetime import datetime
from transformers import pipeline, set_seed

# Initialize the LLM model
generator = pipeline("text-generation", model="gpt2-medium")
set_seed(42)

def advanced_generate(prompt, max_length=250, temperature=0.7):
    """Generate AI response based on structured prompt."""
    response = generator(prompt, max_length=max_length, do_sample=True, temperature=temperature)
    return response[0]['generated_text']

# ----- Database Setup for Calendar Management -----
def get_db_connection():
    conn = sqlite3.connect('calendar.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database for event management."""
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TEXT NOT NULL,
                        event_time TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

init_db()

# ----- Itinerary Suggestion with Advanced LLM -----
def suggest_itinerary(destination):
    """Generate a structured 3-day travel itinerary."""
    prompt = (
        f"Generate a detailed 3-day travel itinerary for {destination}. "
        f"Include places to visit, activities for each day, and restaurant recommendations. "
        f"Follow this format:\n\n"

        f"Day 1:\n"
        f"- Morning: Visit [place] and enjoy [activity].\n"
        f"- Afternoon: Have lunch at [restaurant], then visit [place].\n"
        f"- Evening: Explore [area], have dinner at [restaurant], and enjoy [activity].\n"
        f"Note: [Short comment about the day]\n\n"

        f"Day 2:\n"
        f"- Morning: [activity]\n"
        f"- Afternoon: [activity]\n"
        f"- Evening: [activity]\n"
        f"Note: [comment]\n\n"

        f"Day 3:\n"
        f"- Morning: [activity]\n"
        f"- Afternoon: [activity]\n"
        f"- Evening: [activity]\n"
        f"Note: [comment]\n\n"

        f"Make sure to generate realistic and engaging activities."
    )

    itinerary = advanced_generate(prompt, max_length=350, temperature=0.7)
    return itinerary

# ----- Restaurant/Activity Recommendations with Advanced LLM -----
def recommend_restaurants(user_input):
    prompt = (
        f"Based on the following travel request, provide detailed restaurant and activity "
        f"recommendations with reasons and specifics:\n{user_input}\nRecommendations:"
    )
    recommendations = advanced_generate(prompt, max_length=250, temperature=0.8)
    return recommendations

# ----- Calendar Management -----
def handle_calendar_command(user_input):
    response = ""
    lower_input = user_input.lower().strip()

    # Adding an event
    if lower_input.startswith("add event:"):
        try:
            content = user_input[len("add event:"):].strip()
            description, event_time = content.split(",", 1)
            description = description.strip()
            event_time = event_time.strip()
            datetime.strptime(event_time, "%Y-%m-%d %H:%M")  # Validate datetime format

            conn = get_db_connection()
            conn.execute("INSERT INTO events (description, event_time) VALUES (?, ?)",
                         (description, event_time))
            conn.commit()
            conn.close()

            response = f"✅ Event '{description}' added for {event_time}."
        except Exception as e:
            response = "⚠️ Error: Use format -> add event: Description, YYYY-MM-DD HH:MM"

    # Viewing events
    elif lower_input.startswith("view events"):
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events ORDER BY event_time").fetchall()
        conn.close()
        if events:
            response = "**📅 Your Scheduled Events:**\n\n" + "\n".join(
                [f"📝 {event['id']}: {event['description']} at {event['event_time']}" for event in events])
        else:
            response = "📭 No upcoming events found."

    # Deleting an event
    elif lower_input.startswith("delete event:"):
        try:
            event_id = int(user_input[len("delete event:"):].strip())
            conn = get_db_connection()
            conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            conn.close()
            response = f"🗑️ Event with ID {event_id} deleted."
        except Exception:
            response = "⚠️ Error: Use format -> delete event: ID"
    else:
        response = ("📌 **Commands Available:**\n"
                    "- `add event: Description, YYYY-MM-DD HH:MM`\n"
                    "- `view events`\n"
                    "- `delete event: ID`")
    return response

# ----- Streamlit UI -----
st.title("🗺️ AI Travel Assistant")

user_input = st.text_input("💬 Ask me about your trip (e.g., 'Give me an itinerary for New York'):")

if user_input:
    lower_input = user_input.lower()

    # Check intent
    if "itinerary" in lower_input or "trip plan" in lower_input:
        destination = user_input.replace("give me an itinerary for", "").strip()
        if destination:
            itinerary = suggest_itinerary(destination)
            st.subheader(f"🌎 Travel Itinerary for {destination}")
            st.write(itinerary)
        else:
            st.error("⚠️ Please provide a valid destination.")

    elif "restaurant" in lower_input or "activity" in lower_input:
        recommendations = recommend_restaurants(user_input)
        st.subheader("🍽️ Restaurant & Activity Recommendations")
        st.write(recommendations)

    elif lower_input.startswith("add event:") or lower_input.startswith("view events") or lower_input.startswith("delete event:"):
        response = handle_calendar_command(user_input)
        st.subheader("📅 Calendar Response")
        st.write(response)

    else:
        st.warning("I can help with **itineraries, restaurant recommendations, and calendar management**. "
                   "Use keywords like 'itinerary', 'restaurant', or 'add event:'.")

