let currentQuestion = 1;

let totalQuestions = typeof window.totalQuestions !== "undefined"
    ? window.totalQuestions
    : document.querySelectorAll(".question-card").length;


let markedQuestions = new Set();

let answeredQuestions = new Set();

let remainingTime = 20 * 60;

let timerInterval;



document.addEventListener("DOMContentLoaded", function(){

    startTimer();

    loadSavedAnswers();

    updateProgress();

});





/* ================= QUESTION NAVIGATION ================= */


function openQuestion(number){

    document.querySelectorAll(".question-card")
    .forEach(card=>{
        card.style.display="none";
    });


    let question=document.getElementById(
        "question-"+number
    );


    if(question){

        question.style.display="block";

        currentQuestion=number;

        updatePalette();

    }

}





function nextQuestion(){

    if(currentQuestion < totalQuestions){

        openQuestion(currentQuestion+1);

    }

}





function previousQuestion(){

    if(currentQuestion > 1){

        openQuestion(currentQuestion-1);

    }

}





/* ================= ANSWER SYSTEM ================= */


function answerSelected(number){

    answeredQuestions.add(number);

    saveAnswers();

    updateProgress();

    updatePalette();

}





function clearAnswer(number){

    let card=document.getElementById(
        "question-"+number
    );


    let inputs=card.querySelectorAll(
        "input[type=radio]"
    );


    inputs.forEach(input=>{
        input.checked=false;
    });


    answeredQuestions.delete(number);

    saveAnswers();

    updateProgress();

    updatePalette();

}





/* ================= MARK REVIEW ================= */


function markQuestion(number){

    if(markedQuestions.has(number)){

        markedQuestions.delete(number);

    }

    else{

        markedQuestions.add(number);

    }


    updatePalette();

}





/* ================= PALETTE ================= */


function updatePalette(){

    for(let i=1;i<=totalQuestions;i++){


        let btn=document.getElementById(
            "palette-"+i
        );


        if(!btn) continue;


        btn.className="palette-btn";


        if(markedQuestions.has(i)){

            btn.classList.add("review");

        }

        else if(answeredQuestions.has(i)){

            btn.classList.add("answered");

        }

        else if(i!==currentQuestion){

            btn.classList.add("skipped");

        }

        else{

            btn.classList.add("active");

        }

    }


}





/* ================= PROGRESS ================= */


function updateProgress(){


    let answered =
    answeredQuestions.size;



    let percentage =
    (answered / totalQuestions) * 100;



    let bar =
    document.getElementById(
        "progressFill"
    );


    if(bar){

        bar.style.width =
        percentage+"%";

    }



    let text =
    document.getElementById(
        "progressText"
    );


    if(text){

        text.innerHTML =
        Math.round(percentage)
        +"% Completed";

    }



    let count =
    document.getElementById(
        "answeredCount"
    );


    if(count){

        count.innerHTML=answered;

    }



}/* ================= TIMER ================= */


function startTimer(){

    timerInterval=setInterval(()=>{


        let minutes=Math.floor(
            remainingTime/60
        );


        let seconds=
        remainingTime%60;



        let display=
        document.getElementById("timer");


        if(display){

            display.innerHTML=
            `${minutes<10?"0":""}${minutes}:${seconds<10?"0":""}${seconds}`;

        }



        if(remainingTime===60){

            showTimeWarning();

        }



        if(remainingTime<=0){

            clearInterval(timerInterval);

            alert(
                "Time Finished! Test Submitted Automatically"
            );

            document.getElementById(
                "mockTestForm"
            ).submit();

        }



        remainingTime--;



    },1000);

}






/* ================= LOCAL STORAGE AUTO SAVE ================= */


function saveAnswers(){


    let data={};


    document.querySelectorAll(
        "input[type=radio]:checked"
    )
    .forEach(input=>{

        data[input.name]=input.value;

    });



    localStorage.setItem(
        "mock_answers",
        JSON.stringify(data)
    );


    showAutoSave();

}






