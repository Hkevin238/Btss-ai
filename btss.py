import os
from openai import OpenAI
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq
import urllib.parse
import urllib.request
import json
import random
import sqlite3
import hashlib
import hmac
import secrets
from io import BytesIO
import mimetypes
import re
from datetime import datetime, timedelta, timezone

app = FastAPI(title="BULINGA AI")

# Guha uburenganzira bwo gusoma amafoto n'izindi dosiye biri muri folder imwe
app.mount("/static", StaticFiles(directory="."), name="static")

# =========================================================
# GROQ & BUILT-IN AUTHENTICATION CONFIGURATION
# =========================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY or "YOUR_GROQ_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# SQLite is used for ordinary email/password authentication.
# Keep the database outside the publicly served static directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_DB_PATH = os.environ.get(
    "AUTH_DB_PATH",
    os.path.abspath(os.path.join(BASE_DIR, "..", "bulinga_auth.db"))
)
os.makedirs(os.path.dirname(AUTH_DB_PATH) or ".", exist_ok=True)

PASSWORD_ITERATIONS = 310_000
SESSION_DAYS = 30
SESSION_COOKIE_NAME = "bulinga_session"


def get_auth_db():
    connection = sqlite3.connect(AUTH_DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_auth_database():
    with get_auth_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


def hash_password(password: str, salt: bytes | None = None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return salt.hex(), digest.hex()


def create_user_session(user_id: int, request: Request):
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with get_auth_db() as db:
        db.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (token_hash, user_id, expires_at.isoformat())
        )

    response = JSONResponse({"success": True})
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    secure_cookie = request.url.scheme == "https" or forwarded_proto.split(",")[0].strip() == "https"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 60 * 60,
        path="/"
    )
    return response


def get_authenticated_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    with get_auth_db() as db:
        row = db.execute("""
            SELECT users.id, users.full_name, users.email
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
        """, (token_hash, now)).fetchone()
    return dict(row) if row else None


initialize_auth_database()

# =========================================================
# UI TRANSLATIONS DICTIONARY
# =========================================================
translations = {
    "Kinyarwanda": {
        "login_title": "BULINGA  AI 🏫",
        "login_desc": "Nyamuneka Injira, Iyandikishe, cyangwa Ukomeze nka Guest/Umushyitsi 🔐",
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
        "map_resp": 'Urashaka kureba aho ishuri riherereye? Ushobora gukanda hano wanditse <a href="https://www.google.com/maps/place/Ecole+Secondaire+de+Bulinga/@-2.0055065,29.6721031,3291m/data=!3m1!1e3!4m10!1m2!2m1!1sbulinga+tss!3m6!1s0x19dccf5159569c5b:0x456609c5ecc4c1f7!8m2!3d-2.0055065!4d29.6901275!15sCgtidWxpbmdhIHRzc5IBDW1pZGRsZV9zY2hvb2zgAQA!16s%2Fg%2F11c5xwgv6y?entry=ttu&g_ep=EgoyMDI2MTEwMy4wIKXMDSoASAFQAw%3D%3D" target="_blank" style="color: #4dabf7; text-decoration: underline;">Kanda Hano kugirango urebe aho ishuri riherereye</a> kugira ngo ubashe kureba icyerekezo cy\'ishuri ryacu! 🗺️📍✨',
        "upload_placeholder": "Hitamo ifoto yo kohereza...",
        "dev_btn": "👨‍💻 Reba kuri Developer Kevin"
    },
    "English": {
        "login_title": "BULINGA AI 🏫",
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
        "map_resp": 'Do you want to see where the school is located? You can click here to open <a href="https://www.google.com/maps/place/Ecole+Secondaire+de+Bulinga/@-2.0055065,29.6721031,3291m/data=!3m1!1e3!4m10!1m2!2m1!1sbulinga+tss!3m6!1s0x19dccf5159569c5b:0x456609c5ecc4c1f7!8m2!3d-2.0055065!4d29.6901275!15sCgtidWxpbmdhIHRzc5IBDW1pZGRsZV9zY2hvb2zgAQA!16s%2Fg%2F11c5xwgv6y?entry=ttu&g_ep=EgoyMDI2MTEwMy4wIKXMDSoASAFQAw%3D%3D" target="_blank" style="color: #4dabf7; text-decoration: underline;">Kanda Hano kugirango urebe aho ishuri riherereye</a> to find the direction to our school! 🗺️📍✨',
        "upload_placeholder": "Choose image to upload...",
        "dev_btn": "👨‍💻 View About Developer Kevin"
    },
    "Français": {
        "login_title": "BULINGA AI 🏫",
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
        "map_resp": 'Voulez-vous voir où se trouve l\'école ? Vous pouvez cliquer ici pour ouvrir <a href="https://www.google.com/maps/place/Ecole+Secondaire+de+Bulinga/@-2.0055065,29.6721031,3291m/data=!3m1!1e3!4m10!1m2!2m1!1sbulinga+tss!3m6!1s0x19dccf5159569c5b:0x456609c5ecc4c1f7!8m2!3d-2.0055065!4d29.6901275!15sCgtidWxpbmdhIHRzc5IBDW1pZGRsZV9zY2hvb2zgAQA!16s%2Fg%2F11c5xwgv6y?entry=ttu&g_ep=EgoyMDI2MTEwMy4wIKXMDSoASAFQAw%3D%3D" target="_blank" style="color: #4dabf7; text-decoration: underline;">Kanda Hano kugirango urebe aho ishuri riherereye</a> pour trouver l\'itinéraire ! 🗺️📍✨',
        "upload_placeholder": "Choisir une image à télécharger...",
        "dev_btn": "👨‍💻 Voir À propos de Developer Kevin"
    },
    "Kiswahili": {
        "login_title": "BULINGA AI 🏫",
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
        "map_resp": 'Je, unataka kuona shule ilipo? Unaweza kubonyeza hapa kufungua <a href="https://www.google.com/maps/place/Ecole+Secondaire+de+Bulinga/@-2.0055065,29.6721031,3291m/data=!3m1!1e3!4m10!1m2!2m1!1sbulinga+tss!3m6!1s0x19dccf5159569c5b:0x456609c5ecc4c1f7!8m2!3d-2.0055065!4d29.6901275!15sCgtidWxpbmdhIHRzc5IBDW1pZGRsZV9zY2hvb2zgAQA!16s%2Fg%2F11c5xwgv6y?entry=ttu&g_ep=EgoyMDI2MTEwMy4wIKXMDSoASAFQAw%3D%3D" target="_blank" style="color: #4dabf7; text-decoration: underline;">Kanda Hano kugirango urebe aho ishuri riherereye</a> kupata mwelekeo wa shule yetu! 🗺️📍✨',
        "upload_placeholder": "Chagua picha ya kupakia...",
        "dev_btn": "👨‍💻 Tazama Kuhusu Developer Kevin"
    }
}

