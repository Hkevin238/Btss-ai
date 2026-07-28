from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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"
)

def kora_groq_ai():
    print("=== Bulinga TSS Assistant is Ready Now! Write ' Quit' or 'exit' to Stop. ===")
    
    # System Prompt ivuguruwe yibanda gusa kuri Bulinga TSS iherereye muri Mushishiro, yakozwe na Developer Kevin
    messages_historike = [
        {
            "role": "system", 
            "content": (
                "You are an official AI assistant for Bulinga TSS, a TVET school located in MUHANGA District at in Mushishiro Sector. "
                "You were built and created by Developer Kevin on July 25, 2026, in the afternoon. "
                "STRICT RULE: You are ONLY allowed to know, discuss, and answer questions related to Bulinga TSS "
                "(such as courses offered, admission requirements, school location in Mushishiro, timetables, fees, exams, and school activities). "
                "If a user asks about who built you, state that you were created by Developer Kevin on July 25, 2026, in the afternoon. "
                "If a user asks about anything else outside Bulinga TSS (like general knowledge, coding tutorials, politics, movies, etc.), "
                "you must politely refuse and state that you only have information about Bulinga TSS. "
                "You can reply in Kinyarwanda or English depending on the user's language."
                "You must also say thank you 👍 for those who was interact you ."
            )
        }
    ]
    
    while True:
        ikibazo = input("\nAsk a question: ")
        
        if ikibazo.lower() in ["sohora", "exit", "quit"]:
            print(",Thank you my Friend👍! Goodbye🙋‍♂️👋")
            break
            
        if not ikibazo.strip():
            continue
            
        try:
            # Twongeramo ikibazo cy'umukoresha
            messages_historike.append({"role": "user", "content": ikibazo})
            
            # Kohereza ubutumwa muri Groq
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages_historike,
                temperature=0.3,
                max_tokens=1024
            )
            
            # Gufata igisubizo cya AI
            igisubizo_cya_ai = completion.choices[0].message.content
            
            print("\nAI Response:")
            print(igisubizo_cya_ai)
            
            # Kwongera igisubizo muri historique
            messages_historike.append({"role": "assistant", "content": igisubizo_cya_ai})
            
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    kora_groq_ai()