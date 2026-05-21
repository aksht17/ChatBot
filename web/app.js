const API_BASE_URL =
  (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) ||
  "https://chatbot-2o37.onrender.com";

const messages = [];
let replyContext = "";
const uploadedFiles = []; // Track uploaded files

const elements = {
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("empty-state"),
  messageInput: document.getElementById("message-input"),
  sendButton: document.getElementById("send-button"),
  replyBar: document.getElementById("reply-bar"),
  replyText: document.getElementById("reply-text"),
  clearReply: document.getElementById("clear-reply"),
  attachButton: document.getElementById("attach-button"),
  attachPanel: document.getElementById("attach-panel"),
  fileInput: document.getElementById("file-input"),
  urlInput: document.getElementById("url-input"),
  ingestUrl: document.getElementById("ingest-url"),
  statusText: document.getElementById("status-text"),
  resetChat: document.getElementById("reset-chat"),
  filesList: document.getElementById("files-list")
};

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setStatus(text) {
  elements.statusText.textContent = text;
}

function renderMessages() {
  elements.messages.innerHTML = "";
  if (messages.length === 0) {
    elements.emptyState.classList.remove("hidden");
    return;
  }
  elements.emptyState.classList.add("hidden");

  messages.forEach((message, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${message.role}`;

    const header = document.createElement("div");
    header.className = "message-header";

    const role = document.createElement("div");
    role.className = "message-role";
    role.textContent = message.role === "user" ? "You" : "Agent";

    const replyButton = document.createElement("button");
    replyButton.className = "reply-button";
    replyButton.type = "button";
    replyButton.textContent = "Reply";
    replyButton.addEventListener("click", () => {
      setReplyContext(message.content);
    });

    header.appendChild(role);
    header.appendChild(replyButton);

    // Show reply context if this message was a reply
    if (message.replyTo) {
      const replyIndicator = document.createElement("div");
      replyIndicator.className = "reply-indicator";
      const previewLimit = 100;
      const preview = message.replyTo.length > previewLimit
        ? `${message.replyTo.slice(0, previewLimit)}...`
        : message.replyTo;
      replyIndicator.innerHTML = `<strong>↳ Replying to:</strong> ${escapeHtml(preview)}`;
      replyIndicator.title = `Replied to: ${message.replyTo}`;
      wrapper.appendChild(replyIndicator);
    }

    const text = document.createElement("div");
    text.className = "message-text";
    text.innerHTML = escapeHtml(message.content);
    text.addEventListener("mouseup", () => {
      setTimeout(() => detectSelection(text), 10);
    });

    wrapper.appendChild(header);
    wrapper.appendChild(text);
    elements.messages.appendChild(wrapper);
  });
  
  // Add global selection listener to messages container
  elements.messages.addEventListener("mouseup", () => {
    setTimeout(() => {
      const selection = window.getSelection();
      if (selection.toString().trim().length > 3) {
        detectSelection(null);
      }
    }, 10);
  });
}

function detectSelection(textElement) {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  if (selectedText.length > 3) {
    showSelectionMenu(selectedText, selection, textElement);
  } else {
    hideSelectionMenu();
  }
}

function showSelectionMenu(selectedText, selection, textElement) {
  hideSelectionMenu();
  
  const tooltip = document.createElement("div");
  tooltip.className = "selection-tooltip";
  tooltip.id = "selection-tooltip";
  tooltip.textContent = "📌 Reply to this";
  tooltip.style.zIndex = "1000";
  tooltip.style.pointerEvents = "auto";
  
  try {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    
    let topPosition = rect.top + scrollTop - 50;
    let leftPosition = rect.left + (rect.width / 2) - 45; // center horizontally
    
    // Ensure tooltip stays within viewport
    if (leftPosition < 10) {
      leftPosition = 10;
    }
    if (leftPosition + 90 > window.innerWidth) {
      leftPosition = window.innerWidth - 100;
    }
    if (topPosition < 10) {
      topPosition = rect.bottom + scrollTop + 10; // show below if not enough space above
    }
    
    tooltip.style.position = "fixed";
    tooltip.style.left = `${leftPosition}px`;
    tooltip.style.top = `${topPosition}px`;
  } catch (e) {
    tooltip.style.position = "fixed";
    tooltip.style.left = "50%";
    tooltip.style.top = "50%";
    tooltip.style.transform = "translate(-50%, -50%)";
  }
  
  tooltip.addEventListener("click", (e) => {
    e.stopPropagation();
    setReplyContext(selectedText);
    hideSelectionMenu();
    selection.removeAllRanges();
  });
  
  document.body.appendChild(tooltip);
  
  // Ensure tooltip stays visible
  tooltip.addEventListener("mouseenter", (e) => {
    e.stopPropagation();
  });
}

function hideSelectionMenu() {
  const existing = document.getElementById("selection-tooltip");
  if (existing) {
    existing.remove();
  }
}

function clearSelection() {
  const selection = window.getSelection();
  if (selection && selection.removeAllRanges) {
    try {
      selection.removeAllRanges();
    } catch (e) {
      // ignore
    }
  }
}

function setReplyContext(text) {
  replyContext = text;
  const cleaned = text.replace(/\s+/g, " ").trim();
  const previewLimit = 140;
  const preview = cleaned.length > previewLimit
    ? `${cleaned.slice(0, previewLimit)}...`
    : cleaned;
  elements.replyText.textContent = `Replying to: ${preview || "(selected text)"}`;
  elements.replyText.title = text;
  elements.replyBar.classList.remove("hidden");
  elements.messageInput.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearReplyContext() {
  replyContext = "";
  elements.replyBar.classList.add("hidden");
  elements.replyText.textContent = "";
  elements.replyText.title = "";
}

async function sendMessage() {
  const prompt = elements.messageInput.value.trim();
  if (!prompt) {
    return;
  }

  elements.messageInput.value = "";
  
  // Store message with optional replyTo context
  const userMessage = { role: "user", content: prompt };
  if (replyContext) {
    userMessage.replyTo = replyContext;
  }
  messages.push(userMessage);
  renderMessages();
  setStatus("Sending...");

  let question = prompt;
  if (replyContext) {
    question = `Use the following context when replying.\n\nContext: ${replyContext}\n\nUser: ${prompt}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    const answer = typeof data.answer === "string" ? data.answer : JSON.stringify(data.answer);
    messages.push({ role: "assistant", content: answer });
    clearReplyContext();
  } catch (error) {
    messages.push({ role: "assistant", content: "Sorry, I could not reach the backend." });
  }

  renderMessages();
  setStatus("Attach files or a link to add more context.");
}

async function uploadFiles(files) {
  if (!files || files.length === 0) {
    return;
  }

  setStatus("Uploading files...");
  const uploadedNames = [];

  for (const file of files) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        uploadedNames.push(file.name);
      }
    } catch (error) {
      // ignore individual file errors
    }
  }

  if (uploadedNames.length) {
    // Track uploaded files in UI
    for (const n of uploadedNames) {
      if (!uploadedFiles.includes(n)) {
        uploadedFiles.push(n);
      }
    }
    renderFilesList();
    setStatus(`Uploaded ${uploadedNames.length} file(s).`);
  } else {
    setStatus("Could not upload files.");
  }
}

