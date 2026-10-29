import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq
import urllib.parse

app = FastAPI(title="BULINGA TSS AI")

# Guha uburenganzira bwo gusoma amafoto n'izindi dosiye (removed.jpg, btss.png, bulinga.png) biri muri folder imwe
app.mount("/static", StaticFiles(directory="."), name="static")

# =========================================================
# GROQ CLIENT & CONFIGURATION
# =========================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY or "YOUR_GROQ_API_KEY")

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
        "response_lang_choice": "Hitamo Ururimi rw'Igisubizo",
        "clear_history": "🗑️ Hanagura Amateka y'Ibiganiro",
        "main_title": "Umufasha wa BULINGA TSS",
        "chat_placeholder": "Baza icyo ushaka cyose cyangwa wandike uti 'Amakuru ya Bulinga...' 💬",
        "thinking": "⚪ Bulinga is Thinking....... 💭",
        "img_resp": "Dore amafoto ajyanye na Bulinga Technical Secondary School nk'uko wabinsabye! 📸✨",
        "gen_img_resp": "Dore ifoto wasabye ko nkukorera cyangwa ko nkushushanyiriza! 🎨✨",
        "map_resp": 'Urashaka kureba aho ishuri riherereye? Ushobora gukanda hano wanditse <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank">Google Map</a> kugira ngo ubashe kureba icyerekezo cy\'ishuri ryacu! 🗺️📍✨'
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
        "response_lang_choice": "Choose Response Language",
        "clear_history": "🗑️ Clear Current History",
        "main_title": "BULINGA AI Assistant",
        "chat_placeholder": "Ask anything or type like 'What about Bulinga info...' 💬",
        "thinking": "⚪ Bulinga is Thinking.......",
        "img_resp": "Here are the photos related to Bulinga Technical Secondary School as you requested! 📸✨",
        "gen_img_resp": "Here is the generated image you asked me to create! 🎨✨",
        "map_resp": 'Do you want to see where the school is located? You can click here to open <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank">Google Map</a> to find the direction to our school! 🗺️📍✨'
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
        "response_lang_choice": "Choisir la langue de réponse",
        "clear_history": "🗑️ Effacer l'historique actuel",
        "main_title": "Assistant IA BULINGA",
        "chat_placeholder": "Posez une question ou tapez 'générer une image de...' 💬",
        "thinking": "⚪ Bulinga is Thinking.......",
        "img_resp": "Voici les photos relatives à l'École Secondaire Technique de Bulinga comme demandé !",
        "gen_img_resp": "Voici l'image générée que vous m'avez demandé de créer ! 🎨✨",
        "map_resp": 'Voulez-vous voir où se trouve l\'école ? Vous pouvez cliquer ici pour ouvrir <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank">Google Map</a> pour trouver l\'itinéraire ! 🗺️📍✨'
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
        "response_lang_choice": "Chagua Lugha ya Jibu",
        "clear_history": "🗑️ Futa Historia ya Sasa",
        "main_title": "Msaidizi wa AI wa BULINGA",
        "chat_placeholder": "Uliza chochote auandike 'tengeneza picha ya...' 💬",
        "thinking": "⚪ Bulinga is Thinking.......",
        "img_resp": "Hapa kuna picha zinazohusiana na Shule ya Sekondari ya Ufundi ya Bulinga kama ulivyoomba! 📸✨",
        "gen_img_resp": "Hapa kuna picha uliyoniomba nitengeneze! 🎨✨",
        "map_resp": 'Je, unataka kuona shule ilipo? Unaweza kubonyeza hapa kufungua <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank">Google Map</a> kupata mwelekeo wa shule yetu! 🗺️📍✨'
    }
}

