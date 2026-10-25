// Kept in step with Android LanguagePolicy. No device data leaves the browser.
(function (root) {
  'use strict';
  const supported = new Set(['en','ru','uk','pl','de','fr','es','it','pt','tr','zh','ja','ko','ar','hi','id']);
  const resolve = (choice, preferred = []) => {
    if (choice !== 'auto') return supported.has(choice) ? choice : 'en';
    for (const tag of preferred) {
      let language = String(tag).replaceAll('_', '-').split('-')[0].toLowerCase();
      if (language === 'in') language = 'id';
      if (supported.has(language)) return language;
    }
    return 'en';
  };
  const policy = Object.freeze({resolve});
  if (typeof module === 'object' && module.exports) module.exports = policy;
  else root.DeckivoLanguagePolicy = policy;
})(typeof window === 'undefined' ? {} : window);
