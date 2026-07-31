import os
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Bulinga TSS AI",
    page_icon="🏫",
    layout="centered"
)

# 2. CUSTOM CSS (RAINBOW BACKGROUND) & JAVASCRIPT (POPUP ALERT)
st.markdown(
    """
    <style>
    /* Animation y'amabara y'umukororobya (Rainbow Background) */
    @keyframes rainbowGlow {
        0%   { background-color: #ffadad; }
        14%  { background-color: #ffd6a5; }
        28%  { background-color: #fdffb6; }
        42%  { background-color: #caffbf; }
        57%  { background-color: #9bf6ff; }
        71%  { background-color: #a0c4ff; }
        85%  { background-color: #bdb2ff; }
        100% { background-color: #ffadad; }
    }

    .stApp {
        animation: rainbowGlow 15s infinite alternate ease-in-out;
    }
    </style>

    <script>
    // Popup Alert buri masogonda 5 (5000 milliseconds)
    setInterval(function() {
        alert("Enjoy for using BULINGA TSS AI !!");
    }, 5000);
    </script>
    """,
    unsafe_allow_html=True
)

# 3. API KEYS SETUP
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    groq_api_key = "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"

try:
    tavily_api_key = st.secrets["TAVILY_API_KEY"]
except Exception:
    tavily_api_key = "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" 

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=groq_api_key
)

# Tangiza Tavily Client
tavily_client = None
if tavily_api_key:
    try:
        tavily_client = TavilyClient(api_key=tavily_api_key)
    except Exception:
        tavily_client = None


def get_live_nesa_search(query: str) -> str:
    """Ifata amakuru agezweho kuri Google/NESA binyuze muri Tavily niba ikibazo kijyanye no bataha/itangira"""
    if not tavily_client:
        return ""
    
    keywords = ["nesa", "itangira", "gutaha", "kugaruka", "ibiruhuko", "itangazo", "calendar", "igikuba", "mineduc"]
    
    if any(word in query.lower() for word in keywords):
        try:
            search_result = tavily_client.search(
                query=f"NESA Rwanda school calendar official updates {query}",
                max_results=2
            )
            results = [r['content'] for r in search_result.get('results', [])]
            if results:
                return "\n\n[LIVE SEARCH DATA FROM NESA/MINEDUC]:\n" + "\n".join(results)
        except Exception:
            return ""
    return ""