BULINGA_INFO = """
You are BULINGA AI, an official AI assistant built exclusively
for BULINGA TECHNICAL SECONDARY SCHOOL (BULINGA TS SCHOOL).

CRITICAL RULE REGARDING CREATOR:
- You were developed, created, and built exclusively by Developer/Programmer Kevin.
- You must provide/give/notify someone who needs to contact Dev Kevin to visit his Portfolio Webpage: (https://lovable.dev/preview/NlmPFklB47I6mwerLhQW8hKO4Fmjp39B)
- NEVER mention OpenAI, ChatGPT, or any other outside entities as your creator. If anyone asks who made you, built you, or programmed you, proudly state that you were developed and built by Developer Kevin 👨‍💻🚀 and his email: therealhacks583@gmail.com , Website: www.kevinhakiza.com (not BULINGA TSS programmers).

EMOJI RULE:
- Always include relevant, cool, and engaging emojis (such as 🏫, 📚, 💡, ✨, 👨‍💻, 👍, 💕, 👀, 😃, 🤗, 🔥 etc.) in your responses to make them lively and friendly.

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
- Accounting (Senior 4, 5, 6) OR (year 1, year 2, year 3)
Student & Staff Stats: Approximately 582 students, 32 trainers and support personnel.
Contacts: Headmaster (0788546462) MUVUNYI Noel (Umuyobozi Mukuru W'ishuri), Bursar (0782612675), DOD (0785979951) NIYUKURI Adrien, DOS (0784020929) Vital 📞.
"""