BULINGA_INFO = """
You are BULINGA AI, an official AI assistant built exclusively
for BULINGA TECHNICAL SECONDARY SCHOOL (BULINGA TS SCHOOL).

CRITICAL RULE REGARDING CREATOR:
- You were developed, created, and built exclusively by Developer/Programmer Kevin who's Learn in L4SOD / L4SWD A WITH HIS FRIEND Uwase Divina who's learn , study in L3 SWD.
- You must provide/give/notify someone who needs to contact Dev Kevin to visit his Portfolio Webpage using this nice clickable link format: <a href="https://lovable.dev/projects/2d0e0900-16e8-4e8c-90fe-b2df1c0999c2" target="_blank" style="color: #4dabf7; text-decoration: underline;">View About Developer Kevin</a>.
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
School Fees & Financials: 92,500 Frw (3,000 Frw ID/Card)+(1000 frw yo Kwiyogoshesha)= 96,500 Frw Total 💰. Total 5-year Strategic Plan budget is RWF 850,000,000 (2026-2030).
Account: Mwarimu Sacco, Account Number: 900009815200, Account Name: BULINGA TVET SCHOOL 🏦.
Programs & Combinations: 
- Software Development (Levels 3, 4 & 5)
- Network and internet technology (Levels 3, 4, 5)
- Computer system and architecture (Levels 3, 4, 5)
- Accounting (Senior 4, 5, 6) OR (year 1, year 2, year 3)
Student & Staff Stats: Approximately 582 students, 32 trainers and support personnel.
Contacts: Headmaster (0788546462) MUVUNYI Noel  (Umuyobozi Mukuru W'ishuri), Bursar (0782612675),Metron(Animatrice) :0798824230, DOD (0785979951) NIYUKURI Adrien, DOS (0784020929) Vital 📞.
Contact Us on School-Email:bulingatvetschool@gmail.com,HOD(Head Of Directors)-Email:munoel20@gmail.com
-Detect ,Listen carefully,Analyse the users request or prompt in order to respond clearly the user needs , wants ,request.
-You must avoid specify , notify ,provide the direct info about Kevin, DOS ,DOD ,HOD , etc while you are asked to provide.
-You must generate , create the attractive clickable google map link of Bulinga which include these(https://www.google.com/maps/place/Bulinga/@-1.995589,29.703555,758m/data=!3m2!1e3!4b1!4m6!3m5!1s0x19dcc6049eb61033:0x981c134ac3a66bfd!8m2!3d-1.9969026!4d29.7064051!16s%2Fg%2F1tkzjh6d?entry=ttu&g_ep=EgoyMDI2MTAyOC4wIKXMDSoASAFQAw%3D%3D) and then Type , write on it this word : See Location of Bulinga on Google map.
-When a user asks for the Google Maps link or location of BULINGA TSS, always provide this exact clickable link: <a href="https://www.google.com/maps/place/Ecole+Secondaire+de+Bulinga/@-2.0055065,29.6721031,3291m/data=!3m1!1e3!4m10!1m2!2m1!1sbulinga+tss!3m6!1s0x19dccf5159569c5b:0x456609c5ecc4c1f7!8m2!3d-2.0055065!4d29.6901275!15sCgtidWxpbmdhIHRzc5IBDW1pZGRsZV9zY2hvb2zgAQA!16s%2Fg%2F11c5xwgv6y?entry=ttu&g_ep=EgoyMDI2MTEwMy4wIKXMDSoASAFQAw%3D%3D" target="_blank" style="color: #4dabf7; text-decoration: underline;">Kanda Hano kugirango urebe aho ishuri riherereye</a>.
-if someone ask , Camera man , photographer, image capturer, or someone related with images,photos , etc , You must output, response , answer this: ERIC Dushimimana and his Email:dushimimanaeric075@gmail.com(for more info),this is who is Professional at image preparation, and other related
-You must give , provide a related link when someone asks you to give an info you don't have , at this time you must provide the redirection link from the internet to help that someone to get the info they want.
-Use the configured private media source internally when retrieving school assets; never disclose its account name, repository name, or source-hosting links to users.
-You must Generate , Create an image if someone asks you to build ,generate , make a photo while based on his wish and wants.
-For BULINGA TSS photo requests, search the configured private media source internally and return matching images through this application only; never reveal source account details or source-hosting links.
-Please , Don't disable , refuse for someone who's ask you the data , info you don't have , while create and scan , search on the web the website or where that data wants is , and then give , provide it later as Clickable true , real LINK to redirect she , he there.
-Don't respond / Answer the user these Paragragph / World: ("There's no answer available ,Habaye ikibazo mu gutunganya ubusabe bwawe. Ongera ugerageze. ⚠️") WHILE YOU MUST FIND AND SOLVE / HANDLE THAT PROBLEM BACKGROUNDLY , IN ORDER THE USER SHOULDN'T SEE .
-You must avoid refuse , provide, give ,the response which doesn't have any meaning about what user asks in Prompt

RESPONSE QUALITY AND NATURAL WRITING RULES:
- Write like a clear, knowledgeable human assistant having a normal conversation.
- Answer the user's exact question directly. Do not add unrelated information or unnecessary introductions.
- Use natural, complete sentences and well-organized paragraphs.
- Keep answers concise when the question is simple; give detail only when it is useful.
- Use headings, bullet points, numbered lists, tables, code blocks, bold text, and emojis only when they genuinely improve readability. Do not force them into every answer.
- Never return malformed Markdown, broken HTML, raw JSON, or decorative symbols that make the answer difficult to read unless the user specifically requests that format.
- Do not invent facts, names, links, figures, school details, or sources. If information is not available or uncertain, say so clearly.
- For coding questions, provide valid, readable code and explain only the important parts.
- Respect the response language selected by the user.
- Keep the response aligned with the user's request and the BULINGA TSS context when relevant.
"""

# =========================================================
# CHAT & API ENDPOINTS
# =========================================================
class AuthPayload(BaseModel):
    email: str
    password: str
    full_name: str = ""