SYSTEM_PROMPT = (
    "You are the official AI assistant for Bulinga TSS (Bulinga TVET School), located in Muhanga District, Mushishiro Sector.\n"
    "You were created by Developer Kevin on July 25, 2026, in the afternoon.\n\n"
    
    "STRICT RULES:\n"
    "1. Answer ONLY questions related to Bulinga TSS using the detailed facts provided below.\n"
    "2. If asked who created you, always answer that you were created by Developer Kevin on July 25, 2026, in the afternoon.\n"
    "3. Politely refuse any question outside Bulinga TSS (e.g. general news, coding outside school context, external politics, etc.).\n"
    "4. Reply fluently in Kinyarwanda or English based on the user's language.\n"
    "5. Be warm, polite, concise, and remember to thank the user 👍 for interacting with you.\n\n"
    
    "BULINGA TSS COMPREHENSIVE KNOWLEDGE BASE:\n"
    "- LOCATION & NEIGHBORHOOD: Located in Mushishiro Sector, Muhanga District. Nearby places include ACODES (a private school), a Centre de Santé (Health Center), and a Catholic Church. Climate is usually cool/cold with occasional rain.\n"
    "- HOW TO GET THERE: From Muhanga Taxi Park, take a bus heading to Bulinga, drop off at the tarmac road (kaburimbo), take the dirt road passing through Kabadaha center, go through 4 corners/bends (amakorosi 4) to reach the school.\n"
    "- ACADEMIC LEVEL & COURSES: The school offers A'Level ONLY (No O'Level). Offers Level 3 to Level 5 TVET Trades:\n"
    "  * Software Development: L3 SOD, L4 SOD, L5 SOD\n"
    "  * Networking and Internet Technology: L3 NIT, L4 NIT, L5 NIT\n"
    "  * Computer System and Architecture: L3 CSA, L4 CSA, L5 CSA\n"
    "  * Accounting: S4 ACC, S5 ACC, S6 ACC\n"

    "- SCHOOL CALENDAR & DATES:\n"
    "  * TERM 1: Amashuri atangira muri September, abanyeshuri bataha muri December, bakagaruka muri January.\n"
    "  * TERM 2: Atangira muri January, abanyeshuri bataha muri March/April, bakagaruka muri April.\n"
    "  * TERM 3: Atangira muri April, abanyeshuri bataha muri July, bakazagaruka muri September.\n"
    "  * GENERAL RETURNING RULE: Abanyeshuri bagaruka ku Dimanche mbere ya 5:00 PM kabura gato amashuri agatangira ku Mbere.\n"

    "- FACILITIES & INFRASTRUCTURE: 16 Classrooms, 1 large Hall, 4 Computer Labs (SOD LAB, NIT LAB, ACC LAB, CSA LAB). Fast EdNet internet. Compound fully paved & brick wall fence. Blue painted doors/windows. Clean gardens. 3 Sports fields (Football, Basketball, Volleyball).\n"
    "- UNIFORM CODE: Boys wear black pants, blue shirts, black short shoes with small heels. Girls wear black dresses, blue shirts, black short shoes with small heels.\n"
    "- ADMINISTRATION & STAFF: 33 Teachers. Head Master: MUVUNYI Noel. Administration includes DOS, DOD, 1 Patron, 1 Animatron, IT Person (Elies), and Accountant (Kontabule ushinzwe umutungo).\n"
    "- RELIGIONS IN SCHOOL (5): Catholic, Jehovah's Witnesses, Islam, La Jé Praix, SDA.\n"
    "- VISITING DAY: Last weekend/Sunday of every month.\n"
    "- WEEKDAY ROUTINE: 4:30 AM Wake up -> 5:30-7:00 AM Étude -> 7:00 AM Breakfast -> 8:00 AM Assembly -> Classes (Break @ 10:20 AM) -> 11:45 AM Lunch -> 1:10 PM Afternoon Classes -> 5:30-8:15 PM Evening Étude -> 8:30 PM Dinner -> 9:00 PM Sleep.\n"
    "- WEEKEND ROUTINE: Saturday: Étude -> Travaux/Cleaning -> Families -> Movies. Sunday: Étude -> Church -> Lunch -> Rest -> Evening Étude.\n"
    "- MEAL MENU: Mon: Kawunga/Ibijumba | Tue: Kawunga/Ubugari | Wed: Kawunga/Rice | Thu: Rice/Ubugari | Fri: Rice | Sat: Rice vs Ibijumba | Sun: Kawunga vs Rice\n"
)

st.title("🏫 Bulinga TSS AI Assistant")
st.write("Official Assistant for Bulinga TSS located in Mushishiro, Muhanga.")

# 4. SESSION STATE FOR CHAT
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Display chat history (Koresha btss.png nka Avatar ku bisubizo bya assistant)
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar_img = "btss.png" if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar_img):
            st.markdown(message["content"])

# 5. CHAT INPUT
if prompt := st.chat_input("Baza ikibazo kuri Bulinga TSS..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Bulinga TSS AI irimo gushaka no gutekereza..."):
            
            # Kora Search binyuze muri Tavily niba ikibazo kirimo amagambo ya NESA
            live_data = get_live_nesa_search(prompt)
            
            current_messages = list(st.session_state.messages)
            if live_data:
                current_messages[-1] = {
                    "role": "user", 
                    "content": f"{prompt}\n\n[Use this live information if applicable]:{live_data}"
                }

            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=current_messages,
                temperature=0.3,
                max_tokens=1024
            )
            
            answer = completion.choices[0].message.content
            if "</think>" in answer:
                answer = answer.split("</think>")[-1]
            answer = answer.replace("<think>", "").strip()

        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Baza igisubizo cya assistant uherekeje na logo ya btss.png
        with st.chat_message("assistant", avatar="btss.png"):
            st.markdown(answer)
            
    except Exception as e:
        st.error(f"Harimo ikosa: {e}")
