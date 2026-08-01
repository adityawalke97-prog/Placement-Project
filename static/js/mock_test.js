/*==================================================
        PLACEMENT MOCK TEST
        PART 1
        VARIABLES + TIMER + NAVIGATION
==================================================*/

// ==========================
// GLOBAL VARIABLES
// ==========================

let currentQuestion = 1;

const totalQuestions = window.totalQuestions || 0;

let totalTime = 20 * 60; // 20 Minutes

let timerInterval = null;

// ==========================
// START
// ==========================

document.addEventListener("DOMContentLoaded", function () {

    showInstruction();
    updateQuestion();
    startTimer();
    updateSummary();
    updateProgress();
    restoreAnswers();

});
// ==========================
// TIMER
// ==========================

function startTimer() {

    timerInterval = setInterval(function () {

        totalTime--;

        let minutes = Math.floor(totalTime / 60);

        let seconds = totalTime % 60;

        document.getElementById("timer").innerHTML =
            String(minutes).padStart(2, "0") +
            ":" +
            String(seconds).padStart(2, "0");

        // 1 minute warning

        if (totalTime === 60) {

            document.getElementById("timeModal").style.display = "flex";

        }

        // Auto Submit

        if (totalTime <= 0) {

            clearInterval(timerInterval);

            finalSubmit();

        }

    }, 1000);

}

// ==========================
// SHOW QUESTION
// ==========================

function updateQuestion() {

    document
        .querySelectorAll(".question-card")
        .forEach(function (card) {

            card.style.display = "none";

        });

    document.getElementById(
        "question-" + currentQuestion
    ).style.display = "block";

    document
        .querySelectorAll(".palette-btn")
        .forEach(function (btn) {

            btn.classList.remove("active");

        });

    document
        .getElementById("palette-" + currentQuestion)
        .classList.add("active");

}

// ==========================
// NEXT
// ==========================

function nextQuestion() {

    if (currentQuestion < totalQuestions) {

        currentQuestion++;

        updateQuestion();

    }

}

// ==========================
// PREVIOUS
// ==========================

function previousQuestion() {

    if (currentQuestion > 1) {

        currentQuestion--;

        updateQuestion();

    }

}

// ==========================
// OPEN QUESTION
// ==========================

function openQuestion(number) {

    currentQuestion = number;

    updateQuestion();

}

// ==========================
// FULL SCREEN
// ==========================

function toggleFullscreen() {

    if (!document.fullscreenElement) {

        document.documentElement.requestFullscreen();

    } else {

        document.exitFullscreen();

    }

}
/*==================================================
        PLACEMENT MOCK TEST
        PART 2
        ANSWERS + PALETTE + PROGRESS
==================================================*/

// ==========================
// DATA
// ==========================

let answeredQuestions = new Set();
let markedQuestions = new Set();

// ==========================
// ANSWER SELECTED
// ==========================

function answerSelected(questionNo){

    answeredQuestions.add(questionNo);

    const palette =
        document.getElementById("palette-" + questionNo);

    if(palette){

        palette.classList.remove(
            "not-visited",
            "skipped",
            "review"
        );

        palette.classList.add("answered");

    }

    updateSummary();

}

// ==========================
// UPDATE SUMMARY
// ==========================

function updateSummary(){

    const answered = answeredQuestions.size;

    const marked = markedQuestions.size;

    const remaining =
        totalQuestions - answered;

    document.getElementById("answeredCount").innerText =
        answered;

    document.getElementById("markedCount").innerText =
        marked;

    document.getElementById("remainingCount").innerText =
        remaining;

    updateProgress();

}

// ==========================
// PROGRESS BAR
// ==========================

function updateProgress(){

    const percent =
        totalQuestions === 0
        ? 0
        : Math.round(
            (answeredQuestions.size / totalQuestions) * 100
        );

    document.getElementById("progressFill").style.width =
        percent + "%";

    document.getElementById("progressText").innerText =
        percent + "% Completed";

}

// ==========================
// MARK FOR REVIEW
// ==========================

function markQuestion(questionNo){

    const palette =
        document.getElementById("palette-" + questionNo);

    if(markedQuestions.has(questionNo)){

        markedQuestions.delete(questionNo);

        if(answeredQuestions.has(questionNo)){

            palette.className =
                "palette-btn answered";

        }else{

            palette.className =
                "palette-btn skipped";

        }

    }else{

        markedQuestions.add(questionNo);

        palette.className =
            "palette-btn review";

    }

    updateSummary();

}