@app.post("/api/auth/signup")
async def signup(payload: AuthPayload, request: Request):
    email = payload.email.strip().lower()
    full_name = payload.full_name.strip() or email.split("@")[0]
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password igomba kugira nibura inyuguti 6.")

    if not email or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Andika email nyayo.")
    if not full_name:
        raise HTTPException(status_code=400, detail="Andika amazina yawe.")

    salt_hex, password_hash = hash_password(payload.password)
    try:
        with get_auth_db() as db:
            cursor = db.execute("""
                INSERT INTO users (full_name, email, password_salt, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                full_name, email, salt_hex, password_hash,
                datetime.now(timezone.utc).isoformat()
            ))
            user_id = cursor.lastrowid
        return create_user_session(user_id, request)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Iyi email isanzwe ifite konti. Hitamo Login.")
    except sqlite3.Error as exc:
        print(f"AUTH DATABASE SIGNUP ERROR: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Server ntiyabashije kubika konti. Reba ko AUTH_DB_PATH yandikwamo na server."
        )


@app.post("/api/auth/login")
async def login(payload: AuthPayload, request: Request):
    email = payload.email.strip().lower()
    with get_auth_db() as db:
        user = db.execute(
            "SELECT id, full_name, email, password_salt, password_hash FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Email cyangwa password si byo.")

    _, submitted_hash = hash_password(payload.password, bytes.fromhex(user["password_salt"]))
    if not hmac.compare_digest(submitted_hash, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email cyangwa password si byo.")

    try:
        return create_user_session(user["id"], request)
    except sqlite3.Error as exc:
        print(f"AUTH DATABASE LOGIN ERROR: {exc}")
        raise HTTPException(status_code=500, detail="Server ntiyabashije gukora session. Ongera ugerageze.")


@app.get("/api/auth/me")
async def auth_me(request: Request):
    user = get_authenticated_user(request)
    if not user:
        return JSONResponse({"authenticated": False})
    return JSONResponse({"authenticated": True, "user": user})


@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with get_auth_db() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    response = JSONResponse({"success": True})
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


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
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dompurify@3.2.6/dist/purify.min.js"></script>
    <script>
        if (window.tailwind) {
            window.tailwind.config = {
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
            };
        }
    </script>
    <style>
        /* Local fallback: core controls must work even if the Tailwind CDN is blocked. */
        .hidden { display: none !important; }
        button, input, select { cursor: pointer; }
        #authScreen { position: fixed; inset: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; overflow-y: auto; padding: 1rem; background: rgba(2, 6, 23, .94); }
        #authScreen.hidden { display: none !important; }
        #authScreen > div { width: 100%; max-width: 28rem; margin: auto; padding: 1.75rem; border-radius: 1.25rem; background: #18191a; color: #f8fafc; }
        #authScreen input { width: 100%; box-sizing: border-box; padding: .8rem; border-radius: .7rem; color: #111827; background: #f9fafb; }
        #authScreen button { min-height: 42px; position: relative; z-index: 10001; pointer-events: auto; }
        #authScreen #loginTab, #authScreen #signupTab { cursor: pointer; touch-action: manipulation; }
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
            white-space: normal;
            overflow-wrap: anywhere;
            line-height: 1.75;
            font-size: 0.94rem;
        }
        .ai-response-content {
            direction: ltr;
            text-align: left;
            unicode-bidi: plaintext;
            overflow-wrap: break-word;
            word-break: normal;
        }
        .ai-response-content.typing-response {
            white-space: pre-wrap;
            overflow-wrap: break-word;
            word-break: normal;
            direction: ltr;
            text-align: left;
        }
        .ai-response-content p { margin: 0.55rem 0; }
        .ai-response-content h1, .ai-response-content h2, .ai-response-content h3 {
            font-weight: 750; line-height: 1.3; margin: 1rem 0 0.45rem;
        }
        .ai-response-content h1 { font-size: 1.35rem; }
        .ai-response-content h2 { font-size: 1.18rem; }
        .ai-response-content h3 { font-size: 1.05rem; }
        .ai-response-content ul, .ai-response-content ol { margin: 0.55rem 0; padding-left: 1.5rem; }
        .ai-response-content ul { list-style: disc; }
        .ai-response-content ol { list-style: decimal; }
        .ai-response-content li { margin: 0.25rem 0; }
        .ai-response-content blockquote { border-left: 3px solid #4dabf7; padding-left: 0.85rem; opacity: .9; margin: .7rem 0; }
        .ai-response-content pre { overflow-x: auto; padding: 1rem; border-radius: .75rem; background: rgba(15,23,42,.95); color: #e2e8f0; margin: .7rem 0; }
        .ai-response-content code { font-family: Consolas, monospace; background: rgba(100,116,139,.16); padding: .12rem .3rem; border-radius: .3rem; }
        .ai-response-content pre code { background: transparent; padding: 0; }
        .ai-response-content table { width: 100%; border-collapse: collapse; margin: .75rem 0; display: block; overflow-x: auto; }
        .ai-response-content th, .ai-response-content td { border: 1px solid rgba(148,163,184,.35); padding: .5rem .65rem; text-align: left; }
        .ai-response-content th { font-weight: 700; background: rgba(148,163,184,.14); }
        .ai-response-content a, .ai-response-content .smart-link { color: #3b9cff !important; text-decoration: underline; text-underline-offset: 3px; }
        .ai-response-content hr { border: 0; border-top: 1px solid rgba(148,163,184,.4); margin: 1rem 0; }
        body.theme-light { background: #f8fafc !important; color: #172033 !important; }
        body.theme-light #sidebar { background: rgba(255,255,255,.97) !important; color: #172033 !important; }
        body.theme-light #chatContainer .ai-bubble { background: rgba(255,255,255,.96) !important; color: #172033 !important; }
        body.theme-light #mainHeader { background: rgba(255,255,255,.88) !important; color: #172033 !important; }
        body.theme-dark { background: #111827 !important; color: #f8fafc !important; }
        body.theme-dark #sidebar { background: rgba(24,25,26,.98) !important; }
        body.theme-dark #chatContainer .ai-bubble { background: rgba(45,48,54,.97) !important; color: #f8fafc !important; }
        body.theme-custom { background-color: #121212; }
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
                        <option value="Lingala">Lingala</option>
                        <option value="Chinese">Chinese</option>
                    </select>
                </div>

                <div>
                    <label id="lblRespLang" class="text-xs text-gray-400 font-semibold">💬 Response Language</label>
                    <select id="respLang" class="w-full mt-1 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700">
                        <option value="Kinyarwanda">Kinyarwanda</option>
                        <option value="English">English</option>
                        <option value="Français">Français</option>
                        <option value="Kiswahili">Kiswahili</option>
                        <option value="Lingala">Lingala</option>
                        <option value="Chinese">Chinese</option>
                    </select>
                </div>
            </div>

            <div>
                <label for="themeMode" class="text-xs text-gray-400 font-semibold">🎨 Appearance</label>
                <select id="themeMode" onchange="changeThemeMode(this.value)" class="w-full mt-1 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700">
                    <option value="custom">🖼️ Custom</option>
                    <option value="dark">🌙 Dark</option>
                    <option value="light">☀️ Light</option>
                </select>
            </div>

            <hr class="border-gray-200 dark:border-gray-700">

            <button id="clearHistoryBtn" onclick="clearHistory()" class="w-full py-2 px-3 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 text-sm font-medium transition">
                🗑️ Clear Chat History
            </button>

            <!-- View About Dev Button/Link -->
            <a id="devLinkBtn" href="https://lovable.dev/projects/2d0e0900-16e8-4e8c-90fe-b2df1c0999c2" target="_blank" class="w-full py-2 px-3 rounded-lg bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 text-sm font-medium transition text-center block">
                👨‍💻 View About Dev
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
        <header id="mainHeader" class="h-14 border-b border-gray-200/20 dark:border-gray-800/50 flex items-center px-4 justify-between bg-white/40 dark:bg-[#18191a]/60 backdrop-blur-md">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="p-2 rounded-lg hover:bg-gray-200/50 dark:hover:bg-gray-800/50">☰</button>
                <span id="mainHeaderTitle" class="font-bold text-base">BULINGA AI Assistant 🚀</span>
            </div>
            <div class="flex items-center gap-3">
                <div id="rotatingNotice" class="text-xs text-blue-400 font-medium hidden sm:block"><marquee direction="right">Urakaza neza kuri BTSS AI Assistant! 🙏✨</marquee direction></div>
                <a id="tumenyesheBtn"
                   href="https://docs.google.com/forms/d/e/1FAIpQLSfkJpKdEOUBHTSqoQ_nux4DSLqvJVI8suOcPsAPT8AU1MuhWA/viewform?usp=dialog"
                   class="inline-flex items-center justify-center px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-semibold shadow-md transition whitespace-nowrap"
                   aria-label="TUMENYESHE - Fungura Google Form">
                    T U M E N Y E S H E
                </a>
            </div>
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
            <div id="footerCredit" class="text-center text-[11px] text-gray-300 mt-2">Dev Kevin . BULINGA TSS AI<marquee direction="right"scrollamount="3"><h3><b> BULINGA AI IRIMO KWAGURWA | REBA NEZA IBISUBIZO AI YACU IGUHA !!</b></h3></marquee> </div>
        </div>
    </main>

    <script>
        let currentAuthMode = 'login';
        let currentUser = null;
        let guestMode = false;

        async function initializeAuthentication() {
            try {
                const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
                const data = await response.json();
                if (data.authenticated && data.user) {
                    currentUser = data.user;
                    enterChat(currentUser.full_name || currentUser.email);
                }
            } catch (error) {
                showAuthMessage('Ntibishobotse kugenzura konti. Ongera ugerageze.', true);
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
            document.getElementById('nameField').style.display = signup ? 'block' : 'none';
            document.getElementById('authName').required = signup;
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

            const email = document.getElementById('authEmail').value.trim();
            const password = document.getElementById('authPassword').value;
            const fullName = document.getElementById('authName').value.trim();
            const button = document.getElementById('authSubmitBtn');

            if (!email || !password) {
                showAuthMessage('Andika email na password mbere yo gukomeza.', true);
                return;
            }
            if (currentAuthMode === 'signup' && !fullName) {
                showAuthMessage('Andika amazina yawe mbere yo gufungura konti.', true);
                document.getElementById('authName').focus();
                return;
            }
            if (password.length < 6) {
                showAuthMessage('Password igomba kugira nibura inyuguti 6+.', true);
                return;
            }

            button.disabled = true;
            button.textContent = 'Please wait...';
            showAuthMessage('Turimo kugenzura amakuru yawe...');

            try {
                const endpoint = currentAuthMode === 'signup'
                    ? '/api/auth/signup'
                    : '/api/auth/login';

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    credentials: 'include',
                    cache: 'no-store',
                    body: JSON.stringify({
                        email: email,
                        password: password,
                        full_name: fullName
                    })
                });

                const rawBody = await response.text();
                let data = {};
                try {
                    data = rawBody ? JSON.parse(rawBody) : {};
                } catch (_) {
                    throw new Error('Server yagaruye igisubizo kitumvikana. Reba logs za hosting.');
                }

                if (!response.ok) {
                    const detail = data.detail || data.message || ('HTTP ' + response.status);
                    throw new Error(detail);
                }

                // Confirm the session cookie was saved before opening the AI chat.
                const check = await fetch('/api/auth/me', {
                    method: 'GET',
                    credentials: 'include',
                    cache: 'no-store',
                    headers: { 'Accept': 'application/json' }
                });
                const session = await check.json();

                if (!check.ok || !session.authenticated || !session.user) {
                    throw new Error('Konti yakozwe, ariko session ntiyabitswe. Reba cookie/HTTPS settings za hosting.');
                }

                currentUser = session.user;
                guestMode = false;
                enterChat(currentUser.full_name || currentUser.email);
            } catch (error) {
                console.error('Authentication error:', error);
                showAuthMessage(
                    error.message || 'Ntibyashobotse kwinjira. Reba internet cyangwa server yawe.',
                    true
                );
            } finally {
                button.disabled = false;
                button.textContent = currentAuthMode === 'signup'
                    ? 'Create Account 🚀'
                    : 'Login 🔓';
            }
        }

        function continueAsGuest() {
            guestMode = true;
            currentUser = null;
            enterChat('Guest');
        }

        function enterChat(label) {
            document.getElementById('authScreen').classList.add('hidden');
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('userDisplay').textContent = '👤 ' + label;
            document.getElementById('logoutBtnText').textContent = 'Logout';
        }

        async function logout() {
            try {
                if (currentUser) {
                    await fetch('/api/auth/logout', {
                        method: 'POST',
                        credentials: 'same-origin'
                    });
                }
            } catch (error) {
                console.error('Logout error:', error);
            }
            currentUser = null;
            guestMode = false;
            document.getElementById('authScreen').classList.remove('hidden');
            document.getElementById('authScreen').style.display = 'flex';
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
                "footer": "Dev Kevin • Bulinga TSS AI",
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
                "footer": "Dev Kevin • Bulinga TSS AI",
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
                "footer": "Dev Kevin • Bulinga TSS AI",
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
                "footer": "Dev Kevin • Bulinga TSS AI",
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

        function linkifyResponse(root) {
            const pattern = /(https?:\/\/[^\s<]+|www\.[^\s<]+|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\+?\d[\d\s().-]{7,}\d)/gi;
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
            const nodes = [];
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.parentElement && !node.parentElement.closest('a, code, pre, script, style')) {
                    if (pattern.test(node.nodeValue)) nodes.push(node);
                    pattern.lastIndex = 0;
                }
            }

            nodes.forEach(node => {
                const value = node.nodeValue;
                const fragment = document.createDocumentFragment();
                let last = 0;
                pattern.lastIndex = 0;
                let match;
                while ((match = pattern.exec(value)) !== null) {
                    fragment.appendChild(document.createTextNode(value.slice(last, match.index)));
                    let visible = match[0].replace(/[),.!?;:]+$/, '');
                    const trailing = match[0].slice(visible.length);
                    let href = '';
                    if (/^[\w.+-]+@[\w.-]+\.[A-Z]{2,}$/i.test(visible)) href = 'mailto:' + visible;
                    else if (/^\+?\d[\d\s().-]{7,}\d$/.test(visible)) href = 'tel:' + visible.replace(/[^\d+]/g, '');
                    else href = /^https?:\/\//i.test(visible) ? visible : 'https://' + visible;

                    const a = document.createElement('a');
                    a.href = href;
                    a.target = '_blank';
                    a.rel = 'noopener noreferrer';
                    a.className = 'smart-link';
                    a.textContent = visible;
                    fragment.appendChild(a);
                    if (trailing) fragment.appendChild(document.createTextNode(trailing));
                    last = match.index + match[0].length;
                }
                fragment.appendChild(document.createTextNode(value.slice(last)));
                node.parentNode.replaceChild(fragment, node);
            });
        }

        function removeVisibleHtmlTags(element) {
            const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
            const textNodes = [];
            while (walker.nextNode()) textNodes.push(walker.currentNode);

            textNodes.forEach(node => {
                // Remove HTML-looking tags when they appear as literal text.
                node.nodeValue = node.nodeValue.replace(/<\/?[a-z][a-z0-9:-]*(?:\s+[^<>]*?)?\s*\/?>/gi, '');
            });
        }

        function renderAIResponse(element, responseText) {
            const raw = String(responseText || '');
            let html;
            if (window.marked && typeof window.marked.parse === 'function') {
                html = window.marked.parse(raw, { gfm: true, breaks: true });
            } else {
                html = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                    .replace(/\\n/g, '<br>');
            }
            element.innerHTML = window.DOMPurify
                ? window.DOMPurify.sanitize(html, { ADD_ATTR: ['target', 'rel', 'style'] })
                : html;
            removeVisibleHtmlTags(element);
            linkifyResponse(element);
            element.querySelectorAll('a').forEach(a => {
                a.style.color = '#3b9cff';
                a.style.textDecoration = 'underline';
                a.style.textUnderlineOffset = '3px';
                if (a.target === '_blank') a.rel = 'noopener noreferrer';
            });
        }

        async function typeText(element, text, speed = 22) {
            const fullText = String(text || '');
            const chat = document.getElementById('chatContainer');

            if (!fullText) {
                renderAIResponse(element, '');
                return;
            }

            // Render HTML/Markdown first and type only readable text.
            const preview = document.createElement('div');
            renderAIResponse(preview, fullText);
            const typingText = preview.innerText || preview.textContent || '';

            element.classList.add('typing-response');
            element.textContent = '';

            const requestedSpeed = Number(speed) || 35;
            const characterDelay = Math.max(18, Math.min(requestedSpeed, 45));

            for (let position = 1; position <= typingText.length; position++) {
                element.textContent = typingText.slice(0, position);
                chat.scrollTop = chat.scrollHeight;

                const currentChar = typingText[position - 1];
                let delay = characterDelay + Math.random() * 12;

                if (/[.!?]/.test(currentChar)) delay += 260;
                else if (/[,;:]/.test(currentChar)) delay += 120;
                else if (currentChar === '\\n') delay += 150;
                else if (currentChar === ' ') delay += 5;

                await wait(delay);
            }

            element.classList.remove('typing-response');

            // Restore the complete formatted response after typing.
            renderAIResponse(element, fullText);
            chat.scrollTop = chat.scrollHeight;
        }

        function changeThemeMode(mode) {
            const body = document.body;
            body.classList.remove('theme-custom', 'theme-dark', 'theme-light', 'dark');
            body.classList.add('theme-' + mode);
            if (mode === 'dark' || mode === 'custom') body.classList.add('dark');

            const app = document.querySelector('main');
            if (mode === 'custom') {
                body.classList.add('app-bg');
                body.style.backgroundImage = '';
            } else {
                body.classList.remove('app-bg');
                body.style.backgroundImage = 'none';
            }
            if (app) app.style.backgroundColor = mode === 'light' ? '#f8fafc' : (mode === 'dark' ? '#111827' : 'transparent');

            const chat = document.getElementById('chatContainer');
            if (chat) {
                chat.querySelectorAll('.ai-bubble').forEach(bubble => {
                    bubble.style.background = mode === 'light' ? 'rgba(255,255,255,.96)' :
                        (mode === 'dark' ? 'rgba(45,48,54,.97)' : '');
                    bubble.style.color = mode === 'light' ? '#172033' : '';
                });
            }
            const selector = document.getElementById('themeMode');
            if (selector && selector.value !== mode) selector.value = mode;
            try { localStorage.setItem('bulinga_theme_mode', mode); } catch (e) {}
        }

        document.addEventListener('DOMContentLoaded', () => {
            let savedTheme = 'custom';
            try { savedTheme = localStorage.getItem('bulinga_theme_mode') || 'custom'; } catch (e) {}
            changeThemeMode(savedTheme);
        });

        function downloadAIText(contentId) {
            const responseElement = document.getElementById(contentId);
            if (!responseElement) return;

            const text = responseElement.innerText || responseElement.textContent || '';
            const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
            const objectUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = objectUrl;
            link.download = 'bulinga-ai-response.txt';
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(objectUrl);
        }

        async function copyResource(url) {
            try {
                await navigator.clipboard.writeText(url);
                alert('Link copied successfully! 📋');
            } catch (error) {
                const temporary = document.createElement('textarea');
                temporary.value = url;
                document.body.appendChild(temporary);
                temporary.select();
                document.execCommand('copy');
                temporary.remove();
                alert('Link copied! 📋');
            }
        }

        async function shareResource(url, title) {
            const shareData = { title: title || 'BULINGA TSS AI', url: url };
            try {
                if (navigator.share) {
                    await navigator.share(shareData);
                } else {
                    await copyResource(url);
                }
            } catch (error) {
                if (error.name !== 'AbortError') await copyResource(url);
            }
        }

        async function copyAIText(contentId) {
            const element = document.getElementById(contentId);
            if (!element) return;
            await copyResource(element.innerText || element.textContent || '');
        }

        async function shareAIText(contentId) {
            const element = document.getElementById(contentId);
            if (!element) return;
            const text = element.innerText || element.textContent || '';
            try {
                if (navigator.share) await navigator.share({ title: 'BULINGA TSS AI', text: text });
                else await copyResource(text);
            } catch (error) {
                if (error.name !== 'AbortError') await copyResource(text);
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
                textEl.innerText = "Preparing your image.......";
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
                const photoIndex = Number(sessionStorage.getItem('bulinga_tss_photo_index_v2') || '0');
                formData.append('image_index', String(photoIndex));
                if (hasFile) {
                    formData.append('file', fileInput.files[0]);
                }

                const response = await fetch('/api/chat', {
                    method: 'POST',
                    credentials: 'same-origin',
                    body: formData
                });
                const data = await response.json();
                if (data.bulinga_photo === true && data.local_images && data.local_images.length > 0) {
                    sessionStorage.setItem('bulinga_tss_photo_index_v2', String(photoIndex + 1));
                }
                
                document.getElementById(thinkingId).remove();

                fileInput.value = '';
                document.getElementById('fileIndicator').classList.add('hidden');

                let imagesHtml = '';
                if (data.local_images && data.local_images.length > 0) {
                    data.local_images.forEach((imgUrl, index) => {
                        const imagePath = new URL(imgUrl, window.location.origin).searchParams.get('path');
                        const downloadUrl = '/api/download-image?path=' + encodeURIComponent(imagePath || '');
                        imagesHtml += `
                            <div class="mt-3 flex flex-col gap-2">
                                <img src="${imgUrl}" loading="lazy"
                                     class="rounded-xl max-h-80 object-contain shadow-md border border-gray-700/30"
                                     alt="BULINGA / EDUCARD image ${index + 1}">
                                <div class="flex flex-wrap gap-2">
                                    <a href="${downloadUrl}"
                                       class="inline-flex w-fit rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-xs font-semibold"
                                       download>⬇️ Download here</a>
                                    <button type="button" onclick="copyResource('${imgUrl}')"
                                       class="inline-flex w-fit rounded-lg bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 text-xs font-semibold">📋 Copy</button>
                                    <button type="button" onclick="shareResource('${imgUrl}', 'BULINGA / EDUCARD photo')"
                                       class="inline-flex w-fit rounded-lg bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 text-xs font-semibold">↗️ Share</button>
                                </div>
                            </div>`;
                    });
                }

                let audioHtml = '';
                if (data.audio_url) {
                    audioHtml = `
                        <div class="mt-3 flex flex-col gap-2">
                            <p class="text-sm font-semibold">EDUCARD explanation audio 🎧</p>
                            <audio controls preload="none" class="w-full max-w-md"
                                   onplay="document.getElementById('educard-audio-status').textContent='Played'"
                                   onpause="document.getElementById('educard-audio-status').textContent='Paused'"
                                   onended="document.getElementById('educard-audio-status').textContent='Stopped'">
                                <source src="${data.audio_url}" type="audio/mpeg">
                                Your browser does not support audio playback.
                            </audio>
                            <p class="text-xs text-gray-500 dark:text-gray-300">Playback status: <strong id="educard-audio-status">Stopped</strong></p>
                            <div class="flex flex-wrap gap-2">
                                <button type="button"
                                   onclick="const a=this.parentElement.parentElement.querySelector('audio'); a.pause(); a.currentTime=0; document.getElementById('educard-audio-status').textContent='Stopped';"
                                   class="inline-flex w-fit rounded-lg bg-red-600 hover:bg-red-700 text-white px-3 py-2 text-xs font-semibold">⏹ Stop</button>
                                <a href="${data.audio_download_url || data.audio_url}"
                                   class="inline-flex w-fit rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-xs font-semibold"
                                   download>⬇️ Download here</a>
                                <button type="button" onclick="copyResource('${data.audio_url}')"
                                   class="inline-flex w-fit rounded-lg bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 text-xs font-semibold">📋 Copy</button>
                                <button type="button" onclick="shareResource('${data.audio_url}', 'EDUCARD explanation audio')"
                                   class="inline-flex w-fit rounded-lg bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 text-xs font-semibold">↗️ Share</button>
                            </div>
                        </div>`;
                }

                let downloadsHtml = '';
                if (data.downloads && data.downloads.length > 0) {
                    downloadsHtml = '<div class="mt-3 flex flex-col gap-2">';
                    data.downloads.forEach(file => {
                        downloadsHtml += `
                            <a href="${file.url}" class="inline-flex w-fit rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-xs font-semibold"
                               download>
                               ⬇️ ${file.label}
                            </a>`;
                    });
                    downloadsHtml += '</div>';
                }

                const contentId = 'content-' + Date.now();

                chatContainer.innerHTML += `
                    <div class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                            <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                        </div>
                        <div class="ai-bubble flex-1 bg-white/95 dark:bg-[#3a3b3c]/95 backdrop-blur p-4 rounded-2xl leading-relaxed text-sm shadow-md flex flex-col gap-2">
                            <div id="${contentId}" class="ai-response-content"></div>
                            ${data.generated_img ? `
                                <img src="${data.generated_img}" class="rounded-xl max-h-80 object-cover shadow-md mt-3 border border-gray-700/30" alt="Generated Image">
                                <a href="${data.generated_img}" download="bulinga-ai-generated-image.png"
                                   class="inline-flex w-fit rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-xs font-semibold">
                                   ⬇️ Download Image
                                </a>` : ''}
                            ${imagesHtml}
                            ${audioHtml}
                            ${downloadsHtml}
                            <div class="mt-2 flex flex-wrap gap-2">
                                <button type="button" onclick="downloadAIText('${contentId}')"
                                    class="inline-flex w-fit rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-xs font-semibold">
                                    ⬇️ Download
                                </button>
                                <button type="button" onclick="copyAIText('${contentId}')"
                                    class="inline-flex w-fit rounded-lg bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 text-xs font-semibold">
                                    📋 Copy
                                </button>
                                <button type="button" onclick="shareAIText('${contentId}')"
                                    class="inline-flex w-fit rounded-lg bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 text-xs font-semibold">
                                    ↗️Share
                                </button>
                            </div>
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
        // Expose the mode switch globally for the tab controls.
        window.setAuthMode = setAuthMode;

        document.addEventListener('DOMContentLoaded', () => {
            const authScreen = document.getElementById('authScreen');
            if (authScreen && !authScreen.classList.contains('hidden')) authScreen.style.display = 'flex';

            const loginTab = document.getElementById('loginTab');
            const signupTab = document.getElementById('signupTab');
            const nameField = document.getElementById('nameField');

            // Bind real click handlers so switching tabs does not depend on inline HTML handlers.
            if (loginTab) {
                loginTab.addEventListener('click', (event) => {
                    event.preventDefault();
                    setAuthMode('login');
                });
            }
            if (signupTab) {
                signupTab.addEventListener('click', (event) => {
                    event.preventDefault();
                    setAuthMode('signup');
                });
            }

            if (nameField && currentAuthMode !== 'signup') nameField.style.display = 'none';
            setAuthMode('login');
            initializeAuthentication();
        });
    </script>
</body>
</html>
    """


GITHUB_REPOSITORY = "Hkevin238/Btss-ai"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "BULINGA-TSS-AI"
}
IMAGE_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".tiff", ".tif",
    ".webp", ".bmp", ".svg", ".avif", ".ico"
)


