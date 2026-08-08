"use strict";

/* =========================================================
   INTERVIEW PREPARATION PORTAL
   Complete Frontend Controller
   ========================================================= */

let viewedQuestions = new Set();
let currentRandomId = null;


/* =========================================================
   DOM READY
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
    initializeInterviewPage();
});


/* =========================================================
   INITIALIZE
   ========================================================= */

function initializeInterviewPage() {

    loadSavedProgress();

    restoreBookmarks();

    restoreCompleted();

    updateStats();

    updateProgress();

    updateDailyGoal();

    attachSearchEvents();

    attachFilterEvents();

    attachQuestionEvents();

    attachExtraEvents();

    updateQuestionCount();

}


/* =========================================================
   SEARCH
   ========================================================= */

function attachSearchEvents() {

    const searchInput =
        document.getElementById("searchInput");

    const clearSearchBtn =
        document.getElementById("clearSearchBtn");


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            function () {

                filterQuestions();

                if (clearSearchBtn) {
                    clearSearchBtn.style.display =
                        this.value.trim()
                            ? "block"
                            : "none";
                }

            }
        );

    }


    if (clearSearchBtn) {

        clearSearchBtn.addEventListener(
            "click",
            function () {

                if (searchInput) {
                    searchInput.value = "";
                }

                clearSearchBtn.style.display = "none";

                filterQuestions();

                if (searchInput) {
                    searchInput.focus();
                }

            }
        );

    }

}


/* =========================================================
   FILTER EVENTS
   ========================================================= */

function attachFilterEvents() {

    const filters = [

        "categoryFilter",
        "levelFilter",
        "companyFilter",
        "statusFilter",
        "sortFilter"

    ];


    filters.forEach(function (id) {

        const element =
            document.getElementById(id);

        if (element) {

            element.addEventListener(
                "change",
                filterQuestions
            );

        }

    });


    const resetButton =
        document.getElementById(
            "resetFiltersBtn"
        );


    if (resetButton) {

        resetButton.addEventListener(
            "click",
            resetFilters
        );

    }

}


/* =========================================================
   QUESTION EVENTS
   ========================================================= */

function attachQuestionEvents() {

    document
        .querySelectorAll(".answer-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    toggleAnswer(this);

                }
            );

        });


    document
        .querySelectorAll(".close-answer-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    const card =
                        this.closest(
                            ".question-card"
                        );

                    if (card) {

                        const answerBox =
                            card.querySelector(
                                ".answer-box"
                            );

                        const answerButton =
                            card.querySelector(
                                ".answer-btn"
                            );

                        if (answerBox) {
                            answerBox.style.display =
                                "none";
                        }

                        if (answerButton) {
                            setShowAnswerButton(
                                answerButton
                            );
                        }

                    }

                }
            );

        });


    document
        .querySelectorAll(".bookmark-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    toggleBookmark(this);

                }
            );

        });


    document
        .querySelectorAll(".copy-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    copyQuestion(this);

                }
            );

        });


    document
        .querySelectorAll(".copy-answer-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    copyAnswer(this);

                }
            );

        });


    document
        .querySelectorAll(".share-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    shareQuestion(this);

                }
            );

        });


    document
        .querySelectorAll(".complete-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    markCompleted(this);

                }
            );

        });

}


/* =========================================================
   EXTRA EVENTS
   ========================================================= */

