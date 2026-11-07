import os
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq
import urllib.parse
import random
from supabase import create_client, Client

app = FastAPI(title="BULINGA TSS AI")

# Guha uburenganzira bwo gusoma amafoto n'izindi dosiye biri muri folder imwe
app.mount("/static", StaticFiles(directory="."), name="static")

# =========================================================
# GROQ & SUPABASE CONFIGURATION
# =========================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY or "YOUR_GROQ_API_KEY")

# Guhuza na Supabase ukoresha Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
# Use the Supabase ANON/PUBLISHABLE key here. Never expose the service_role key.
SUPABASE_KEY = (os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# UI TRANSLATIONS DICTIONARY
# =========================================================
translations = {
    "Kinyarwanda": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Nyamuneka Injira, Iyandikishe, cyangwa Ukomeze nka Guest 🔐",
        "user_label": "Izina ry'ukoresha (Username)",
        "pass_label": "Ijambo ry'ibanga (Password)",
        "login_btn": "Injira 🔓",
        "signup_btn": "Fungura Konti 🚀",
        "guest_btn": "Koresha utiyandikishije ⚡",
        "sidebar_control": "🔐 Konti n'Uburenganzira",
        "logged_in_as": "👤 Winjiye nka",
        "logout_btn": "Sohoka 🚪",
        "theme_header": "🎨 Ishusho y'Aha hagaragara",
        "lang_header": "🌐 Ururimi rwose (Global Language)",
        "sys_lang_label": "🌐 Ururimi rwa System",
        "resp_lang_label": "💬 Ururimi rw'Igisubizo",
        "clear_history": "🗑️ Hanagura Amateka y'Ibiganiro",
        "main_title": "Umufasha wa BULINGA TSS",
        "chat_placeholder": "Baza icyo ushaka cyose cyangwa wandike uti 'Amakuru ya Bulinga...' 💬",
        "thinking": "⚪ Bulinga is Thinking....... 💭",
        "img_resp": "Dore amafoto ajyanye na Bulinga Technical Secondary School nk'uko wabinsabye! 📸✨",
        "gen_img_resp": "Dore ifoto wasabye ko nkukorera cyangwa ko nkushushanyiriza! 🎨✨",
        "map_resp": 'Urashaka kureba aho ishuri riherereye? Ushobora gukanda hano wanditse <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> kugira ngo ubashe kureba icyerekezo cy\'ishuri ryacu! 🗺️📍✨',
        "upload_placeholder": "Hitamo ifoto yo kohereza...",
        "dev_btn": "👨‍💻 Reba kuri Developer Kevin"
    },
    "English": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Please Login, Sign Up, or Continue as Guest 🔐",
        "user_label": "Username",
        "pass_label": "Password",
        "login_btn": "Login 🔓",
        "signup_btn": "Create Account 🚀",
        "guest_btn": "Use without Register ⚡",
        "sidebar_control": "🔐 Account & Control",
        "logged_in_as": "👤 Logged in as",
        "logout_btn": "Logout 🚪",
        "theme_header": "🎨 Appearance / Theme",
        "lang_header": "🌐 Global Language Settings",
        "sys_lang_label": "🌐 System Language",
        "resp_lang_label": "💬 Response Language",
        "clear_history": "🗑️ Clear Current History",
        "main_title": "BULINGA AI Assistant",
        "chat_placeholder": "Ask anything or type like 'What about Bulinga info...' 💬",
        "thinking": "⚪ Bulinga is Thinking.......",
        "img_resp": "Here are the photos related to Bulinga Technical Secondary School as you requested! 📸✨",
        "gen_img_resp": "Here is the generated image you asked me to create! 🎨✨",
        "map_resp": 'Do you want to see where the school is located? You can click here to open <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> to find the direction to our school! 🗺️📍✨',
        "upload_placeholder": "Choose image to upload...",
        "dev_btn": "👨‍💻 View About Developer Kevin"
    },
    "Français": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Veuillez vous connecter, vous inscrire ou continuer en tant qu'invité 🔐",
        "user_label": "Nom d'utilisateur",
        "pass_label": "Mot de passe",
        "login_btn": "Se connecter 🔓",
        "signup_btn": "Créer un compte 🚀",
        "guest_btn": "Utiliser sans s'inscrire ⚡",
        "sidebar_control": "🔐 Compte et contrôle",
        "logged_in_as": "👤 Connecté en tant que",
        "logout_btn": "Se déconnecter 🚪",
        "theme_header": "🎨 Apparence / Thème",
        "lang_header": "🌐 Paramètres de langue globale",
        "sys_lang_label": "🌐 Langue du Système",
        "resp_lang_label": "💬 Langue de Réponse",
        "clear_history": "🗑️ Effacer l'historique actuel",
        "main_title": "Assistant IA BULINGA",
        "chat_placeholder": "Posez une question ou tapez 'générer une image de...' 💬",
        "thinking": "⚪ Bulinga is Thinking.......",
        "img_resp": "Voici les photos relatives à l'École Secondaire Technique de Bulinga comme demandé !",
        "gen_img_resp": "Voici l'image générée que vous m'avez demandé de créer ! 🎨✨",
        "map_resp": 'Voulez-vous voir où se trouve l\'école ? Vous pouvez cliquer ici pour ouvrir <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> pour trouver l\'itinéraire ! 🗺️📍✨',
        "upload_placeholder": "Choisir une image à télécharger...",
        "dev_btn": "👨‍💻 Voir À propos de Developer Kevin"
    },
    "Kiswahili": {
        "login_title": "BULINGA TSS AI 🏫",
        "login_desc": "Tafadhali Ingia, Jisajili, au Endelea kama Mgeni 🔐",
        "user_label": "Jina la mtumiaji",
        "pass_label": "Nenosiri",
        "login_btn": "Ingia 🔓",
        "signup_btn": "Fungua Akaunti 🚀",
        "guest_btn": "Tumia bila kusajili ⚡",
        "sidebar_control": "🔐 Akaunti na Udhibiti",
        "logged_in_as": "👤 Umeingia kama",
        "logout_btn": "Toka 🚪",
        "theme_header": "🎨 Mwonekano / Mandhari",
        "lang_header": "🌐 Mipangilio ya Lugha ya Kimataifa",
        "sys_lang_label": "🌐 Lugha ya Mfumo",
        "resp_lang_label": "💬 Lugha ya Majibu",
        "clear_history": "🗑️ Futa Historia ya Sasa",
        "main_title": "Msaidizi wa AI wa BULINGA",
        "chat_placeholder": "Uliza chochote auandike 'tengeneza picha ya...' 💬",
        "thinking": "⚪ Bulinga is Thinking.......",
        "img_resp": "Hapa kuna picha zinazohusiana na Shule ya Sekondari ya Ufundi ya Bulinga kama ulivyoomba! 📸✨",
        "gen_img_resp": "Hapa kuna picha uliyoniomba nitengeneze! 🎨✨",
        "map_resp": 'Je, unataka kuona shule ilipo? Unaweza kubonyeza hapa kufungua <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> kupata mwelekeo wa shule yetu! 🗺️📍✨',
        "upload_placeholder": "Chagua picha ya kupakia...",
        "dev_btn": "👨‍💻 Tazama Kuhusu Developer Kevin"
    }
}