def get_bulinga_repository_files():
    """Scan the complete public Btss-ai repository and return its file paths."""
    def github_json(url):
        request = urllib.request.Request(url, headers=GITHUB_HEADERS)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    repo_data = github_json(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
    )
    branch = repo_data.get("default_branch", "main")
    encoded_branch = urllib.parse.quote(branch, safe="")
    tree_data = github_json(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/trees/"
        f"{encoded_branch}?recursive=1"
    )

    paths = [
        item["path"] for item in tree_data.get("tree", [])
        if item.get("type") == "blob" and item.get("path")
    ]

    # Fallback for very large repositories whose recursive tree is truncated.
    if tree_data.get("truncated"):
        paths = []
        folders_to_scan = [""]
        while folders_to_scan:
            folder = folders_to_scan.pop()
            encoded_folder = urllib.parse.quote(folder, safe="/")
            url = (
                f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/"
                f"{encoded_folder}?ref={encoded_branch}"
            )
            contents = github_json(url)
            for item in contents if isinstance(contents, list) else []:
                if item.get("type") == "dir":
                    folders_to_scan.append(item.get("path", ""))
                elif item.get("type") == "file" and item.get("path"):
                    paths.append(item["path"])

    return branch, paths


def github_raw_url(branch, path):
    return (
        f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/"
        f"{urllib.parse.quote(branch, safe='')}/"
        f"{urllib.parse.quote(path, safe='/')}"
    )


