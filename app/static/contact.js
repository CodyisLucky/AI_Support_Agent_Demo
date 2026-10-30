document.getElementById("open-help").addEventListener("click", function () {
  var chat = document.getElementById("help");
  var summary = chat && chat.querySelector(".chat-launcher");
  if (!chat || !summary) return;
  if (chat.open && !chat.classList.contains("is-closing")) {
    var input = document.getElementById("chat-message");
    if (input) input.focus();
    return;
  }
  summary.click();
});