BULINGA_INFO = """
You are BULINGA AI, an official AI assistant built exclusively
for BULINGA TECHNICAL SECONDARY SCHOOL (BULINGA TS SCHOOL).

CRITICAL RULE REGARDING CREATOR:
- You were developed, created, and built exclusively by Developer/Programmer Kevin.
- You must provide/give/notify someone who needs to contact Dev Kevin to visit his Portfolio Webpage using this nice clickable link format: <a href="https://lovable.dev/preview/NlmPFklB47I6mwerLhQW8hKO4Fmjp39B" target="_blank" style="color: #4dabf7; text-decoration: underline;">View About Developer Kevin</a>.
- NEVER mention OpenAI, ChatGPT, or any other outside entities as your creator. If anyone asks who made you, built you, or programmed you, proudly state that you were developed and built by Developer Kevin 👨‍💻🚀 and his email: therealhacks583@gmail.com , Website: www.kevinhakiza.com (not BULINGA TSS programmers).

EMOJI RULE:
- Always include relevant, cool, and engaging emojis (such as 🏫, 📚, 💡, ✨, 👨‍💻, 👍, 💕, 👀, 😃, 🤗, 🔥 etc.) in your responses to make them lively and friendly.

FORMATTING & COLOR RULES:
- When writing responses, you are fully empowered and required to use bold formatting (e.g., <b>bold</b> or markdown equivalents) for emphasis on key terms, names, and titles.
- You can and should output text in different colors using HTML span tags with inline styles (e.g., <span style="color: #4dabf7;">blue text</span>, <span style="color: #ff6b6b;">red text</span>, <span style="color: #51cf66;">green text</span>, <span style="color: #ffd43b;">yellow text</span>) depending on what the user needs or to make the text engaging and colorful!

CORE RULE & INSTANT LINK REQUIREMENT:
- You are a helpful, smart, and versatile assistant. Answer any questions the user asks—whether it's about general knowledge, coding, science, mathematics, geography, history, everyday life, or specific details about BULINGA TVET SCHOOL. Never refuse to answer general questions; be helpful and accurate on all topics while proudly representing BULINGA TVET SCHOOL! 🌍💡
- You must provide INSTANT CLICKABLE LINKS: Whenever a user asks for a link, Google map, email, website, phone contact(numbers), portfolio, or any web resource, you MUST instantly provide a fully functional, clickable HTML anchor tag (`<a href="..." target="_blank" style="color: #4dabf7; text-decoration: underline;">...</a>`) so they can easily click and get redirected immediately!
- Style words like <span style="color: #ff7675;">Email</span>, <span style="color: #55efc4;">Website</span>, <span style="color: #74b9ff;">Phone number</span>, <span style="color: #a29bfe;">Google map link</span>, etc., with distinct colors when necessary, ensuring different words do not share the exact same plain color.

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
- Accounting (Senior 4, 5, 6) OR (year 1, year 2, year 3)
Student & Staff Stats: Approximately 582 students, 32 trainers and support personnel.
Contacts: Headmaster (0788546462) MUVUNYI Noel  (Umuyobozi Mukuru W'ishuri), Bursar (0782612675), DOD (0785979951) NIYUKURI Adrien, DOS (0784020929) Vital 📞.
Contact Us on School-Email:bulingatvetschool@gmail.com,HOD(Head Of Directors)-Email:munoel20@gmail.com
-Detect ,Listen carefully,Analyse the users request or prompt in order to respond clearly the user needs , wants ,request.
-You must avoid specify , notify ,provide the direct info about Kevin, DOS ,DOD ,HOD , etc while you are asked to provide.
-You must generate , create the attractive clickable google map link of Bulinga which include these(https://www.google.com/maps/place/Bulinga/@-1.995589,29.703555,758m/data=!3m2!1e3!4b1!4m6!3m5!1s0x19dcc6049eb61033:0x981c134ac3a66bfd!8m2!3d-1.9969026!4d29.7064051!16s%2Fg%2F1tkzjh6d?entry=ttu&g_ep=EgoyMDI2MTAyOC4wIKXMDSoASAFQAw%3D%3D) and then Type , write on it this word : See Location of Bulinga on Google map.
-You must also give the Google Map Clickable link of BULINGA TSS which includes(https://www.google.com/maps/place/Ecole+Secondaire+de+Bulinga/@-2.0055065,29.6721031,3033m/data=!3m1!1e3!4m10!1m2!2m1!1sbulinga+tss!3m6!1s0x19dccf5159569c5b:0x456609c5ecc4c1f7!8m2!3d-2.0055065!4d29.6901275!15sCgtidWxpbmdhIHRzc5IBDW1pZGRsZV9zY2hvb2zgAQA!16s%2Fg%2F11c5xwgv6y?entry=ttu&g_ep=EgoyMDI2MTAyOC4wIKXMDSoASAFQAw%3D%3D) and then Type , write on it this word: See Location of Bulinga TSS on Google map
-if someone ask , Camera man , photographer, image capturer, or someone related with images,photos , etc , You must output, response , answer this: ERIC Dushimimana and his Email:dushimimanaeric075@gmail.com(for more info),this is who is Professional at image preparation, and other related
"""