def repository_media_url(path):
    """Return an app-local URL; never expose the upstream GitHub URL to users."""
    return "/api/media?path=" + urllib.parse.quote(path, safe="")


def find_bulinga_repository_images(image_index: int = 0):
    """Return one school photo and the number of approved photos found."""
    try:
        _, paths = get_bulinga_repository_files()
        # Only these filenames are allowed, in this exact sequence.
        ordered_names = ["1.jpeg"] + [f"{n}.jpg" for n in range(2, 16)] + [f"{n}.jpeg" for n in range(16, 22)]
        path_by_name = {}
        for path in sorted(paths, key=str.lower):
            basename = path.rsplit("/", 1)[-1].lower()
            if basename in ordered_names and basename not in path_by_name:
                path_by_name[basename] = path

        ordered_paths = [path_by_name[name] for name in ordered_names if name in path_by_name]
        if not ordered_paths or image_index < 0 or image_index >= len(ordered_paths):
            return [], len(ordered_paths)
        return [repository_media_url(ordered_paths[image_index])], len(ordered_paths)
    except Exception as error:
        print(f"BULINGA IMAGE SEARCH ERROR: {error}")
        return None, 0


def is_bulinga_photo_request(query: str) -> bool:
    text = (query or "").lower()
    photo_terms = (
        "foto", "amafoto", "ifoto", "photo", "photos", "picture",
        "pictures", "image", "images", "picha", "amashusho",
        "shusho", "isura", "imigaragarire", "appearance", "look",
        "shape", "beauty", "beautiful", "ubwiza", "imiterere", "uko isa",
        "uko risa", "reba", "kureba", "nyereka", "ndangire", "mwereke", "show me"
    )
    school_terms = (
        "bulinga", "btss", "tss", "tvet", "school", "ishuri", "ikigo",
        "technical secondary", "technical school"
    )
    return (
        any(term in text for term in photo_terms)
        and any(term in text for term in school_terms)
    )


