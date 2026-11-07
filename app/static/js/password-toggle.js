(() => {
  document.querySelectorAll("[data-password-toggle-button]").forEach((button) => {
    const input = button.parentElement.querySelector("[data-password-toggle]");
    if (!input) return;

    button.addEventListener("click", () => {
      const showing = input.type === "password";
      input.type = showing ? "text" : "password";
      button.textContent = showing ? "Hide" : "Show";
      button.setAttribute("aria-label", `${showing ? "Hide" : "Show"} password`);
      button.setAttribute("aria-pressed", String(showing));
    });
  });
})();
