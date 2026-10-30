(function () {
  const guestFields = document.getElementById("guest-fields");
  const accountFields = document.getElementById("account-fields");
  const newCard = document.getElementById("new-card");
  const saveCard = document.getElementById("save-card");

  function syncAccount() {
    const choice = document.querySelector('input[name="checkout_as"]:checked');
    const asAccount = choice && choice.value === "account";
    if (guestFields) guestFields.hidden = asAccount;
    if (accountFields) accountFields.hidden = !asAccount;
    if (saveCard) saveCard.hidden = choice ? !asAccount : false;
  }

  function syncPay() {
    const choice = document.querySelector('input[name="pay_with"]:checked');
    const useSaved = choice && choice.value === "saved";
    if (newCard) newCard.hidden = Boolean(useSaved);
  }

  document.querySelectorAll('input[name="checkout_as"]').forEach((input) => {
    input.addEventListener("change", syncAccount);
  });
  document.querySelectorAll('input[name="pay_with"]').forEach((input) => {
    input.addEventListener("change", syncPay);
  });
  syncAccount();
  syncPay();
})();