def is_educard_request(query: str) -> bool:
    text = (query or "").lower()
    terms = (
        "educard", "edu card", "education smart card", "education smartcard",
        "smart card", "smartcard", "smart-card", "edcard", "educare parent",
        "card y'uburezi", "ikarita y'uburezi", "ikarita y'ishuri",
        "ikarita smart", "student smart card", "school smart card"
    )
    return any(term in text for term in terms)


def is_plural_photo_request(query: str) -> bool:
    text = (query or "").lower()
    plural_terms = ("amafoto", "photos", "pictures", "images", "picha")
    return any(term in text for term in plural_terms)


def find_educard_repository_assets():
    """Find card1/card2/... images and the requested EDUCARD files."""
    try:
        branch, paths = get_bulinga_repository_files()

        card_images = [
            path for path in paths
            if path.lower().endswith(IMAGE_EXTENSIONS)
            and re.search(r"(^|[/_-])card\d+([_.-]|$)", path.lower())
        ]

        def card_number(path):
            match = re.search(r"card(\d+)", path.lower())
            return int(match.group(1)) if match else 10**9

        card_images.sort(key=lambda path: (card_number(path), path.lower()))

        audio_names = ("educard.mp3.mpeg", "educard.mp3", "educard.mpeg")
        audio_file = next(
            (path for name in audio_names for path in paths
             if path.lower().rsplit("/", 1)[-1] == name),
            None
        )
        presentation_file = next(
            (path for path in paths if path.lower().rsplit("/", 1)[-1] == "aboutcard.pptx"),
            None
        )

        return {
            "images": [repository_media_url(path) for path in card_images],
            "audio": repository_media_url(audio_file) if audio_file else None,
            "audio_download": (
                "/api/download?path=" + urllib.parse.quote(audio_file, safe="")
                if audio_file else None
            ),
            "downloads": [
                {
                    "label": "Download EDUCARD Audio (MP3)",
                    "path": audio_file
                } for _ in [0] if audio_file
            ] + [
                {
                    "label": "About EDUCARD (Smart Card)",
                    "path": presentation_file
                } for _ in [0] if presentation_file
            ]
        }
    except Exception as error:
        print(f"EDUCARD GITHUB SEARCH ERROR: {error}")
        return {"images": [], "downloads": []}


