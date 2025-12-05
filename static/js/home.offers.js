// Minimal stub for home.offers.js
// Prevents 404 and provides a safe init point for homepage offer scripts.
(function(){
    if (window.homeOffersInitialized) return;
    window.homeOffersInitialized = true;

    document.addEventListener('DOMContentLoaded', function(){
        // No-op: real behavior may be implemented elsewhere.
        // Keep this file present to avoid missing-script errors in the console.
        // console.debug('home.offers.js stub initialized');
    });
})();
