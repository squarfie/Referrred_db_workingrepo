(function () {
  'use strict';

  var jqueryWired = false;

  function moveModalToBody(modal) {
    if (!modal) {
      return;
    }

    if (modal.parentNode !== document.body) {
      document.body.appendChild(modal);
    }

    modal.style.zIndex = '120060';
    modal.style.pointerEvents = 'auto';

    var dialog = modal.querySelector('.modal-dialog');
    if (dialog) {
      dialog.style.zIndex = '120061';
      dialog.style.pointerEvents = 'auto';
    }
  }

  function normalizeModals(root) {
    var scope = root || document;
    scope.querySelectorAll('.modal').forEach(moveModalToBody);
  }

  function wireJqueryModalEvents() {
    if (jqueryWired || !window.jQuery) {
      return false;
    }

    jqueryWired = true;
    window.jQuery(document).on('show.bs.modal shown.bs.modal', '.modal', function () {
      moveModalToBody(this);
    });

    return true;
  }

  function waitForJqueryModalEvents(attemptsLeft) {
    if (wireJqueryModalEvents() || attemptsLeft <= 0) {
      return;
    }

    window.setTimeout(function () {
      waitForJqueryModalEvents(attemptsLeft - 1);
    }, 100);
  }

  function getModalFromTrigger(trigger) {
    var selector = trigger.getAttribute('data-target') ||
      trigger.getAttribute('data-bs-target') ||
      trigger.getAttribute('href');

    if (!selector || selector.charAt(0) !== '#') {
      return null;
    }

    try {
      return document.querySelector(selector);
    } catch (error) {
      return null;
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    normalizeModals(document);
    waitForJqueryModalEvents(50);
  });

  window.addEventListener('load', function () {
    normalizeModals(document);
    waitForJqueryModalEvents(50);
  });

  document.addEventListener('show.bs.modal', function (event) {
    if (event.target && event.target.classList && event.target.classList.contains('modal')) {
      moveModalToBody(event.target);
    }
  }, true);

  document.addEventListener('click', function (event) {
    var trigger = event.target.closest('[data-toggle="modal"], [data-bs-toggle="modal"]');
    if (!trigger) {
      return;
    }

    moveModalToBody(getModalFromTrigger(trigger));
    waitForJqueryModalEvents(50);
  }, true);
}());
