/*==================================================
        INTERVIEW PREPARATION
        PART 1
        SEARCH + FILTER + ANSWER + PROGRESS
==================================================*/

// ==========================
// GLOBAL
// ==========================

const questionCards = document.querySelectorAll(".question-card");

const searchInput = document.getElementById("searchInput");

const categoryFilter = document.getElementById("categoryFilter");

const levelFilter = document.getElementById("levelFilter");

const companyFilter = document.getElementById("companyFilter");

const progressFill = document.getElementById("progressFill");

const progressPercent = document.getElementById("progressPercent");

let viewedQuestions = new Set();

// ==========================
// SEARCH
// ==========================

if(searchInput){

searchInput.addEventListener("keyup",function(){

    filterQuestions();

});

}

// ==========================
// FILTER
// ==========================

if(categoryFilter){

categoryFilter.addEventListener("change",filterQuestions);

}

if(levelFilter){

levelFilter.addEventListener("change",filterQuestions);

}

if(companyFilter){

companyFilter.addEventListener("change",filterQuestions);

}

// ==========================
// FILTER FUNCTION
// ==========================

function filterQuestions(){

    const search =
        searchInput ? searchInput.value.toLowerCase() : "";

    const category =
        categoryFilter ? categoryFilter.value : "";

    const level =
        levelFilter ? levelFilter.value : "";

    const company =
        companyFilter ? companyFilter.value : "";

    questionCards.forEach(function(card){

        const text =
            card.innerText.toLowerCase();

        const c =
            card.dataset.category || "";

        const l =
            card.dataset.level || "";

        const com =
            card.dataset.company || "";

        const visible =
            text.includes(search)
            &&
            (category==="" || c===category)
            &&
            (level==="" || l===level)
            &&
            (company==="" || com===company);

        card.style.display =
            visible ? "block" : "none";

    });

}

// ==========================
// SHOW ANSWER
// ==========================

function toggleAnswer(btn){

    const answer =
        btn.parentElement.querySelector(".answer-box");

    if(!answer) return;

    if(answer.style.display==="block"){

        answer.style.display="none";

        btn.innerHTML="Show Answer";

    }else{

        answer.style.display="block";

        btn.innerHTML="Hide Answer";

        viewedQuestions.add(btn.dataset.id);

        updateProgress();

    }

}

// ==========================
// PROGRESS
// ==========================

function updateProgress(){

    const total =
        questionCards.length;

    const completed =
        viewedQuestions.size;

    const percent =
        total===0 ? 0 :
        Math.round((completed/total)*100);

    if(progressFill){

        progressFill.style.width =
            percent+"%";

    }

    if(progressPercent){

        progressPercent.innerHTML =
            percent+"%";

    }

}
/*==================================================
        INTERVIEW PREPARATION
        PART 2
        BOOKMARK + COPY + SHARE + TOAST
==================================================*/

// ==========================
// BOOKMARK
// ==========================

restoreBookmarks();

function toggleBookmark(btn){

    const id = btn.dataset.id;

    let bookmarks =
        JSON.parse(localStorage.getItem("interview_bookmarks")) || [];

    if(bookmarks.includes(id)){

        bookmarks =
            bookmarks.filter(x => x !== id);

        btn.classList.remove("active");

        btn.innerHTML =
            '<i class="far fa-bookmark"></i>';

        showToast("Bookmark Removed");

    }else{

        bookmarks.push(id);

        btn.classList.add("active");

        btn.innerHTML =
            '<i class="fas fa-bookmark"></i>';

        showToast("Question Bookmarked");

    }

    localStorage.setItem(
        "interview_bookmarks",
        JSON.stringify(bookmarks)
    );

}

function restoreBookmarks(){

    let bookmarks =
        JSON.parse(localStorage.getItem("interview_bookmarks")) || [];

    document.querySelectorAll(".bookmark-btn").forEach(function(btn){

        const id = btn.dataset.id;

        if(bookmarks.includes(id)){

            btn.classList.add("active");

            btn.innerHTML =
                '<i class="fas fa-bookmark"></i>';

        }

    });

}

// ==========================
// COPY QUESTION
// ==========================

