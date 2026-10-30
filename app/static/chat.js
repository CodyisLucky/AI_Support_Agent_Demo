(function () {
  var chat = document.getElementById("help");
  var summary = chat && chat.querySelector(".chat-launcher");
  var panel = document.getElementById("chat-panel");
  var log = document.getElementById("chat-log");
  var form = chat && chat.querySelector(".chat-form");
  var input = document.getElementById("chat-message");
  var error = document.getElementById("chat-error");
  var status = document.getElementById("chat-status");
  var ref = document.getElementById("chat-ref");
  var refId = document.getElementById("chat-ref-id");
  var handoff = document.getElementById("chat-handoff");
  var handoffEmail = document.getElementById("chat-handoff-email");
  var handoffLive = document.getElementById("chat-handoff-live");
  if (!chat || !summary || !panel || !log || !form || !input || !error || !status) return;
  if (!ref || !refId || !handoff || !handoffEmail || !handoffLive) return;

  var button = form.querySelector("button");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var openedByShopper = false;

  function scrollLog() {
    log.scrollTop = log.scrollHeight;
  }

  function showError(text) {
    error.textContent = text || "";
  }

  function syncButton() {
    button.disabled = input.value.trim() === "" || form.getAttribute("aria-busy") === "true";
  }

  function appendMessage(message) {
    if (!message || (message.role !== "shopper" && message.role !== "agent")) return;
    if (typeof message.text !== "string" || !message.text) return;
    var empty = log.querySelector(".chat-empty");
    if (empty) empty.remove();
    var item = document.createElement("li");
    item.className = message.role === "shopper" ? "chat-shopper" : "chat-agent";
    var paragraphs = Array.isArray(message.paragraphs) && message.paragraphs.length ? message.paragraphs : [message.text];
    paragraphs.forEach(function (text) {
      var paragraph = document.createElement("p");
      paragraph.textContent = text;
      item.appendChild(paragraph);
    });
    if (typeof message.details === "string" && message.details) {
      var details = document.createElement("p");
      details.className = "chat-details";
      details.textContent = message.details;
      item.appendChild(details);
    }
    log.appendChild(item);
  }

  var typing = null;

  function showTyping() {
    var empty = log.querySelector(".chat-empty");
    if (empty) empty.remove();
    typing = document.createElement("li");
    typing.className = "chat-agent chat-typing";
    var paragraph = document.createElement("p");
    paragraph.textContent = "Typing…";
    typing.appendChild(paragraph);
    log.appendChild(typing);
    scrollLog();
  }

  function hideTyping() {
    if (typing) typing.remove();
    typing = null;
  }

  function showConversation(id) {
    if (typeof id !== "string" || !id) return;
    refId.textContent = id;
    ref.hidden = false;
  }

  function showHandoff(info) {
    if (!info || typeof info.mailto !== "string") return;
    handoffEmail.href = info.mailto;
    var live = typeof info.live_chat_url === "string" ? info.live_chat_url : "";
    if (/^https?:\/\//.test(live)) {
      handoffLive.href = live;
      handoffLive.hidden = false;
    } else {
      handoffLive.hidden = true;
    }
    handoff.hidden = false;
    input.placeholder = "Add a note for our team";
  }

  function remember() {
    try {
      sessionStorage.setItem("lumen-chat-open", chat.open ? "1" : "0");
    } catch (err) {}
  }

  try {
    if (chat.open) sessionStorage.setItem("lumen-chat-open", "1");
  } catch (err) {}

  if (chat.open) scrollLog();
  syncButton();
  input.addEventListener("input", syncButton);

  var closeTimer = 0;

  function finishClose(event) {
    if (event && event.target !== panel) return;
    if (event && event.propertyName !== (reduce ? "opacity" : "transform")) return;
    if (!chat.classList.contains("is-closing")) return;
    panel.removeEventListener("transitionend", finishClose);
    clearTimeout(closeTimer);
    chat.open = false;
    chat.classList.remove("is-closing");
  }

  function cancelClose() {
    chat.classList.remove("is-closing");
    panel.removeEventListener("transitionend", finishClose);
    clearTimeout(closeTimer);
  }

  function closeChat() {
    if (!chat.open || chat.classList.contains("is-closing")) return;
    summary.focus();
    chat.classList.add("is-closing");
    panel.addEventListener("transitionend", finishClose);
    closeTimer = setTimeout(finishClose, 700);
  }

  summary.addEventListener("click", function (event) {
    if (chat.classList.contains("is-closing")) {
      event.preventDefault();
      cancelClose();
      return;
    }
    if (chat.open) {
      event.preventDefault();
      closeChat();
      return;
    }
    chat.classList.add("play");
    openedByShopper = true;
  });

  chat.addEventListener("toggle", function () {
    var shopperOpened = openedByShopper;
    openedByShopper = false;
    remember();
    if (!chat.open) {
      if (chat.contains(document.activeElement)) summary.focus();
      return;
    }
    scrollLog();
    if (shopperOpened) input.focus();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape" || !chat.open || chat.classList.contains("is-closing")) return;
    event.preventDefault();
    closeChat();
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var text = input.value.trim();
    if (!text) {
      showError("Enter a message.");
      return;
    }
    if (form.getAttribute("aria-busy") === "true") return;
    form.setAttribute("aria-busy", "true");
    syncButton();
    showError("");
    status.textContent = "";
    showTyping();

    fetch("/chat", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: new URLSearchParams({ chat_message: text }),
      credentials: "same-origin"
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        }).catch(function () {
          return { ok: false, body: {} };
        });
      })
      .then(function (result) {
        var body = result.body || {};
        hideTyping();
        if (!result.ok || !Array.isArray(body.messages)) {
          showError(typeof body.error === "string" && body.error ? body.error : "That message could not be sent. Try again.");
          return;
        }
        body.messages.forEach(appendMessage);
        showConversation(body.conversation_id);
        showHandoff(body.handoff);
        scrollLog();
        input.value = "";
        var reply = body.messages.filter(function (item) {
          return item && item.role === "agent" && typeof item.text === "string";
        }).pop();
        if (reply) {
          requestAnimationFrame(function () {
            status.textContent = reply.text;
          });
        }
      })
      .catch(function () {
        hideTyping();
        showError("That message could not be sent. Try again.");
      })
      .then(function () {
        form.removeAttribute("aria-busy");
        syncButton();
        input.focus();
      });
  });
})();
