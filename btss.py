import os
import streamlit as st
from PIL import Image
from groq import Groq
import urllib.parse

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="BULINGA TSS AI",
    page_icon="btss.png",
    layout="centered",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. THEME STATE INITIALIZATION (DARK / LIGHT MODE)
# =========================================================

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark Mode 🌙"


# =========================================================
# 3. CUSTOM CSS (DYNAMIC BASED ON THEME)
# =========================================================

if st.session_state.theme_mode == "Dark Mode 🌙":
    bg_color = "#121212"
    app_bg_image = """
        radial-gradient(6px 6px at 20px 30px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(8px 8px at 40px 70px, #0084ff, rgba(0,0,0,0)),
        radial-gradient(5px 5px at 90px 40px, #ffd700, rgba(0,0,0,0)),
        radial-gradient(7px 7px at 160px 120px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(6px 6px at 230px 180px, #0084ff, rgba(0,0,0,0)),
        radial-gradient(8px 8px at 350px 250px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(6px 6px at 450px 350px, #ffd700, rgba(0,0,0,0))
    """
    text_color = "#e4e6eb"
    sidebar_bg = "#18191a"
    chat_input_bg = "#242526"
    chat_input_border = "#3a3b3c"
    chat_input_text = "#e4e6eb"
    assistant_bubble_bg = "#3a3b3c"
    assistant_bubble_text = "#e4e6eb"
    btn_bg = "#3a3b3c"
    btn_color = "#e4e6eb"
else:
    bg_color = "#f0f2f6"
    app_bg_image = "none"
    text_color = "#111111"
    sidebar_bg = "#ffffff"
    chat_input_bg = "#ffffff"
    chat_input_border = "#cccccc"
    chat_input_text = "#111111"
    assistant_bubble_bg = "#e0e0fb"
    assistant_bubble_text = "#111111"
    btn_bg = "#e0e0e0"
    btn_color = "#111111"

