const lightId = "light.jbl_partylight_stick";
const buttonId = "button.jbl_partylight_reconectar_bluetooth";
const selector = "[data-jbl-bluetooth-reconnect]";
const installed = Symbol.for("jbl-partylight.reconnect");

customElements.whenDefined("ha-more-info-dialog").then(() => {
  const prototype = customElements.get("ha-more-info-dialog").prototype;
  if (prototype[installed]) return;
  prototype[installed] = true;
  const nativeUpdated = prototype.updated;

  prototype.updated = function (changes) {
    nativeUpdated?.call(this, changes);
    const root = this.shadowRoot;
    if (!root) return;
    const info = root.querySelector('ha-more-info-info');
    const existing = root.querySelector(selector);
    if (info?.entityId !== lightId) {
      existing?.remove();
      return;
    }
    if (existing) return;

    const row = document.createElement("div");
    row.setAttribute("data-jbl-bluetooth-reconnect", "");
    row.style.cssText = "display:grid;justify-items:center;gap:8px;padding:12px 16px 4px";
    const button = document.createElement("button");
    button.type = "button";
    button.style.cssText = [
      "display:inline-flex", "align-items:center", "gap:8px", "min-height:44px",
      "padding:8px 16px", "border:1px solid var(--divider-color)", "border-radius:24px",
      "background:var(--secondary-background-color)", "color:var(--primary-text-color)",
      "font:inherit", "cursor:pointer",
    ].join(";");
    const icon = document.createElement("ha-icon");
    icon.setAttribute("icon", "mdi:bluetooth-connect");
    icon.setAttribute("aria-hidden", "true");
    const label = document.createElement("span");
    label.textContent = "Reconectar Bluetooth";
    button.append(icon, label);
    const status = document.createElement("div");
    status.setAttribute("role", "status");
    status.style.cssText = "color:var(--secondary-text-color);font-size:13px;text-align:center";
    button.addEventListener("click", async () => {
      if (button.disabled) return;
      button.disabled = true;
      status.textContent = "Buscando a JBL...";
      try {
        await this.hass.callService("button", "press", { entity_id: buttonId });
        status.textContent = "JBL encontrada. Estado atualizado.";
      } catch {
        status.textContent = "JBL indisponível. Ligue a luminária e feche o app JBL antes de tentar novamente.";
      } finally {
        button.disabled = false;
      }
    });
    row.append(button, status);
    info.parentElement.append(row);
  };
});