# =========================================================
# CHAT & API ENDPOINT
# =========================================================
@app.get("/", response_class=HTMLResponse)
async def chat_ui():
    return """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BULINGA TSS AI - ChatGPT / Gemini Style</title>
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
        
        /* Custom Background Image removed.jpg fully visible with light overlay */
        .app-bg {
            background-image: linear-gradient(rgba(18, 18, 18, 0.25), rgba(18, 18, 18, 0.25)), url('/static/removed.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        
        /* Clean formatted AI response text styling */
        .ai-response-content {
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.6;
        }
    </style>
</head>
<body class="bg-gray-50 dark:bg-darkBg text-gray-900 dark:text-gray-100 h-screen flex overflow-hidden app-bg">

    <!-- SIDEBAR -->
    <aside id="sidebar" class="w-72 bg-white/95 dark:bg-sidebarBg/95 backdrop-blur border-r border-gray-200 dark:border-gray-800 flex flex-col justify-between transition-all duration-300 z-20">
        <div class="p-4 flex flex-col gap-4 overflow-y-auto">
            <div class="flex items-center justify-between">
                <h1 class="text-lg font-bold moving-title">BULINGA TSS AI 🏫</h1>
                <button onclick="toggleSidebar()" class="p-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">✕</button>
            </div>
            
            <hr class="border-gray-200 dark:border-gray-700">

            <!-- Language & Theme Controls -->
            <div class="flex flex-col gap-3 text-sm">
                <div>
                    <label class="text-xs text-gray-400 font-semibold">🌐 System Language</label>
                    <select id="sysLang" class="w-full mt-1 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700">
                        <option value="Kinyarwanda">Kinyarwanda</option>
                        <option value="English">English</option>
                        <option value="Français">Français</option>
                        <option value="Kiswahili">Kiswahili</option>
                    </select>
                </div>

                <div>
                    <label class="text-xs text-gray-400 font-semibold">💬 Response Language</label>
                    <select id="respLang" class="w-full mt-1 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700">
                        <option value="Kinyarwanda">Kinyarwanda</option>
                        <option value="English">English</option>
                        <option value="Français">Français</option>
                        <option value="Kiswahili">Kiswahili</option>
                    </select>
                </div>
            </div>

            <hr class="border-gray-200 dark:border-gray-700">

            <button onclick="clearHistory()" class="w-full py-2 px-3 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 text-sm font-medium transition">
                🗑️ Clear Chat History
            </button>

            <!-- View About Developer Kevin Button/Link -->
            <a href="https://lovable.dev/preview/NlmPFklB47I6mwerLhQW8hKO4Fmjp39B" target="_blank" class="w-full py-2 px-3 rounded-lg bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 text-sm font-medium transition text-center block">
                👨‍💻 View About Developer Kevin
            </a>
        </div>

        <div class="p-4 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between text-sm">
            <span id="userDisplay" class="truncate font-medium">👤 Guest</span>
            <button onclick="logout()" class="text-xs bg-gray-200 dark:bg-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700">Logout</button>
        </div>
    </aside>

    <!-- MAIN CHAT AREA -->
    <main class="flex-1 flex flex-col h-full relative bg-transparent">
        <!-- Top Navbar -->
        <header class="h-14 border-b border-gray-200/20 dark:border-gray-800/50 flex items-center px-4 justify-between bg-white/40 dark:bg-[#18191a]/60 backdrop-blur-md">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="p-2 rounded-lg hover:bg-gray-200/50 dark:hover:bg-gray-800/50">☰</button>
                <span class="font-bold text-base">BULINGA AI Assistant 🚀</span>
            </div>
            <div id="rotatingNotice" class="text-xs text-blue-400 font-medium hidden sm:block">Urakaza neza kuri BTSS AI Assistant! 🙏✨</div>
        </header>

        <!-- Chat Messages Feed -->
        <div id="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col gap-6">
            <div class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                    <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                </div>
                <div class="flex-1 bg-white/90 dark:bg-[#3a3b3c]/90 backdrop-blur p-4 rounded-2xl leading-relaxed text-sm shadow-md ai-response-content">
                    Murakaza neza kuri Bulinga TSS AI! Baza icyo ushaka cyose cyangwa se ubaze amakuru y'ishuri ryacu. 🏫✨
                </div>
            </div>
        </div>

        <!-- Chat Input Form -->
        <div class="p-4 bg-transparent max-w-4xl w-full mx-auto">
            <form id="chatForm" onsubmit="sendMessage(event)" class="relative flex items-center bg-white/95 dark:bg-[#242526]/95 backdrop-blur border border-gray-300 dark:border-[#3a3b3c] rounded-2xl shadow-xl px-4 py-2">
                <input type="text" id="userInput" placeholder="Baza icyo ushaka cyose cyangwa wandike 'Amakuru ya Bulinga'..." autocomplete="off"
                    class="w-full bg-transparent focus:outline-none text-sm py-2 pr-12 text-gray-900 dark:text-gray-100">
                <button type="submit" class="absolute right-3 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition shadow">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"/></svg>
                </button>
            </form>
            <div class="text-center text-[11px] text-gray-300 mt-2">Developed by Developer Kevin • Bulinga TSS AI</div>
        </div>
    </main>

    <script>
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('hidden');
        }

        function clearHistory() {
            document.getElementById('chatContainer').innerHTML = '';
        }

        function logout() {
            alert('Logged out successfully!');
            location.reload();
        }

        async function sendMessage(e) {
            e.preventDefault();
            const inputField = document.getElementById('userInput');
            const query = inputField.value.trim();
            if(!query) return;

            const chatContainer = document.getElementById('chatContainer');
            
            // Append User Message cleanly
            chatContainer.innerHTML += `
                <div class="flex items-start gap-4 max-w-3xl mx-auto w-full justify-end">
                    <div class="bg-blue-600 text-white p-4 rounded-2xl leading-relaxed text-sm shadow-md max-w-[75%] ai-response-content">${query}</div>
                    <div class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white font-bold text-sm shadow-md">U</div>
                </div>`;
            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Thinking Bubble with "Bulinga is Thinking......."
            const thinkingId = 'thinking-' + Date.now();
            chatContainer.innerHTML += `
                <div id="${thinkingId}" class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                    <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                        <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                    </div>
                    <div class="bg-white/90 dark:bg-[#3a3b3c]/90 backdrop-blur p-4 rounded-2xl italic text-gray-400 text-sm shadow-md">⚪ Bulinga is Thinking....... 💭</div>
                </div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            const respLang = document.getElementById('respLang').value;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, response_lang: respLang })
                });
                const data = await response.json();
                
                document.getElementById(thinkingId).remove();

                // Build local images html if requested
                let imagesHtml = '';
                if (data.local_images && data.local_images.length > 0) {
                    data.local_images.forEach(imgUrl => {
                        imagesHtml += `<img src="${imgUrl}" class="rounded-xl max-h-80 object-cover shadow-md mt-3 border border-gray-700/30" alt="Bulinga TSS Photo">`;
                    });
                }

                // Append Assistant Message with btss.png icon avatar instead of "AI" text
                chatContainer.innerHTML += `
                    <div class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                            <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                        </div>
                        <div class="flex-1 bg-white/95 dark:bg-[#3a3b3c]/95 backdrop-blur p-4 rounded-2xl leading-relaxed text-sm shadow-md flex flex-col gap-2">
                            <div class="ai-response-content">${data.response}</div>
                            <img src="/static/btss.png" class="rounded-xl max-h-80 object-cover shadow-md mt-3 border border-gray-700/30" alt="Bulinga TSS Logo/Photo">
                            ${data.generated_img ? `<img src="${data.generated_img}" class="rounded-xl max-h-80 object-cover shadow-md mt-3 border border-gray-700/30" alt="Generated Image">` : ''}
                            ${imagesHtml}
                        </div>
                    </div>`;
                chatContainer.scrollTop = chatContainer.scrollHeight;
            } catch (err) {
                document.getElementById(thinkingId).remove();
                alert('Connection error occurred.');
            }
        }
    </script>
</body>
</html>
    """