function attachExtraEvents() {

    const randomQuestionBtn =
        document.getElementById(
            "randomQuestionBtn"
        );

    const randomVisibleBtn =
        document.getElementById(
            "randomVisibleBtn"
        );

    const randomAgainBtn =
        document.getElementById(
            "randomAgainBtn"
        );

    const closeRandomModal =
        document.getElementById(
            "closeRandomModal"
        );

    const openRandomQuestionBtn =
        document.getElementById(
            "openRandomQuestionBtn"
        );

    const continueBtn =
        document.getElementById(
            "continueBtn"
        );

    const scrollTopBtn =
        document.getElementById(
            "scrollTopBtn"
        );


    if (randomQuestionBtn) {

        randomQuestionBtn.addEventListener(
            "click",
            function () {

                showRandomQuestion();

            }
        );

    }


    if (randomVisibleBtn) {

        randomVisibleBtn.addEventListener(
            "click",
            function () {

                showRandomQuestion(true);

            }
        );

    }


    if (randomAgainBtn) {

        randomAgainBtn.addEventListener(
            "click",
            function () {

                showRandomQuestion(
                    true,
                    true
                );

            }
        );

    }


    if (closeRandomModal) {

        closeRandomModal.addEventListener(
            "click",
            closeRandomModalWindow
        );

    }


    if (openRandomQuestionBtn) {

        openRandomQuestionBtn.addEventListener(
            "click",
            openRandomQuestion
        );

    }


    if (continueBtn) {

        continueBtn.addEventListener(
            "click",
            continueLastQuestion
        );

    }


    if (scrollTopBtn) {

        scrollTopBtn.addEventListener(
            "click",
            scrollTopPage
        );

    }


    const modal =
        document.getElementById(
            "randomModal"
        );


    if (modal) {

        modal.addEventListener(
            "click",
            function (event) {

                if (event.target === modal) {

                    closeRandomModalWindow();

                }

            }
        );

    }


    window.addEventListener(
        "scroll",
        handleScroll
    );


    document.addEventListener(
        "keydown",
        handleKeyboardShortcuts
    );

}


/* =========================================================
   SHOW / HIDE ANSWER
   ========================================================= */

function toggleAnswer(button) {

    const card =
        button.closest(".question-card");


    if (!card) {
        return;
    }


    const answerBox =
        card.querySelector(".answer-box");


    if (!answerBox) {

        console.error(
            "Answer box not found."
        );

        return;
    }


    const questionId =
        card.dataset.id;


    const isVisible =
        answerBox.style.display !== "none";


    if (isVisible) {

        answerBox.style.display = "none";

        setShowAnswerButton(button);

        return;

    }


    answerBox.style.display = "block";


    button.innerHTML =
        `<span>👁️</span> Hide Answer`;


    button.classList.add(
        "answer-open"
    );


    if (questionId) {

        viewedQuestions.add(
            String(questionId)
        );

        saveProgress();

        saveRecent(questionId);

    }


    updateProgress();

}


/* =========================================================
   SHOW ANSWER BUTTON
   ========================================================= */

function setShowAnswerButton(button) {

    if (!button) {
        return;
    }


    button.innerHTML =
        `<span>💡</span> Show Answer`;


    button.classList.remove(
        "answer-open"
    );

}


/* =========================================================
   SEARCH + FILTER
   ========================================================= */

function filterQuestions() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );

    const categoryFilter =
        document.getElementById(
            "categoryFilter"
        );

    const levelFilter =
        document.getElementById(
            "levelFilter"
        );

    const companyFilter =
        document.getElementById(
            "companyFilter"
        );

    const statusFilter =
        document.getElementById(
            "statusFilter"
        );

    const sortFilter =
        document.getElementById(
            "sortFilter"
        );


    const search =
        searchInput
            ? searchInput.value
                .toLowerCase()
                .trim()
            : "";


    const category =
        categoryFilter
            ? categoryFilter.value
            : "";


    const level =
        levelFilter
            ? levelFilter.value
            : "";


    const company =
        companyFilter
            ? companyFilter.value
            : "";


    const status =
        statusFilter
            ? statusFilter.value
            : "";


    const sort =
        sortFilter
            ? sortFilter.value
            : "default";


    const container =
        document.getElementById(
            "questionsContainer"
        );


    if (!container) {
        return;
    }


    const cards = Array.from(
        container.querySelectorAll(
            ".question-card"
        )
    );


    let visibleCards = [];


    cards.forEach(function (card) {

        const text =
            card.innerText
                .toLowerCase();


        const cardCategory =
            (
                card.dataset.category || ""
            ).toLowerCase();


        const cardLevel =
            (
                card.dataset.level || ""
            ).toLowerCase();


        const cardCompany =
            (
                card.dataset.company || ""
            ).toLowerCase();


        const id =
            String(
                card.dataset.id || ""
            );


        const completed =
            isCompleted(id);


        const bookmarked =
            isBookmarked(id);


        const searchMatch =
            !search ||
            text.includes(search);


        const categoryMatch =
            !category ||
            cardCategory ===
                category.toLowerCase();


        const levelMatch =
            !level ||
            cardLevel ===
                level.toLowerCase();


        const companyMatch =
            !company ||
            cardCompany ===
                company.toLowerCase();


        let statusMatch = true;


        if (status === "completed") {

            statusMatch = completed;

        }
        else if (status === "pending") {

            statusMatch = !completed;

        }
        else if (status === "bookmarked") {

            statusMatch = bookmarked;

        }


        const visible =
            searchMatch &&
            categoryMatch &&
            levelMatch &&
            companyMatch &&
            statusMatch;


        card.style.display =
            visible ? "" : "none";


        if (visible) {

            visibleCards.push(card);

        }

    });


    sortCards(
        visibleCards,
        sort,
        container
    );


    updateQuestionCount(
        visibleCards.length
    );

}


