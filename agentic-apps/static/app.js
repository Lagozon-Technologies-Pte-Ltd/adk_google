let sessionId = null;
let currentStream = null;
let activeAssistantNode = null;

const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("msg");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const statusPill = document.getElementById("status-pill");
const sessionListEl = document.getElementById("session-list");

function setStatus(text) {
  statusPill.textContent = text;
}

function addMessage(text, variant) {
  const node = document.createElement("div");
  node.className = `message ${variant}`;
  if (variant === "message-bot") {
    node.dataset.rawText = text || "";
    node.textContent = text;
  } else {
    node.textContent = text;
  }
  chatEl.appendChild(node);
  chatEl.scrollTop = chatEl.scrollHeight;
  return node;
}

function addRouteBadge(agentName) {
  const node = document.createElement("div");
  node.className = "route-badge";
  node.textContent = `Routed to: ${agentName}`;
  chatEl.appendChild(node);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatInline(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  return html;
}

function markdownToHtml(markdown) {
  const normalized = (markdown || "").replace(/\r/g, "");
  const lines = normalized.split("\n");
  const blocks = [];
  let inList = false;

  for (const line of lines) {
    const listMatch = line.match(/^\s*\d+\.\s+(.+)$/);

    if (listMatch) {
      if (!inList) {
        blocks.push("<ol>");
        inList = true;
      }
      blocks.push(`<li>${formatInline(listMatch[1])}</li>`);
      continue;
    }

    if (inList) {
      blocks.push("</ol>");
      inList = false;
    }

    if (line.trim().length === 0) {
      blocks.push('<div class="spacer"></div>');
      continue;
    }

    blocks.push(`<p>${formatInline(line)}</p>`);
  }

  if (inList) {
    blocks.push("</ol>");
  }

  return blocks.join("") || "<p></p>";
}

function finalizeAssistantMessage() {
  if (!activeAssistantNode) {
    return;
  }
  const raw = activeAssistantNode.dataset.rawText || "";
  activeAssistantNode.innerHTML = markdownToHtml(raw);
  activeAssistantNode = null;
}

function closeCurrentStream() {
  if (currentStream) {
    currentStream.close();
    currentStream = null;
  }
}

function renderSessionList(sessions) {
  sessionListEl.innerHTML = "";

  if (!sessions.length) {
    const empty = document.createElement("div");
    empty.className = "session-empty";
    empty.textContent = "No chats yet.";
    sessionListEl.appendChild(empty);
    return;
  }

  sessions.forEach((session) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "session-item";
    if (session.session_id === sessionId) {
      btn.classList.add("active");
    }
    btn.textContent = session.title || "Untitled Chat";
    btn.title = session.title || "Untitled Chat";
    btn.addEventListener("click", () => {
      openSession(session.session_id).catch(() => {
        addMessage("Could not load selected session.", "message-system");
      });
    });
    sessionListEl.appendChild(btn);
  });
}

async function refreshSessionList() {
  const response = await fetch("/sessions");
  const data = await response.json();
  renderSessionList(data.sessions || []);
}

function renderStoredAssistant(content, agentCsv) {
  if (agentCsv) {
    const uniqueAgents = Array.from(
      new Set(
        agentCsv
          .split(",")
          .map((a) => a.trim())
          .filter(Boolean)
      )
    );
    uniqueAgents.forEach((agent) => addRouteBadge(agent));
  }

  const node = addMessage("", "message-bot");
  node.dataset.rawText = content || "";
  node.innerHTML = markdownToHtml(node.dataset.rawText);
}

async function openSession(targetSessionId) {
  closeCurrentStream();
  finalizeAssistantMessage();
  sendBtn.disabled = true;
  setStatus("Loading chat...");

  const response = await fetch(`/sessions/${targetSessionId}/messages`);
  if (!response.ok) {
    throw new Error("Failed to load messages");
  }
  const data = await response.json();

  sessionId = targetSessionId;
  chatEl.innerHTML = "";

  if (!data.messages || !data.messages.length) {
    addMessage("New session started. How can I help you today?", "message-system");
  } else {
    data.messages.forEach((msg) => {
      if (msg.role === "user") {
        addMessage(msg.content, "message-user");
      } else if (msg.role === "assistant") {
        renderStoredAssistant(msg.content, msg.agent);
      }
    });
  }

  await refreshSessionList();
  setStatus("Ready");
  sendBtn.disabled = false;
  inputEl.focus();
}

async function createNewChat() {
  closeCurrentStream();
  finalizeAssistantMessage();
  sendBtn.disabled = true;
  setStatus("Starting new chat...");

  const response = await fetch("/new_chat", { method: "POST" });
  const data = await response.json();
  sessionId = data.session_id;

  chatEl.innerHTML = "";
  addMessage("New session started. How can I help you today?", "message-system");

  await refreshSessionList();
  setStatus("Ready");
  sendBtn.disabled = false;
  inputEl.focus();
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();

  if (!text || !sessionId) {
    return;
  }

  closeCurrentStream();
  finalizeAssistantMessage();

  addMessage(text, "message-user");
  inputEl.value = "";
  sendBtn.disabled = true;
  setStatus("Assistant is responding...");

  activeAssistantNode = addMessage("", "message-bot");

  currentStream = new EventSource(
    `/chat/stream?user_input=${encodeURIComponent(text)}&session_id=${sessionId}`
  );

  currentStream.onmessage = (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch {
      payload = { type: "text", text: String(event.data || "") };
    }

    if (typeof payload === "string") {
      activeAssistantNode.dataset.rawText += payload;
      activeAssistantNode.textContent = activeAssistantNode.dataset.rawText;
      chatEl.scrollTop = chatEl.scrollHeight;
      return;
    }

    if (payload.type === "agent" && payload.agent) {
      addRouteBadge(payload.agent);
      return;
    }

    if (payload.type === "text" && payload.text && activeAssistantNode) {
      activeAssistantNode.dataset.rawText += payload.text;
      activeAssistantNode.textContent = activeAssistantNode.dataset.rawText;
      chatEl.scrollTop = chatEl.scrollHeight;
    }
  };

  currentStream.onerror = async () => {
    closeCurrentStream();
    finalizeAssistantMessage();
    await refreshSessionList();
    setStatus("Ready");
    sendBtn.disabled = false;
  };
});

newChatBtn.addEventListener("click", () => {
  createNewChat().catch(() => {
    addMessage("Could not start a new session.", "message-system");
    setStatus("Connection issue");
  });
});

(async () => {
  try {
    await refreshSessionList();
    const response = await fetch("/sessions");
    const data = await response.json();
    if (data.sessions && data.sessions.length) {
      await openSession(data.sessions[0].session_id);
    } else {
      await createNewChat();
    }
  } catch {
    addMessage("Unable to connect to backend.", "message-system");
    setStatus("Connection issue");
  }
})();
