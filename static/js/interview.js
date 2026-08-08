"use strict";

let viewedQuestions = new Set();

document.addEventListener("DOMContentLoaded", function () {
    initializeInterviewPage();
});

function initializeInterviewPage() {
    loadSavedProgress();
    restoreBookmarks();
    restoreCompleted();
    updateStats();
    updateProgress();
    updateDailyGoal();

    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const levelFilter = document.getElementById("levelFilter");
    const companyFilter = document.getElementById("companyFilter");
    const resetButton = document.getElementById("resetFiltersBtn");

    if (searchInput) {
        searchInput.addEventListener("input", filterQuestions);
    }

    if (categoryFilter) {
        categoryFilter.addEventListener("change", filterQuestions);
    }

    if (levelFilter) {
        levelFilter.addEventListener("change", filterQuestions);
    }

    if (companyFilter) {
        companyFilter.addEventListener("change", filterQuestions);
    }

    if (resetButton) {
        resetButton.addEventListener("click", resetFilters);
    }

    document.querySelectorAll(".answer-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            toggleAnswer(this);
        });
    });

    document.querySelectorAll(".bookmark-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            toggleBookmark(this);
        });
    });

    document.querySelectorAll(".copy-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            copyQuestion(this);
        });
    });

    document.querySelectorAll(".share-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            shareQuestion(this);
        });
    });

    document.querySelectorAll(".complete-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            markCompleted(this);
        });
    });

    const scrollButton = document.getElementById("scrollTopBtn");

    if (scrollButton) {
        scrollButton.addEventListener("click", scrollTopPage);
    }

    const continueButton = document.getElementById("continueBtn");

    if (continueButton) {
        continueButton.addEventListener(
            "click",
            continueLastQuestion
        );
    }

    window.addEventListener("scroll", handleScroll);

    document.addEventListener("keydown", handleKeyboardShortcuts);
}

/* =========================
   SHOW / HIDE ANSWER
========================= */
function toggleAnswer(button) {
    const card = button.closest(".question-card");

    if (!card) {
        console.error("Question card not found");
        return;
    }

    const answerBox = card.querySelector(".answer-box");

    if (!answerBox) {
        console.error("Answer box not found");
        return;
    }

    const questionId = card.dataset.id;

    const isVisible = answerBox.classList.contains("show");

    if (isVisible) {
        answerBox.classList.remove("show");

        button.innerHTML = `
            <i class="fas fa-lightbulb"></i>
            Show Answer
        `;
    } else {
        answerBox.classList.add("show");

        button.innerHTML = `
            <i class="fas fa-eye-slash"></i>
            Hide Answer
        `;

        if (questionId) {
            viewedQuestions.add(questionId);
            saveProgress();
            updateProgress();
            saveRecent(questionId);
        }
    }
}

/* =========================
   SEARCH AND FILTER
========================= */

function filterQuestions() {
    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const levelFilter = document.getElementById("levelFilter");
    const companyFilter = document.getElementById("companyFilter");

    const search = searchInput
        ? searchInput.value.toLowerCase().trim()
        : "";

    const category = categoryFilter
        ? categoryFilter.value
        : "";

    const level = levelFilter
        ? levelFilter.value
        : "";

    const company = companyFilter
        ? companyFilter.value
        : "";

    document.querySelectorAll(".question-card").forEach(function (card) {
        const text = card.innerText.toLowerCase();

        const cardCategory = card.dataset.category || "";
        const cardLevel = card.dataset.level || "";
        const cardCompany = card.dataset.company || "";

        const matches =
            text.includes(search) &&
            (category === "" || cardCategory === category) &&
            (level === "" || cardLevel === level) &&
            (company === "" || cardCompany === company);

        card.style.display = matches ? "" : "none";
    });
}

function resetFilters() {
    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const levelFilter = document.getElementById("levelFilter");
    const companyFilter = document.getElementById("companyFilter");

    if (searchInput) {
        searchInput.value = "";
    }

    if (categoryFilter) {
        categoryFilter.value = "";
    }

    if (levelFilter) {
        levelFilter.value = "";
    }

    if (companyFilter) {
        companyFilter.value = "";
    }

    filterQuestions();
}

