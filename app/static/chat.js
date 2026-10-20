(function () {
  var chat = document.getElementById("help");
  var summary = chat && chat.querySelector(".chat-launcher");
  var panel = document.getElementById("chat-panel");
  var log = document.getElementById("chat-log");
  var form = chat && chat.querySelector(".chat-form");
  var input = document.getElementById("chat-message");
  var error = document.getElementById("chat-error");
  var status = document.getElementById("chat-status");
  if (!chat || !summary || !panel || !log || !form || !input || !error || !status) return;

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
    var paragraph = document.createElement("p");
    paragraph.textContent = message.text;
    item.appendChild(paragraph);
    log.appendChild(item);
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
        if (!result.ok || !Array.isArray(body.messages)) {
          showError(typeof body.error === "string" && body.error ? body.error : "That message could not be sent. Try again.");
          return;
        }
        body.messages.forEach(appendMessage);
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
        showError("That message could not be sent. Try again.");
      })
      .then(function () {
        form.removeAttribute("aria-busy");
        syncButton();
        input.focus();
      });
  });
})();