// ==========================
// CLEAR ANSWER
// ==========================

function clearAnswer(questionNo){

    const radios =
        document.getElementsByName(
            "q" + window.questionIds[questionNo-1]
        );

    radios.forEach(function(r){

        r.checked = false;

    });

    answeredQuestions.delete(questionNo);

    const palette =
        document.getElementById("palette-" + questionNo);

    if(markedQuestions.has(questionNo)){

        palette.className =
            "palette-btn review";

    }else{

        palette.className =
            "palette-btn skipped";

    }

    updateSummary();

}

// ==========================
// UPDATE SUBMIT MODAL
// ==========================

function openSubmitModal(){

    document.getElementById("submitModal").style.display =
        "flex";

    document.getElementById("submitAnswered").innerText =
        answeredQuestions.size;

    document.getElementById("submitMarked").innerText =
        markedQuestions.size;

    document.getElementById("submitNotAnswered").innerText =
        totalQuestions - answeredQuestions.size;

}
/*==================================================
        PLACEMENT MOCK TEST
        PART 3
        AUTO SAVE + BOOKMARK + SHORTCUTS
==================================================*/

// ==========================
// AUTO SAVE
// ==========================

function autoSave() {

    const selectedAnswers = {};

    document.querySelectorAll("input[type='radio']:checked").forEach(function (radio) {

        selectedAnswers[radio.name] = radio.value;

    });

    localStorage.setItem(
        "mock_answers",
        JSON.stringify(selectedAnswers)
    );

    showAutoSave();

}

// Auto Save every 20 seconds

setInterval(autoSave, 20000);

// ==========================
// SHOW AUTO SAVE MESSAGE
// ==========================

function showAutoSave() {

    const box = document.getElementById("autosaveBox");

    if (!box) return;

    box.style.display = "block";

    setTimeout(function () {

        box.style.display = "none";

    }, 2000);

}

// ==========================
// RESTORE SAVED ANSWERS
// ==========================

function restoreAnswers() {

    const saved =
        JSON.parse(localStorage.getItem("mock_answers"));

    if (!saved) return;

    for (const name in saved) {

        const radios =
            document.getElementsByName(name);

        radios.forEach(function (radio) {

            if (radio.value === saved[name]) {

                radio.checked = true;

            }

        });

    }

}

document.addEventListener("DOMContentLoaded", restoreAnswers);

// ==========================
// BOOKMARK SYSTEM
// ==========================

let bookmarks = [];

function toggleBookmark(questionNo) {

    if (bookmarks.includes(questionNo)) {

        bookmarks =
            bookmarks.filter(q => q !== questionNo);

    } else {

        bookmarks.push(questionNo);

    }

    updateBookmarks();

}

function updateBookmarks() {

    const list =
        document.getElementById("bookmarkList");

    if (!list) return;

    list.innerHTML = "";

    if (bookmarks.length === 0) {

        list.innerHTML =
            "<p>No bookmarked questions.</p>";

        return;

    }

    bookmarks.forEach(function (q) {

        list.innerHTML +=
        `<button class="bookmark-btn"
        onclick="openQuestion(${q})">
        Question ${q}
        </button>`;

    });

}

// ==========================
// KEYBOARD SHORTCUTS
// ==========================

document.addEventListener("keydown", function (e) {

    switch (e.key) {

        case "ArrowRight":
            nextQuestion();
            break;

        case "ArrowLeft":
            previousQuestion();
            break;

        case "m":
        case "M":
            markQuestion(currentQuestion);
            break;

        case "c":
        case "C":
            clearAnswer(currentQuestion);
            break;

    }

});

// ==========================
// MOBILE PALETTE
// ==========================

function openPaletteMobile() {

    const sidebar =
        document.querySelector(".question-sidebar");

    if (!sidebar) return;

    if (sidebar.style.display === "block") {

        sidebar.style.display = "none";

    } else {

        sidebar.style.display = "block";

    }

}
/*==================================================
        PLACEMENT MOCK TEST
        PART 4
        SECURITY + AUTO SUBMIT + RESULT
==================================================*/

// ==========================
// PREVENT REFRESH WARNING
// ==========================

