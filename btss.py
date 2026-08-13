import base64
import os
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# 1. PAGE CONFIG (Layout Centered force ku miterere ya Mobile UI)
# Twongereyeho page_title yihariye izatuma itagaragaramo "- Streamlit"
st.set_page_config(
    page_title="BULINGA TSS AI",
    page_icon="btss.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. HASHOWE KANGAHE KUGIRA NGO TITLE YA BROWSER YEMEZE NEZA IZINA RYAWE GUSA
st.markdown("""
    <script>
        document.title = "BULINGA TSS AI";
        const observer = new MutationObserver(function(mutations) {
            if (document.title.includes("Streamlit")) {
                document.title = "BULINGA TSS AI";
            }
        });
        observer.observe(document.querySelector('head'), { subtree: true, childList: true });
    </script>
""", unsafe_allow_html=True)

# 3. FUNCTION BWO GUHINDURA IFOTO MO BASE64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

img_base64 = get_base64_image("btss.png")

# 4. CUSTOM CSS (PURE BLACK DARK MODE & CHATGPT MOBILE STYLE BUBBLES)
bg_css = f"""
<style>
/* Pure Black OLED Background */
.stApp {{
    background-color: #000000 !important;
    color: #ffffff !important;
}}

/* Hide default Streamlit elements */
header, footer, [data-testid="stHeader"] {{ 
    display: none !important; 
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    max-width: 600px !important;
}}

/* Top App Bar Header UI (ChatGPT style) */
.top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0px 20px 0px;
    border-bottom: 1px solid #1a1a1a;
    margin-bottom: 20px;
}}

.top-bar-title {{
    font-size: 1.3rem;
    font-weight: 600;
    color: #ffffff;
}}

.top-bar-icons {{
    display: flex;
    gap: 18px;
    font-size: 1.2rem;
    color: #cccccc;
}}

/* Custom Chat Container Styling */
[data-testid="stChatMessageContent"] {{
    background-color: transparent !important;
    padding: 0px !important;
}}

/* User Message Container (Pill Right Aligned) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
    flex-direction: row-reverse !important;
    text-align: right !important;
    margin-bottom: 18px !important;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {{
    background-color: #2f2f2f !important;
    color: #ffffff !important;
    margin-left: auto !important;
    margin-right: 0px !important;
    padding: 12px 18px !important;
    border-radius: 22px !important;
    max-width: 80% !important;
    font-size: 1rem !important;
    line-height: 1.4 !important;
}}

/* Assistant Message Container (Left Aligned Plain Text) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
    flex-direction: row !important;
    text-align: left !important;
    margin-bottom: 22px !important;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {{
    background-color: transparent !important;
    color: #ffffff !important;
    margin-right: auto !important;
    margin-left: 0px !important;
    max-width: 100% !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
}}

/* Action Icons below AI Responses */
.action-bar {{
    display: flex;
    gap: 16px;
    color: #8e8e93;
    font-size: 1.05rem;
    margin-top: 8px;
    cursor: pointer;
}}

/* Hide Default Avatars */
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {{
    display: none !important;
}}

/* Custom Chat Input Box */
.stChatInputContainer {{
    background-color: #000000 !important;
}}

.stChatInput > div {{
    background-color: #2f2f2f !important;
    border-radius: 25px !important;
    border: none !important;
    color: #ffffff !important;
}}
</style>
"""

st.markdown(bg_css, unsafe_allow_html=True)

# Top Bar Header Interface
st.markdown("""
<div class="top-bar">
    <div style="font-size: 1.4rem; cursor: pointer;">☰</div>
    <div class="top-bar-title">BULINGA TSS AI </div>
    <div class="top-bar-icons">
        <span style="cursor: pointer;">📝</span>
        <span style="cursor: pointer;">⋮</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. API KEYS SETUP
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY ntiyabonywe muri Streamlit Secrets!")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=groq_api_key
)

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
    "You were created by Developer Kevin on July 25, 2026, at the afternoon.\n\n"
    
    "STRICT RULES:\n"
    "1. Answer ONLY questions related to Bulinga TSS using the detailed facts provided below.\n"
    "2. If asked who created you, always answer that you were created by Developer Kevin on July 25, 2026, in the afternoon.\n"
    "3. Politely refuse any question outside Bulinga TSS (e.g. general news, coding outside school context, external politics, etc.).\n"
    "4. Reply fluently in Kinyarwanda or English based on the user's language.\n"
    "5. Be warm, polite, concise, and remember to thank the user 👍 for interacting with you.\n\n"
    
    "BULINGA TSS COMPREHENSIVE KNOWLEDGE BASE:\n"
    "- LOCATION & NEIGHBORHOOD: Located in Mushishiro Sector, Muhanga District. Nearby places include ACODES (a private school), a Centre de Santé (Health Center), and a Catholic Church. Climate is usually cool/cold with occasional rain.\n"
    "- CONTACT INFORMATION: School Email: bulingatvetschool@gmail.com | Headmaster Email: munoel20@gmail.com | Phone: +250788546462\n"
    "- FEES & PAYMENTS:\n"
    "  * Total School Fees per term: 95,500 FRW (Minerval: 92,000 FRW + Ubwishingizi bw'impanuka: 1,500 FRW + Ikarita y'ishuri n'imyitwarire: 2,000 FRW).\n"
    "  * Bank Account: Umwalimu SACCO Account No: 900009815200\n"
    "  * Mobile Money Payment Code: *182*3*10*1*Code_y_umunyeshuri_yo_muri_SDMS#\n"
    "- SCHOOL RULES & PROHIBITED ITEMS:\n"
    "  * STRICTLY PROHIBITED: Laptop / Machine / Mudasobwa NIZEMEWE na kidogo k'abanyeshuri!\n"
    "  * WARNING/IKITONDERWA: Umunyeshuri uzazana ikintu icyo ari cyo cyose kitemewe mu ishuri aracyamburwa kandi NTABWO agisubizwa burundu!\n"
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
    "- ADMINISTRATION & STAFF: 33 Teachers. Head Master: MUVUNYI Noel (Email: munoel20@gmail.com). Administration includes DOS, DOD, 1 Patron, 1 Animatron, IT Person (Elies), and Accountant (Kontabule ushinzwe umutungo).\n"
    "- RELIGIONS IN SCHOOL (5): Catholic, Jehovah's Witnesses, Islam, La Jé Praix, SDA.\n"
    "- VISITING DAY: Last weekend/Sunday of every month.\n"
    "- WEEKDAY ROUTINE: 4:30 AM Wake up -> 5:30-7:00 AM Étude -> 7:00 AM Breakfast -> 8:00 AM Assembly -> Classes (Break @ 10:20 AM) -> 11:45 AM Lunch -> 1:10 PM Afternoon Classes -> 5:30-8:15 PM Evening Étude -> 8:30 PM Dinner -> 9:00 PM Sleep.\n"
    "- WEEKEND ROUTINE: Saturday: Étude -> Travaux/Cleaning -> Families -> Movies. Sunday: Étude -> Church -> Lunch -> Rest -> Evening Étude.\n"
    "- MEAL MENU: Mon: Kawunga/Ibijumba | Tue: Kawunga/Ubugari | Wed: Kawunga/Rice | Thu: Rice/Ubugari | Fri: Rice | Sat: Rice vs Ibijumba | Sun: Kawunga vs Rice\n"
)

# 6. SESSION STATE FOR CHAT
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Display Chat History Exact like ChatGPT Mobile App
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                st.markdown("""
                <div class="action-bar">
                    <span>📋</span>
                    <span>👍</span>
                    <span>👎</span>
                    <span>🔊</span>
                    <span>🔄</span>
                    <span>🔗</span>
                </div>
                """, unsafe_allow_html=True)

# 7. CHAT INPUT & RESPONSE
if prompt := st.chat_input("Ask related BULINGA TSS...."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner(""):
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

            message_placeholder.markdown(answer)
            st.markdown("""
            <div class="action-bar">
                <span>📋</span>
                <span>👍</span>
                <span>👎</span>
                <span>🔊</span>
                <span>🔄</span>
                <span>🔗</span>
            </div>
            """, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"Harimo ikosa: {e}")
