            } catch (err) {
                document.getElementById(thinkingId).remove();
                alert('Connection error occurred.');
            }
        }
    </script>
</body>
</html>
    """

@app.post("/api/chat")
async def handle_chat(
    query: str = Form(...),
    response_lang: str = Form("Kinyarwanda"),
    file: UploadFile = File(None)
):
    query_lower = query.lower()
    
    image_keywords = ["foto", "photo", "ishuri", "school", "ifoto", "icyapa", "image", "logo", "akarango", "btss"]
    is_image_query = any(kw in query_lower for kw in image_keywords)
    
    gen_img_keywords = ["generate image", "kora ifoto", "shushanya", "draw", "create image", "ushushanye", "rekama ifoto", "image ya"]
    is_gen_img = any(kw in query_lower for kw in gen_img_keywords)
    
    map_keywords = ["map", "google map", "ahoherereye", "location", "icyerekezo", "direction", "irebe"]
    is_map = any(kw in query_lower for kw in map_keywords)

    file_analysis_note = ""
    if file:
        file_analysis_note = f"\n[User uploaded an image file named: {file.filename} for analysis.]"

    system_prompt = BULINGA_INFO + file_analysis_note + f"\n\nCURRENT RESPONSE LANGUAGE REQUIREMENT:\n{response_lang}\nYou MUST strictly answer the user in this exact language ({response_lang}) and include cool emojis! 🚀"

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
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
            response_text = resp_dict.get(response_lang, resp_dict["English"])
            encoded_prompt = urllib.parse.quote(query)
            generated_img_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&nologo=true"

        if is_image_query and not is_gen_img:
            img_resp_dict = {
                "Kinyarwanda": "Dore ifoto y'ikigo cyacu cyiza cya Bulinga Technical Secondary School nk'uko wabisabye! 📸✨",
                "English": "Here is a photo of our wonderful Bulinga Technical Secondary School as you requested! 📸✨",
                "Français": "Voici une photo de notre belle École Secondaire Technique de Bulinga comme demandé !",
                "Kiswahili": "Hapa kuna picha ya shule yetu nzuri ya Bulinga Technical Secondary School kama ulivyoomba! 📸✨"
            }
            response_text = img_resp_dict.get(response_lang, img_resp_dict["English"])
            
            # Guhitamo imwe muri za foto ziri muri repo kuva kuri 1 kugeza kuri 21 (jpg cyangwa jpeg)
            possible_images = []
            for i in range(1, 22):
                for ext in ["jpeg", "jpg", "png"]:
                    filename = f"{i}.{ext}"
                    if os.path.exists(filename):
                        possible_images.append(f"/static/{filename}")
            
            # KONGEREHO na btss.png cyangwa bulinga.png niba zihari
            if os.path.exists("btss.png"):
                possible_images.append("/static/btss.png")
            if os.path.exists("bulinga.png"):
                possible_images.append("/static/bulinga.png")

            if possible_images:
                # Guhitamo imwe mu buryo bwa random cyangwa zose hamwe (aha duhitamo imwe cyangwa nyinshi uko ubishaka, dufashe imwe cyangwa ebyiri zishyushye)
                chosen_img = random.choice(possible_images)
                local_images.append(chosen_img)

        if is_map:
            map_dict = {
                "Kinyarwanda": 'Urashaka kureba aho ishuri riherereye? Ushobora gukanda hano wanditse <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> kugira ngo ubashe kureba icyerekezo cy\'ishuri ryacu! 🗺️📍✨',
                "English": 'Do you want to see where the school is located? You can click here to open <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> to find the direction to our school! 🗺️📍✨',
                "Français": 'Voulez-vous voir où se trouve l\'école ? Vous pouvez cliquer ici pour ouvrir <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> pour trouver l\'itinéraire ! 🗺️📍✨',
                "Kiswahili": 'Je, unataka kuona shule ilipo? Unaweza kubonyeza hapa kufungua <a href="https://maps.google.com/?cid=5000695181927039479&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" target="_blank" style="color: #4dabf7; text-decoration: underline;">Google Map</a> kupata mwelekeo wa shule yetu! 🗺️📍✨'
            }
            response_text = map_dict.get(response_lang, map_dict["English"])

        return {
            "response": response_text, 
            "generated_img": generated_img_url,
            "local_images": local_images
        }
    except Exception as e:
        return {"response": f"❌ Habaye ikibazo mu gusubiza: `{str(e)}`", "generated_img": None, "local_images": []}
