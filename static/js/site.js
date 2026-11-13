document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector("[data-menu-toggle]");
  const nav = document.querySelector("[data-main-nav]");
  toggle?.addEventListener("click", () => {
    const open = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!open));
    nav?.classList.toggle("is-open", !open);
  });
  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => button.closest("[data-toast]")?.classList.add("hide"));
  });
  document.querySelector("[data-print]")?.addEventListener("click", () => window.print());
  document.querySelectorAll("[data-gallery-src]").forEach((button) => {
    button.addEventListener("click", () => {
      const mainImage = document.querySelector("#product-main-image");
      if (!mainImage) return;
      mainImage.src = button.dataset.gallerySrc;
      mainImage.alt = button.dataset.galleryAlt || "Visuel du produit";
      document.querySelectorAll("[data-gallery-src]").forEach((thumb) => thumb.classList.toggle("is-active", thumb === button));
    });
  });
  document.querySelectorAll("[data-toast]").forEach((toast) => {
    window.setTimeout(() => toast.classList.add("hide"), 6500);
  });
  document.body.addEventListener("cartUpdated", () => {
    const stack = document.querySelector(".toast-stack") || Object.assign(document.createElement("div"), { className: "toast-stack" });
    if (!stack.isConnected) document.body.append(stack);
    const toast = Object.assign(document.createElement("div"), { className: "toast toast-success", textContent: "Ajouté à ton panier." });
    stack.append(toast);
    window.setTimeout(() => toast.classList.add("hide"), 3200);
    window.setTimeout(() => toast.remove(), 3600);
  });

  const money = (cents) => new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(cents / 100);
  const updatePosTotal = () => {
    const total = [...document.querySelectorAll("[data-pos-price]")].reduce((sum, input) => {
      const quantity = Math.max(0, Number.parseInt(input.value || "0", 10) || 0);
      return sum + (Number.parseInt(input.dataset.posPrice || "0", 10) * quantity);
    }, 0);
    const target = document.querySelector("#pos-total");
    if (target) target.textContent = money(total);
  };
  const updateCheckout = () => {
    const fulfillment = document.querySelector('input[name="fulfillment"]:checked')?.value;
    const zone = document.querySelector("#id_delivery_zone");
    const option = zone?.options[zone.selectedIndex];
    const fee = fulfillment === "DELIVERY" ? Number.parseInt(option?.dataset.fee || "0", 10) : 0;
    const subtotal = Number.parseInt(document.querySelector("#checkout-total")?.dataset.subtotal || "0", 10);
    const shipping = document.querySelector("#checkout-shipping");
    const total = document.querySelector("#checkout-total");
    const deliveryFields = document.querySelector(".delivery-fields");
    if (deliveryFields) deliveryFields.hidden = fulfillment !== "DELIVERY";
    if (shipping) shipping.textContent = fulfillment === "DELIVERY" && zone?.value ? money(fee) : (fulfillment === "DELIVERY" ? "À choisir" : money(0));
    if (total) total.textContent = money(subtotal + fee);
  };
  document.addEventListener("input", (event) => {
    if (event.target.matches("[data-pos-price]")) updatePosTotal();
  });
  document.addEventListener("change", (event) => {
    if (event.target.matches('input[name="fulfillment"], #id_delivery_zone')) updateCheckout();
  });
  updatePosTotal();
  updateCheckout();
});