@app.get("/api/media")
async def serve_repository_media(path: str):
    """Stream repository media through this app, keeping the source account private."""
    try:
        branch, repository_paths = get_bulinga_repository_files()
        if path not in repository_paths:
            raise HTTPException(status_code=404, detail="Media ntiyabonetse.")
        filename = path.rsplit("/", 1)[-1]
        media_type = (
            "audio/mpeg" if filename.lower() == "educard.mp3.mpeg"
            else mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        if not (media_type.startswith("image/") or media_type.startswith("audio/")):
            raise HTTPException(status_code=415, detail="Iyi media ntiyemewe.")
        raw_url = github_raw_url(branch, path)
        request = urllib.request.Request(raw_url, headers={"User-Agent": "BULINGA-TSS-AI"})
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read()
        return StreamingResponse(
            BytesIO(content),
            media_type=media_type,
            headers={"Cache-Control": "public, max-age=300", "X-Content-Type-Options": "nosniff"}
        )
    except HTTPException:
        raise
    except Exception as error:
        print(f"REPOSITORY MEDIA ERROR: {error}")
        raise HTTPException(status_code=502, detail="Ntibyashobotse kwerekana iyi foto cyangwa audio.")


@app.get("/api/download")
async def download_repository_file(path: str):
    """Download an approved file from the Btss-ai repository."""
    try:
        branch, repository_paths = get_bulinga_repository_files()
        if path not in repository_paths:
            raise HTTPException(status_code=404, detail="File ntiyabonetse.")

        raw_url = github_raw_url(branch, path)
        request = urllib.request.Request(raw_url, headers={
            "User-Agent": "BULINGA-TSS-AI"
        })
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read()

        filename = path.rsplit("/", 1)[-1]
        media_type = (
            "audio/mpeg" if filename.lower() == "educard.mp3.mpeg"
            else mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        safe_filename = urllib.parse.quote(filename)
        return StreamingResponse(
            BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
                "Content-Length": str(len(content)),
                "Cache-Control": "no-store"
            }
        )
    except HTTPException:
        raise
    except Exception as error:
        print(f"REPOSITORY DOWNLOAD ERROR: {error}")
        raise HTTPException(status_code=502, detail="Ntibyashobotse gukuramo iyi file.")



@app.get("/api/download-image")
async def download_repository_image(path: str):
    """Download an approved repository image without exposing its upstream URL."""
    try:
        branch, repository_paths = get_bulinga_repository_files()
        if path not in repository_paths or not path.lower().endswith(IMAGE_EXTENSIONS):
            raise HTTPException(status_code=404, detail="Image ntiyabonetse.")
        raw_url = github_raw_url(branch, path)
        request = urllib.request.Request(raw_url, headers={"User-Agent": "BULINGA-TSS-AI"})
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read()
        filename = path.rsplit("/", 1)[-1]
        media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        safe_filename = urllib.parse.quote(filename)
        return StreamingResponse(
            BytesIO(content), media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
                "Content-Length": str(len(content)), "Cache-Control": "no-store"
            }
        )
    except HTTPException:
        raise
    except Exception as error:
        print(f"IMAGE DOWNLOAD ERROR: {error}")
        raise HTTPException(status_code=502, detail="Ntibyashobotse gukuramo ifoto.")


