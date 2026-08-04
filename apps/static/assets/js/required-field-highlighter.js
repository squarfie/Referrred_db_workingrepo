(function () {
  "use strict";

  const FIELD_SELECTOR = [
    "input[required]:not([type=hidden]):not([disabled]):not([readonly])",
    "select[required]:not([disabled]):not([readonly])",
    "textarea[required]:not([disabled]):not([readonly])",
    "[data-required=true]:not([disabled]):not([readonly])"
  ].join(",");

  function isVisible(field) {
    return Boolean(field.offsetParent || field.getClientRects().length);
  }

  function fieldValueMissing(field) {
    if (!isVisible(field)) return false;

    if (field.type === "checkbox" || field.type === "radio") {
      const group = field.name
        ? field.form.querySelectorAll(`[name="${CSS.escape(field.name)}"]`)
        : [field];
      return !Array.from(group).some(item => item.checked);
    }

    if (field.tagName === "SELECT" && field.multiple) {
      return Array.from(field.options).every(option => !option.selected);
    }

    return String(field.value || "").trim() === "";
  }

  function findFieldWrapper(field) {
    return (
      field.closest(".form-group") ||
      field.closest(".field-block") ||
      field.closest(".staff-block") ||
      field.closest(".custom-file") ||
      field.parentElement
    );
  }

  function getFieldLabel(field) {
    const id = field.id;
    const label = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`) : null;
    const wrapperLabel = findFieldWrapper(field)?.querySelector("label");
    const text = (label || wrapperLabel)?.textContent || "This field";
    return text.replace(/\*/g, "").trim() || "This field";
  }

  function ensureFeedback(field) {
    const wrapper = findFieldWrapper(field);
    if (!wrapper) return null;

    let feedback = wrapper.querySelector(":scope > .required-field-feedback");
    if (!feedback) {
      feedback = document.createElement("div");
      feedback.className = "required-field-feedback";
      wrapper.appendChild(feedback);
    }
    feedback.textContent = `${getFieldLabel(field)} is required.`;
    return feedback;
  }

  function setInvalid(field, invalid) {
    const wrapper = findFieldWrapper(field);
    field.classList.toggle("required-field-missing", invalid);
    field.classList.toggle("is-invalid", invalid);
    field.setAttribute("aria-invalid", invalid ? "true" : "false");
    wrapper?.classList.toggle("required-field-group-missing", invalid);

    const feedback = ensureFeedback(field);
    if (feedback) {
      feedback.hidden = !invalid;
    }
  }

  function validateField(field) {
    const invalid = fieldValueMissing(field);
    setInvalid(field, invalid);
    return !invalid;
  }

  function validateForm(form) {
    const fields = Array.from(form.querySelectorAll(FIELD_SELECTOR));
    const missing = fields.filter(field => !validateField(field));

    if (missing.length) {
      missing[0].scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => missing[0].focus({ preventScroll: true }), 250);
    }

    return missing.length === 0;
  }

  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.dataset.skipRequiredHighlight === "true") return;

    if (!validateForm(form)) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);

  document.addEventListener("invalid", function (event) {
    if (event.target.matches?.(FIELD_SELECTOR)) {
      validateField(event.target);
    }
  }, true);

  document.addEventListener("input", function (event) {
    if (event.target.matches?.(FIELD_SELECTOR)) {
      validateField(event.target);
    }
  });

  document.addEventListener("change", function (event) {
    if (event.target.matches?.(FIELD_SELECTOR)) {
      validateField(event.target);
    }
  });
})();
