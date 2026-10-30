(function () {
  var chat = document.getElementById("help");
  try {
    if (sessionStorage.getItem("lumen-chat-open") === "1") chat.open = true;
  } catch (err) {}
})();
