import os
import streamlit as st
from openai import OpenAI

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Bulinga TSS AI",
    page_icon="🏫",
    layout="centered"
)

# 2. API KEY SETUP (Iba muri Streamlit Secrets, itabonetse ikafata iyawe nshya)
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    groq_api_key = "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"

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=groq_api_key
)

SYSTEM_PROMPT = (
    "You are the official AI assistant for Bulinga TSS, a TVET school located in Muhanga District, Mushishiro Sector.\n"
    "You were built and created by Developer Kevin on July 25, 2026, in the afternoon.\n\n"
    "STRICT RULES:\n"
    "1. You are ONLY allowed to answer questions related to Bulinga TSS "
    "(such as trades/courses offered, admission, location in Mushishiro, timetables, fees, exams, and school life).\n"
    "2. If asked who built or created you, state clearly that you were created by Developer Kevin on July 25, 2026, in the afternoon.\n"
    "3. If a user asks about anything outside Bulinga TSS (general knowledge, coding, politics, entertainment, etc.), "
    "politely refuse and state that your expertise is strictly limited to Bulinga TSS.\n"
    "4. Respond fluently in Kinyarwanda or English depending on the user's input.\n"
    "5. Keep responses concise, warm, helpful, and courteous. Always remember to thank the user 👍 for interacting with you."
)

st.title("🏫 Bulinga TSS AI Assistant")
st.write("Official Assistant for Bulinga TSS located in Mushishiro, Muhanga.")

# 3. SESSION STATE FOR CHAT
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Display chat history (excluding system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 4. CHAT INPUT
if prompt := st.chat_input("Baza ikibazo kuri Bulinga TSS..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Bulinga TSS AI irimo gutekereza..."):
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state.messages,
                temperature=0.3,
                max_tokens=1024
            )
            
            answer = completion.choices[0].message.content
            if "</think>" in answer:
                answer = answer.split("</think>")[-1]
            answer = answer.replace("<think>", "").strip()

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            
    except Exception as e:
        st.error(f"Harimo ikosa: {e}")
