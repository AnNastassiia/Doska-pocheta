(function () {
    'use strict';

    function initReveal() {
        var items = document.querySelectorAll('.reveal');
        if (!items.length) {
            return;
        }

        if (!('IntersectionObserver' in window)) {
            items.forEach(function (el) {
                el.classList.add('is-visible');
            });
            return;
        }

        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { root: null, rootMargin: '0px 0px -8% 0px', threshold: 0.12 }
        );

        items.forEach(function (el) {
            observer.observe(el);
        });
    }

    function initTopbarScroll() {
        var topbar = document.querySelector('.topbar');
        if (!topbar) {
            return;
        }
        var onScroll = function () {
            if (window.scrollY > 12) {
                topbar.classList.add('is-scrolled');
            } else {
                topbar.classList.remove('is-scrolled');
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    function initSmoothAnchors() {
        document.querySelectorAll('a[href^="#"]').forEach(function (link) {
            var id = link.getAttribute('href');
            if (!id || id === '#') {
                return;
            }
            var target = document.querySelector(id);
            if (!target) {
                return;
            }
            link.addEventListener('click', function (event) {
                event.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initReveal();
        initTopbarScroll();
        initSmoothAnchors();
    });
})();