function copyQuestion(btn){

    const question = btn.closest(".question-card")
                        .querySelector(".question-title")
                        .innerText;

    navigator.clipboard.writeText(question);

    btn.innerHTML = "Copied ✓";

    btn.classList.add("copied");

    showToast("Question Copied");

    setTimeout(function(){

        btn.innerHTML = "Copy";

        btn.classList.remove("copied");

    },2000);

}

// ==========================
// SHARE QUESTION
// ==========================

function shareQuestion(btn){

    const question = btn.closest(".question-card")
                        .querySelector(".question-title")
                        .innerText;

    if(navigator.share){

        navigator.share({

            title:"Interview Question",

            text:question

        });

    }else{

        navigator.clipboard.writeText(question);

        showToast("Copied for Sharing");

    }

}

// ==========================
// TOAST
// ==========================

function showToast(message){

    const toast =
        document.getElementById("toast");

    if(!toast) return;

    toast.innerHTML = message;

    toast.style.display = "block";

    setTimeout(function(){

        toast.style.display = "none";

    },2500);

}

// ==========================
// SAVE PROGRESS
// ==========================

window.addEventListener("beforeunload",function(){

    localStorage.setItem(

        "interview_progress",

        JSON.stringify([...viewedQuestions])

    );

});

document.addEventListener("DOMContentLoaded",function(){

    const saved =
        JSON.parse(localStorage.getItem("interview_progress"));

    if(saved){

        viewedQuestions =
            new Set(saved);

        updateProgress();

    }

});
/*==================================================
        INTERVIEW PREPARATION
        PART 3
        FAVORITES + COMPLETED + GOAL +
        SCROLL TO TOP + CONTINUE
==================================================*/

// ==========================
// MARK COMPLETED
// ==========================

restoreCompleted();

function markCompleted(btn){

    const card = btn.closest(".question-card");

    const id = btn.dataset.id;

    let completed =
        JSON.parse(localStorage.getItem("completed_questions")) || [];

    if(completed.includes(id)){

        completed =
            completed.filter(x => x !== id);

        card.classList.remove("completed");

        btn.innerHTML = "✔ Mark Completed";

        showToast("Removed from Completed");

    }else{

        completed.push(id);

        card.classList.add("completed");

        btn.innerHTML = "✅ Completed";

        viewedQuestions.add(id);

        updateProgress();

        showToast("Question Completed");

    }

    localStorage.setItem(

        "completed_questions",

        JSON.stringify(completed)

    );

}

// ==========================
// RESTORE COMPLETED
// ==========================

function restoreCompleted(){

    const completed =
        JSON.parse(localStorage.getItem("completed_questions")) || [];

    document.querySelectorAll(".complete-btn").forEach(function(btn){

        const id = btn.dataset.id;

        if(completed.includes(id)){

            btn.innerHTML = "✅ Completed";

            btn.closest(".question-card")
               .classList.add("completed");

        }

    });

}

// ==========================
// DAILY GOAL
// ==========================

function updateDailyGoal(){

    const completed =
        JSON.parse(localStorage.getItem("completed_questions")) || [];

    const todayGoal = 20;

    const progress =
        Math.min(completed.length,todayGoal);

    const percent =
        Math.round((progress/todayGoal)*100);

    const bar =
        document.getElementById("dailyGoalFill");

    const text =
        document.getElementById("dailyGoalText");

    if(bar){

        bar.style.width = percent+"%";

    }

    if(text){

        text.innerHTML =
            progress+" / "+todayGoal+" Questions";

    }

}

document.addEventListener(

    "DOMContentLoaded",

    updateDailyGoal

);

// ==========================
// SCROLL TO TOP
// ==========================

const scrollBtn =
    document.getElementById("scrollTop");

window.addEventListener("scroll",function(){

    if(!scrollBtn) return;

    if(window.scrollY>400){

        scrollBtn.style.display="block";

    }else{

        scrollBtn.style.display="none";

    }

});

function scrollTopPage(){

    window.scrollTo({

        top:0,

        behavior:"smooth"

    });

}

// ==========================
// SAVE LAST QUESTION
// ==========================

