import base64
import os
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# 1. PAGE CONFIG
st.set_page_config(
    page_title="BULINGA TSS AI",
    page_icon="btss.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 2. HASHOWE JAVASCRIPT KUGIRA NGO TITLE YA BROWSER IBE "BULINGA TSS AI" GUSA
st.markdown(
    """
    <script>
        const titleObserver = new MutationObserver(function(mutations) {
            if (document.title !== "BULINGA TSS AI") {
                document.title = "BULINGA TSS AI";
            }
        });
        titleObserver.observe(document.querySelector('head'), { subtree: true, childList: true });
        document.title = "BULINGA TSS AI";
    </script>
""",
    unsafe_allow_html=True,
)


# 3. FUNCTION BWO GUHINDURA IFOTO MO BASE64
def get_base64_image(image_path):
  if os.path.exists(image_path):
    with open(image_path, "rb") as img_file:
      return base64.b64encode(img_file.read()).decode()
  return ""


img_base64 = get_base64_image("btss.png")

# 4. CUSTOM CSS
bg_css = f"""
<style>
.stApp {{ background-color: #000000 !important; color: #ffffff !important; }}
header, footer, [data-testid="stHeader"] {{ display: none !important; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 5rem !important; max-width: 600px !important; }}
.top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0px 20px 0px; border-bottom: 1px solid #1a1a1a; margin-bottom: 20px; }}
.top-bar-title {{ font-size: 1.3rem; font-weight: 600; color: #ffffff; }}
.top-bar-icons {{ display: flex; gap: 18px; font-size: 1.2rem; color: #cccccc; }}
[data-testid="stChatMessageContent"] {{ background-color: transparent !important; padding: 0px !important; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{ flex-direction: row-reverse !important; text-align: right !important; margin-bottom: 18px !important; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {{ background-color: #2f2f2f !important; color: #ffffff !important; margin-left: auto !important; margin-right: 0px !important; padding: 12px 18px !important; border-radius: 22px !important; max-width: 80% !important; font-size: 1rem !important; line-height: 1.4 !important; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{ flex-direction: row !important; text-align: left !important; margin-bottom: 22px !important; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {{ background-color: transparent !important; color: #ffffff !important; margin-right: auto !important; margin-left: 0px !important; max-width: 100% !important; font-size: 1rem !important; line-height: 1.5 !important; }}
.action-bar {{ display: flex; gap: 16px; color: #8e8e93; font-size: 1.05rem; margin-top: 8px; cursor: pointer; }}
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
.stChatInputContainer {{ background-color: #000000 !important; }}
.stChatInput > div {{ background-color: #2f2f2f !important; border-radius: 25px !important; border: none !important; color: #ffffff !important; }}
</style>
"""
st.markdown(bg_css, unsafe_allow_html=True)

# Top Bar Header
st.markdown(
    """
<div class="top-bar">
    <div style="font-size: 1.4rem; cursor: pointer;">☰</div>
    <div class="top-bar-title">BULINGA TSS AI </div>
    <div class="top-bar-icons">
        <span style="cursor: pointer;">📝</span>
        <span style="cursor: pointer;">⋮</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# 5. API KEYS SETUP
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

if not groq_api_key:
  st.error("⚠️ GROQ_API_KEY ntiyabonywe!")
  st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1", api_key=groq_api_key
)
tavily_client = (
    TavilyClient(api_key=tavily_api_key) if tavily_api_key else None
)


def get_live_nesa_search(query: str) -> str:
  if not tavily_client:
    return ""
  keywords = [
      "nesa",
      "itangira",
      "gutaha",
      "kugaruka",
      "ibiruhuko",
      "itangazo",
      "calendar",
      "igikuba",
      "mineduc",
  ]
  if any(word in query.lower() for word in keywords):
    try:
      search_result = tavily_client.search(
          query=f"NESA Rwanda {query}", max_results=2
      )
      results = [r["content"] for r in search_result.get("results", [])]
      return (
          "\n\n[LIVE SEARCH DATA]:\n" + "\n".join(results) if results else ""
      )
    except:
      return ""
  return ""


SYSTEM_PROMPT = (
    "You are the official AI assistant for Bulinga TSS. Created by Developer"
    ' Kevin on July 25, 2026.\n" "STRICT RULES: Answer ONLY Bulinga TSS'
    " related questions. Be polite, use Kinyarwanda or English.\n"
    "KNOWLEDGE: Bulinga TSS, Mushishiro, Muhanga. Fees: 95,500 FRW. Bank:"
    ' 900009815200 (Umwalimu SACCO).\n" "Prohibited: Laptops/Machines. Uniform:'
    " Black/Blue. Headmaster: MUVUNYI Noel."
)

if "messages" not in st.session_state:
  st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for message in st.session_state.messages:
  if message["role"] != "system":
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

if prompt := st.chat_input("Ask related BULINGA TSS...."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)
  with st.chat_message("assistant"):
    message_placeholder = st.empty()
    live_data = get_live_nesa_search(prompt)
    current_messages = list(st.session_state.messages)
    if live_data:
      current_messages[-1] = {
          "role": "user",
          "content": f"{prompt}\n\n{live_data}",
      }

    # Guhamagara Groq API ukoresha model nshya ya openai/gpt-oss-20b
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b", messages=current_messages, temperature=0.3
    )

    answer = (
        completion.choices[0]
        .message.content.replace("<think>", "")
        .split("</think>")[-1]
        .strip()
    )
    message_placeholder.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