function renderFilesList() {
  if (!elements.filesList) return;
  elements.filesList.innerHTML = "";
  if (!uploadedFiles.length) return;

  uploadedFiles.forEach((name) => {
    const tag = document.createElement("div");
    tag.className = "file-tag";
    tag.dataset.name = name;

    const span = document.createElement("div");
    span.className = "file-tag-name";
    span.textContent = name;

    const del = document.createElement("button");
    del.className = "file-delete-btn";
    del.type = "button";
    del.title = `Delete ${name}`;
    del.innerHTML = "✕";
    del.addEventListener("click", () => {
      deleteUploadedFile(name);
    });

    tag.appendChild(span);
    tag.appendChild(del);
    elements.filesList.appendChild(tag);
  });
}

function removeUploadedFile(name) {
  const nextFiles = uploadedFiles.filter((fileName) => fileName !== name);
  uploadedFiles.length = 0;
  uploadedFiles.push(...nextFiles);
  renderFilesList();
}

async function deleteUploadedFile(name) {
  setStatus(`Removing file...`);
  removeUploadedFile(name);
  try {
    const resp = await fetch(`${API_BASE_URL}/delete-source`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: name }),
    });
    if (!resp.ok) throw new Error(`Delete failed ${resp.status}`);
    setStatus(`Removed ${name}`);
  } catch (err) {
    setStatus(`Removed ${name} locally.`);
  }
}

async function ingestUrl() {
  const url = elements.urlInput.value.trim();
  if (!url) {
    return;
  }

  setStatus("Ingesting URL...");

  try {
    const response = await fetch(`${API_BASE_URL}/upload-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      throw new Error("URL ingest failed");
    }

    setStatus("URL ingested successfully.");
    elements.urlInput.value = "";
  } catch (error) {
    setStatus("Could not ingest URL.");
  }
}

function toggleAttachPanel() {
  elements.attachPanel.classList.toggle("hidden");
}

function closeAttachPanel() {
  elements.attachPanel.classList.add("hidden");
}

function resetChat() {
  messages.length = 0;
  clearReplyContext();
  renderMessages();
}

function autoResize() {
  elements.messageInput.style.height = "auto";
  elements.messageInput.style.height = `${elements.messageInput.scrollHeight}px`;
}

elements.sendButton.addEventListener("click", sendMessage);

elements.messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

elements.messageInput.addEventListener("input", autoResize);

elements.clearReply.addEventListener("click", clearReplyContext);

elements.attachButton.addEventListener("click", toggleAttachPanel);

elements.fileInput.addEventListener("change", (event) => {
  uploadFiles(event.target.files);
  event.target.value = "";
  closeAttachPanel();
});

elements.ingestUrl.addEventListener("click", () => {
  ingestUrl();
  closeAttachPanel();
});

elements.resetChat.addEventListener("click", resetChat);

document.addEventListener("click", (event) => {
  if (!elements.attachPanel.contains(event.target) && !elements.attachButton.contains(event.target)) {
    closeAttachPanel();
  }
});

document.addEventListener("mousedown", (e) => {
  // Don't hide the tooltip if clicking inside it
  if (e.target && e.target.closest && e.target.closest('.selection-tooltip')) {
    return;
  }
  hideSelectionMenu();
});

renderMessages();
renderFilesList();