function loadSavedAnswers(){


    let saved=
    localStorage.getItem(
        "mock_answers"
    );



    if(!saved) return;



    let data=
    JSON.parse(saved);



    Object.keys(data)
    .forEach(name=>{


        let input=
        document.querySelector(
            `input[name="${name}"][value="${data[name]}"]`
        );



        if(input){

            input.checked=true;


            let question =
            input.closest(".question-card");


            if(question){

                let id=
                question.id.replace(
                    "question-",
                    ""
                );


                answeredQuestions.add(
                    Number(id)
                );

            }

        }


    });



}







/* ================= AUTO SAVE MESSAGE ================= */


function showAutoSave(){


    let box=
    document.getElementById(
        "autosaveBox"
    );


    if(!box) return;



    box.style.display="block";


    box.innerHTML=
    "💾 Saved";



    setTimeout(()=>{

        box.style.display="none";

    },1500);


}





setInterval(()=>{

    saveAnswers();

},10000);







/* ================= KEYBOARD SHORTCUT ================= */


document.addEventListener(
"keydown",
function(event){


    if(event.key==="ArrowRight"){

        nextQuestion();

    }


    if(event.key==="ArrowLeft"){

        previousQuestion();

    }



    if(event.key.toLowerCase()==="m"){

        markQuestion(
            currentQuestion
        );

    }



    if(event.key.toLowerCase()==="c"){

        clearAnswer(
            currentQuestion
        );

    }



});






/* ================= FULLSCREEN ================= */


function toggleFullscreen(){


    if(!document.fullscreenElement){

        document.documentElement.requestFullscreen();

    }

    else{

        document.exitFullscreen();

    }


}






/* ================= TIME WARNING ================= */


function showTimeWarning(){


    let modal=
    document.getElementById(
        "timeModal"
    );


    if(modal){

        modal.style.display="flex";

    }


}







/* ================= SUBMIT CONFIRM ================= */


document.getElementById(
"mockTestForm"
)
?.addEventListener(
"submit",
function(event){


    let unanswered =
    totalQuestions -
    answeredQuestions.size;



    if(unanswered>0){


        let confirmSubmit=
        confirm(
        "You have "+
        unanswered+
        " unanswered questions. Submit?"
        );



        if(!confirmSubmit){

            event.preventDefault();

        }


    }


});







/* ================= CLEAN DATA AFTER SUBMIT ================= */


function clearTestData(){

    localStorage.removeItem(
        "mock_answers"
    );

}
let currentQuestion = 1;
const totalQuestions = document.querySelectorAll(".question-card").length;

// Open specific question
function openQuestion(index) {
    document.querySelectorAll(".question-card").forEach((card, i) => {
        card.style.display = (i + 1 === index) ? "block" : "none";
    });
    currentQuestion = index;
}

// Next Question
function nextQuestion() {
    if (currentQuestion < totalQuestions) {
        openQuestion(currentQuestion + 1);
    }
}

// Previous Question
function previousQuestion() {
    if (currentQuestion > 1) {
        openQuestion(currentQuestion - 1);
    }
}

// Answer Selected
function answerSelected(index) {
    document.getElementById(`palette-${index}`).classList.remove("not-visited");
    document.getElementById(`palette-${index}`).classList.add("answered");
    updateSummary();
}

// Clear Answer
function clearAnswer(index) {
    const radios = document.querySelectorAll(`#question-${index} input[type="radio"]`);
    radios.forEach(r => r.checked = false);
    document.getElementById(`palette-${index}`).classList.remove("answered");
    document.getElementById(`palette-${index}`).classList.add("skipped");
    updateSummary();
}

// Mark Question
function markQuestion(index) {
    document.getElementById(`palette-${index}`).classList.add("review");
    updateSummary();
}

// Update Summary + Progress
function updateSummary() {
    const answered = document.querySelectorAll(".palette-btn.answered").length;
    const marked = document.querySelectorAll(".palette-btn.review").length;
    const remaining = totalQuestions - answered;

    document.getElementById("answeredCount").innerText = answered;
    document.getElementById("markedCount").innerText = marked;
    document.getElementById("remainingCount").innerText = remaining;

    const progress = Math.round((answered / totalQuestions) * 100);
    document.getElementById("progressFill").style.width = progress + "%";
    document.getElementById("progressText").innerText = progress + "% Completed";
}