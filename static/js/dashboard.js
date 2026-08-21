/* =========================================================
   PLACEMENT TRAINING PORTAL
   STUDENT DASHBOARD JAVASCRIPT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    console.log("Student Dashboard Loaded");


    /* =====================================================
       1. ANIMATED NUMBER COUNTERS
       ===================================================== */

    const counters = document.querySelectorAll(
        ".stat-card h2"
    );

    counters.forEach(function (counter) {

        const text = counter.textContent.trim();

        /*
         * Extract number from:
         * 120
         * 85%
         * 7
         */

        const match = text.match(/\d+/);

        if (!match) {
            return;
        }

        const target = parseInt(match[0]);

        const hasPercent =
            text.includes("%");

        let current = 0;

        const duration = 1000;

        const stepTime =
            Math.max(
                20,
                duration / target
            );

        const timer = setInterval(function () {

            current++;

            counter.textContent =
                current +
                (hasPercent ? "%" : "");

            if (current >= target) {

                counter.textContent =
                    target +
                    (hasPercent ? "%" : "");

                clearInterval(timer);
            }

        }, stepTime);

    });


    /* =====================================================
       2. PROGRESS BAR ANIMATION
       ===================================================== */

    const progressBars =
        document.querySelectorAll(
            ".progress-fill"
        );

    progressBars.forEach(function (bar) {

        const finalWidth =
            bar.style.width;

        bar.style.width = "0%";

        setTimeout(function () {

            bar.style.width =
                finalWidth;

        }, 300);

    });


    /* =====================================================
       3. QUICK CARD CLICK FEEDBACK
       ===================================================== */

    const quickCards =
        document.querySelectorAll(
            ".quick-card"
        );

    quickCards.forEach(function (card) {

        card.addEventListener(
            "click",
            function () {

                card.classList.add(
                    "clicked"
                );

                setTimeout(function () {

                    card.classList.remove(
                        "clicked"
                    );

                }, 300);

            }
        );

    });


    /* =====================================================
       4. CURRENT DATE
       ===================================================== */

    const dateElements =
        document.querySelectorAll(
            "[data-dashboard-date]"
        );

    if (dateElements.length > 0) {

        const today = new Date();

        const options = {
            day: "2-digit",
            month: "short",
            year: "numeric"
        };

        const formattedDate =
            today.toLocaleDateString(
                "en-IN",
                options
            );

        dateElements.forEach(function (element) {

            element.textContent =
                formattedDate;

        });

    }


    /* =====================================================
       5. PLACEMENT SCORE
       ===================================================== */

    const circle =
        document.querySelector(
            ".circle"
        );

    if (circle) {

        const scoreElement =
            circle.querySelector("h1");

        if (scoreElement) {

            const scoreText =
                scoreElement.textContent;

            const match =
                scoreText.match(/\d+/);

            if (match) {

                const score =
                    parseInt(match[0]);

                const safeScore =
                    Math.min(
                        Math.max(score, 0),
                        100
                    );

                circle.style.background =
                    `conic-gradient(
                        #2563eb ${safeScore}%,
                        #e8edf5 ${safeScore}%
                    )`;

            }

        }

    }


    /* =====================================================
       6. TOOLTIP FOR STAT CARDS
       ===================================================== */

    const statCards =
        document.querySelectorAll(
            ".stat-card"
        );

    statCards.forEach(function (card) {

        card.addEventListener(
            "mouseenter",
            function () {

                card.setAttribute(
                    "data-hover",
                    "true"
                );

            }
        );

        card.addEventListener(
            "mouseleave",
            function () {

                card.removeAttribute(
                    "data-hover"
                );

            }
        );

    });


    /* =====================================================
       7. SMOOTH INTERNAL NAVIGATION
       ===================================================== */

    const links =
        document.querySelectorAll(
            'a[href^="#"]'
        );

    links.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const targetId =
                    link.getAttribute(
                        "href"
                    );

                if (
                    targetId === "#" ||
                    targetId.length < 2
                ) {
                    return;
                }

                const target =
                    document.querySelector(
                        targetId
                    );

                if (!target) {
                    return;
                }

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }
        );

    });


    /* =====================================================
       8. SCROLL REVEAL
       ===================================================== */

    const revealElements =
        document.querySelectorAll(
            ".progress-card, " +
            ".goal-card, " +
            ".activity-card, " +
            ".placement-card, " +
            ".recommendation-card, " +
            ".campus-drive, " +
            ".motivation-card"
        );

    if (
        "IntersectionObserver"
        in window
    ) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(
                        function (entry) {

                            if (
                                entry.isIntersecting
                            ) {

                                entry.target.classList.add(
                                    "visible"
                                );

                                observer.unobserve(
                                    entry.target
                                );

                            }

                        }
                    );

                },
                {
                    threshold: 0.12
                }
            );

        revealElements.forEach(
            function (element) {

                element.classList.add(
                    "scroll-hidden"
                );

                observer.observe(
                    element
                );

            }
        );

    }


    /* =====================================================
       9. PREVENT DOUBLE CLICK
       ===================================================== */

    const actionLinks =
        document.querySelectorAll(
            ".btn-primary, " +
            ".btn-secondary, " +
            ".quick-card, " +
            ".recommend-item"
        );

    actionLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function () {

                link.style.pointerEvents =
                    "none";

                setTimeout(function () {

                    link.style.pointerEvents =
                        "";

                }, 1000);

            }
        );

    });


    /* =====================================================
       10. DASHBOARD LOADED EVENT
       ===================================================== */

    window.dispatchEvent(
        new CustomEvent(
            "dashboardReady"
        )
    );

});