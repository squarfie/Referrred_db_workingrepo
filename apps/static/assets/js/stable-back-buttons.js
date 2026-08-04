(function () {
  "use strict";

  var backButtonSelector = [
    'a[data-stable-back-button]',
    'button[data-stable-back-button]',
    'input[data-stable-back-button]',
    '[role="button"][data-stable-back-button]',
    '.btn[data-stable-back-button]',
    'a[data-back-target]',
    'button[data-back-target]',
    'input[data-back-target]',
    '[role="button"][data-back-target]',
    '.btn-back',
    '.back-btn',
    '[aria-label*="Back"]',
    '[aria-label*="back"]',
    '[title*="Back"]',
    '[title*="back"]',
    'a[onclick*="history.back"]',
    'button[onclick*="history.back"]',
    'input[onclick*="history.back"]',
    '[role="button"][onclick*="history.back"]',
    'a[onclick*="window.history.back"]',
    'button[onclick*="window.history.back"]',
    'input[onclick*="window.history.back"]',
    '[role="button"][onclick*="window.history.back"]',
    'a[href^="javascript:history.back"]',
    'a[href^="javascript:window.history.back"]'
  ].join(",");

  function startsWithAny(path, prefixes) {
    return prefixes.some(function (prefix) {
      return path.indexOf(prefix) === 0;
    });
  }

  function normalizedText(element) {
    return (element.textContent || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function resolveStableBackTarget(pathname) {
    var path = (pathname || window.location.pathname || "/").toLowerCase();

    if (path === "/" || path === "") {
      return "/";
    }

    if (path === "/settings" || path.indexOf("/settings/") === 0) {
      return "/settings/";
    }

    if (
      startsWithAny(path, [
        "/breakpoints",
        "/breakpoints-edit",
        "/breakpoints-delete",
        "/antibiotics",
        "/antibiotics-edit",
        "/antibiotics-delete",
        "/organism",
        "/organisms",
        "/organism-edit",
        "/organism-delete",
        "/sitecode",
        "/site-code",
        "/site-add",
        "/site-view",
        "/site-edit",
        "/site-delete",
        "/specimen",
        "/specimens",
        "/specimen-edit",
        "/specimen-delete",
        "/phenotype",
        "/pre-phenotype",
        "/post-phenotype",
        "/recommendation",
        "/recommendations",
        "/emerging/criteria",
        "/tat/config",
        "/tat_config",
        "/tat-configuration",
        "/settings/non-working",
        "/contact",
        "/add_contact",
        "/delete_contact",
        "/edit_contact",
        "/accounts",
        "/staff",
        "/ars_staff",
        "/arsp_staff",
        "/upload-sitecode",
        "/upload-organism",
        "/upload-antibiotics",
        "/upload-breakpoints",
        "/upload-specimens"
      ])
    ) {
      return "/settings/";
    }

    if (path.indexOf("/final/concordance_report") === 0) {
      return "/final/concordance_history/";
    }

    if (path.indexOf("/final/concordance/batch/") === 0 || path.indexOf("/final/concordance/accession/") === 0) {
      return "/final/concordance_history/";
    }

    if (path.indexOf("/final/concordance_history") === 0) {
      return "/final/concordance_analysis/";
    }

    if (path.indexOf("/final/concordance_analysis") === 0 || path.indexOf("/final/concordance") === 0) {
      return "/final/concordance_analysis/";
    }

    if (startsWithAny(path, ["/final/edit_final", "/final/map", "/final/ast", "/final/projects", "/final/emerging"])) {
      return "/final/show_final_table";
    }

    if (path.indexOf("/tat/analysis") === 0) {
      return "/tat/running/";
    }

    if (path.indexOf("/tat/running") === 0 || path.indexOf("/tat/scanning") === 0 || /^\/tat\/\d+\/?$/.test(path)) {
      return "/tat/running/";
    }

    if (path.indexOf("/tat/") === 0) {
      return "/settings/";
    }

    if (path.indexOf("/upload/") === 0) {
      if (path.indexOf("/upload/get-details/") === 0) {
        return "/upload/wgs/data-overview";
      }

      if (path.indexOf("/upload/wgs/data-overview") === 0) {
        return "/upload/data_center/";
      }

      return "/upload/data_center/";
    }

    if (
      startsWithAny(path, [
        "/edit/",
        "/raw-data/",
        "/map_fields",
        "/test_results-view",
        "/search_results",
        "/review_batches",
        "/projects/wgs/classification",
        "/lab_result"
      ])
    ) {
      return "/show/";
    }

    if (path.indexOf("/batch-edit") === 0 || path.indexOf("/batches") === 0) {
      return "/batches/";
    }

    if (path.indexOf("/batch") === 0) {
      return "/batches/";
    }

    return "/";
  }

  function isInteractiveElement(element) {
    return !!(
      element &&
      element.matches &&
      element.matches('a, button, input, [role="button"], .btn')
    );
  }

  function isBackToTopElement(element, text, href, title) {
    var id = (element.getAttribute("id") || "").toLowerCase();
    var aria = (element.getAttribute("aria-label") || "").toLowerCase();

    return (
      id === "mybtn" ||
      id.indexOf("backtotop") !== -1 ||
      text.indexOf("back to top") !== -1 ||
      text.indexOf("top") !== -1 ||
      title.indexOf("top") !== -1 ||
      aria.indexOf("top") !== -1 ||
      href === "#top" ||
      href === "#mytop"
    );
  }

  function isLegacyBackElement(element) {
    if (!element || element.nodeType !== 1) {
      return false;
    }

    if (!isInteractiveElement(element)) {
      return false;
    }

    var onclick = element.getAttribute("onclick") || "";
    var href = element.getAttribute("href") || "";
    var text = normalizedText(element);
    var aria = (element.getAttribute("aria-label") || "").toLowerCase();
    var title = (element.getAttribute("title") || "").toLowerCase();

    if (isBackToTopElement(element, text, href, title)) {
      return false;
    }

    var looksLikeBack =
      text === "back" ||
      text === "← back" ||
      text === "< back" ||
      text.indexOf(" back") !== -1 ||
      text.indexOf("←") !== -1 ||
      aria.indexOf("back") !== -1 ||
      title.indexOf("back") !== -1 ||
      element.classList.contains("btn-back") ||
      element.classList.contains("back-btn");

  return (
    element.hasAttribute("data-stable-back-button") ||
    element.hasAttribute("data-back-target") ||
    onclick.indexOf("history.back") !== -1 ||
    onclick.indexOf("window.history.back") !== -1 ||
      href.indexOf("javascript:history.back") === 0 ||
      href.indexOf("javascript:window.history.back") === 0 ||
      looksLikeBack
    );
  }

  function findBackButtonTarget(start) {
    var target = start && start.closest ? start.closest(backButtonSelector) : null;
    return isLegacyBackElement(target) ? target : null;
  }

  function prepareBackButtons(root) {
    var scope = root && root.querySelectorAll ? root : document;
    var elements = [];

    if (scope.matches && scope.matches(backButtonSelector)) {
      elements.push(scope);
    }

    scope.querySelectorAll(backButtonSelector).forEach(function (element) {
      elements.push(element);
    });

    elements.forEach(function (element) {
      if (!isLegacyBackElement(element)) {
        return;
      }

      element.setAttribute("data-stable-back-button", "true");
      element.style.pointerEvents = "auto";
      element.style.cursor = "pointer";
      if (!element.style.position || element.style.position === "static") {
        element.style.position = "relative";
      }
      if (!element.style.zIndex) {
        element.style.zIndex = "1000";
      }

      if (!element.getAttribute("data-back-target")) {
        element.setAttribute("data-back-target", resolveStableBackTarget());
      }
      element.removeAttribute("onclick");

      if (element.tagName === "A") {
        element.setAttribute("href", element.getAttribute("data-back-target"));
      }

      if (element.tagName === "BUTTON" && !element.getAttribute("type")) {
        element.setAttribute("type", "button");
      }
    });
  }

  document.addEventListener(
    "click",
    function (event) {
      var backButton = findBackButtonTarget(event.target);

      if (!backButton) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      if (event.stopImmediatePropagation) {
        event.stopImmediatePropagation();
      }

      window.location.assign(backButton.getAttribute("data-back-target") || resolveStableBackTarget());
    },
    true
  );

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      prepareBackButtons(document);
    });
  } else {
    prepareBackButtons(document);
  }

  if (window.MutationObserver) {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            prepareBackButtons(node);
          }
        });
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  window.ARSPStableBack = {
    resolveBackTarget: resolveStableBackTarget
  };
})();