/* =========================
   BOOKMARK
========================= */

function toggleBookmark(button) {
    const id = button.dataset.id;

    if (!id) {
        return;
    }

    let bookmarks =
        JSON.parse(
            localStorage.getItem("interview_bookmarks")
        ) || [];

    if (bookmarks.includes(id)) {
        bookmarks = bookmarks.filter(function (item) {
            return item !== id;
        });

        button.classList.remove("active");

        button.innerHTML =
            '<i class="far fa-bookmark"></i>';

        showToast("Bookmark Removed");
    } else {
        bookmarks.push(id);

        button.classList.add("active");

        button.innerHTML =
            '<i class="fas fa-bookmark"></i>';

        showToast("Question Bookmarked");
    }

    localStorage.setItem(
        "interview_bookmarks",
        JSON.stringify(bookmarks)
    );

    updateStats();
}

function restoreBookmarks() {
    const bookmarks =
        JSON.parse(
            localStorage.getItem("interview_bookmarks")
        ) || [];

    document.querySelectorAll(".bookmark-btn").forEach(
        function (button) {
            const id = button.dataset.id;

            if (bookmarks.includes(id)) {
                button.classList.add("active");

                button.innerHTML =
                    '<i class="fas fa-bookmark"></i>';
            }
        }
    );
}

/* =========================
   COMPLETED
========================= */

function markCompleted(button) {
    const card = button.closest(".question-card");

    if (!card) {
        return;
    }

    const id = card.dataset.id;

    if (!id) {
        return;
    }

    let completed =
        JSON.parse(
            localStorage.getItem("completed_questions")
        ) || [];

    if (completed.includes(id)) {
        completed = completed.filter(function (item) {
            return item !== id;
        });

        card.classList.remove("completed");

        button.innerHTML = `
            <i class="fas fa-check-circle"></i>
            Mark Completed
        `;

        showToast("Removed from Completed");
    } else {
        completed.push(id);

        card.classList.add("completed");

        button.innerHTML = `
            <i class="fas fa-check-circle"></i>
            Completed
        `;

        viewedQuestions.add(id);

        saveProgress();
        updateProgress();

        showToast("Question Completed");
    }

    localStorage.setItem(
        "completed_questions",
        JSON.stringify(completed)
    );

    updateStats();
}

function restoreCompleted() {
    const completed =
        JSON.parse(
            localStorage.getItem("completed_questions")
        ) || [];

    document.querySelectorAll(".complete-btn").forEach(
        function (button) {
            const card = button.closest(".question-card");

            if (!card) {
                return;
            }

            const id = card.dataset.id;

            if (completed.includes(id)) {
                card.classList.add("completed");

                button.innerHTML = `
                    <i class="fas fa-check-circle"></i>
                    Completed
                `;
            }
        }
    );
}

/* =========================
   COPY QUESTION
========================= */

function copyQuestion(button) {
    const card = button.closest(".question-card");

    if (!card) {
        return;
    }

    const title = card.querySelector(".question-title");

    if (!title) {
        return;
    }

    const question = title.innerText.trim();

    navigator.clipboard.writeText(question)
        .then(function () {
            showToast("Question Copied");

            button.innerHTML =
                '<i class="fas fa-check"></i> Copied';

            setTimeout(function () {
                button.innerHTML =
                    '<i class="fas fa-copy"></i> Copy';
            }, 2000);
        })
        .catch(function () {
            showToast("Copy failed");
        });
}

/* =========================
   SHARE QUESTION
========================= */

function shareQuestion(button) {
    const card = button.closest(".question-card");

    if (!card) {
        return;
    }

    const title = card.querySelector(".question-title");

    if (!title) {
        return;
    }

    const question = title.innerText.trim();

    if (navigator.share) {
        navigator.share({
            title: "Interview Question",
            text: question
        }).catch(function () {
            // User cancelled sharing.
        });
    } else {
        navigator.clipboard.writeText(question)
            .then(function () {
                showToast("Copied for Sharing");
            });
    }
}

/* =========================
   PROGRESS
========================= */

function saveProgress() {
    localStorage.setItem(
        "interview_progress",
        JSON.stringify([...viewedQuestions])
    );
}