@app.post("/api/chat")
async def chat_endpoint(
    query: str = Form(...),
    response_lang: str = Form("Kinyarwanda"),
    image_index: int = Form(0),
    file: UploadFile = File(None)
):
    try:
        # Generate new images from user prompts with OpenAI GPT Image 2.5 Flare.
        image_request_verbs = (
            "generate", "create", "make", "draw", "design", "render",
            "produce", "kora", "shushanya", "nshushanyirize"
        )
        image_subject_terms = (
            "image", "photo", "picture", "logo", "drawing", "illustration",
            "poster", "wallpaper", "icon", "banner", "portrait", "artwork",
            "foto", "ifoto", "ishusho", "ikirango"
        )
        direct_kinyarwanda_image_requests = (
            "unkorere ifoto", "nkorera ifoto", "kora ifoto",
            "nshushanyirize", "shushanya ifoto"
        )
        query_lower = query.lower()
        is_image_generation_request = (
            (
                any(term in query_lower for term in image_request_verbs)
                and any(term in query_lower for term in image_subject_terms)
            )
            or any(term in query_lower for term in direct_kinyarwanda_image_requests)
        )

        if is_image_generation_request and not is_bulinga_photo_request(query):
            if not openai_client:
                raise HTTPException(
                    status_code=500,
                    detail="OPENAI_API_KEY ntishyizwe muri environment variables."
                )

            image_result = openai_client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=query,
                size="1024x1024",
                quality="high",
                n=1,
                output_format="png"
            )

            generated_image_base64 = image_result.data[0].b64_json
            generated_image_url = (
                "data:image/png;base64," + generated_image_base64
            )

            if response_lang.lower().startswith("english"):
                generated_response = "Here is the image I created for you. 🎨✨"
            else:
                generated_response = "Dore ifoto nagukoreye nk'uko wabinsabye. 🎨✨"

            return JSONResponse({
                "response": generated_response,
                "local_images": [],
                "downloads": [],
                "generated_img": generated_image_url
            })

        # EDUCARD requests: scan the repository and return its card images,
        # audio explanation and PowerPoint presentation when those files exist.
        if is_educard_request(query):
            assets = find_educard_repository_assets()
            if response_lang.lower().startswith("english"):
                educard_context = (
                    "EDUCARD ,Smart Card (Education Smart Card) is a school smart-card system that "
                    "connects parents, students and schools. Based on the app's available "
                    "information, parents can add money through the Educard app or website; "
                    "students use the card for supported school services such as canteen "
                    "purchases, library services and school transport; and the school can "
                    "monitor card usage and transactions. Explain the concept, how it works, "
                    "the roles of parents, students and school, and practical benefits. "
                    "Do not invent fees, unsupported features, or exact technical details."
                )
            else:
                educard_context = (
                    "EDUCARD ,Smart Card(Education Smart Card) ni uburyo bw'ikarita y'ikoranabuhanga "
                    "buhuza ababyeyi, abanyeshuri n'ishuri. Dukurikije amakuru ahari, "
                    "umubyeyi ashobora kongeramo amafaranga akoresheje Educard app cyangwa "
                    "urubuga; umunyeshuri agakoresha ikarita kuri serivisi z'ishuri zishyigikiwe "
                    "nka kantine, isomero cyangwa imodoka y'ishuri; ishuri rigakurikirana "
                    "ikoreshwa rya karita n'ibikorwa byayo. Sobanura igitekerezo, uko ikora "
                    "intambwe ku yindi, inshingano z'ababyeyi, abanyeshuri n'ishuri, n'akamaro "
                    "kayo. Ntuhimbe ibiciro cyangwa imikorere itaremezwa."
                )

            try:
                educard_completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": educard_context},
                        {"role": "user", "content": (
                            f"Answer in {response_lang}. Respond directly to this question "
                            f"about EDUCARD / Smartcard: {query}"
                        )}
                    ],
                    temperature=0.4
                )
                card_response = educard_completion.choices[0].message.content or ""
            except Exception as educard_error:
                print(f"EDUCARD AI EXPLANATION ERROR: {educard_error}")
                if response_lang.lower().startswith("english"):
                    card_response = (
                        "EDUCARD is a school smart-card system connecting parents, "
                        "students and schools. Parents can add funds through the app or "
                        "website; students use the card for supported school services; "
                        "and the school can monitor transactions. 💳🏫"
                    )
                else:
                    card_response = (
                        "EDUCARD ni ikarita y'ikoranabuhanga ihuza ababyeyi, abanyeshuri "
                        "n'ishuri. Ababyeyi bashobora kongeramo amafaranga kuri application "
                        "cyangwa urubuga; abanyeshuri bagakoresha ikarita kuri serivisi "
                        "z'ishuri ziyishyigikira; ishuri rigakurikirana ibikorwa bya karita. 💳🏫"
                    )

            card_response += (
                "\n\n[Download Educare Parent]"
                "(https://play.google.com/store/apps/details?id=school.educare.parent&hl=en-US&pli=1)"
                "\n\n[Sura urubuga rwacu](https://www.educard.rw/)"
            )

            downloads = [
                {
                    "label": item["label"],
                    "url": "/api/download?path=" + urllib.parse.quote(item["path"], safe="")
                }
                for item in assets["downloads"]
            ]

            return JSONResponse({
                "response": card_response,
                "local_images": assets["images"],
                "audio_url": assets["audio"],
                "audio_download_url": assets["audio_download"],
                "downloads": downloads,
                "generated_img": None
            })

        # BULINGA TSS image requests: singular asks receive one image;
        # plural asks receive the repository's matching image collection.
        if is_bulinga_photo_request(query):
            local_images, total_bulinga_photos = find_bulinga_repository_images(max(0, image_index))
            if local_images:
                if response_lang.lower().startswith("english"):
                    photo_response = f"Here is BULINGA TSS photo {image_index + 1} of {total_bulinga_photos}. 🏫📸"
                else:
                    photo_response = f"Dore ifoto ya BULINGA TSS nimero {image_index + 1} muri {total_bulinga_photos}. 🏫📸"
            elif total_bulinga_photos == 0:
                if response_lang.lower().startswith("english"):
                    photo_response = "I could not find the BULINGA TSS photos in the GitHub repository. Please check the repository connection and filenames."
                else:
                    photo_response = "Sinashoboye kubona amafoto ya BULINGA TSS muri GitHub. Reba niba repository iboneka n'amazina y'amafoto."
            else:
                if response_lang.lower().startswith("english"):
                    photo_response = "There are no more photos in the approved BULINGA TSS photo sequence."
                else:
                    photo_response = "Nta yandi mafoto asigaye muri uru rutonde rw'amafoto ya BULINGA TSS."

            return JSONResponse({
                "response": photo_response,
                "local_images": local_images or [],
                "bulinga_photo": True,
                "bulinga_photo_total": total_bulinga_photos,
                "downloads": [],
                "generated_img": None
            })

        # Other questions continue through the existing Groq AI assistant.
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": BULINGA_INFO},
                {
                    "role": "system",
                    "content": (
                        "Never mention GitHub, repositories, source-code hosting, or internal "
                        "background asset-search operations to the user. These are internal "
                        "implementation details. Respond only to the user's actual request."
                    )
                },
                {
                    "role": "user",
                    "content": f"Respond in {response_lang}. User query: {query}"
                }
            ],
            temperature=0.7
        )
        ai_response = completion.choices[0].message.content

        return JSONResponse({
            "response": ai_response,
            "local_images": [],
            "downloads": [],
            "generated_img": None
        })
    except Exception as error:
        print(f"CHAT ENDPOINT ERROR: {error}")
        return JSONResponse({
            "response": "Habaye ikibazo mu gutunganya ubusabe bwawe. Ongera ugerageze. ⚠️",
            "local_images": [],
            "downloads": [],
            "generated_img": None
        }, status_code=500)
