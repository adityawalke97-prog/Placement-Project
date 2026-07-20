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