# =========================================================
# CHAT & API ENDPOINTS
# =========================================================
@app.get("/api/config")
async def public_config():
    return JSONResponse({
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_KEY
    })


@app.get("/", response_class=HTMLResponse)
async def chat_ui():
    return """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BULINGA TSS AI</title>
    <link rel="icon" type="image/png" href="/static/btss.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkBg: '#121212',
                        sidebarBg: '#18191a',
                        bubbleUser: '#0084ff',
                        bubbleAssistantDark: '#3a3b3c',
                        bubbleAssistantLight: '#e0e0fb'
                    }
                }
            }
        }
    </script>
    <style>
        @keyframes bounceSlow {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-6px); }
            100% { transform: translateY(0px); }
        }
        .moving-title { animation: bounceSlow 3s ease-in-out infinite; display: inline-block; }
        
        .app-bg {
            background-image: linear-gradient(rgba(18, 18, 18, 0.25), rgba(18, 18, 18, 0.25)), url('/static/removed.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        
        .ai-response-content {
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.6;
        }
    </style>
</head>
<body class="bg-gray-50 dark:bg-darkBg text-gray-900 dark:text-gray-100 h-screen flex overflow-hidden app-bg">

    <!-- AUTHENTICATION SCREEN -->
    <section id="authScreen" class="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto bg-slate-950/90 backdrop-blur-md">
        <div class="w-full max-w-md my-auto rounded-3xl border border-white/10 bg-white dark:bg-[#18191a] p-7 shadow-2xl">
            <div class="text-center mb-6">
                <img src="/static/btss.png" alt="BULINGA TSS" class="w-16 h-16 object-contain mx-auto mb-3">
                <h1 class="text-2xl font-extrabold">BULINGA TSS AI 🏫</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">Sign in, create an account, or continue as a guest.</p>
            </div>

            <div class="grid grid-cols-2 gap-2 mb-5 rounded-xl bg-gray-100 dark:bg-gray-800 p-1">
                <button id="loginTab" type="button" onclick="setAuthMode('login')" class="py-2 rounded-lg bg-blue-600 text-white font-semibold">Login</button>
                <button id="signupTab" type="button" onclick="setAuthMode('signup')" class="py-2 rounded-lg text-gray-600 dark:text-gray-300 font-semibold">Sign Up</button>
            </div>

            <form id="authForm" onsubmit="submitEmailAuth(event)" class="space-y-3">
                <div id="nameField" class="hidden">
                    <label class="text-xs font-semibold text-gray-500">Full name</label>
                    <input id="authName" type="text" autocomplete="name" placeholder="Your name" class="mt-1 w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-3 outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="text-xs font-semibold text-gray-500">Email address</label>
                    <input id="authEmail" type="email" required autocomplete="email" placeholder="you@example.com" class="mt-1 w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-3 outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="text-xs font-semibold text-gray-500">Password</label>
                    <input id="authPassword" type="password" required minlength="6" autocomplete="current-password" placeholder="At least 6 characters" class="mt-1 w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-3 outline-none focus:border-blue-500">
                </div>
                <button id="authSubmitBtn" type="submit" class="w-full rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 transition">Login 🔓</button>
            </form>

            <div class="flex items-center gap-3 my-4">
                <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
                <span class="text-xs text-gray-400">OR</span>
                <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
            </div>

            <button type="button" onclick="continueWithGoogle()" class="w-full rounded-xl border border-gray-300 dark:border-gray-700 py-3 font-semibold hover:bg-gray-100 dark:hover:bg-gray-800 transition flex items-center justify-center gap-3">
                <span class="font-bold text-lg">G</span> Continue with Google
            </button>
            <button type="button" onclick="continueAsGuest()" class="w-full mt-3 rounded-xl bg-gray-100 dark:bg-gray-800 py-3 font-semibold hover:bg-gray-200 dark:hover:bg-gray-700 transition">
                Continue without Register ⚡
            </button>
            <p id="authMessage" role="status" class="text-sm text-center mt-4 text-blue-500"></p>
            <p class="text-[11px] text-center text-gray-400 mt-4">Your account is Secured &amp; Private Always .</p>
        </div>
    </section>

    <!-- SIDEBAR -->
    <aside id="sidebar" class="w-72 bg-white/95 dark:bg-sidebarBg/95 backdrop-blur border-r border-gray-200 dark:border-gray-800 flex flex-col justify-between transition-all duration-300 z-20">
        <div class="p-4 flex flex-col gap-4 overflow-y-auto">
            <div class="flex items-center justify-between">
                <h1 id="sidebarTitleText" class="text-lg font-bold moving-title">BULINGA TSS AI 🏫</h1>
                <button onclick="toggleSidebar()" class="p-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">✕</button>
            </div>
            
            <hr class="border-gray-200 dark:border-gray-700">

            <!-- Language & Theme Controls -->
            <div class="flex flex-col gap-3 text-sm">
                <div>
                    <label id="lblSysLang" class="text-xs text-gray-400 font-semibold">🌐 System Language</label>
                    <select id="sysLang" onchange="changeSystemLanguage()" class="w-full mt-1 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700">
                        <option value="Kinyarwanda">Kinyarwanda</option>
                        <option value="English">English</option>
                        <option value="Français">Français</option>
                        <option value="Kiswahili">Kiswahili</option>
                    </select>
                </div>

                <div>
                    <label id="lblRespLang" class="text-xs text-gray-400 font-semibold">💬 Response Language</label>
                    <select id="respLang" class="w-full mt-1 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700">
                        <option value="Kinyarwanda">Kinyarwanda</option>
                        <option value="English">English</option>
                        <option value="Français">Français</option>
                        <option value="Kiswahili">Kiswahili</option>
                    </select>
                </div>
            </div>

            <hr class="border-gray-200 dark:border-gray-700">

            <button id="clearHistoryBtn" onclick="clearHistory()" class="w-full py-2 px-3 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 text-sm font-medium transition">
                🗑️ Clear Chat History
            </button>

            <!-- View About Developer Kevin Button/Link -->
            <a id="devLinkBtn" href="https://lovable.dev/preview/NlmPFklB47I6mwerLhQW8hKO4Fmjp39B" target="_blank" class="w-full py-2 px-3 rounded-lg bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 text-sm font-medium transition text-center block">
                👨‍💻 View About Developer Kevin
            </a>
        </div>

        <div class="p-4 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between text-sm">
            <span id="userDisplay" class="truncate font-medium">👤 Guest</span>
            <button id="logoutBtnText" onclick="logout()" class="text-xs bg-gray-200 dark:bg-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700">Logout</button>
        </div>
    </aside>

    <!-- MAIN CHAT AREA -->
    <main class="flex-1 flex flex-col h-full relative bg-transparent">
        <!-- Top Navbar -->
        <header class="h-14 border-b border-gray-200/20 dark:border-gray-800/50 flex items-center px-4 justify-between bg-white/40 dark:bg-[#18191a]/60 backdrop-blur-md">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="p-2 rounded-lg hover:bg-gray-200/50 dark:hover:bg-gray-800/50">☰</button>
                <span id="mainHeaderTitle" class="font-bold text-base">BULINGA AI Assistant 🚀</span>
            </div>
            <div id="rotatingNotice" class="text-xs text-blue-400 font-medium hidden sm:block">Urakaza neza kuri BTSS AI Assistant! 🙏✨</div>
        </header>

        <!-- Chat Messages Feed -->
        <div id="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col gap-6">
        </div>

        <!-- Chat Input Form with Image Upload Support -->
        <div class="p-4 bg-transparent max-w-4xl w-full mx-auto">
            <form id="chatForm" onsubmit="sendMessage(event)" class="relative flex items-center bg-white/95 dark:bg-[#242526]/95 backdrop-blur border border-gray-300 dark:border-[#3a3b3c] rounded-2xl shadow-xl px-4 py-2 gap-2">
                <!-- Image Upload Button -->
                <label for="imageUpload" class="cursor-pointer p-2 text-gray-500 hover:text-blue-500 transition" title="Upload Image">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                </label>
                <input type="file" id="imageUpload" accept="image/*" class="hidden" onchange="previewImageName()">

                <input type="text" id="userInput" placeholder="Baza icyo ushaka cyose cyangwa wandike 'Amakuru ya Bulinga'..." autocomplete="off"
                    class="w-full bg-transparent focus:outline-none text-sm py-2 pr-12 text-gray-900 dark:text-gray-100">

                <button type="submit" class="absolute right-3 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition shadow">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"/></svg>
                </button>
            </form>
            <div id="fileIndicator" class="text-xs text-blue-400 mt-1 px-2 hidden"></div>
            <div id="footerCredit" class="text-center text-[11px] text-gray-300 mt-2">Developed by Developer Kevin • Bulinga TSS AI</div>
        </div>
    </main>

    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script>
        let supabaseClient = null;
        let currentAuthMode = 'login';
        let currentUser = null;
        let guestMode = false;

        async function initializeAuthentication() {
            try {
                const configResponse = await fetch('/api/config');
                const config = await configResponse.json();
                if (config.supabase_url && config.supabase_anon_key && window.supabase) {
                    supabaseClient = window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
                    const { data: { session } } = await supabaseClient.auth.getSession();
                    if (session) {
                        currentUser = session.user;
                        enterChat(currentUser.email || currentUser.user_metadata?.full_name || 'User');
                    }
                    supabaseClient.auth.onAuthStateChange((_event, session) => {
                        if (session) {
                            currentUser = session.user;
                            enterChat(currentUser.email || currentUser.user_metadata?.full_name || 'User');
                        }
                    });
                } else {
                    showAuthMessage('Authentication is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY in your hosting environment.');
                }
            } catch (error) {
                showAuthMessage('Could not initialize authentication. Check your Supabase settings.');
            }
        }

        function showAuthMessage(message, isError = false) {
            const el = document.getElementById('authMessage');
            if (el) {
                el.textContent = message;
                el.className = 'text-sm text-center mt-4 ' + (isError ? 'text-red-500' : 'text-blue-500');
            }
        }

        function setAuthMode(mode) {
            currentAuthMode = mode;
            const signup = mode === 'signup';
            document.getElementById('nameField').classList.toggle('hidden', !signup);
            document.getElementById('authPassword').autocomplete = signup ? 'new-password' : 'current-password';
            document.getElementById('authSubmitBtn').textContent = signup ? 'Create Account 🚀' : 'Login 🔓';
            document.getElementById('loginTab').className = signup
                ? 'py-2 rounded-lg text-gray-600 dark:text-gray-300 font-semibold'
                : 'py-2 rounded-lg bg-blue-600 text-white font-semibold';
            document.getElementById('signupTab').className = signup
                ? 'py-2 rounded-lg bg-blue-600 text-white font-semibold'
                : 'py-2 rounded-lg text-gray-600 dark:text-gray-300 font-semibold';
            showAuthMessage('');
        }

        async function submitEmailAuth(event) {
            event.preventDefault();
            if (!supabaseClient) {
                showAuthMessage('Supabase is not configured. Please check the server environment variables.', true);
                return;
            }

            const email = document.getElementById('authEmail').value.trim();
            const password = document.getElementById('authPassword').value;
            const fullName = document.getElementById('authName').value.trim();
            const button = document.getElementById('authSubmitBtn');
            button.disabled = true;
            button.textContent = 'Please wait...';

            try {
                if (currentAuthMode === 'signup') {
                    const { data, error } = await supabaseClient.auth.signUp({
                        email,
                        password,
                        options: { data: { full_name: fullName } }
                    });
                    if (error) throw error;
                    if (data.session) {
                        currentUser = data.user;
                        enterChat(email);
                    } else {
                        showAuthMessage('Account created. Check your email to confirm, then log in.');
                        setAuthMode('login');
                    }
                } else {
                    const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
                    if (error) throw error;
                    currentUser = data.user;
                    enterChat(email);
                }
            } catch (error) {
                showAuthMessage(error.message || 'Authentication failed.', true);
            } finally {
                button.disabled = false;
                button.textContent = currentAuthMode === 'signup' ? 'Create Account 🚀' : 'Login 🔓';
            }
        }

        async function continueWithGoogle() {
            if (!supabaseClient) {
                showAuthMessage('Supabase is not configured. Please check the server environment variables.', true);
                return;
            }
            const { error } = await supabaseClient.auth.signInWithOAuth({
                provider: 'google',
                options: { redirectTo: window.location.origin }
            });
            if (error) showAuthMessage(error.message, true);
        }

        function continueAsGuest() {
            guestMode = true;
            currentUser = null;
            enterChat('Guest');
        }

        function enterChat(label) {
            document.getElementById('authScreen').classList.add('hidden');
            document.getElementById('userDisplay').textContent = '👤 ' + label;
            document.getElementById('logoutBtnText').textContent = 'Logout';
        }

        async function logout() {
            if (supabaseClient && currentUser) {
                await supabaseClient.auth.signOut();
            }
            currentUser = null;
            guestMode = false;
            document.getElementById('authScreen').classList.remove('hidden');
            document.getElementById('userDisplay').textContent = '👤 Guest';
            document.getElementById('authForm').reset();
            setAuthMode('login');
            document.getElementById('chatContainer').innerHTML = '';
        }

        const translationsData = {
            "Kinyarwanda": {
                "sidebar_title": "BULINGA TSS AI 🏫",
                "lbl_sys": "🌐 Ururimi rwa System",
                "lbl_resp": "💬 Ururimi rw'Igisubizo",
                "clear_history": "🗑️ Hanagura Amateka y'Ibiganiro",
                "dev_link": "👨‍💻 Reba kuri Developer Kevin",
                "logout": "Sohoka",
                "main_title": "BULINGA AI Assistant 🚀",
                "placeholder": "Baza icyo ushaka cyose cyangwa wandike 'Amakuru ya Bulinga'...",
                "footer": "Developed by Dev Kevin • Bulinga TSS AI",
                "thinking": "⚪ Bulinga is Thinking....... 💭"
            },
            "English": {
                "sidebar_title": "BULINGA TSS AI 🏫",
                "lbl_sys": "🌐 System Language",
                "lbl_resp": "💬 Response Language",
                "clear_history": "🗑️ Clear Chat History",
                "dev_link": "👨‍💻 View About Developer Kevin",
                "logout": "Logout",
                "main_title": "BULINGA AI Assistant 🚀",
                "placeholder": "Ask anything or type like 'What about Bulinga info...'",
                "footer": "Developed by Dev Kevin • Bulinga TSS AI",
                "thinking": "⚪ Bulinga is Thinking......."
            },
            "Français": {
                "sidebar_title": "BULINGA TSS AI 🏫",
                "lbl_sys": "🌐 Langue du Système",
                "lbl_resp": "💬 Langue de Réponse",
                "clear_history": "🗑️ Effacer l'historique",
                "dev_link": "👨‍💻 Voir À propos de Developer Kevin",
                "logout": "Se déconnecter",
                "main_title": "Assistant IA BULINGA 🚀",
                "placeholder": "Posez une question ou tapez 'Amakuru ya Bulinga'...",
                "footer": "Developed by Dev Kevin • Bulinga TSS AI",
                "thinking": "⚪ Bulinga is Thinking......."
            },
            "Kiswahili": {
                "sidebar_title": "BULINGA TSS AI 🏫",
                "lbl_sys": "🌐 Lugha ya Mfumo",
                "lbl_resp": "💬 Lugha ya Majibu",
                "clear_history": "🗑️ Futa Historia ya Sasa",
                "dev_link": "👨‍💻 Tazama Kuhusu Developer Kevin",
                "logout": "Toka",
                "main_title": "Msaidizi wa AI wa BULINGA 🚀",
                "placeholder": "Uliza chochote auandike 'Amakuru ya Bulinga'...",
                "footer": "Developed by Dev Kevin • Bulinga TSS AI",
                "thinking": "⚪ Bulinga is Thinking......."
            }
        };

        function changeSystemLanguage() {
            const lang = document.getElementById('sysLang').value;
            document.getElementById('respLang').value = lang;
            
            const t = translationsData[lang] || translationsData["English"];
            document.getElementById('sidebarTitleText').innerText = t.sidebar_title;
            document.getElementById('lblSysLang').innerText = t.lbl_sys;
            document.getElementById('lblRespLang').innerText = t.lbl_resp;
            document.getElementById('clearHistoryBtn').innerText = t.clear_history;
            document.getElementById('devLinkBtn').innerText = t.dev_link;
            document.getElementById('logoutBtnText').innerText = t.logout;
            document.getElementById('mainHeaderTitle').innerText = t.main_title;
            document.getElementById('userInput').placeholder = t.placeholder;
            document.getElementById('footerCredit').innerText = t.footer;
        }

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('hidden');
        }

        function clearHistory() {
            document.getElementById('chatContainer').innerHTML = '';
        }

        // Logout is handled by the Supabase-aware logout() function above.

        function wait(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        function previewImageName() {
            const fileInput = document.getElementById('imageUpload');
            const indicator = document.getElementById('fileIndicator');
            if (fileInput.files && fileInput.files[0]) {
                indicator.innerText = "📎 Selected: " + fileInput.files[0].name;
                indicator.classList.remove('hidden');
            } else {
                indicator.classList.add('hidden');
            }
        }

        function makePlainUrlsClickable(value) {
            const urlPattern = /\bhttps?:\/\/[^\s<]+/gi;
            return String(value).split(/(<[^>]+>)/g).map(part => {
                if (part.startsWith('<') && part.endsWith('>')) return part;
                return part.replace(urlPattern, url => {
                    const cleanUrl = url.replace(/[),.!?;:]+$/, '');
                    const trailing = url.slice(cleanUrl.length);
                    return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" style="color:#4dabf7;text-decoration:underline;word-break:break-word;">${cleanUrl}</a>${trailing}`;
                });
            }).join('');
        }

        async function typeText(element, text, speed = 15) {
            text = makePlainUrlsClickable(text);
            element.innerHTML = "";
            let length = text.length;
            let i = 0;
            while (i < length) {
                if (text[i] === '<') {
                    let closeIdx = text.indexOf('>', i);
                    if (closeIdx !== -1) {
                        element.innerHTML += text.substring(i, closeIdx + 1);
                        i = closeIdx + 1;
                    } else {
                        element.innerHTML += text[i];
                        i++;
                    }
                } else {
                    element.innerHTML += text[i];
                    i++;
                }
                document.getElementById('chatContainer').scrollTop = document.getElementById('chatContainer').scrollHeight;
                await wait(speed);
            }
        }

        async function sendMessage(e) {
            e.preventDefault();
            const inputField = document.getElementById('userInput');
            const fileInput = document.getElementById('imageUpload');
            const query = inputField.value.trim();
            const hasFile = fileInput.files && fileInput.files[0];

            if(!query && !hasFile) return;

            const chatContainer = document.getElementById('chatContainer');
            const respLang = document.getElementById('respLang').value;
            const sysLang = document.getElementById('sysLang').value;
            
            let filePreviewHtml = '';
            if (hasFile) {
                filePreviewHtml = `<div class="text-xs italic opacity-80">[Attached Image: ${fileInput.files[0].name}]</div>`;
            }

            chatContainer.innerHTML += `
                <div class="flex items-start gap-4 max-w-3xl mx-auto w-full justify-end">
                    <div class="bg-blue-600 text-white p-4 rounded-2xl leading-relaxed text-sm shadow-md max-w-[75%] ai-response-content flex flex-col gap-2">
                        ${filePreviewHtml}
                        <span>${query || "Analyze uploaded image"}</span>
                    </div>
                    <div class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white font-bold text-sm shadow-md">U</div>
                </div>`;
            
            const currentQuery = query || "Analyze this image";
            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            const thinkingId = 'thinking-' + Date.now();
            chatContainer.innerHTML += `
                <div id="${thinkingId}" class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                    <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                        <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                    </div>
                    <div id="${thinkingId}-text" class="bg-white/90 dark:bg-[#3a3b3c]/90 backdrop-blur p-4 rounded-2xl italic text-gray-400 text-sm shadow-md">⚪ Bulinga is Thinking....... 💭</div>
                </div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            const isImgQuery = query.toLowerCase().includes('foto') || query.toLowerCase().includes('photo') || query.toLowerCase().includes('ishuri') || query.toLowerCase().includes('school');
            
            if (isImgQuery) {
                const textEl = document.getElementById(`${thinkingId}-text`);
                await wait(800);
                textEl.innerText = "Generating your image.......";
                await wait(800);
                textEl.innerText = "Please wait a moment......";
                await wait(800);
                textEl.innerText = "Be ready to see a Magic 🪄";
                await wait(800);
            } else {
                await wait(120);
            }

            try {
                const formData = new FormData();
                formData.append('query', currentQuery);
                formData.append('response_lang', respLang);
                if (hasFile) {
                    formData.append('file', fileInput.files[0]);
                }

                const requestHeaders = {};
                if (supabaseClient) {
                    const { data: { session } } = await supabaseClient.auth.getSession();
                    if (session?.access_token) {
                        requestHeaders.Authorization = `Bearer ${session.access_token}`;
                    }
                }
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: requestHeaders,
                    body: formData
                });
                const data = await response.json();
                
                document.getElementById(thinkingId).remove();

                fileInput.value = '';
                document.getElementById('fileIndicator').classList.add('hidden');

                let imagesHtml = '';
                if (data.local_images && data.local_images.length > 0) {
                    data.local_images.forEach(imgUrl => {
                        imagesHtml += `<img src="${imgUrl}" class="rounded-xl max-h-80 object-cover shadow-md mt-3 border border-gray-700/30" alt="Bulinga TSS Photo">`;
                    });
                }

                const contentId = 'content-' + Date.now();

                chatContainer.innerHTML += `
                    <div class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                            <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                        </div>
                        <div class="flex-1 bg-white/95 dark:bg-[#3a3b3c]/95 backdrop-blur p-4 rounded-2xl leading-relaxed text-sm shadow-md flex flex-col gap-2">
                            <div id="${contentId}" class="ai-response-content"></div>
                            ${data.generated_img ? `<img src="${data.generated_img}" class="rounded-xl max-h-80 object-cover shadow-md mt-3 border border-gray-700/30" alt="Generated Image">` : ''}
                            ${imagesHtml}
                        </div>
                    </div>`;
                chatContainer.scrollTop = chatContainer.scrollHeight;

                const targetEl = document.getElementById(contentId);
                await typeText(targetEl, data.response, 8);

            } catch (err) {
                document.getElementById(thinkingId).remove();
                alert('Connection error occurred.');
            }
        }
        document.addEventListener('DOMContentLoaded', initializeAuthentication);
    </script>
</body>
</html>
    """