document.querySelectorAll(".answer-btn").forEach(function(btn){

    btn.addEventListener("click",function(){

        const card =
            this.closest(".question-card");

        if(card){

            localStorage.setItem(

                "last_question",

                card.id

            );

        }

    });

});

// ==========================
// CONTINUE LAST QUESTION
// ==========================

document.addEventListener(

"DOMContentLoaded",

function(){

    const last =
        localStorage.getItem("last_question");

    if(last){

        const card =
            document.getElementById(last);

        if(card){

            card.scrollIntoView({

                behavior:"smooth",

                block:"center"

            });

        }

    }

});
/*==================================================
        INTERVIEW PREPARATION
        PART 4
        RANDOM + STREAK + TIMER +
        RECENT + SHORTCUTS
==================================================*/

// ==========================
// RANDOM QUESTION
// ==========================

function randomQuestion(){

    const cards =
        document.querySelectorAll(".question-card");

    if(cards.length===0) return;

    const random =
        Math.floor(Math.random()*cards.length);

    cards[random].scrollIntoView({

        behavior:"smooth",

        block:"center"

    });

    showToast("Random Question Opened");

}

// ==========================
// STREAK
// ==========================

function updateStreak(){

    const today =
        new Date().toLocaleDateString();

    let last =
        localStorage.getItem("streak_date");

    let streak =
        parseInt(localStorage.getItem("streak")) || 0;

    if(last!==today){

        streak++;

        localStorage.setItem("streak",streak);

        localStorage.setItem("streak_date",today);

    }

    const streakBox =
        document.getElementById("streakCount");

    if(streakBox){

        streakBox.innerHTML=streak;

    }

}

document.addEventListener(

    "DOMContentLoaded",

    updateStreak

);

// ==========================
// STUDY TIMER
// ==========================

let studyMinutes = 0;

setInterval(function(){

    studyMinutes++;

    const timer =
        document.getElementById("studyTime");

    if(timer){

        timer.innerHTML =
            studyMinutes+" Min";

    }

},60000);

// ==========================
// RECENT QUESTIONS
// ==========================

function saveRecent(id){

    let recent =
        JSON.parse(localStorage.getItem("recent_questions")) || [];

    recent =
        recent.filter(q=>q!==id);

    recent.unshift(id);

    if(recent.length>10){

        recent.pop();

    }

    localStorage.setItem(

        "recent_questions",

        JSON.stringify(recent)

    );

}

document.querySelectorAll(".answer-btn").forEach(function(btn){

    btn.addEventListener("click",function(){

        saveRecent(btn.dataset.id);

    });

});

// ==========================
// RECENT PANEL
// ==========================

function loadRecent(){

    const panel =
        document.getElementById("recentList");

    if(!panel) return;

    panel.innerHTML="";

    const recent =
        JSON.parse(localStorage.getItem("recent_questions")) || [];

    recent.forEach(function(id){

        panel.innerHTML +=

        `<button class="secondary-btn"
        onclick="document.getElementById('question-${id}')
        .scrollIntoView({behavior:'smooth'})">

        Question ${id}

        </button>`;

    });

}

document.addEventListener(

    "DOMContentLoaded",

    loadRecent

);

// ==========================
// KEYBOARD SHORTCUTS
// ==========================

document.addEventListener("keydown",function(e){

    if(e.ctrlKey && e.key==="f"){

        e.preventDefault();

        searchInput.focus();

    }

    if(e.key==="Home"){

        scrollTopPage();

    }

    if(e.key==="r" || e.key==="R"){

        randomQuestion();

    }

});

// ==========================
// QUICK STATS
// ==========================

function updateStats(){

    const completed =
        JSON.parse(localStorage.getItem("completed_questions")) || [];

    const bookmarked =
        JSON.parse(localStorage.getItem("interview_bookmarks")) || [];

    const completedBox =
        document.getElementById("completedCount");

    const bookmarkBox =
        document.getElementById("bookmarkCount");

    if(completedBox){

        completedBox.innerHTML =
            completed.length;

    }

    if(bookmarkBox){

        bookmarkBox.innerHTML =
            bookmarked.length;

    }

}

document.addEventListener(

    "DOMContentLoaded",

    updateStats

);

console.log("Interview JS Part 4 Loaded");