class ChatRequest(BaseModel):
    query: str
    response_lang: str = "Kinyarwanda"

@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    query_lower = req.query.lower()
    
    image_keywords = ["foto", "photo", "ishuri", "school", "ifoto", "icyapa", "image", "logo", "akarango"]
    is_image_query = any(kw in query_lower for kw in image_keywords)
    
    gen_img_keywords = ["generate image", "kora ifoto", "shushanya", "draw", "create image", "ushushanye", "rekama ifoto", "image ya"]
    is_gen_img = any(kw in query_lower for kw in gen_img_keywords)
    
    map_keywords = ["map", "google map", "ahoherereye", "location", "icyerekezo", "direction", "irebe"]
    is_map = any(kw in query_lower for kw in map_keywords)

    system_prompt = BULINGA_INFO + f"\n\nCURRENT RESPONSE LANGUAGE REQUIREMENT:\n{req.response_lang}\nYou MUST strictly answer the user in this exact language ({req.response_lang}) and include cool emojis! 🚀"

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.query}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        response_text = completion.choices[0].message.content
        
        generated_img_url = None
        local_images = []

        if is_gen_img:
            resp_dict = {
                "Kinyarwanda": "Dore ifoto wasabye ko nkukorera cyangwa ko nkushushanyiriza! 🎨✨",
                "English": "Here is the generated image you asked me to create! 🎨✨",
                "Français": "Voici l'image générée que vous m'avez demandé de créer ! 🎨✨",
                "Kiswahili": "Hapa kuna picha uliyoniomba nitengeneze! 🎨✨"
            }
            response_text = resp_dict.get(req.response_lang, resp_dict["English"])
            encoded_prompt = urllib.parse.quote(req.query)
            generated_img_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&nologo=true"

        if is_image_query and not is_gen_img:
            img_resp_dict = {
                "Kinyarwanda": "Dore amafoto ajyanye na Bulinga Technical Secondary School nk'uko wabinsabye! 📸✨",
                "English": "Here are the photos related to Bulinga Technical Secondary School as you requested! 📸✨",
                "Français": "Voici les photos relatives à l'École Secondaire Technique de Bulinga comme demandé !",
                "Kiswahili": "Hapa kuna picha zinazohusiana na Shule ya Sekondari ya Ufundi ya Bulinga kama ulivyoomba! 📸✨"
            }
            response_text = img_resp_dict.get(req.response_lang, img_resp_dict["English"])
            
            # Gushakisha btss.png na bulinga.png muri folder imwe
            if os.path.exists("btss.png"):
                local_images.append("/static/btss.png")
            if os.path.exists("bulinga.png"):
                local_images.append("/static/bulinga.png")

        if is_map:
            map_dict = {
                "Kinyarwanda": 'Urashaka kureba aho ishuri riherereye? Ushobora gukanda hano wanditse <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> kugira ngo ubashe kureba icyerekezo cy\'ishuri ryacu! 🗺️📍✨',
                "English": 'Do you want to see where the school is located? You can click here to open <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> to find the direction to our school! 🗺️📍✨',
                "Français": 'Voulez-vous voir où se trouve l\'école ? Vous pouvez cliquer ici pour ouvrir <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> pour trouver l\'itinéraire ! 🗺️📍✨',
                "Kiswahili": 'Je, unataka kuona shule ilipo? Unaweza kubonyeza hapa kufungua <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> kupata mwelekeo wa shule yetu! 🗺️📍✨'
            }
            response_text = map_dict.get(req.response_lang, map_dict["English"])

        return {
            "response": response_text, 
            "generated_img": generated_img_url,
            "local_images": local_images
        }
    except Exception as e:
        return {"response": f"❌ Habaye ikibazo mu gusubiza: `{str(e)}`", "generated_img": None, "local_images": []}