/* =========================================================
   SORT
   ========================================================= */

function sortCards(
    cards,
    sort,
    container
) {

    if (
        !container ||
        sort === "default"
    ) {
        return;
    }


    const difficulty = {
        "basic": 1,
        "intermediate": 2,
        "advanced": 3,
        "expert": 4
    };


    cards.sort(function (a, b) {

        const titleA =
            (
                a.querySelector(
                    ".question-title"
                )?.innerText || ""
            ).toLowerCase();


        const titleB =
            (
                b.querySelector(
                    ".question-title"
                )?.innerText || ""
            ).toLowerCase();


        if (sort === "az") {

            return titleA.localeCompare(
                titleB
            );

        }


        if (sort === "za") {

            return titleB.localeCompare(
                titleA
            );

        }


        const levelA =
            difficulty[
                (
                    a.dataset.level || ""
                ).toLowerCase()
            ] || 0;


        const levelB =
            difficulty[
                (
                    b.dataset.level || ""
                ).toLowerCase()
            ] || 0;


        if (sort === "easy") {

            return levelA - levelB;

        }


        if (sort === "hard") {

            return levelB - levelA;

        }


        return 0;

    });


    cards.forEach(function (card) {

        container.appendChild(card);

    });

}


/* =========================================================
   RESET FILTERS
   ========================================================= */

function resetFilters() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );

    const filterIds = [

        "categoryFilter",
        "levelFilter",
        "companyFilter",
        "statusFilter",
        "sortFilter"

    ];


    if (searchInput) {

        searchInput.value = "";

    }


    filterIds.forEach(function (id) {

        const element =
            document.getElementById(id);

        if (element) {

            element.value =
                id === "sortFilter"
                    ? "default"
                    : "";

        }

    });


    const clearSearchBtn =
        document.getElementById(
            "clearSearchBtn"
        );


    if (clearSearchBtn) {

        clearSearchBtn.style.display =
            "none";

    }


    filterQuestions();

    showToast(
        "Filters Reset"
    );

}


/* =========================================================
   BOOKMARK
   ========================================================= */

function toggleBookmark(button) {

    const id =
        String(
            button.dataset.id || ""
        );


    if (!id) {
        return;
    }


    let bookmarks =
        JSON.parse(
            localStorage.getItem(
                "interview_bookmarks"
            )
        ) || [];


    bookmarks =
        bookmarks.map(String);


    if (bookmarks.includes(id)) {

        bookmarks =
            bookmarks.filter(
                function (item) {

                    return item !== id;

                }
            );


        button.classList.remove(
            "active"
        );


        button.innerHTML =
            `<i class="far fa-bookmark"></i>`;


        showToast(
            "🔖 Bookmark Removed"
        );

    }
    else {

        bookmarks.push(id);


        button.classList.add(
            "active"
        );


        button.innerHTML =
            `<i class="fas fa-bookmark"></i>`;


        showToast(
            "🔖 Question Bookmarked"
        );

    }


    localStorage.setItem(
        "interview_bookmarks",
        JSON.stringify(bookmarks)
    );


    updateStats();

    filterQuestions();

}


