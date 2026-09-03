/* =====================================
   PREMIUM DASHBOARD JS - PART 1
===================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ===========================
       Animated Counter
    =========================== */

    document.querySelectorAll(".stat-card h2").forEach(counter => {

        let text = counter.innerText.replace(/[^0-9]/g, "");

        if (text === "") return;

        let target = parseInt(text);

        let current = 0;

        let increment = Math.ceil(target / 80);

        let suffix = counter.innerText.replace(/[0-9]/g, "");

        const update = () => {

            current += increment;

            if (current >= target) {

                current = target;

            }

            counter.innerText = current + suffix;

            if (current < target) {

                requestAnimationFrame(update);

            }

        };

        update();

    });


    /* ===========================
       Progress Bar Animation
    =========================== */

    document.querySelectorAll(".progress-fill").forEach(bar => {

        let width = bar.style.width;

        bar.style.width = "0";

        setTimeout(() => {

            bar.style.width = width;

            bar.style.transition = "1.5s ease";

        }, 300);

    });


    /* ===========================
       Weekly Performance Chart
    =========================== */

    if (document.getElementById("performanceChart")) {

        new Chart(document.getElementById("performanceChart"), {

            type: "line",

            data: {

                labels: [
                    "Mon",
                    "Tue",
                    "Wed",
                    "Thu",
                    "Fri",
                    "Sat",
                    "Sun"
                ],

                datasets: [{

                    label: "Score",

                    data: [62, 71, 83, 79, 91, 86, 95],

                    borderWidth: 3,

                    tension: .4,

                    fill: true

                }]

            },

            options: {

                responsive: true,

                plugins: {

                    legend: {

                        display: false

                    }

                }

            }

        });

    }


    /* ===========================
       Subject Accuracy Chart
    =========================== */

    if (document.getElementById("subjectChart")) {

        new Chart(document.getElementById("subjectChart"), {

            type: "doughnut",

            data: {

                labels: [

                    "Java",

                    "Python",

                    "DBMS",

                    "OS",

                    "CN"

                ],

                datasets: [{

                    data: [

                        90,

                        85,

                        75,

                        80,

                        70

                    ],

                    borderWidth: 1

                }]

            },

            options: {

                responsive: true,

                plugins: {

                    legend: {

                        position: "bottom"

                    }

                }

            }

        });

    }


    /* ===========================
       Card Hover Animation
    =========================== */

    document.querySelectorAll(".glass").forEach(card => {

        card.addEventListener("mouseenter", () => {

            card.style.transform = "translateY(-6px)";

        });

        card.addEventListener("mouseleave", () => {

            card.style.transform = "translateY(0)";

        });

    });

});/* =====================================
   PREMIUM DASHBOARD JS - PART 2
   Dark Mode • Notification • AI
===================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================
       Dynamic Greeting
    ========================== */

    const greeting = document.getElementById("greeting");

    if (greeting) {

        const hour = new Date().getHours();

        let text = "Welcome";

        if (hour < 12) {

            text = "🌞 Good Morning";

        } else if (hour < 17) {

            text = "☀️ Good Afternoon";

        } else {

            text = "🌙 Good Evening";

        }

        greeting.innerHTML = text;

    }


    /* ==========================
       Live Clock
    ========================== */

    const clock = document.getElementById("liveClock");

    function updateClock() {

        if (!clock) return;

        clock.innerHTML = new Date().toLocaleTimeString();

    }

    setInterval(updateClock, 1000);

    updateClock();


    /* ==========================
       Dark Mode
    ========================== */

    const darkBtn = document.getElementById("darkMode");

    if (darkBtn) {

        if (localStorage.getItem("theme") === "dark") {

            document.body.classList.add("dark");

            darkBtn.innerHTML = '<i class="fas fa-sun"></i>';

        }

        darkBtn.onclick = () => {

            document.body.classList.toggle("dark");

            if (document.body.classList.contains("dark")) {

                localStorage.setItem("theme", "dark");

                darkBtn.innerHTML = '<i class="fas fa-sun"></i>';

            } else {

                localStorage.setItem("theme", "light");

                darkBtn.innerHTML = '<i class="fas fa-moon"></i>';

            }

        };

    }


    /* ==========================
       Notification Badge
    ========================== */

    const badge = document.getElementById("notifyCount");

    if (badge) {

        let count = 5;

        badge.innerHTML = count;

        setInterval(() => {

            count++;

            badge.innerHTML = count;

            badge.classList.add("pulse");

            setTimeout(() => {

                badge.classList.remove("pulse");

            }, 700);

        }, 45000);

    }


    /* ==========================
       Floating AI Button
    ========================== */

    const ai = document.querySelector(".floating-ai");

    if (ai) {

        ai.addEventListener("mouseenter", () => {

            ai.style.transform = "scale(1.1)";

        });

        ai.addEventListener("mouseleave", () => {

            ai.style.transform = "scale(1)";

        });

    }


    /* ==========================
       Scroll Reveal
    ========================== */

    const observer = new IntersectionObserver(entries => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {

                entry.target.classList.add("show");

            }

        });

    }, {

        threshold: .15

    });

    document.querySelectorAll(".glass").forEach(card => {

        card.classList.add("hidden");

        observer.observe(card);

    });


    /* ==========================
       Daily Goal Progress
    ========================== */

    document.querySelectorAll("progress").forEach(bar => {

        const value = bar.value;

        bar.value = 0;

        let current = 0;

        const timer = setInterval(() => {

            current++;

            bar.value = current;

            if (current >= value) {

                clearInterval(timer);

            }

        }, 20);

    });


    /* ==========================
       Auto Toast
    ========================== */

    setTimeout(() => {

        const toast = document.createElement("div");

        toast.className = "dashboard-toast";

        toast.innerHTML =
            "🎉 Welcome back! Keep preparing for your placement.";

        document.body.appendChild(toast);

        setTimeout(() => {

            toast.classList.add("show");

        }, 100);

        setTimeout(() => {

            toast.classList.remove("show");

            setTimeout(() => {

                toast.remove();

            }, 400);

        }, 4000);

    }, 1200);

});