st.markdown(f"""
<style>
@keyframes moveSparkles {{
    0% {{ background-position: 0 0, 0 0, 0 0; }}
    100% {{ background-position: -10000px 5000px, 5000px -10000px, -7500px -7500px; }}
}}

.stApp {{
    background-color: {bg_color} !important;
    background-image: {app_bg_image} !important;
    background-repeat: repeat !important;
    background-size: 500px 500px !important;
    animation: moveSparkles 80s linear infinite !important;
    color: {text_color} !important;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ background: transparent !important; }}

@keyframes bounceSlow {{
    0% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-8px); }}
    100% {{ transform: translateY(0px); }}
}}

.moving-title {{
    display: inline-block;
    animation: bounceSlow 3s ease-in-out infinite;
}}

.chat-row {{
    display: flex;
    width: 100%;
    margin-top: 10px;
    margin-bottom: 10px;
}}

.chat-row.user {{ justify-content: flex-end; }}
.chat-row.assistant {{ justify-content: flex-start; }}

.chat-bubble {{
    max-width: 75%;
    padding: 10px 14px;
    font-size: 15px;
    line-height: 1.4;
    word-wrap: break-word;
}}

.chat-bubble a {{
    color: #4dabf7 !important;
    text-decoration: underline !important;
}}

.chat-row.user .chat-bubble {{
    background-color: #0084ff;
    color: #ffffff;
    border-radius: 18px 18px 4px 18px;
}}

.chat-row.assistant .chat-bubble {{
    background-color: {assistant_bubble_bg};
    color: {assistant_bubble_text};
    border-radius: 18px 18px 18px 4px;
}}

.stChatInputContainer {{
    background-color: {chat_input_bg} !important;
    border-radius: 24px !important;
    border: 1px solid {chat_input_border} !important;
    padding: 4px 12px !important;
}}

.stChatInputContainer textarea {{
    color: {chat_input_text} !important;
    font-size: 15px !important;
}}

.thinking-text {{
    font-style: italic;
    color: #b0b3b8;
}}

section[data-testid="stSidebar"] {{
    background-color: {sidebar_bg} !important;
}}

.stButton button {{
    border-radius: 8px !important;
    border: none !important;
    background-color: {btn_bg} !important;
    color: {btn_color} !important;
}}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 4. SESSION STATE & LOCAL STORAGE INITIALIZATION (NO DB)
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = "Main Chat"

if "users_db" not in st.session_state:
    st.session_state.users_db = {"admin": "1234"}

if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}

def load_chat_history(username, session_id):
    key = f"{username}_{session_id}"
    return st.session_state.chat_histories.get(key, [])

def save_message_to_db(username, session_id, role, content, show_image=False, generated_img_url=None):
    key = f"{username}_{session_id}"
    if key not in st.session_state.chat_histories:
        st.session_state.chat_histories[key] = []
    st.session_state.chat_histories[key].append({
        "role": role,
        "content": content,
        "show_image": show_image,
        "generated_img_url": generated_img_url
    })

def verify_user(username, password):
    if username in st.session_state.users_db and st.session_state.users_db[username] == password:
        return True, "Login successfully"
    return False, "Izina ry'umukoresha cyangwa ijambo ry'ibanga ntabwo aribyo."

def create_user(username, password):
    if username in st.session_state.users_db:
        return False, "Konti ifite iri zina isanzweho."
    if not username or not password:
        return False, "Nyamuneka yuzuza ibisabwa byose."
    st.session_state.users_db[username] = password
    return True, "Konti yaremwe neza!"


# =========================================================
# 5. UI DICTIONARY (TRANSLATIONS FOR SYSTEM INTERFACE)
# =========================================================

translations = {
    "Kinyarwanda": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Nyamuneka Injira, Iyandikishe, cyangwa Ukomeze nka Guest 🔐",
        "auth_choice": "Hitamo Igikorwa",
        "mode_login": "Injira",
        "mode_signup": "Iyandikishe",
        "user_label": "Izina ry'ukoresha (Username)",
        "pass_label": "Ijambo ry'ibanga (Password)",
        "signup_btn": "Fungura Konti 🚀",
        "login_btn": "Injira 🔓",
        "or_text": "- CYANGWA -",
        "guest_btn": "Koresha utiyandikishije ⚡",
        "sidebar_control": "🔐 Konti n'Uburenganzira",
        "logged_in_as": "👤 Winjiye nka",
        "logout_btn": "Sohoka 🚪",
        "theme_header": "🎨 Ishusho y'Aha hagaragara",
        "theme_choice": "Hitamo Uburyo",
        "lang_header": "🌐 Ururimi rwose (Global Language)",
        "lang_choice": "Hitamo Ururimi rwa System",
        "response_lang_choice": "Hitamo Ururimi rw'Igisubizo",
        "clear_history": "🗑️ Hanagura Amateka y'Ibiganiro",
        "upload_header": "📎 Shyiramo Dosiye / Ifoto",
        "upload_label": "Shyiramo ifoto cyangwa dosiye",
        "main_title": "Umufasha wa BULINGA TSS",
        "chat_placeholder": "Baza icyo ushaka cyose cyangwa wandike uti 'Amakuru ya Bulinga...' 💬",
        "thinking": "⚪ BULINGA AI irimo gutekereza... 💭",
        "img_resp": "Dore amafoto ajyanye na Bulinga Technical Secondary School nk'uko wabinsabye! 📸✨",
        "gen_img_resp": "Dore ifoto wasabye ko nkukorera cyangwa ko nkushushanyiriza! 🎨✨",
        "map_resp": "Urashaka kureba aho ishuri riherereye? Ushobora gukanda hano wanditse <a href=\"https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ\" target=\"_blank\">Google Map</a> kugira ngo ubashe kureba icyerekezo cy'ishuri ryacu! 🗺️📍✨"
    },
    "English": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Please Login, Sign Up, or Continue as Guest 🔐",
        "auth_choice": "Choose Action",
        "mode_login": "Login",
        "mode_signup": "Sign Up",
        "user_label": "Username",
        "pass_label": "Password",
        "signup_btn": "Create Account 🚀",
        "login_btn": "Login 🔓",
        "or_text": "- OR -",
        "guest_btn": "Use without Register ⚡",
        "sidebar_control": "🔐 Account & Control",
        "logged_in_as": "👤 Logged in as",
        "logout_btn": "Logout 🚪",
        "theme_header": "🎨 Appearance / Theme",
        "theme_choice": "Choose Mode",
        "lang_header": "🌐 Global Language Settings",
        "lang_choice": "Choose System Language",
        "response_lang_choice": "Choose Response Language",
        "clear_history": "🗑️ Clear Current History",
        "upload_header": "📎 Upload Files / Photos",
        "upload_label": "Upload image or document",
        "main_title": "BULINGA AI Assistant",
        "chat_placeholder": "Ask anything or type like 'What about Bulinga info...' 💬",
        "thinking": "⚪ BULINGA AI is thinking....",
        "img_resp": "Here are the photos related to Bulinga Technical Secondary School as you requested! 📸✨",
        "gen_img_resp": "Here is the generated image you asked me to create! 🎨✨",
        "map_resp": "Do you want to see where the school is located? You can click here to open <a href=\"https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ\" target=\"_blank\">Google Map</a> to find the direction to our school! 🗺️📍✨"
    },
    "Français": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Veuillez vous connecter, vous inscrire ou continuer en tant qu'invité 🔐",
        "auth_choice": "Choisir une action",
        "mode_login": "Connexion",
        "mode_signup": "S'inscrire",
        "user_label": "Nom d'utilisateur",
        "pass_label": "Mot de passe",
        "signup_btn": "Créer un compte 🚀",
        "login_btn": "Se connecter 🔓",
        "or_text": "- OU -",
        "guest_btn": "Utiliser sans s'inscrire ⚡",
        "sidebar_control": "🔐 Compte et contrôle",
        "logged_in_as": "👤 Connecté en tant que",
        "logout_btn": "Se déconnecter 🚪",
        "theme_header": "🎨 Apparence / Thème",
        "theme_choice": "Choisir le mode",
        "lang_header": "🌐 Paramètres de langue globale",
        "lang_choice": "Choisir la langue du système",
        "response_lang_choice": "Choisir la langue de réponse",
        "clear_history": "🗑️ Effacer l'historique actuel",
        "upload_header": "📎 Télécharger des fichiers / Photos",
        "upload_label": "Télécharger une image ou un document",
        "main_title": "Assistant IA BULINGA",
        "chat_placeholder": "Posez une question ou tapez 'générer une image de...' 💬",
        "thinking": "⚪ BULINGA AI réfléchit....",
        "img_resp": "Voici les photos relatives à l'École Secondaire Technique de Bulinga comme demandé ! 📸✨",
        "gen_img_resp": "Voici l'image générée que vous m'avez demandé de créer ! 🎨✨",
        "map_resp": "Voulez-vous voir où se trouve l'école ? Vous pouvez cliquer ici pour ouvrir <a href=\"https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ\" target=\"_blank\">Google Map</a> pour trouver l'itinéraire ! 🗺️📍✨"
    },
    "Kiswahili": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Tafadhali Ingia, Jisajili, au Endelea kama Mgeni 🔐",
        "auth_choice": "Chagua Hatua",
        "mode_login": "Ingia",
        "mode_signup": "Jisajili",
        "user_label": "Jina la mtumiaji",
        "pass_label": "Nenosiri",
        "signup_btn": "Fungua Akaunti 🚀",
        "login_btn": "Ingia 🔓",
        "or_text": "- AU -",
        "guest_btn": "Tumia bila kusajili ⚡",
        "sidebar_control": "🔐 Akaunti na Udhibiti",
        "logged_in_as": "👤 Umeingia kama",
        "logout_btn": "Toka 🚪",
        "theme_header": "🎨 Mwonekano / Mandhari",
        "theme_choice": "Chagua Hali",
        "lang_header": "🌐 Mipangilio ya Lugha ya Kimataifa",
        "lang_choice": "Chagua Lugha ya Mfumo",
        "response_lang_choice": "Chagua Lugha ya Jibu",
        "clear_history": "🗑️ Futa Historia ya Sasa",
        "upload_header": "📎 Pakia Faili / Picha",
        "upload_label": "Pakia picha au waraka",
        "main_title": "Msaidizi wa AI wa BULINGA",
        "chat_placeholder": "Uliza chochote auandike 'tengeneza picha ya...' 💬",
        "thinking": "⚪ BULINGA AI inafikiri....",
        "img_resp": "Hapa kuna picha zinazohusiana na Shule ya Sekondari ya Ufundi ya Bulinga kama ulivyoomba! 📸✨",
        "gen_img_resp": "Hapa kuna picha uliyoniomba nitengeneze! 🎨✨",
        "map_resp": "Je, unataka kuona shule ilipo? Unaweza kubonyeza hapa kufungua <a href=\"https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ\" target=\"_blank\">Google Map</a> kupata mwelekeo wa shule yetu! 🗺️📍✨"
    }
}

AVAILABLE_LANGUAGES = ["Kinyarwanda", "English", "Français", "Kiswahili"]


# =========================================================
# 6. AUTHENTICATION SYSTEM
# =========================================================

if not st.session_state.logged_in:
    login_lang = st.selectbox("🌐 Choose Language / Hitamo Ururimi", AVAILABLE_LANGUAGES, index=0)
    t = translations[login_lang]

    st.markdown(f'<h1 class="moving-title" style="text-align: center;">{t["login_title"]}</h1>', unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #b0b3b8;'>{t['login_desc']}</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_mode = st.radio(t["auth_choice"], [t["mode_login"], t["mode_signup"]], horizontal=True)

        username_input = st.text_input(t["user_label"])
        password_input = st.text_input(t["pass_label"], type="password")

        if auth_mode == t["mode_signup"]:
            if st.button(t["signup_btn"], use_container_width=True):
                if username_input and password_input:
                    success, msg = create_user(username_input, password_input)
                    if success:
                        st.success("✅ Account created successfully! Please switch to Login." if login_lang == "English" else "✅ Konti yaremwe neza! Nyamuneka hindura ujye aho kwinjira.")
                    else:
                        st.error(f"⚠️ {msg}")
                else:
                    st.warning("⚠️ Please fill in all fields." if login_lang == "English" else "⚠️ Nyamuneka  kora ibice byose bisabwa.")
        else:
            if st.button(t["login_btn"], use_container_width=True):
                success, msg = verify_user(username_input, password_input)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username_input
                    st.success(f"🎉 Welcome back, {username_input}!" if login_lang == "English" else f"🎉 Murakaza neza, {username_input}!")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        st.markdown(f"<div style='text-align: center; margin: 10px 0; color: #b0b3b8;'>{t['or_text']}</div>", unsafe_allow_html=True)

        if st.button(t["guest_btn"], use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.current_user = "Guest"
            st.rerun()

    st.stop()


# =========================================================
# 7. SIDEBAR
# =========================================================

st.sidebar.subheader("🌐 Global Language")
selected_lang = st.sidebar.selectbox("Choose System Language", AVAILABLE_LANGUAGES, index=0)
t = translations[selected_lang]

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Response Language")
response_lang = st.sidebar.selectbox(t["response_lang_choice"], AVAILABLE_LANGUAGES, index=0)

st.sidebar.title(t["sidebar_control"])
st.sidebar.write(f"{t['logged_in_as']}: **{st.session_state.current_user}**")

if st.sidebar.button(t["logout_btn"]):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader(t["theme_header"])
selected_theme = st.sidebar.radio(t["theme_choice"], ["Dark Mode 🌙", "Light Mode ☀️"], index=0 if st.session_state.theme_mode == "Dark Mode 🌙" else 1)
if selected_theme != st.session_state.theme_mode:
    st.session_state.theme_mode = selected_theme
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button(t["clear_history"]):
    key = f"{st.session_state.current_user}_{st.session_state.current_session_id}"
    if key in st.session_state.chat_histories:
        st.session_state.chat_histories[key] = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader(t["upload_header"])
uploaded_file = st.sidebar.file_uploader(t["upload_label"], type=["png", "jpg", "jpeg", "pdf", "txt"])

# =========================================================
# 8. BULINGA AI SYSTEM PROMPT
# =========================================================

BULINGA_INFO = """
You are BULINGA AI, an official AI assistant built exclusively
for BULINGA TECHNICAL SECONDARY SCHOOL (BULINGA TS SCHOOL).

CRITICAL RULE REGARDING CREATOR:
- You were developed, created, and built exclusively by Developer/Programmer Kevin.
- NEVER mention OpenAI, ChatGPT, or any other outside entities as your creator. If anyone asks who made you, built you, or programmed you, proudly state that you were developed and built by Developer Kevin 👨‍💻🚀 and his email: therealhacks583@gmail.com , Website: www.kevinhakiza.com (not BULINGA TSS programmers).

EMOJI RULE:
- Always include relevant, cool, and engaging emojis (such as 🏫, 📚, 💡, ✨, 👨‍💻, 👍,💕,👀,😃,🤗,🔥 etc.) in your responses to make them lively and friendly.

CORE RULE:
You are a helpful, smart, and versatile assistant. Answer any questions the user asks—whether it's about general knowledge, coding, science, mathematics, geography, history, everyday life, or specific details about BULINGA TVET SCHOOL. Never refuse to answer general questions; be helpful and accurate on all topics while proudly representing BULINGA TVET SCHOOL! 🌍💡

SCHOOL DETAILS & STRATEGIC PLAN (2026-2030):
School Name: BULINGA TECHNICAL SECONDARY SCHOOL (BULINGA TSS) 🏫
Vision: “To become a center of excellence in ICT and business education, producing competent, innovative graduates who drive Rwanda's digital economy and entrepreneurship by 2030.”
Mission: “To provide quality, competency-based technical and vocational education that equips learners with relevant ICT, business, and soft skills for successful careers and sustainable socio-economic development.”
Location: Kiyoro Village, Munazi Cell, Mushishiro Sector, Muhanga District, Southern Province, Rwanda 📍.
School Fees & Financials: 96,000 Frw + 1,500 Frw Insurance + 2,000 Frw ID/Card = 96,500 Frw Total 💰. Total 5-year Strategic Plan budget is RWF 850,000,000 (2026-2030).
Account: Mwarimu Sacco, Account Number: 900009815200, Account Name: BULINGA TVET SCHOOL 🏦.
Programs & Combinations: 
- Software Development (Levels 3, 4 & 5)
- Network and internet technology (Levels 3, 4, 5)
- Computer system and architecture (Levels 3, 4, 5)
- Accounting (Senior 4, 5, 6) OR (year 1, year 2,year 3)
Student & Staff Stats: Approximately 582 students, 32 trainers and support personnel.
Contacts: Headmaster (0788546462) MUVUNYI Noel(Umuyobozi Mukuru W'ishuri), Bursar (0782612675), DOD (0785979951) NIYUKURI Adrien, DOS (0784020929) Vital 📞.
"""


# =========================================================
# 9. GROQ API KEY & CLIENT
# =========================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY or "YOUR_GROQ_API_KEY"
)


# =========================================================
# 10. MAIN HEADER & ROTATING THANK YOU MESSAGE
# =========================================================

st.markdown(f'<h1 class="moving-title">{t["main_title"]}</h1>', unsafe_allow_html=True)

@st.fragment(run_every=8)
def show_rotating_thank_you():
    if "thank_you_toggle" not in st.session_state:
        st.session_state.thank_you_toggle = True
    else:
        st.session_state.thank_you_toggle = not st.session_state.thank_you_toggle

    if st.session_state.thank_you_toggle:
        st.markdown("<p style='color: #4dabf7; font-weight: 500;'>Urakaza neza kuri BTSS AI Assistant! 🙏✨</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #4dabf7; font-weight: 500;'>Thanks for using BTSS AI Assistant! 🚀✨</p>", unsafe_allow_html=True)

show_rotating_thank_you()

current_messages = load_chat_history(st.session_state.current_user, st.session_state.current_session_id)


# =========================================================
# 11. DISPLAY CHAT HISTORY
# =========================================================

for message in current_messages:
    role = message["role"]
    content = message["content"]

    if role == "user":
        st.markdown(f'<div class="chat-row user"><div class="chat-bubble">{content}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-row assistant"><div class="chat-bubble">{content}</div></div>', unsafe_allow_html=True)
        if message.get("show_image", False):
            if os.path.exists("bulinga.png"):
                st.image("bulinga.png", caption="BULINGA TSS- Ifoto y'ibiro(front-view) by'Ishuri 🏫", use_container_width=True)
            if os.path.exists("btss.png"):
                st.image("btss.png", caption="BULINGA TSS- Ifoto ya BTSS ✨", use_container_width=True)
        if message.get("generated_img_url"):
            st.image(message["generated_img_url"], caption="Generated Image 🎨✨", use_container_width=True)


# =========================================================
# 12. CHAT INPUT & RESPONSE HANDLING (WITH IMAGE AUTO GENERATE)
# =========================================================

user_query = st.chat_input(t["chat_placeholder"])

if user_query or uploaded_file:
    file_context_msg = ""
    if uploaded_file is not None:
        file_context_msg = f"\n[Attached File: {uploaded_file.name}]"

    full_user_input = (user_query or "") + file_context_msg

    save_message_to_db(st.session_state.current_user, st.session_state.current_session_id, "user", full_user_input)
    st.markdown(f'<div class="chat-row user"><div class="chat-bubble">{full_user_input}</div></div>', unsafe_allow_html=True)

    query_lower = (user_query or "").lower()
    image_keywords = ["foto", "photo", "ishuri", "school", "ifoto", "icyapa", "image", "logo", "akarango"]
    is_image_query = any(kw in query_lower for kw in image_keywords)

    map_keywords = ["map", "google map", "ahoherereye", "location", "icyerekezo", "direction", "irebe", "aho riherereye"]
    is_map_query = any(kw in query_lower for kw in map_keywords)

    # Image generation check keywords (e.g. generate image, kora ifoto, shushanya, draw, etc.)
    gen_img_keywords = ["generate image", "kora ifoto", "shushanya", "draw", "create image", "ushushanye", "rekama ifoto", "image ya"]
    is_gen_img_query = any(kw in query_lower for kw in gen_img_keywords)

    thinking_placeholder = st.empty()
    thinking_placeholder.markdown(
        f'<div class="chat-row assistant"><div class="chat-bubble thinking-text">{t["thinking"]}</div></div>',
        unsafe_allow_html=True
    )

    try:
        messages_payload = [
            {
                "role": "system",
                "content": BULINGA_INFO + f"\n\nCURRENT RESPONSE LANGUAGE REQUIREMENT:\n{response_lang}\nYou MUST strictly answer the user in this exact language ({response_lang}) and include cool emojis! 🚀"
            }
        ]

        current_messages = load_chat_history(st.session_state.current_user, st.session_state.current_session_id)
        for message in current_messages:
            messages_payload.append({
                "role": message["role"],
                "content": message["content"]
            })

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages_payload,
            temperature=0.7,
            max_tokens=1024
        )

        response_text = completion.choices[0].message.content
        thinking_placeholder.empty()

        generated_img_url = None
        if is_gen_img_query:
            gen_img_resp_dict = {
                "Kinyarwanda": translations["Kinyarwanda"]["gen_img_resp"],
                "English": translations["English"]["gen_img_resp"],
                "Français": translations["Français"]["gen_img_resp"],
                "Kiswahili": translations["Kiswahili"]["gen_img_resp"]
            }
            response_text = gen_img_resp_dict.get(response_lang, translations["English"]["gen_img_resp"])
            # Auto generate image URL via Pollinations AI based on user prompt query
            encoded_prompt = urllib.parse.quote(user_query)
            generated_img_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&nologo=true"

        if is_image_query and not is_gen_img_query:
            img_resp_dict = {
                "Kinyarwanda": translations["Kinyarwanda"]["img_resp"],
                "English": translations["English"]["img_resp"],
                "Français": translations["Français"]["img_resp"],
                "Kiswahili": translations["Kiswahili"]["img_resp"]
            }
            response_text = img_resp_dict.get(response_lang, translations["English"]["img_resp"])

        if is_map_query:
            map_resp_dict = {
                "Kinyarwanda": translations["Kinyarwanda"]["map_resp"],
                "English": translations["English"]["map_resp"],
                "Français": translations["Français"]["map_resp"],
                "Kiswahili": translations["Kiswahili"]["map_resp"]
            }
            response_text = map_resp_dict.get(response_lang, translations["English"]["map_resp"])

        st.markdown(f'<div class="chat-row assistant"><div class="chat-bubble">{response_text}</div></div>', unsafe_allow_html=True)

        if is_image_query and not is_gen_img_query:
            if os.path.exists("bulinga.png"):
                st.image("bulinga.png", caption="BULINGA - Ifoto ya Administration(Front-view) y'Ishuri 🏫", use_container_width=True)
            if os.path.exists("btss.png"):
                st.image("btss.png", caption="BULINGA TSS - Logo ya BTSS ✨", use_container_width=True)

        if generated_img_url:
            st.image(generated_img_url, caption="Generated Image 🎨✨", use_container_width=True)

        save_message_to_db(st.session_state.current_user, st.session_state.current_session_id, "assistant", response_text, show_image=(is_image_query and not is_gen_img_query), generated_img_url=generated_img_url)

    except Exception as e:
        thinking_placeholder.empty()
        st.error(f"❌ Hello User ! Habaye ikibazo. ⚠️\n\n**Error:**\n`{e}`")