@app.post("/api/chat")
async def chat_endpoint(
    request: Request,
    query: str = Form(...),
    response_lang: str = Form("Kinyarwanda"),
    file: UploadFile = File(None)
):
    try:
        # Guest requests are allowed. If a token is supplied, it must be valid.
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            if not supabase:
                return JSONResponse({"response": "Authentication service is not configured.", "local_images": [], "generated_img": None}, status_code=503)
            access_token = authorization.split(" ", 1)[1].strip()
            try:
                supabase.auth.get_user(access_token)
            except Exception:
                return JSONResponse({"response": "Your session has expired. Please log in again.", "local_images": [], "generated_img": None}, status_code=401)
        # Hano ushobora gukoresha supabase nka query cyangwa insert niba ubikeneye:
        # urugero: supabase.table("chat_logs").insert({"query": query}).execute()

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": BULINGA_INFO},
                {"role": "user", "content": f"Respond in {response_lang}. User query: {query}"}
            ],
            temperature=0.7
        )
        ai_response = completion.choices[0].message.content

        return JSONResponse({
            "response": ai_response,
            "local_images": [],
            "generated_img": None
        })
    except Exception as e:
        return JSONResponse({
            "response": f"Habaye ikibazo: {str(e)} ⚠️",
            "local_images": [],
            "generated_img": None
        }, status_code=500)
