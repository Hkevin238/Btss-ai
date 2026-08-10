import base64
import os
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Bulinga TSS AI",
    page_icon="btss.png",
    layout="centered"
)

# 2. FUNCTION BWO GUHINDURA IFOTO MO BASE64 KU ZERA MURI BACKGROUND
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

img_base64 = get_base64_image("btss.png")

# 3. CUSTOM CSS (BACKGROUND WATERMARK & UI Y'UBUTUMWA: USER -> RIGHT, AI -> LEFT)
bg_css = f"""
<style>
/* Watermark Background */
.stApp::before {{
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-image: url('data:image/png;base64,{img_base64}');
    background-size: 380px;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0.12;
    z-index: -1;
    pointer-events: none;
}}

/* Container yo gutunganya ubutumwa bwose */
[data-testid="stChatMessageContent"] {{
    border-radius: 18px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    line-height: 1.4 !important;
}}

/* Ubutumwa bwa User (Kujyana Iburyo - Right side) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
    flex-direction: row-reverse !important;
    text-align: right !important;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {{
    background-color: #2f2f2f !important;
    color: #ffffff !important;
    margin-left: auto !important;
    margin-right: 0px !important;
    border-radius: 18px 18px 4px 18px !important;
    max-width: 80% !important;
}}

/* Ubutumwa bwa AI / Assistant (Kuba Ibumoso - Left side) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
    flex-direction: row !important;
    text-align: left !important;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {{
    background-color: transparent !important;
    color: #ffffff !important;
    margin-right: auto !important;
    margin-left: 0px !important;
    border-radius: 18px 18px 18px 4px !important;
    max-width: 85% !important;
}}

/* Guhisha avatar y'umukoresha (User Avatar) */
[data-testid="stChatMessageAvatarUser"] {{
    display: none !important;
}}
</style>

<script>
// Popup Alert buri masogonda 5
setInterval(function() {{
    alert("Enjoy using BULINGA TSS AI !!");
}}, 5000);
</script>
"""

st.markdown(bg_css, unsafe_allow_html=True)

# 4. API KEYS SETUP (Guhingura muri Secrets neza)
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY ntiyabonywe muri Streamlit Secrets!")
    st.stop()

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

st.title("🏫 Bulinga TSS AI Assistant")
st.write("Official Assistant for Bulinga TSS located in Muhanga, Mushishiro.")

# 5. SESSION STATE FOR CHAT
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Display chat history
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar_img = "btss.png" if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar_img):
            st.markdown(message["content"])

# 6. CHAT INPUT & RESPONSE
if prompt := st.chat_input("Ask related Bulinga TSS..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant", avatar="btss.png"):
            message_placeholder = st.empty()
            
            with st.status("Bulinga TSS AI thinking....", expanded=False) as status:
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
                
                status.update(label="Done!", state="complete", expanded=False)

            message_placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"Harimo ikosa: {e}")
