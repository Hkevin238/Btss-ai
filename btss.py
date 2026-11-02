
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

        // Turn plain URLs, emails and phone numbers into colored clickable links.
        // Existing HTML links (such as the Google Maps link) are preserved.
        function formatResponseHtml(rawText) {
            const parts = String(rawText || "").split(/(<a\b[^>]*>[\s\S]*?<\/a>)/gi);

            return parts.map(part => {
                if (/^<a\b/i.test(part)) return part;

                let html = part
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");

                // Color common profile/contact labels according to their type.
                html = html.replace(
                    /(^|\n)(\s*)(Website|Web|Urubuga|Email|E-mail|Phone|Telephone|Tel|Mobile|Address|Location|Google Map|Map)\s*:/gi,
                    (match, lineStart, spaces, label) => {
                        const key = label.toLowerCase();
                        let color = "#38bdf8";
                        if (key.includes("email") || key.includes("e-mail")) color = "#a78bfa";
                        else if (["phone", "telephone", "tel", "mobile"].includes(key)) color = "#22c55e";
                        else if (["address", "location"].includes(key)) color = "#f59e0b";
                        else if (key.includes("map")) color = "#ec4899";
                        return `${lineStart}${spaces}<strong style="color:${color}">${label}:</strong>`;
                    }
                );

                // Make email addresses clickable.
                html = html.replace(
                    /([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/gi,
                    '<a href="mailto:$1" style="color:#a78bfa;text-decoration:underline;font-weight:600;">$1</a>'
                );

                // Make full web addresses and www domains clickable.
                html = html.replace(
                    /(^|[\s(])((?:https?:\/\/|www\.)[^\s<]+)/gi,
                    (match, prefix, address) => {
                        const cleanAddress = address.replace(/[),.;!?]+$/, "");
                        const trailing = address.slice(cleanAddress.length);
                        const href = cleanAddress.toLowerCase().startsWith("www.")
                            ? "https://" + cleanAddress
                            : cleanAddress;
                        return `${prefix}<a href="${href}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8;text-decoration:underline;font-weight:600;">${cleanAddress}</a>${trailing}`;
                    }
                );

                // Make phone numbers clickable.
                html = html.replace(
                    /(^|[\s:])(\+?\d[\d\s().-]{6,}\d)(?=$|[\s<])/g,
                    (match, prefix, number) => {
                        const digits = number.replace(/[^\d+]/g, "");
                        return `${prefix}<a href="tel:${digits}" style="color:#22c55e;text-decoration:underline;font-weight:600;">${number}</a>`;
                    }
                );

                return html;
            }).join("");
        }

        async function typeText(element, text, speed = 1) {
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
            const t = translationsData[sysLang] || translationsData["English"];
            
            let filePreviewHtml = '';
            if (hasFile) {
                filePreviewHtml = `<div class="text-xs italic opacity-80">[Attached Image: ${fileInput.files[0].name}]</div>`;
            }

            // Append User Message cleanly
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

            // Thinking / Rotating Messages with custom cycle as requested
            const thinkingId = 'thinking-' + Date.now();
            chatContainer.innerHTML += `
                <div id="${thinkingId}" class="flex items-start gap-4 max-w-3xl mx-auto w-full">
                    <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md overflow-hidden p-1">
                        <img src="/static/btss.png" class="w-full h-full object-contain" alt="BTSS">
                    </div>
                    <div id="${thinkingId}-text" class="bg-white/90 dark:bg-[#3a3b3c]/90 backdrop-blur p-4 rounded-2xl italic text-gray-400 text-sm shadow-md">⚪ Bulinga is Thinking....... 💭</div>
                </div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Rotating animation sequence for image query or general query
            const isImgQuery = query.toLowerCase().includes('foto') || query.toLowerCase().includes('photo') || query.toLowerCase().includes('ishuri') || query.toLowerCase().includes('school');
            
            if (isImgQuery) {
                const textEl = document.getElementById(`${thinkingId}-text`);
                textEl.innerText = "Preparing your response... ⚡";
            }

            try {
                const formData = new FormData();
                formData.append('query', currentQuery);
                formData.append('response_lang', respLang);
                if (hasFile) {
                    formData.append('file', fileInput.files[0]);
                }

                const response = await fetch('/api/chat', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