/* =========================================================
   RESTORE BOOKMARKS
   ========================================================= */

function restoreBookmarks() {

    let bookmarks =
        JSON.parse(
            localStorage.getItem(
                "interview_bookmarks"
            )
        ) || [];


    bookmarks =
        bookmarks.map(String);


    document
        .querySelectorAll(
            ".bookmark-btn"
        )
        .forEach(function (button) {

            const id =
                String(
                    button.dataset.id || ""
                );


            if (bookmarks.includes(id)) {

                button.classList.add(
                    "active"
                );


                button.innerHTML =
                    `<i class="fas fa-bookmark"></i>`;

            }

        });

}


/* =========================================================
   COMPLETED
   ========================================================= */

function markCompleted(button) {

    const card =
        button.closest(
            ".question-card"
        );


    if (!card) {
        return;
    }


    const id =
        String(
            card.dataset.id || ""
        );


    if (!id) {
        return;
    }


    let completed =
        JSON.parse(
            localStorage.getItem(
                "completed_questions"
            )
        ) || [];


    completed =
        completed.map(String);


    if (completed.includes(id)) {

        completed =
            completed.filter(
                function (item) {

                    return item !== id;

                }
            );


        card.classList.remove(
            "completed"
        );


        button.innerHTML =
            `✅ Mark Completed`;


        showToast(
            "Completion Removed"
        );

    }
    else {

        completed.push(id);


        card.classList.add(
            "completed"
        );


        button.innerHTML =
            `✅ Completed`;


        viewedQuestions.add(id);

        saveProgress();


        showToast(
            "🎉 Question Completed!"
        );

    }


    localStorage.setItem(
        "completed_questions",
        JSON.stringify(completed)
    );


    updateStats();

    updateProgress();

    updateDailyGoal();

    filterQuestions();

}


/* =========================================================
   RESTORE COMPLETED
   ========================================================= */

function restoreCompleted() {

    let completed =
        JSON.parse(
            localStorage.getItem(
                "completed_questions"
            )
        ) || [];


    completed =
        completed.map(String);


    document
        .querySelectorAll(
            ".complete-btn"
        )
        .forEach(function (button) {

            const card =
                button.closest(
                    ".question-card"
                );


            if (!card) {
                return;
            }


            const id =
                String(
                    card.dataset.id || ""
                );


            if (completed.includes(id)) {

                card.classList.add(
                    "completed"
                );


                button.innerHTML =
                    `✅ Completed`;

            }

        });

}


/* =========================================================
   COPY QUESTION
   ========================================================= */

function copyQuestion(button) {

    const card =
        button.closest(
            ".question-card"
        );


    if (!card) {
        return;
    }


    const title =
        card.querySelector(
            ".question-title"
        );


    if (!title) {
        return;
    }


    const question =
        title.innerText.trim();


    copyToClipboard(
        question
    )
    .then(function () {

        showToast(
            "📋 Question Copied"
        );


        const original =
            button.innerHTML;


        button.innerHTML =
            `✓ Copied`;


        setTimeout(function () {

            button.innerHTML =
                original;

        }, 2000);

    });

}


/* =========================================================
   COPY ANSWER
   ========================================================= */

function copyAnswer(button) {

    const card =
        button.closest(
            ".question-card"
        );


    if (!card) {
        return;
    }


    const answerBox =
        card.querySelector(
            ".answer-box"
        );


    if (!answerBox) {
        return;
    }


    const content =
        answerBox
            .querySelector(
                ".answer-content"
            );


    const question =
        card.querySelector(
            ".question-title"
        );


    let text =
        "Interview Question:\n";


    if (question) {

        text +=
            question.innerText.trim() +
            "\n\n";

    }


    text +=
        "Answer:\n";


    if (content) {

        text +=
            content.innerText.trim();

    }


    copyToClipboard(text)
        .then(function () {

            showToast(
                "📋 Answer Copied"
            );

        });

}


/* =========================================================
   CLIPBOARD
   ========================================================= */

