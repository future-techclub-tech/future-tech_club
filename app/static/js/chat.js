(() => {
  const fontSizeLabel = document.querySelector("[data-chat-font-label]");
  const fontSizeControls = document.querySelectorAll("[data-chat-font-change]");
  let messageFontSize = 1;
  const updateMessageFontSize = () => {
    document.documentElement.style.setProperty("--chat-message-font-size", `${messageFontSize}rem`);
    if (fontSizeLabel) fontSizeLabel.textContent = `${Math.round(messageFontSize * 100)}%`;
  };
  fontSizeControls.forEach((button) => {
    button.addEventListener("click", () => {
      messageFontSize = Math.min(1.6, Math.max(0.8, messageFontSize + Number(button.dataset.chatFontChange) * 0.1));
      updateMessageFontSize();
    });
  });
  updateMessageFontSize();

  const conversation = document.querySelector("[data-chat-messages]");
  const form = document.querySelector("[data-chat-form]");
  if (!conversation || !form) return;

  const errorBox = document.querySelector("[data-chat-error]");
  const bodyInput = form.querySelector("[data-chat-body]");
  const fileInput = form.querySelector("[data-chat-file]");
  const attachmentPreview = document.querySelector("[data-chat-attachment-preview]");
  const sendButton = form.querySelector(".chat-send-button");
  const messagesUrl = conversation.dataset.messagesUrl;
  const sendUrl = conversation.dataset.sendUrl;
  let loading = false;
  let firstLoad = true;
  let connectionLost = false;

  const showError = (message) => {
    errorBox.textContent = message;
    errorBox.hidden = !message;
  };

  const formattedTime = (isoTime) => {
    const time = new Date(isoTime);
    if (Number.isNaN(time.getTime())) return "";
    return time.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  };

  const renderMessage = (message, currentUserId) => {
    const article = document.createElement("article");
    const isOwn = message.sender_id === currentUserId;
    article.className = `chat-message ${isOwn ? "chat-message-own" : "chat-message-other"}`;
    article.dataset.messageId = String(message.id);

    const meta = document.createElement("div");
    meta.className = "chat-message-meta";
    const sender = document.createElement("strong");
    sender.textContent = isOwn ? "You" : message.sender;
    const timestamp = document.createElement("time");
    timestamp.dateTime = message.sent_at;
    timestamp.textContent = formattedTime(message.sent_at);
    meta.append(sender, timestamp);

    const bubble = document.createElement("div");
    bubble.className = "chat-message-bubble";
    if (message.body) {
      const text = document.createElement("div");
      text.className = "chat-message-text";
      text.textContent = message.body;
      bubble.append(text);
    }
    if (message.attachment_url) {
      const attachment = document.createElement("a");
      attachment.className = "chat-attachment";
      attachment.href = message.attachment_url;
      attachment.setAttribute("download", "");
      attachment.textContent = `📎 ${message.attachment_name || "Download attachment"}`;
      bubble.append(attachment);
    }
    article.append(meta, bubble);

    const footer = document.createElement("div");
    footer.className = "chat-message-footer";
    if (message.edited) {
      const edited = document.createElement("span");
      edited.className = "chat-edited-label";
      edited.textContent = "edited";
      footer.append(edited);
    }
    if (message.can_edit) {
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "chat-edit-button";
      edit.textContent = "Edit";
      edit.addEventListener("click", () => editMessage(message));
      footer.append(edit);
    }
    if (footer.childElementCount) article.append(footer);
    return article;
  };

  const editMessage = async (message) => {
    const editedBody = window.prompt("Edit your message (available for 5 minutes):", message.body || "");
    if (editedBody === null) return;
    const data = new FormData();
    data.append("body", editedBody);
    const csrf = form.querySelector('[name="csrf_token"]');
    data.append("csrf_token", csrf.value);
    try {
      const response = await fetch(message.edit_url, {
        method: "POST",
        body: data,
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) {
        showError(response.status === 409
          ? "The five-minute edit window has expired."
          : "This message could not be edited.");
        await refreshMessages();
        return;
      }
      showError("");
      await refreshMessages();
    } catch {
      showError("Could not reach the chat server. Your edit was not saved.");
    }
  };

  const refreshMessages = async () => {
    if (loading) return;
    loading = true;
    const nearBottom = conversation.scrollHeight - conversation.scrollTop - conversation.clientHeight < 100;
    try {
      const response = await fetch(messagesUrl, {
        cache: "no-store",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Chat messages could not be refreshed.");
      const data = await response.json();
      if (connectionLost) showError("");
      connectionLost = false;
      const fragment = document.createDocumentFragment();
      if (!data.messages.length) {
        const empty = document.createElement("p");
        empty.className = "chat-loading";
        empty.textContent = "No messages yet. Send a message to start the conversation.";
        fragment.append(empty);
      }
      for (const message of data.messages) {
        fragment.append(renderMessage(message, data.current_user_id));
      }
      conversation.replaceChildren(fragment);
      if (firstLoad || nearBottom) conversation.scrollTop = conversation.scrollHeight;
      firstLoad = false;
    } catch {
      if (firstLoad) {
        conversation.textContent = "Could not load messages. Check your connection and try again.";
      } else {
        connectionLost = true;
        showError("Connection lost. Retrying chat updates…");
      }
    } finally {
      loading = false;
    }
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!bodyInput.value.trim() && !fileInput.files.length) {
      showError("Write a message or attach a file.");
      return;
    }
    sendButton.disabled = true;
    showError("");
    try {
      const response = await fetch(sendUrl, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) {
        showError(response.status === 413
          ? "Files must be 25 MB or smaller."
          : "Your message could not be sent. Please try again.");
        return;
      }
      bodyInput.value = "";
      bodyInput.style.height = "";
      fileInput.value = "";
      attachmentPreview.hidden = true;
      attachmentPreview.textContent = "";
      await refreshMessages();
      conversation.scrollTop = conversation.scrollHeight;
    } catch {
      showError("Could not reach the chat server. Your message was not sent.");
    } finally {
      sendButton.disabled = false;
    }
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    attachmentPreview.hidden = !file;
    attachmentPreview.textContent = file
      ? `${file.name} · ${(file.size / (1024 * 1024)).toFixed(2)} MB`
      : "";
    showError(file && file.size > 25 * 1024 * 1024
      ? "Files must be 25 MB or smaller."
      : "");
  });

  bodyInput.addEventListener("input", () => {
    bodyInput.style.height = "auto";
    bodyInput.style.height = `${Math.min(bodyInput.scrollHeight, 140)}px`;
  });

  bodyInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  refreshMessages();
  window.setInterval(refreshMessages, 1000);
})();
