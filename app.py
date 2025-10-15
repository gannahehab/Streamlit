import streamlit as st
import random
import time

st.title("🎭 Mood Randomizer App")

moods = {
    "Happy": "😄 You’re radiating sunshine today!",
    "Tired": "😴 You deserve a nap (or 3).",
    "Focused": "🎯 Nothing can stop you right now.",
    "Stressed": "💥 Take a deep breath — you’ve got this.",
    "Curious": "🧠 Curiosity creates genius.",
    "Chill": "🧊 You’re in your calm era.",
    "Powerful": "🔥 No one’s competing with you — it’s your day."
}

if st.button("🔮 Reveal My Mood"):
    with st.spinner("Analyzing your aura..."):
        time.sleep(1.5)
    mood, message = random.choice(list(moods.items()))
    st.subheader(f"{mood} {message}")

st.caption("✨ Click again to see what your vibe is this time!")
