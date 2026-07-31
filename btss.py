import os
from openai import OpenAI

# 1. Gufata API Key mu buryo bw'umutekano (Environment Variable cyangwa ikoresha iy'agateganyo)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

def clean_response(text: str) -> str:
    """Igafasha gukora isuku ku bisubizo bya AI niba harimo ama-tag ya reasoning/thinking."""
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text.replace("<think>", "").strip()

def kora_groq_ai():
    print("=========================================================================")
    print("=== Bulinga TSS Assistant is Ready! Write 'exit', 'quit', or 'sohora' ===")
    print("=========================================================================")
    
    # System Prompt ikosoye kandi isobanutse neza
    messages_historike = [
        {
            "role": "system", 
            "content": (
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
        }
    ]
    
    while True:
        try:
            ikibazo = input("\nAsk a question (Bulinga TSS): ").strip()
            
            # Gusoza ikiganiro
            if ikibazo.lower() in ["sohora", "exit", "quit", "q"]:
                print("\nThank you my Friend 👍! Goodbye 🙋‍♂️👋")
                break
                
            if not ikibazo:
                continue
                
            # Kwongeramo ikibazo cy'umukoresha muri historique
            messages_historike.append({"role": "user", "content": ikibazo})
            
            # Kohereza ubutumwa kuri Groq API
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages_historike,
                temperature=0.3,
                max_tokens=1024
            )
            
            # Gufata no gukora isuku ku gisubizo
            raw_content = completion.choices[0].message.content
            ibisubizo_bipfunyitse = clean_response(raw_content)
            
            print("\nAI Response:")
            print(ibisubizo_bipfunyitse)
            
            # Kwongera igisubizo muri historique
            messages_historike.append({"role": "assistant", "content": ibisubizo_bipfunyitse})
            
        except KeyboardInterrupt:
            print("\n\nSession closed. Goodbye 👋")
            break
        except Exception as e:
            print(f"\n⚠️ An error occurred: {e}")

if __name__ == "__main__":
    kora_groq_ai()
