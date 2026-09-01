(function () {
  "use strict";

  var SORTABLE_TABLE_SELECTOR = "table";
  var SORTABLE_SKIP_SELECTOR = "[data-no-sort], .no-sort";
  var DETAIL_ROW_SELECTOR = ".batch-child-row, .detail-row, .collapse-row, .child-row";

  function injectStyles() {
    if (document.getElementById("sortable-tables-style")) {
      return;
    }

    var style = document.createElement("style");
    style.id = "sortable-tables-style";
    style.textContent = [
      "table.js-sortable-table thead th.js-sortable-header { cursor: pointer; user-select: none; position: relative; padding-left: 1.4rem; padding-right: 1.4rem; }",
      "table.js-sortable-table thead th.js-sortable-header:not(.text-center):not(.text-right) { padding-left: .75rem; }",
      "table.js-sortable-table thead th.js-sortable-header::after { content: '\\f0dc'; font-family: 'Font Awesome 5 Free','FontAwesome',sans-serif; font-weight: 900; font-size: .72rem; color: currentColor; opacity: .6; position: absolute; right: .45rem; top: 50%; transform: translateY(-50%); }",
      "table.js-sortable-table thead th.js-sortable-header[aria-sort='ascending']::after { content: '\\f0de'; opacity: 1; }",
      "table.js-sortable-table thead th.js-sortable-header[aria-sort='descending']::after { content: '\\f0dd'; opacity: 1; }",
      "table.js-sortable-table thead th.js-sortable-header:hover { filter: brightness(1.08); }",
      "table.js-sortable-table thead th.js-sortable-header:hover::after { opacity: .9; }",
      "table.js-sortable-table thead th.js-sortable-header:focus-visible { outline: 2px solid currentColor; outline-offset: -2px; }"
    ].join("\n");

    document.head.appendChild(style);
  }

  function getCellText(row, index) {
    var cell = row.children[index];
    if (!cell) {
      return "";
    }

    var sortValue = cell.getAttribute("data-sort-value");
    if (sortValue !== null) {
      return sortValue.trim();
    }

    var input = cell.querySelector("input, select, textarea");
    if (input) {
      if (input.type === "checkbox" || input.type === "radio") {
        return input.checked ? "1" : "0";
      }
      return (input.value || "").trim();
    }

    return (cell.textContent || "").replace(/\s+/g, " ").trim();
  }

  function normalizeValue(value) {
    var text = (value || "").trim();
    var lowered = text.toLowerCase();

    if (!text || lowered === "-" || lowered === "n/a" || lowered === "na") {
      return { type: "empty", value: "" };
    }

    var numeric = Number(text.replace(/,/g, "").replace(/%$/, ""));
    if (!Number.isNaN(numeric) && /^-?\d[\d,]*(\.\d+)?%?$/.test(text)) {
      return { type: "number", value: numeric };
    }

    var parsedDate = Date.parse(text);
    if (!Number.isNaN(parsedDate) && /[A-Za-z]{3,}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}\/\d{1,2}\/\d{2,4}/.test(text)) {
      return { type: "date", value: parsedDate };
    }

    return { type: "text", value: lowered };
  }

  function compareValues(left, right, direction) {
    var a = normalizeValue(left);
    var b = normalizeValue(right);

    if (a.type === "empty" && b.type !== "empty") {
      return 1;
    }
    if (b.type === "empty" && a.type !== "empty") {
      return -1;
    }

    var result;
    if (a.type === b.type && (a.type === "number" || a.type === "date")) {
      result = a.value - b.value;
    } else {
      result = String(a.value).localeCompare(String(b.value), undefined, {
        numeric: true,
        sensitivity: "base"
      });
    }

    return direction === "asc" ? result : -result;
  }

  function collectRowGroups(tbody) {
    var groups = [];
    var currentGroup = null;

    Array.prototype.forEach.call(tbody.rows, function (row, index) {
      var isDetailRow = row.matches(DETAIL_ROW_SELECTOR) || row.dataset.batchRow;

      if (isDetailRow && currentGroup) {
        currentGroup.rows.push(row);
        return;
      }

      currentGroup = {
        row: row,
        rows: [row],
        originalIndex: index
      };
      groups.push(currentGroup);
    });

    return groups;
  }

  function sortTableByColumn(table, header, columnIndex) {
    var tbody = table.tBodies[0];
    if (!tbody) {
      return;
    }

    var currentSort = header.getAttribute("aria-sort");
    var direction = currentSort === "ascending" ? "desc" : "asc";
    var groups = collectRowGroups(tbody);

    groups.sort(function (left, right) {
      var compared = compareValues(
        getCellText(left.row, columnIndex),
        getCellText(right.row, columnIndex),
        direction
      );

      if (compared === 0) {
        return left.originalIndex - right.originalIndex;
      }

      return compared;
    });

    Array.prototype.forEach.call(table.querySelectorAll("thead th[aria-sort]"), function (th) {
      th.setAttribute("aria-sort", "none");
    });
    header.setAttribute("aria-sort", direction === "asc" ? "ascending" : "descending");

    var fragment = document.createDocumentFragment();
    groups.forEach(function (group) {
      group.rows.forEach(function (row) {
        fragment.appendChild(row);
      });
    });
    tbody.appendChild(fragment);
  }

  function getColumnIndex(header) {
    var row = header.parentElement;
    var index = 0;

    Array.prototype.some.call(row.children, function (cell) {
      if (cell === header) {
        return true;
      }
      index += cell.colSpan || 1;
      return false;
    });

    return index;
  }

  function shouldSkipHeader(header) {
    if (header.matches(SORTABLE_SKIP_SELECTOR)) {
      return true;
    }
    if ((header.colSpan || 1) > 1) {
      return true;
    }
    return !(header.textContent || "").trim();
  }

  function makeTableSortable(table) {
    if (table.matches(SORTABLE_SKIP_SELECTOR)) {
      return;
    }

    if (table.dataset.sortableReady === "true") {
      return;
    }

    var headerRow = table.tHead && table.tHead.rows.length ? table.tHead.rows[table.tHead.rows.length - 1] : null;
    var tbody = table.tBodies[0];
    if (!headerRow || !tbody || tbody.rows.length < 2) {
      return;
    }

    table.dataset.sortableReady = "true";
    table.classList.add("js-sortable-table");

    Array.prototype.forEach.call(headerRow.cells, function (header) {
      if (shouldSkipHeader(header)) {
        return;
      }

      var columnIndex = getColumnIndex(header);
      header.classList.add("js-sortable-header");
      header.setAttribute("tabindex", "0");
      header.setAttribute("role", "button");
      header.setAttribute("aria-sort", "none");
      header.title = header.title || "Sort";

      header.addEventListener("click", function (event) {
        if (event.target.closest("a, button, input, select, textarea, label")) {
          return;
        }
        sortTableByColumn(table, header, columnIndex);
      });

      header.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          sortTableByColumn(table, header, columnIndex);
        }
      });
    });
  }

  function initializeSortableTables(root) {
    injectStyles();
    Array.prototype.forEach.call((root || document).querySelectorAll(SORTABLE_TABLE_SELECTOR), makeTableSortable);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initializeSortableTables(document);
  });

  document.addEventListener("htmx:afterSwap", function (event) {
    initializeSortableTables(event.target || document);
  });

  window.initializeSortableTables = initializeSortableTables;
})();
