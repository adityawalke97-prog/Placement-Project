/* ===========================================
   Placement Mock Test
   Author : Aditya
=========================================== */

/* ---------- Global Variables ---------- */

let currentQuestion = 1;

const totalQuestions =
window.totalQuestions || 0;

const answeredQuestions = new Set();

const markedQuestions = new Set();

let remainingTime = 20 * 60;

let timerInterval = null;


/* ---------- Page Load ---------- */

document.addEventListener("DOMContentLoaded", () => {

    openQuestion(1);

    loadSavedAnswers();

    updatePalette();

    updateSummary();

    startTimer();

});


/* ---------- Open Question ---------- */

function openQuestion(number){

    const cards =
    document.querySelectorAll(".question-card");

    cards.forEach(card=>{

        card.style.display="none";

    });

    const current =
    document.getElementById(
    "question-"+number);

    if(current){

        current.style.display="block";

        currentQuestion=number;

        updatePalette();

    }

}


/* ---------- Navigation ---------- */

function nextQuestion(){

    if(currentQuestion<totalQuestions){

        openQuestion(currentQuestion+1);

    }

}


function previousQuestion(){

    if(currentQuestion>1){

        openQuestion(currentQuestion-1);

    }

}


/* ---------- Answer ---------- */

function answerSelected(number){

    answeredQuestions.add(number);

    saveAnswers();

    updatePalette();

    updateSummary();

}


/* ---------- Clear ---------- */

function clearAnswer(number){

    const card=document.getElementById(
    "question-"+number);

    if(!card) return;

    card.querySelectorAll(
    "input[type=radio]")

    .forEach(r=>r.checked=false);

    answeredQuestions.delete(number);

    saveAnswers();

    updatePalette();

    updateSummary();

}


/* ---------- Review ---------- */

function markQuestion(number){

    if(markedQuestions.has(number))

        markedQuestions.delete(number);

    else

        markedQuestions.add(number);

    updatePalette();

    updateSummary();

}


/* ---------- Palette ---------- */

function updatePalette(){

    for(let i=1;i<=totalQuestions;i++){

        const btn=document.getElementById(
        "palette-"+i);

        if(!btn) continue;

        btn.className="palette-btn";

        if(answeredQuestions.has(i))

            btn.classList.add("answered");

        else

            btn.classList.add("not-visited");

        if(markedQuestions.has(i))

            btn.classList.add("review");

        if(i===currentQuestion)

            btn.classList.add("active");

    }

}


/* ---------- Summary ---------- */

function updateSummary(){

    const answered=

    answeredQuestions.size;

    const review=

    markedQuestions.size;

    const remaining=

    totalQuestions-answered;

    document.getElementById(
    "answeredCount").innerHTML=
    answered;

    document.getElementById(
    "markedCount").innerHTML=
    review;

    document.getElementById(
    "remainingCount").innerHTML=
    remaining;

    const progress=
    Math.round(
    answered/totalQuestions*100);

    document.getElementById(
    "progressFill").style.width=
    progress+"%";

    document.getElementById(
    "progressText").innerHTML=
    progress+"% Completed";

}
/* ==========================================
   TIMER
========================================== */

function startTimer() {

    const timer =
    document.getElementById("timer");

    if (!timer) return;

    timerInterval = setInterval(() => {

        let minutes =
        Math.floor(remainingTime / 60);

        let seconds =
        remainingTime % 60;

        timer.innerHTML =
            String(minutes).padStart(2, "0")
            + ":" +
            String(seconds).padStart(2, "0");

        if (remainingTime === 60) {

            showTimeWarning();

        }

        if (remainingTime <= 0) {

            clearInterval(timerInterval);

            alert("Time Over!");

            document.getElementById(
                "mockTestForm"
            ).submit();

            return;

        }

        remainingTime--;

    }, 1000);

}



/* ==========================================
   AUTO SAVE
========================================== */

function saveAnswers() {

    const answers = {};

    document.querySelectorAll(
        "input[type=radio]:checked"
    ).forEach(input => {

        answers[input.name] = input.value;

    });

    localStorage.setItem(
        "mock_answers",
        JSON.stringify(answers)
    );

    showSaveMessage();

}



function loadSavedAnswers() {

    const saved =
    localStorage.getItem(
        "mock_answers"
    );

    if (!saved) return;

    const answers =
    JSON.parse(saved);

    Object.keys(answers).forEach(name => {

        const input =
        document.querySelector(

            `input[name="${name}"][value="${answers[name]}"]`

        );

        if (input) {

            input.checked = true;

            const question =
            input.closest(".question-card");

            if (question) {

                const number =
                parseInt(

                    question.id.replace(
                        "question-",
                        ""
                    )

                );

                answeredQuestions.add(number);

            }

        }

    });

}