function loadSavedProgress() {
    const saved =
        JSON.parse(
            localStorage.getItem("interview_progress")
        ) || [];

    viewedQuestions = new Set(saved);
}

function updateProgress() {
    const total =
        document.querySelectorAll(".question-card").length;

    const completed = viewedQuestions.size;

    const percent = total === 0
        ? 0
        : Math.min(100, Math.round((completed / total) * 100));

    const progressFill =
        document.getElementById("progressFill");

    const progressPercent =
        document.getElementById("progressPercent");

    const progressText =
        document.getElementById("progressText");

    if (progressFill) {
        progressFill.style.width = percent + "%";
    }

    if (progressPercent) {
        progressPercent.innerText = percent + "%";
    }

    if (progressText) {
        progressText.innerText = percent + "%";
    }
}

/* =========================
   STATS
========================= */

function updateStats() {
    const completed =
        JSON.parse(
            localStorage.getItem("completed_questions")
        ) || [];

    const bookmarks =
        JSON.parse(
            localStorage.getItem("interview_bookmarks")
        ) || [];

    const completedCount =
        document.getElementById("completedCount");

    const bookmarkCount =
        document.getElementById("bookmarkCount");

    if (completedCount) {
        completedCount.innerText = completed.length;
    }

    if (bookmarkCount) {
        bookmarkCount.innerText = bookmarks.length;
    }
}

/* =========================
   RECENT QUESTIONS
========================= */

function saveRecent(id) {
    if (!id) {
        return;
    }

    let recent =
        JSON.parse(
            localStorage.getItem("recent_questions")
        ) || [];

    recent = recent.filter(function (item) {
        return item !== id;
    });

    recent.unshift(id);

    if (recent.length > 10) {
        recent.pop();
    }

    localStorage.setItem(
        "recent_questions",
        JSON.stringify(recent)
    );

    localStorage.setItem("last_question", id);
}

/* =========================
   CONTINUE LAST QUESTION
========================= */

function continueLastQuestion() {
    const lastId =
        localStorage.getItem("last_question");

    if (!lastId) {
        showToast("No recent question found");
        return;
    }

    const card =
        document.getElementById("question-" + lastId);

    if (card) {
        card.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

        card.classList.add("highlight-question");

        setTimeout(function () {
            card.classList.remove("highlight-question");
        }, 2000);
    } else {
        showToast("Recent question is on another page");
    }
}

/* =========================
   DAILY GOAL
========================= */

function updateDailyGoal() {
    const completed =
        JSON.parse(
            localStorage.getItem("completed_questions")
        ) || [];

    const todayGoal = 20;
    const progress = Math.min(
        completed.length,
        todayGoal
    );

    const percent = Math.round(
        (progress / todayGoal) * 100
    );

    const goalBar =
        document.getElementById("dailyGoalFill");

    const goalText =
        document.getElementById("dailyGoalText");

    if (goalBar) {
        goalBar.style.width = percent + "%";
    }

    if (goalText) {
        goalText.innerText =
            progress + " / " + todayGoal + " Questions";
    }
}

/* =========================
   SCROLL TO TOP
========================= */

function handleScroll() {
    const scrollButton =
        document.getElementById("scrollTopBtn");

    if (!scrollButton) {
        return;
    }

    scrollButton.style.display =
        window.scrollY > 400 ? "block" : "none";
}

function scrollTopPage() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

/* =========================
   TOAST
========================= */

function showToast(message) {
    const toast =
        document.getElementById("toast");

    if (!toast) {
        return;
    }

    toast.innerText = message;
    toast.style.display = "block";

    setTimeout(function () {
        toast.style.display = "none";
    }, 2500);
}

/* =========================
   KEYBOARD SHORTCUTS
========================= */

function handleKeyboardShortcuts(event) {
    const searchInput =
        document.getElementById("searchInput");

    if (
        event.ctrlKey &&
        event.key.toLowerCase() === "f"
    ) {
        event.preventDefault();

        if (searchInput) {
            searchInput.focus();
        }
    }

    if (event.key === "Home") {
        scrollTopPage();
    }
}