window.addEventListener("beforeunload", function (e) {

    e.preventDefault();

    e.returnValue =
        "Your test is still running.";

});

// ==========================
// DISABLE RIGHT CLICK
// ==========================

document.addEventListener("contextmenu", function (e) {

    e.preventDefault();

});

// ==========================
// DISABLE COPY
// ==========================

document.addEventListener("copy", function (e) {

    e.preventDefault();

});

// ==========================
// DISABLE CUT
// ==========================

document.addEventListener("cut", function (e) {

    e.preventDefault();

});

// ==========================
// DISABLE SELECT
// ==========================

document.addEventListener("selectstart", function (e) {

    e.preventDefault();

});

// ==========================
// TAB CHANGE WARNING
// ==========================

let tabChanged = 0;

document.addEventListener("visibilitychange", function () {

    if (document.hidden) {

        tabChanged++;

        if (tabChanged >= 3) {

            alert(
                "You changed the tab multiple times. Test will be submitted."
            );

            finalSubmit();

        }

    }

});

// ==========================
// RESULT PREVIEW
// ==========================

function showResultPreview(score, correct, wrong, skipped) {

    document.getElementById("resultPreview").style.display = "grid";

    document.getElementById("finalScore").innerText =
        score + "%";

    document.getElementById("correctCount").innerText =
        correct;

    document.getElementById("wrongCount").innerText =
        wrong;

    document.getElementById("skipCount").innerText =
        skipped;

}

// ==========================
// AI ANALYSIS
// ==========================

function generateAnalysis(score) {

    if (score >= 80) {

        document.getElementById("strongTopics").innerText =
            "Excellent Performance";

        document.getElementById("weakTopics").innerText =
            "Practice Mock Interviews";

    }

    else if (score >= 60) {

        document.getElementById("strongTopics").innerText =
            "Good Fundamentals";

        document.getElementById("weakTopics").innerText =
            "Revise DBMS, Aptitude";

    }

    else {

        document.getElementById("strongTopics").innerText =
            "Need More Practice";

        document.getElementById("weakTopics").innerText =
            "Java, Python, DBMS";

    }

}

// ==========================
// EXIT TEST
// ==========================

function exitTest() {

    if (confirm("Exit Test?")) {

        localStorage.removeItem("mock_answers");

        window.location.href = "/dashboard";

    }

}
/*==================================================
        PLACEMENT MOCK TEST
        PART 5 - FINAL INITIALIZATION
==================================================*/

// ==========================
// INITIALIZE SUMMARY
// ==========================

document.addEventListener("DOMContentLoaded", function () {

    updateSummary();

    updateProgress();

});

// ==========================
// RESTORE CURRENT QUESTION
// ==========================

const savedQuestion = localStorage.getItem("current_question");

if (savedQuestion) {

    currentQuestion = parseInt(savedQuestion);

    updateQuestion();

}

function saveCurrentQuestion() {

    localStorage.setItem(
        "current_question",
        currentQuestion
    );

}

// Save current question after navigation

const oldNext = nextQuestion;

nextQuestion = function () {

    oldNext();

    saveCurrentQuestion();

};

const oldPrevious = previousQuestion;

previousQuestion = function () {

    oldPrevious();

    saveCurrentQuestion();

};

// ==========================
// RESET TEST DATA
// ==========================

function resetTest() {

    localStorage.removeItem("mock_answers");

    localStorage.removeItem("current_question");

    answeredQuestions.clear();

    markedQuestions.clear();

}

// ==========================
// FORM SUBMIT
// ==========================

document
.getElementById("mockTestForm")
.addEventListener("submit", function () {

    resetTest();

});

// ==========================
// ERROR HANDLING
// ==========================

window.onerror = function (message, source, line) {

    console.error(
        "Mock Test Error:",
        message,
        source,
        line
    );

};

// ==========================
// END
// ==========================

console.log("Placement Mock Test Loaded Successfully");

// ==========================
// FINAL SUBMIT
// ==========================

function finalSubmit() {

    clearInterval(timerInterval);

    localStorage.removeItem("mock_answers");

    document.getElementById("mockTestForm").submit();

}
function showInstruction() {
    document.getElementById("instructionModal").style.display = "flex";
}

function closeInstruction() {
    document.getElementById("instructionModal").style.display = "none";
}