/* ==========================================
   SAVE MESSAGE
========================================== */

function showSaveMessage() {

    const box =
    document.getElementById(
        "autosaveBox"
    );

    if (!box) return;

    box.style.display = "block";

    box.innerHTML = "💾 Saved";

    setTimeout(() => {

        box.style.display = "none";

    }, 1500);

}



/* Auto Save Every 10 Seconds */

setInterval(() => {

    saveAnswers();

}, 10000);



/* ==========================================
   FULLSCREEN
========================================== */

function toggleFullscreen() {

    if (!document.fullscreenElement) {

        document.documentElement
        .requestFullscreen();

    }

    else {

        document.exitFullscreen();

    }

}



/* ==========================================
   MOBILE PALETTE
========================================== */

function openPaletteMobile() {

    const sidebar =
    document.querySelector(
        ".question-sidebar"
    );

    if (sidebar) {

        sidebar.classList.toggle(
            "show"
        );

    }

}



/* ==========================================
   TIME WARNING
========================================== */

function showTimeWarning() {

    const modal =
    document.getElementById(
        "timeModal"
    );

    if (modal) {

        modal.style.display = "flex";

    }

}
/* ==========================================
   KEYBOARD SHORTCUTS
========================================== */

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

        case "Escape":
            closeInstruction();
            closeSubmitModal();
            closeTimeModal();
            closeExitModal();
            break;

    }

});


/* ==========================================
   SUBMIT CONFIRMATION
========================================== */

const form = document.getElementById("mockTestForm");

if (form) {

    form.addEventListener("submit", function (e) {

        const unanswered =
        totalQuestions -
        answeredQuestions.size;

        if (unanswered > 0) {

            const ok = confirm(

                "You still have " +
                unanswered +
                " unanswered questions.\n\nSubmit Test?"

            );

            if (!ok) {

                e.preventDefault();

                return;

            }

        }

        clearSavedAnswers();

    });

}


/* ==========================================
   RESULT PREVIEW
========================================== */

function showResultPreview(
correct = 0,
wrong = 0,
skipped = 0
){

    const result =
    document.getElementById(
        "resultPreview"
    );

    if(!result) return;

    result.style.display="block";

    document.getElementById(
        "correctCount"
    ).innerHTML=correct;

    document.getElementById(
        "wrongCount"
    ).innerHTML=wrong;

    document.getElementById(
        "skipCount"
    ).innerHTML=skipped;

    const score =
    totalQuestions===0
    ?0
    :Math.round(
        (correct/totalQuestions)*100
    );

    document.getElementById(
        "finalScore"
    ).innerHTML=
    score+"%";

}


/* ==========================================
   BOOKMARK PANEL
========================================== */

function updateBookmarkPanel(){

    const list =
    document.getElementById(
        "bookmarkList"
    );

    if(!list) return;

    if(markedQuestions.size===0){

        list.innerHTML=
        "<p>No bookmarked questions</p>";

        return;

    }

    list.innerHTML="";

    markedQuestions.forEach(num=>{

        const btn=
        document.createElement("button");

        btn.innerHTML=
        "Question "+num;

        btn.onclick=()=>{

            openQuestion(num);

        };

        list.appendChild(btn);

    });

}


/* Update bookmark whenever review changes */

const oldMarkQuestion =
markQuestion;

markQuestion=function(number){

    oldMarkQuestion(number);

    updateBookmarkPanel();

};


/* ==========================================
   AI ANALYSIS (Demo)
========================================== */

function generateAIAnalysis(){

    const strong =
    document.getElementById(
        "strongTopics"
    );

    const weak =
    document.getElementById(
        "weakTopics"
    );

    if(strong){

        strong.innerHTML=
        "Java Basics, OOP";

    }

    if(weak){

        weak.innerHTML=
        "Collections, SQL Joins";

    }

}


/* ==========================================
   LOCAL STORAGE
========================================== */

function clearSavedAnswers(){

    localStorage.removeItem(
        "mock_answers"
    );

}


/* ==========================================
   BEFORE PAGE CLOSE
========================================== */

window.addEventListener(
"beforeunload",

function(e){

    if(answeredQuestions.size>0){

        e.preventDefault();

        e.returnValue="";

    }

});


/* ==========================================
   INITIALIZE
========================================== */

document.addEventListener(
"DOMContentLoaded",

function(){

    updateBookmarkPanel();

    generateAIAnalysis();

});
