const API_URL = "/chat";
const chat = document.getElementById("chat");
const q = document.getElementById("q");
const sendBtn = document.getElementById("sendBtn");
const latencyEl = document.getElementById("latency");
let lastInputWasVoice = false;

function escapeHtml(s){
  return s.replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;" }[c]));
}
function addMsg(role, text){
  const div = document.createElement("div");
  div.className = "msg " + (role === "user" ? "user" : "bot");
  div.innerHTML = `<div class="role">${role === "user" ? "You" : "Assistant"}</div>
                   <div>${escapeHtml(text).replace(/\n/g,"<br>")}</div>`;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function speakText(text) {
  if ('speechSynthesis' in window) {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'en-US';
    window.speechSynthesis.cancel(); // Stop any current speech
    window.speechSynthesis.speak(utter);
  }
}

async function send(){
  const text = q.value.trim();
  if(!text) return;
  addMsg("user", text);
  q.value = "";
  sendBtn.disabled = true;

  const t0 = performance.now();
  addMsg("bot", "Searching policy documents…");

  try{
    const res = await fetch(API_URL, {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    addMsg("bot", data.answer || "No answer returned.");
    if (data.answer && lastInputWasVoice) speakText(data.answer);
    lastInputWasVoice = false;
  } catch (e){
    addMsg("bot", "❌ Backend not reachable. Start: uvicorn api:app --reload");
  } finally {
    const t1 = performance.now();
    latencyEl.textContent = `Latency: ${(t1 - t0).toFixed(0)} ms`;
    sendBtn.disabled = false;
    q.focus();
  }
}

window.askQuick = (text) => { q.value = text; lastInputWasVoice = false; send(); }
window.clearChat = () => { chat.innerHTML = ""; }

sendBtn.addEventListener("click", send);
q.addEventListener("keydown", (e)=>{ if(e.key === "Enter") send(); });


addMsg("bot", "Hi! Ask insurance questions. I’ll answer only from your indexed policy documents.");

// --- Voice input (Speech-to-Text) support ---
const micBtn = document.getElementById("micBtn");
let recognizing = false;
let recognition;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    recognizing = true;
    micBtn.classList.add('active');
    micBtn.title = 'Listening...';
  };
  recognition.onend = () => {
    recognizing = false;
    micBtn.classList.remove('active');
    micBtn.title = 'Speak';
  };
  recognition.onerror = (event) => {
    recognizing = false;
    micBtn.classList.remove('active');
    micBtn.title = 'Speak';
    addMsg('bot', '❌ Voice recognition error: ' + event.error);
  };
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    q.value = transcript;
    lastInputWasVoice = true;
    send();
  };

  micBtn.addEventListener('click', () => {
    if (recognizing) {
      recognition.stop();
      return;
    }
    recognition.start();
  });
} else {
  micBtn.disabled = true;
  micBtn.title = 'Speech recognition not supported in this browser.';
}
