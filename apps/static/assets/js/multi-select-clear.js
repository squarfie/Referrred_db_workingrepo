(function () {
  "use strict";

  function triggerChange(select) {
    select.dispatchEvent(new Event("change", { bubbles: true }));

    if (window.jQuery) {
      window.jQuery(select).trigger("change");
    }
  }

  function clearSelect(select) {
    Array.prototype.forEach.call(select.options, function (option) {
      option.selected = false;
    });

    select.selectedIndex = -1;
    triggerChange(select);
  }

  function enhanceSelect(select) {
    if (!select || select.dataset.multiClearEnhanced === "true") {
      return;
    }

    select.dataset.multiClearEnhanced = "true";

    var actions = document.createElement("div");
    actions.className = "arsp-multi-select-actions";

    var button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-sm btn-outline-secondary arsp-multi-select-clear";
    button.innerHTML = '<i class="fas fa-times mr-1"></i>Clear selection';
    button.setAttribute("aria-label", "Clear selected options");
    button.setAttribute("title", "Clear selected options");
    button.disabled = select.disabled;

    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      clearSelect(select);
    });

    actions.appendChild(button);
    select.insertAdjacentElement("afterend", actions);
  }

  function enhance(root) {
    var scope = root && root.querySelectorAll ? root : document;

    if (scope.matches && scope.matches("select[multiple]")) {
      enhanceSelect(scope);
    }

    scope.querySelectorAll("select[multiple]").forEach(enhanceSelect);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      enhance(document);
    });
  } else {
    enhance(document);
  }

  if (window.MutationObserver) {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            enhance(node);
          }
        });
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }
}());
