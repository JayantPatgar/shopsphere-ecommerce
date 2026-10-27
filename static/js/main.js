document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav-links");
  if (menuButton && nav) {
    menuButton.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      menuButton.setAttribute("aria-expanded", String(open));
      menuButton.textContent = open ? "×" : "☰";
    });
  }

  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });
  document.querySelectorAll(".flash").forEach((flash) => {
    window.setTimeout(() => {
      if (flash.isConnected) {
        flash.style.transition = "opacity .3s ease";
        flash.style.opacity = "0";
        window.setTimeout(() => flash.remove(), 350);
      }
    }, 6500);
  });

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  const urlInput = document.getElementById("image-url");
  const preview = document.getElementById("image-preview");
  const placeholder = document.getElementById("preview-placeholder");
  if (urlInput && preview && placeholder) {
    const updatePreview = () => {
      const url = urlInput.value.trim();
      if (!url) {
        preview.hidden = true;
        placeholder.hidden = false;
        return;
      }
      preview.onload = () => {
        preview.hidden = false;
        placeholder.hidden = true;
      };
      preview.onerror = () => {
        preview.hidden = true;
        placeholder.hidden = false;
        placeholder.textContent = "Preview unavailable. Check that this is a direct public image URL.";
      };
      preview.src = url;
    };
    urlInput.addEventListener("input", updatePreview);
    if (urlInput.value.trim()) updatePreview();
  }
});


function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);

    if (!input) return;

    if (input.type === "password") {
        input.type = "text";
        button.textContent = "Hide";
    } else {
        input.type = "password";
        button.textContent = "Show";
    }
}