function copyToClipboard(text) {

    if (
        navigator.clipboard &&
        window.isSecureContext
    ) {

        return navigator.clipboard.writeText(
            text
        );

    }


    return new Promise(function (
        resolve,
        reject
    ) {

        const textarea =
            document.createElement(
                "textarea"
            );


        textarea.value = text;

        textarea.style.position =
            "fixed";

        textarea.style.left =
            "-9999px";


        document.body.appendChild(
            textarea
        );


        textarea.select();


        try {

            document.execCommand(
                "copy"
            );

            document.body.removeChild(
                textarea
            );

            resolve();

        }
        catch (error) {

            document.body.removeChild(
                textarea
            );

            reject(error);

        }

    });

}


/* =========================================================
   SHARE
   ========================================================= */

function shareQuestion(button) {

    const card =
        button.closest(
            ".question-card"
        );


    if (!card) {
        return;
    }


    const title =
        card.querySelector(
            ".question-title"
        );


    if (!title) {
        return;
    }


    const question =
        title.innerText.trim();


    if (navigator.share) {

        navigator.share({

            title:
                "Interview Question",

            text:
                question,

            url:
                window.location.href

        })
        .then(function () {

            showToast(
                "📤 Shared Successfully"
            );

        })
        .catch(function () {

            /* User cancelled */

        });


    }
    else {

        copyToClipboard(
            question
        )
        .then(function () {

            showToast(
                "📋 Copied for Sharing"
            );

        });

    }

}


/* =========================================================
   RANDOM QUESTION
   ========================================================= */

function showRandomQuestion(
    visibleOnly = false,
    avoidCurrent = false
) {

    let cards =
        Array.from(
            document.querySelectorAll(
                ".question-card"
            )
        );


    if (visibleOnly) {

        cards =
            cards.filter(function (card) {

                return card.style.display !==
                    "none";

            });

    }


    if (!cards.length) {

        showToast(
            "No questions available"
        );

        return;

    }


    if (
        avoidCurrent &&
        cards.length > 1
    ) {

        cards =
            cards.filter(function (card) {

                return String(
                    card.dataset.id
                ) !==
                String(currentRandomId);

            });

    }


    const randomIndex =
        Math.floor(
            Math.random() *
            cards.length
        );


    const card =
        cards[randomIndex];


    currentRandomId =
        card.dataset.id;


    const title =
        card.querySelector(
            ".question-title"
        );


    const category =
        card.dataset.category ||
        "General";


    const level =
        card.dataset.level ||
        "Basic";


    const company =
        card.dataset.company ||
        "";


    const content =
        document.getElementById(
            "randomQuestionContent"
        );


    if (!content) {
        return;
    }


    content.innerHTML = `

        <div class="random-meta">

            <span>📂 ${escapeHtml(category)}</span>

            <span>⭐ ${escapeHtml(level)}</span>

            ${
                company
                    ? `<span>🏢 ${escapeHtml(company)}</span>`
                    : ""
            }

        </div>

        <h3>
            ${
                title
                    ? escapeHtml(
                        title.innerText
                    )
                    : "Question"
            }
        </h3>

    `;


    const modal =
        document.getElementById(
            "randomModal"
        );


    if (modal) {

        modal.classList.add(
            "show"
        );

        document.body.classList.add(
            "modal-open"
        );

    }

}


/* =========================================================
   OPEN RANDOM QUESTION
   ========================================================= */

function openRandomQuestion() {

    if (!currentRandomId) {
        return;
    }


    const card =
        document.getElementById(
            "question-" +
            currentRandomId
        );


    closeRandomModalWindow();


    if (!card) {

        showToast(
            "Question not found"
        );

        return;

    }


    card.scrollIntoView({

        behavior: "smooth",

        block: "center"

    });


    card.classList.add(
        "highlight-question"
    );


    setTimeout(function () {

        card.classList.remove(
            "highlight-question"
        );

    }, 2500);


    const answerButton =
        card.querySelector(
            ".answer-btn"
        );


    if (answerButton) {

        setTimeout(function () {

            toggleAnswer(
                answerButton
            );

        }, 600);

    }

}


/* =========================================================
   CLOSE RANDOM MODAL
   ========================================================= */

