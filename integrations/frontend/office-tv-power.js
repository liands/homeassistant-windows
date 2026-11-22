const entityId = "remote.televisao_ir_exemplo";
const marker = "data-office-tv-power";

const styles = `
  :host([${marker}]) ha-switch {
    position: relative;
    --ha-switch-width: 40px;
    --ha-switch-size: 34px;
    --ha-switch-background-color: transparent;
    --ha-switch-thumb-background-color: transparent;
    --ha-switch-checked-background-color: transparent;
    --ha-switch-checked-thumb-background-color: transparent;
    --ha-switch-border-color: transparent;
    --ha-switch-thumb-border-color: transparent;
    --ha-switch-checked-border-color: transparent;
    --ha-switch-checked-border-color-hover: transparent;
    --ha-switch-checked-thumb-border-color: transparent;
    --ha-switch-thumb-box-shadow: none;
  }

  :host([${marker}]) ha-switch::after {
    content: "";
    position: absolute;
    inset: 50% auto auto 50%;
    translate: -50% -50%;
    width: 26px;
    height: 26px;
    pointer-events: none;
    background: var(--secondary-text-color, #a0a0a0);
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.3' stroke-linecap='round' d='M12 2.6v8.3M6.7 5.6a8.4 8.4 0 1 0 10.6 0'/%3E%3C/svg%3E") center / contain no-repeat;
  }

  :host([${marker}="on"]) ha-switch {
    filter: drop-shadow(0 0 5px rgb(255 193 7 / 60%));
  }

  :host([${marker}="on"]) ha-switch::after {
    background: #ffc107;
  }

  :host([${marker}="unavailable"]) ha-switch::after {
    opacity: .35;
  }
`;

function inMoreInfo(element) {
  for (let host = element.getRootNode().host; host; host = host.getRootNode().host) {
    if (host.localName === "ha-more-info-dialog") return true;
  }
  return false;
}

customElements.whenDefined("ha-entity-toggle").then(() => {
  const prototype = customElements.get("ha-entity-toggle").prototype;
  const nativeUpdated = prototype.updated;
  const installed = Symbol.for("office-tv-power.updated");
  if (prototype[installed]) return;
  prototype[installed] = true;

  // Keep the native switch, its keyboard support, and its service call.
  prototype.updated = function (changedProperties) {
    nativeUpdated.call(this, changedProperties);
    if (this.stateObj?.entity_id !== entityId || !inMoreInfo(this)) {
      if (this.hasAttribute(marker)) this.removeAttribute(marker);
      return;
    }
    const root = this.shadowRoot;
    if (!root?.querySelector("ha-switch")) return;
    if (!root.querySelector("style[data-office-tv-power-style]")) {
      const style = document.createElement("style");
      style.setAttribute("data-office-tv-power-style", "");
      style.textContent = styles;
      root.append(style);
    }
    this.setAttribute(marker, this.stateObj.state);
  };
});