function closeRandomModalWindow() {

    const modal =
        document.getElementById(
            "randomModal"
        );


    if (modal) {

        modal.classList.remove(
            "show"
        );

    }


    document.body.classList.remove(
        "modal-open"
    );

}


/* =========================================================
   CONTINUE LAST QUESTION
   ========================================================= */

function continueLastQuestion() {

    const lastId =
        localStorage.getItem(
            "last_question"
        );


    if (!lastId) {

        showToast(
            "📚 No recent question"
        );

        return;

    }


    const card =
        document.getElementById(
            "question-" +
            lastId
        );


    if (!card) {

        showToast(
            "Question is on another page"
        );

        return;

    }


    card.scrollIntoView({

        behavior: "smooth",

        block: "center"

    });


    card.classList.add(
        "highlight-question"
    );


    setTimeout(function () {

        card.classList.remove(
            "highlight-question"
        );

    }, 2500);


    const answerBox =
        card.querySelector(
            ".answer-box"
        );


    const answerButton =
        card.querySelector(
            ".answer-btn"
        );


    if (
        answerBox &&
        answerButton
    ) {

        answerBox.style.display =
            "block";

        answerButton.innerHTML =
            `👁️ Hide Answer`;

    }

}


/* =========================================================
   RECENT QUESTION
   ========================================================= */

function saveRecent(id) {

    if (!id) {
        return;
    }


    id = String(id);


    let recent =
        JSON.parse(
            localStorage.getItem(
                "recent_questions"
            )
        ) || [];


    recent =
        recent.map(String);


    recent =
        recent.filter(function (item) {

            return item !== id;

        });


    recent.unshift(id);


    if (recent.length > 10) {

        recent =
            recent.slice(0, 10);

    }


    localStorage.setItem(
        "recent_questions",
        JSON.stringify(recent)
    );


    localStorage.setItem(
        "last_question",
        id
    );

}


/* =========================================================
   PROGRESS
   ========================================================= */

function saveProgress() {

    localStorage.setItem(
        "interview_progress",
        JSON.stringify(
            Array.from(
                viewedQuestions
            )
        )
    );

}


/* =========================================================
   LOAD PROGRESS
   ========================================================= */

function loadSavedProgress() {

    const saved =
        JSON.parse(
            localStorage.getItem(
                "interview_progress"
            )
        ) || [];


    viewedQuestions =
        new Set(
            saved.map(String)
        );

}


/* =========================================================
   UPDATE PROGRESS
   ========================================================= */

function updateProgress() {

    const cards =
        document.querySelectorAll(
            ".question-card"
        );


    const total =
        cards.length;


    let completed =
        0;


    cards.forEach(function (card) {

        const id =
            String(
                card.dataset.id || ""
            );


        if (
            viewedQuestions.has(id)
        ) {

            completed++;

        }

    });


    const percent =
        total === 0
            ? 0
            : Math.min(
                100,
                Math.round(
                    (completed / total) *
                    100
                )
            );


    const progressFill =
        document.getElementById(
            "progressFill"
        );


    const progressPercent =
        document.getElementById(
            "progressPercent"
        );


    const progressText =
        document.getElementById(
            "progressText"
        );


    if (progressFill) {

        progressFill.style.width =
            percent + "%";

    }


    if (progressPercent) {

        progressPercent.innerText =
            percent + "%";

    }


    if (progressText) {

        progressText.innerText =
            percent + "%";

    }

}


/* =========================================================
   STATS
   ========================================================= */

function updateStats() {

    const completed =
        JSON.parse(
            localStorage.getItem(
                "completed_questions"
            )
        ) || [];


    const bookmarks =
        JSON.parse(
            localStorage.getItem(
                "interview_bookmarks"
            )
        ) || [];


    const completedCount =
        document.getElementById(
            "completedCount"
        );


    const bookmarkCount =
        document.getElementById(
            "bookmarkCount"
        );


    if (completedCount) {

        completedCount.innerText =
            completed.length;

    }


    if (bookmarkCount) {

        bookmarkCount.innerText =
            bookmarks.length;

    }

}


/* =========================================================
   DAILY GOAL
   ========================================================= */

function updateDailyGoal() {

    const completed =
        JSON.parse(
            localStorage.getItem(
                "completed_questions"
            )
        ) || [];


    const goal = 20;


    const progress =
        Math.min(
            completed.length,
            goal
        );


    const percent =
        Math.round(
            (progress / goal) *
            100
        );


    const goalBar =
        document.getElementById(
            "dailyGoalFill"
        );


    const goalText =
        document.getElementById(
            "dailyGoalText"
        );


    if (goalBar) {

        goalBar.style.width =
            percent + "%";

    }


    if (goalText) {

        goalText.innerText =
            progress +
            " / " +
            goal +
            " Questions";

    }

}


/* =========================================================
   CHECK COMPLETED
   ========================================================= */

function isCompleted(id) {

    const completed =
        JSON.parse(
            localStorage.getItem(
                "completed_questions"
            )
        ) || [];


    return completed
        .map(String)
        .includes(
            String(id)
        );

}


/* =========================================================
   CHECK BOOKMARK
   ========================================================= */

function isBookmarked(id) {

    const bookmarks =
        JSON.parse(
            localStorage.getItem(
                "interview_bookmarks"
            )
        ) || [];


    return bookmarks
        .map(String)
        .includes(
            String(id)
        );

}


/* =========================================================
   QUESTION COUNT
   ========================================================= */

function updateQuestionCount(
    visibleCount = null
) {

    const cards =
        document.querySelectorAll(
            ".question-card"
        );


    const visible =
        visibleCount !== null
            ? visibleCount
            : Array.from(cards)
                .filter(function (card) {

                    return card.style.display !==
                        "none";

                }).length;


    const text =
        document.getElementById(
            "questionCountText"
        );


    const filterText =
        document.getElementById(
            "filterResultText"
        );


    if (text) {

        text.innerText =
            "Showing " +
            visible +
            " questions";

    }


    if (filterText) {

        filterText.innerText =
            "Showing " +
            visible +
            " matching questions";

    }

}


/* =========================================================
   SCROLL TOP
   ========================================================= */

function handleScroll() {

    const button =
        document.getElementById(
            "scrollTopBtn"
        );


    if (!button) {
        return;
    }


    button.style.display =
        window.scrollY > 400
            ? "flex"
            : "none";

}


/* =========================================================
   SCROLL TOP ACTION
   ========================================================= */

function scrollTopPage() {

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}


/* =========================================================
   TOAST
   ========================================================= */

let toastTimer = null;


function showToast(message) {

    const toast =
        document.getElementById(
            "toast"
        );


    if (!toast) {
        return;
    }


    toast.innerText =
        message;


    toast.classList.add(
        "show"
    );


    toast.style.display =
        "block";


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(function () {

            toast.classList.remove(
                "show"
            );


            setTimeout(function () {

                toast.style.display =
                    "none";

            }, 250);

        }, 2200);

}


/* =========================================================
   KEYBOARD SHORTCUTS
   ========================================================= */

function handleKeyboardShortcuts(
    event
) {

    const tag =
        document.activeElement
            ?.tagName
            ?.toLowerCase();


    const typing =
        tag === "input" ||
        tag === "textarea" ||
        tag === "select";


    /* CTRL + F */

    if (
        event.ctrlKey &&
        event.key.toLowerCase() === "f"
    ) {

        event.preventDefault();


        const search =
            document.getElementById(
                "searchInput"
            );


        if (search) {

            search.focus();

        }

        return;

    }


    /* ESC */

    if (event.key === "Escape") {

        closeRandomModalWindow();

        return;

    }


    /* R = Random */

    if (
        event.key.toLowerCase() === "r" &&
        !typing
    ) {

        showRandomQuestion();

        return;

    }


    /* HOME */

    if (
        event.key === "Home" &&
        !typing
    ) {

        scrollTopPage();

    }

}


/* =========================================================
   ESCAPE HTML
   ========================================================= */

function escapeHtml(value) {

    if (value === null ||
        value === undefined) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


/* =========================================================
   DEBUG
   ========================================================= */

console.log(
    "Interview Preparation JS loaded successfully."
);
