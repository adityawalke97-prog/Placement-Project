
/*=========================================================
    COURSE LEARNING JS
    PART 1
    Initialization • Variables • Theme • Sidebar • Lessons
=========================================================*/

"use strict";

/*=========================================================
    DOM Ready
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.init();

});

/*=========================================================
    LMS Object
=========================================================*/

const LMS = {

    currentLesson: 0,

    lessons: [],

    progress: 0,

    storage: {

        lesson: "course_current_lesson",

        progress: "course_progress",

        theme: "course_theme"

    },

    elements: {},

    config: {

        animationDuration: 400,

        autoSave: true

    },

    /*============================================*/

    init() {

        this.cacheDOM();

        this.loadTheme();

        this.loadLessons();

        this.restoreProgress();

        this.bindEvents();

        this.updateProgress();

        console.log("Course Learning Initialized");

    },

    /*============================================*/

    cacheDOM() {

        this.elements.sidebar =
            document.querySelector(".lesson-sidebar");

        this.elements.lessonItems =
            document.querySelectorAll(".lesson-item");

        this.elements.video =
            document.querySelector("video");

        this.elements.progress =
            document.querySelector(".progress-fill");

        this.elements.themeBtn =
            document.querySelector("#themeToggle");

        this.elements.nextBtn =
            document.querySelector("#nextLesson");

        this.elements.prevBtn =
            document.querySelector("#prevLesson");

        this.elements.lessonTitle =
            document.querySelector("#lessonTitle");

    },

    /*============================================*/

    loadLessons() {

        this.lessons =
            Array.from(
                document.querySelectorAll(".lesson-item")
            );

    },

    /*============================================*/

    bindEvents() {

        this.bindLessonEvents();

        this.bindNavigation();

        this.bindTheme();

        this.bindVideo();

    },

    /*============================================*/

    bindLessonEvents() {

        this.lessons.forEach((lesson, index) => {

            lesson.addEventListener("click", () => {

                this.selectLesson(index);

            });

        });

    },

    /*============================================*/

    bindNavigation() {

        if (this.elements.nextBtn) {

            this.elements.nextBtn.addEventListener("click", () => {

                this.nextLesson();

            });

        }

        if (this.elements.prevBtn) {

            this.elements.prevBtn.addEventListener("click", () => {

                this.previousLesson();

            });

        }

    },

    /*============================================*/

    bindTheme() {

        if (!this.elements.themeBtn) return;

        this.elements.themeBtn.addEventListener("click", () => {

            document.body.classList.toggle("dark-mode");

            localStorage.setItem(

                this.storage.theme,

                document.body.classList.contains("dark-mode")

            );

        });

    },

    /*============================================*/

    loadTheme() {

        const dark =
            localStorage.getItem(this.storage.theme);

        if (dark === "true") {

            document.body.classList.add("dark-mode");

        }

    },

    /*============================================*/

    bindVideo() {

        if (!this.elements.video) return;

        this.elements.video.addEventListener("ended", () => {

            this.completeLesson();

        });

        this.elements.video.addEventListener("timeupdate", () => {

            this.saveWatchTime();

        });

    },

    /*============================================*/

    selectLesson(index) {

        this.currentLesson = index;

        this.lessons.forEach(item => {

            item.classList.remove("active");

        });

        this.lessons[index].classList.add("active");

        localStorage.setItem(

            this.storage.lesson,

            index

        );

        console.log("Lesson:", index);

    },

    /*============================================*/

    restoreProgress() {

        const lesson =
            localStorage.getItem(this.storage.lesson);

        if (lesson !== null) {

            this.selectLesson(Number(lesson));

        }

    },

    /*============================================*/

    nextLesson() {

        if (this.currentLesson >= this.lessons.length - 1)

            return;

        this.selectLesson(this.currentLesson + 1);

    },

    /*============================================*/

    previousLesson() {

        if (this.currentLesson <= 0)

            return;

        this.selectLesson(this.currentLesson - 1);

    },

    /*============================================*/

    completeLesson() {

        this.progress +=
            (100 / this.lessons.length);

        if (this.progress > 100)

            this.progress = 100;

        this.updateProgress();

    },

    /*============================================*/

    updateProgress() {

        if (!this.elements.progress) return;

        this.elements.progress.style.width =
            this.progress + "%";

        localStorage.setItem(

            this.storage.progress,

            this.progress

        );

    },

    /*============================================*/

    saveWatchTime() {

        if (!this.elements.video) return;

        localStorage.setItem(

            "watch_time",

            this.elements.video.currentTime

        );

    }

};

/*=========================================================
    COURSE LEARNING JS
    PART 2
    Continue Learning • Progress • Auto Next • Toast
=========================================================*/

/*=========================================================
    Restore Video Time
=========================================================*/

LMS.restoreWatchTime = function () {

    if (!this.elements.video) return;

    const watchTime = localStorage.getItem("watch_time");

    if (watchTime) {

        this.elements.video.currentTime = parseFloat(watchTime);

    }

};

/*=========================================================
    Save Progress
=========================================================*/

LMS.saveProgress = function () {

    const data = {

        lesson: this.currentLesson,

        progress: this.progress,

        updated: new Date().toISOString()

    };

    localStorage.setItem(
        "course_learning_progress",
        JSON.stringify(data)
    );

};

/*=========================================================
    Load Progress
=========================================================*/

LMS.loadProgress = function () {

    const data = localStorage.getItem("course_learning_progress");

    if (!data) return;

    const progress = JSON.parse(data);

    this.currentLesson = progress.lesson || 0;

    this.progress = progress.progress || 0;

    this.selectLesson(this.currentLesson);

    this.updateProgress();

};

/*=========================================================
    Auto Next Lesson
=========================================================*/

LMS.autoNextLesson = function () {

    if (this.currentLesson >= this.lessons.length - 1) {

        this.showToast(
            "🎉 Course Completed!",
            "Congratulations!"
        );

        return;

    }

    this.nextLesson();

};

/*=========================================================
    Complete Lesson
=========================================================*/

LMS.completeLesson = function () {

    this.progress += (100 / this.lessons.length);

    if (this.progress > 100) {

        this.progress = 100;

    }

    this.updateProgress();

    this.saveProgress();

    this.showToast(
        "✅ Lesson Completed",
        "Progress Saved Successfully"
    );

    setTimeout(() => {

        this.autoNextLesson();

    }, 1200);

};

/*=========================================================
    Circular Progress
=========================================================*/

LMS.updateCircularProgress = function () {

    const circle = document.querySelector(".progress-circle");

    if (!circle) return;

    const value = Math.round(this.progress);

    circle.style.background =
        `conic-gradient(#2563eb ${value * 3.6}deg,#e5e7eb 0deg)`;

    const text = circle.querySelector("span");

    if (text) {

        text.textContent = value + "%";

    }

};

/*=========================================================
    Animate Progress Bar
=========================================================*/

LMS.animateProgress = function () {

    if (!this.elements.progress) return;

    this.elements.progress.style.transition =
        "width .6s ease";

    this.elements.progress.style.width =
        this.progress + "%";

    this.updateCircularProgress();

};

/*=========================================================
    Toast Notification
=========================================================*/

LMS.showToast = function (title, message) {

    const toast = document.querySelector(".custom-toast");

    if (!toast) return;

    toast.classList.add("show");

    const titleElement =
        toast.querySelector(".toast-title");

    const messageElement =
        toast.querySelector(".toast-message");

    if (titleElement) {

        titleElement.textContent = title;

    }

    if (messageElement) {

        messageElement.textContent = message;

    }

    setTimeout(() => {

        toast.classList.remove("show");

    }, 3000);

};

/*=========================================================
    Loader
=========================================================*/

LMS.hideLoader = function () {

    const loader = document.getElementById("loader");

    if (!loader) return;

    setTimeout(() => {

        loader.style.opacity = "0";

        loader.style.visibility = "hidden";

    }, 600);

};

/*=========================================================
    Reading Progress Bar
=========================================================*/

LMS.updateReadingProgress = function () {

    const progressBar =
        document.getElementById("readingProgress");

    if (!progressBar) return;

    const scrollTop =
        window.scrollY;

    const docHeight =
        document.documentElement.scrollHeight -
        window.innerHeight;

    const percent =
        (scrollTop / docHeight) * 100;

    progressBar.style.width =
        percent + "%";

};

window.addEventListener("scroll", () => {

    LMS.updateReadingProgress();

});

/*=========================================================
    Continue Learning Button
=========================================================*/

LMS.continueLearning = function () {

    this.loadProgress();

    this.restoreWatchTime();

    this.showToast(
        "📚 Continue Learning",
        "Previous progress restored"
    );

};

/*=========================================================
    Initialize Extra Features
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.loadProgress();

    LMS.restoreWatchTime();

    LMS.hideLoader();

});

/*=========================================================
    COURSE LEARNING JS
    PART 3
    Notes • Copy Code • Bookmark • Reading Time • Search
=========================================================*/

"use strict";

/*=========================================================
    NOTES SEARCH
=========================================================*/

LMS.searchNotes = function () {

    const input = document.querySelector("#notesSearch");

    const notes = document.querySelectorAll(".note-card");

    if (!input) return;

    input.addEventListener("keyup", function () {

        const keyword = this.value.toLowerCase().trim();

        notes.forEach(note => {

            const text = note.innerText.toLowerCase();

            if (text.includes(keyword)) {

                note.style.display = "";

            } else {

                note.style.display = "none";

            }

        });

    });

};

/*=========================================================
    COPY CODE BUTTON
=========================================================*/

LMS.copyCode = function () {

    const buttons =
        document.querySelectorAll(".copy-btn");

    buttons.forEach(button => {

        button.addEventListener("click", function () {

            const block =
                this.closest(".editor-container");

            if (!block) return;

            const textarea =
                block.querySelector("textarea");

            const code =
                textarea
                    ? textarea.value
                    : block.querySelector("pre code")?.innerText;

            if (!code) return;

            navigator.clipboard.writeText(code);

            const original = this.innerHTML;

            this.innerHTML = "✅ Copied";

            setTimeout(() => {

                this.innerHTML = original;

            }, 2000);

        });

    });

};

/*=========================================================
    DOWNLOAD NOTES
=========================================================*/

LMS.downloadNotes = function () {

    const btn =
        document.querySelector("#downloadNotes");

    if (!btn) return;

    btn.addEventListener("click", () => {

        const content =
            document.querySelector(".notes-content");

        if (!content) return;

        const blob = new Blob(
            [content.innerText],
            { type: "text/plain" }
        );

        const url =
            URL.createObjectURL(blob);

        const a =
            document.createElement("a");

        a.href = url;

        a.download = "course_notes.txt";

        a.click();

        URL.revokeObjectURL(url);

        LMS.showToast(
            "📥 Download",
            "Notes downloaded successfully"
        );

    });

};

/*=========================================================
    BOOKMARK LESSON
=========================================================*/

LMS.bookmarkLesson = function () {

    const buttons =
        document.querySelectorAll(".bookmark-btn");

    buttons.forEach(btn => {

        btn.addEventListener("click", function () {

            this.classList.toggle("active");

            const lesson =
                LMS.currentLesson;

            let bookmarks =
                JSON.parse(
                    localStorage.getItem("bookmarks")
                ) || [];

            if (!bookmarks.includes(lesson)) {

                bookmarks.push(lesson);

            } else {

                bookmarks =
                    bookmarks.filter(id => id !== lesson);

            }

            localStorage.setItem(
                "bookmarks",
                JSON.stringify(bookmarks)
            );

            LMS.showToast(
                "⭐ Bookmark Updated",
                "Lesson saved successfully"
            );

        });

    });

};

/*=========================================================
    LOAD BOOKMARKS
=========================================================*/

LMS.loadBookmarks = function () {

    const bookmarks =
        JSON.parse(
            localStorage.getItem("bookmarks")
        ) || [];

    document
        .querySelectorAll(".lesson-item")
        .forEach((lesson, index) => {

            if (bookmarks.includes(index)) {

                lesson.classList.add("bookmarked");

            }

        });

};

/*=========================================================
    READING TIME
=========================================================*/

LMS.calculateReadingTime = function () {

    const notes =
        document.querySelector(".notes-content");

    const output =
        document.querySelector("#readingTime");

    if (!notes || !output) return;

    const words =
        notes.innerText.trim().split(/\s+/).length;

    const minutes =
        Math.max(1, Math.ceil(words / 200));

    output.innerHTML =
        `${minutes} min read`;

};

/*=========================================================
    FAVORITES
=========================================================*/

LMS.toggleFavorite = function (courseId) {

    let favorites =
        JSON.parse(
            localStorage.getItem("favoriteCourses")
        ) || [];

    if (favorites.includes(courseId)) {

        favorites =
            favorites.filter(id => id !== courseId);

    } else {

        favorites.push(courseId);

    }

    localStorage.setItem(
        "favoriteCourses",
        JSON.stringify(favorites)
    );

};

/*=========================================================
    KEYBOARD SHORTCUTS
=========================================================*/

LMS.keyboardShortcuts = function () {

    document.addEventListener("keydown", e => {

        if (e.target.tagName === "INPUT" ||
            e.target.tagName === "TEXTAREA") {

            return;

        }

        switch (e.key.toLowerCase()) {

            case "arrowright":

                LMS.nextLesson();

                break;

            case "arrowleft":

                LMS.previousLesson();

                break;

            case " ":

                if (LMS.elements.video) {

                    e.preventDefault();

                    if (LMS.elements.video.paused) {

                        LMS.elements.video.play();

                    } else {

                        LMS.elements.video.pause();

                    }

                }

                break;

            case "d":

                document.body.classList.toggle("dark-mode");

                break;

        }

    });

};

/*=========================================================
    INITIALIZE PART 3
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.searchNotes();

    LMS.copyCode();

    LMS.downloadNotes();

    LMS.bookmarkLesson();

    LMS.loadBookmarks();

    LMS.calculateReadingTime();

    LMS.keyboardShortcuts();

});

/*=========================================================
    COURSE LEARNING JS
    PART 4
    Quiz Engine • Timer • Score • Result Modal • Retry
=========================================================*/

"use strict";

/*=========================================================
    QUIZ MODULE
=========================================================*/

LMS.quiz = {

    questions: [],

    current: 0,

    score: 0,

    answers: [],

    timer: null,

    timeLeft: 600 //10 Minutes

};

/*=========================================================
    LOAD QUESTIONS
=========================================================*/

LMS.loadQuiz = function () {

    const items = document.querySelectorAll(".quiz-question-card");

    LMS.quiz.questions = Array.from(items);

    LMS.quiz.current = 0;

    LMS.quiz.score = 0;

    LMS.quiz.answers = [];

    LMS.showQuestion(0);

};

/*=========================================================
    SHOW QUESTION
=========================================================*/

LMS.showQuestion = function (index) {

    const cards = document.querySelectorAll(".quiz-question-card");

    cards.forEach(card => {

        card.style.display = "none";

    });

    if (cards[index]) {

        cards[index].style.display = "block";

    }

    LMS.updateQuestionCounter();

};

/*=========================================================
    QUESTION COUNTER
=========================================================*/

LMS.updateQuestionCounter = function () {

    const counter = document.querySelector("#questionCounter");

    if (!counter) return;

    counter.innerHTML =
        `${LMS.quiz.current + 1} / ${LMS.quiz.questions.length}`;

};

/*=========================================================
    SELECT ANSWER
=========================================================*/

LMS.selectAnswer = function () {

    document.querySelectorAll(".quiz-option").forEach(option => {

        option.addEventListener("click", function () {

            const parent =
                this.closest(".quiz-question-card");

            parent.querySelectorAll(".quiz-option")
                .forEach(item => item.classList.remove("selected"));

            this.classList.add("selected");

            LMS.quiz.answers[LMS.quiz.current] =
                this.dataset.answer;

        });

    });

};

/*=========================================================
    NEXT QUESTION
=========================================================*/

LMS.nextQuestion = function () {

    if (LMS.quiz.current >= LMS.quiz.questions.length - 1) {

        LMS.finishQuiz();

        return;

    }

    LMS.quiz.current++;

    LMS.showQuestion(LMS.quiz.current);

};

/*=========================================================
    PREVIOUS QUESTION
=========================================================*/

LMS.previousQuestion = function () {

    if (LMS.quiz.current <= 0) return;

    LMS.quiz.current--;

    LMS.showQuestion(LMS.quiz.current);

};

/*=========================================================
    QUIZ TIMER
=========================================================*/

LMS.startQuizTimer = function () {

    const timer = document.querySelector("#quizTimer");

    if (!timer) return;

    clearInterval(LMS.quiz.timer);

    LMS.quiz.timer = setInterval(() => {

        LMS.quiz.timeLeft--;

        const min =
            Math.floor(LMS.quiz.timeLeft / 60);

        const sec =
            LMS.quiz.timeLeft % 60;

        timer.innerHTML =
            `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;

        if (LMS.quiz.timeLeft <= 0) {

            clearInterval(LMS.quiz.timer);

            LMS.finishQuiz();

        }

    }, 1000);

};

/*=========================================================
    CALCULATE SCORE
=========================================================*/

LMS.calculateScore = function () {

    LMS.quiz.score = 0;

    document.querySelectorAll(".quiz-question-card")
        .forEach((question, index) => {

            const correct =
                question.dataset.correct;

            if (LMS.quiz.answers[index] === correct) {

                LMS.quiz.score++;

            }

        });

};

/*=========================================================
    FINISH QUIZ
=========================================================*/

LMS.finishQuiz = function () {

    clearInterval(LMS.quiz.timer);

    LMS.calculateScore();

    LMS.saveQuizResult();

    LMS.showQuizResult();

};

/*=========================================================
    RESULT MODAL
=========================================================*/

LMS.showQuizResult = function () {

    const modal = document.querySelector("#quizResultModal");

    if (!modal) return;

    const score = document.querySelector("#quizScore");

    if (score) {

        score.innerHTML =
            `${LMS.quiz.score} / ${LMS.quiz.questions.length}`;

    }

    modal.classList.add("show");

};

/*=========================================================
    CLOSE RESULT
=========================================================*/

LMS.closeQuizResult = function () {

    const modal =
        document.querySelector("#quizResultModal");

    if (!modal) return;

    modal.classList.remove("show");

};

/*=========================================================
    SAVE RESULT
=========================================================*/

LMS.saveQuizResult = function () {

    const history =
        JSON.parse(localStorage.getItem("quizResults")) || [];

    history.push({

        score: LMS.quiz.score,

        total: LMS.quiz.questions.length,

        percentage:
            Math.round(
                (LMS.quiz.score / LMS.quiz.questions.length) * 100
            ),

        date: new Date().toLocaleString()

    });

    localStorage.setItem(

        "quizResults",

        JSON.stringify(history)

    );

};

/*=========================================================
    RETRY QUIZ
=========================================================*/

LMS.retryQuiz = function () {

    clearInterval(LMS.quiz.timer);

    LMS.quiz.current = 0;

    LMS.quiz.score = 0;

    LMS.quiz.answers = [];

    LMS.quiz.timeLeft = 600;

    document.querySelectorAll(".quiz-option")
        .forEach(option => {

            option.classList.remove(

                "selected",
                "correct",
                "wrong"

            );

        });

    LMS.closeQuizResult();

    LMS.showQuestion(0);

    LMS.startQuizTimer();

};

/*=========================================================
    QUIZ BUTTON EVENTS
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.loadQuiz();

    LMS.selectAnswer();

    LMS.startQuizTimer();

    document.querySelector("#nextQuestion")
        ?.addEventListener("click", LMS.nextQuestion);

    document.querySelector("#previousQuestion")
        ?.addEventListener("click", LMS.previousQuestion);

    document.querySelector("#retryQuiz")
        ?.addEventListener("click", LMS.retryQuiz);

});

/*=========================================================
    COURSE LEARNING JS
    PART 5
    XP • Levels • Streak • Achievements • Daily Goals
=========================================================*/

"use strict";

/*=========================================================
    GAMIFICATION DATA
=========================================================*/

LMS.gamification = {

    xp: Number(localStorage.getItem("course_xp")) || 0,

    level: Number(localStorage.getItem("course_level")) || 1,

    streak: Number(localStorage.getItem("course_streak")) || 0,

    lastVisit: localStorage.getItem("course_last_visit") || "",

    achievements:
        JSON.parse(localStorage.getItem("course_achievements")) || []

};

/*=========================================================
    ADD XP
=========================================================*/

LMS.addXP = function (amount) {

    this.gamification.xp += amount;

    localStorage.setItem(
        "course_xp",
        this.gamification.xp
    );

    this.updateXP();

    this.checkLevelUp();

};

/*=========================================================
    UPDATE XP UI
=========================================================*/

LMS.updateXP = function () {

    const value = document.querySelector("#xpValue");

    const bar = document.querySelector("#xpBar");

    if (value) {

        value.textContent = this.gamification.xp;

    }

    if (bar) {

        const progress =
            this.gamification.xp % 100;

        bar.style.width = progress + "%";

    }

};

/*=========================================================
    LEVEL SYSTEM
=========================================================*/

LMS.checkLevelUp = function () {

    const required =
        this.gamification.level * 100;

    if (this.gamification.xp >= required) {

        this.gamification.level++;

        localStorage.setItem(
            "course_level",
            this.gamification.level
        );

        this.showToast(
            "🎉 Level Up!",
            `You reached Level ${this.gamification.level}`
        );

        this.updateLevel();

    }

};

/*=========================================================
    UPDATE LEVEL
=========================================================*/

LMS.updateLevel = function () {

    const element =
        document.querySelector("#userLevel");

    if (element) {

        element.textContent =
            this.gamification.level;

    }

};

/*=========================================================
    DAILY STREAK
=========================================================*/

LMS.updateStreak = function () {

    const today =
        new Date().toDateString();

    if (this.gamification.lastVisit === today) {

        return;

    }

    const yesterday =
        new Date();

    yesterday.setDate(yesterday.getDate() - 1);

    if (
        this.gamification.lastVisit ===
        yesterday.toDateString()
    ) {

        this.gamification.streak++;

    } else {

        this.gamification.streak = 1;

    }

    this.gamification.lastVisit = today;

    localStorage.setItem(
        "course_last_visit",
        today
    );

    localStorage.setItem(
        "course_streak",
        this.gamification.streak
    );

    const streak =
        document.querySelector("#streakValue");

    if (streak) {

        streak.textContent =
            this.gamification.streak;

    }

};

/*=========================================================
    ACHIEVEMENTS
=========================================================*/

LMS.unlockAchievement = function (title) {

    if (
        this.gamification.achievements.includes(title)
    ) {

        return;

    }

    this.gamification.achievements.push(title);

    localStorage.setItem(
        "course_achievements",
        JSON.stringify(
            this.gamification.achievements
        )
    );

    this.showToast(
        "🏆 Achievement Unlocked",
        title
    );

};

/*=========================================================
    CHECK ACHIEVEMENTS
=========================================================*/

LMS.checkAchievements = function () {

    if (this.progress >= 25) {

        this.unlockAchievement(
            "Completed 25% Course"
        );

    }

    if (this.progress >= 50) {

        this.unlockAchievement(
            "Halfway Hero"
        );

    }

    if (this.progress >= 100) {

        this.unlockAchievement(
            "Course Master"
        );

    }

    if (this.gamification.streak >= 7) {

        this.unlockAchievement(
            "7 Day Streak"
        );

    }

};

/*=========================================================
    DAILY GOALS
=========================================================*/

LMS.completeGoal = function (goalId) {

    const goal =
        document.querySelector(
            `[data-goal="${goalId}"]`
        );

    if (!goal) return;

    goal.classList.add("completed");

    this.addXP(20);

    this.showToast(
        "🎯 Goal Completed",
        "You earned 20 XP"
    );

};

/*=========================================================
    COURSE COMPLETION BONUS
=========================================================*/

LMS.rewardCompletion = function () {

    if (this.progress < 100) return;

    this.addXP(100);

    this.unlockAchievement(
        "Completed Entire Course"
    );

};

/*=========================================================
    STUDY TIME
=========================================================*/

LMS.trackStudyTime = function () {

    let minutes =
        Number(
            localStorage.getItem("study_minutes")
        ) || 0;

    setInterval(() => {

        minutes++;

        localStorage.setItem(
            "study_minutes",
            minutes
        );

        const time =
            document.querySelector("#studyTime");

        if (time) {

            time.textContent =
                minutes + " min";

        }

    }, 60000);

};

/*=========================================================
    ANALYTICS
=========================================================*/

LMS.updateAnalytics = function () {

    const lessons =
        document.querySelector("#completedLessons");

    if (lessons) {

        lessons.textContent =
            this.currentLesson + 1;

    }

    const progress =
        document.querySelector("#analyticsProgress");

    if (progress) {

        progress.textContent =
            Math.round(this.progress) + "%";

    }

};

/*=========================================================
    INITIALIZE
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.updateXP();

    LMS.updateLevel();

    LMS.updateStreak();

    LMS.trackStudyTime();

    LMS.updateAnalytics();

    LMS.checkAchievements();

});

/*=========================================================
    COURSE LEARNING JS
    PART 6
    Dark Mode • Toast Queue • Scroll Effects • Settings
=========================================================*/

"use strict";

/*=========================================================
    SETTINGS
=========================================================*/

LMS.settings = {

    darkMode:
        localStorage.getItem("setting_dark") === "true",

    animation:
        localStorage.getItem("setting_animation") !== "false",

    sound:
        localStorage.getItem("setting_sound") === "true"

};

/*=========================================================
    APPLY SETTINGS
=========================================================*/

LMS.applySettings = function () {

    document.body.classList.toggle(
        "dark-mode",
        this.settings.darkMode
    );

    if (!this.settings.animation) {

        document.body.classList.add("reduce-motion");

    }

};

/*=========================================================
    TOGGLE DARK MODE
=========================================================*/

LMS.toggleDarkMode = function () {

    this.settings.darkMode = !this.settings.darkMode;

    localStorage.setItem(
        "setting_dark",
        this.settings.darkMode
    );

    this.applySettings();

    this.showToast(
        "🌙 Theme Updated",
        this.settings.darkMode
            ? "Dark Mode Enabled"
            : "Light Mode Enabled"
    );

};

/*=========================================================
    TOAST QUEUE
=========================================================*/

LMS.toastQueue = [];

LMS.showToastQueue = function (title, message) {

    this.toastQueue.push({ title, message });

    if (this.toastQueue.length === 1) {

        this.processToastQueue();

    }

};

LMS.processToastQueue = function () {

    if (this.toastQueue.length === 0) return;

    const toast =
        this.toastQueue[0];

    this.showToast(
        toast.title,
        toast.message
    );

    setTimeout(() => {

        this.toastQueue.shift();

        this.processToastQueue();

    }, 3200);

};

/*=========================================================
    SCROLL REVEAL
=========================================================*/

LMS.revealOnScroll = function () {

    const items =
        document.querySelectorAll(".reveal");

    const trigger =
        window.innerHeight * 0.9;

    items.forEach(item => {

        const top =
            item.getBoundingClientRect().top;

        if (top < trigger) {

            item.classList.add("active");

        }

    });

};

/*=========================================================
    SCROLL TO TOP
=========================================================*/

LMS.scrollToTop = function () {

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

};

LMS.initScrollButton = function () {

    const btn =
        document.querySelector(".scroll-top");

    if (!btn) return;

    window.addEventListener("scroll", () => {

        btn.style.display =
            window.scrollY > 250
                ? "flex"
                : "none";

    });

    btn.addEventListener("click", () => {

        this.scrollToTop();

    });

};

/*=========================================================
    HELP BUTTON
=========================================================*/

LMS.initHelpButton = function () {

    const btn =
        document.querySelector(".help-button");

    if (!btn) return;

    btn.addEventListener("click", () => {

        this.showToast(
            "💡 Help",
            "Need assistance? Contact your instructor."
        );

    });

};

/*=========================================================
    SOUND
=========================================================*/

LMS.playSound = function (type = "success") {

    if (!this.settings.sound) return;

    const audio =
        new Audio();

    switch (type) {

        case "success":

            audio.src = "/static/audio/success.mp3";

            break;

        case "error":

            audio.src = "/static/audio/error.mp3";

            break;

        default:

            audio.src = "/static/audio/click.mp3";

    }

    audio.play().catch(() => {});

};

/*=========================================================
    USER PREFERENCES
=========================================================*/

LMS.savePreference = function (key, value) {

    localStorage.setItem(

        `pref_${key}`,

        JSON.stringify(value)

    );

};

LMS.getPreference = function (key, fallback = null) {

    const value =
        localStorage.getItem(`pref_${key}`);

    if (!value) return fallback;

    return JSON.parse(value);

};

/*=========================================================
    PAGE VISIT COUNTER
=========================================================*/

LMS.updateVisitCounter = function () {

    let visits =
        Number(localStorage.getItem("page_visits")) || 0;

    visits++;

    localStorage.setItem(
        "page_visits",
        visits
    );

    const element =
        document.querySelector("#visitCount");

    if (element) {

        element.textContent = visits;

    }

};

/*=========================================================
    ONLINE STATUS
=========================================================*/

LMS.updateConnectionStatus = function () {

    const status =
        document.querySelector("#connectionStatus");

    if (!status) return;

    const update = () => {

        if (navigator.onLine) {

            status.textContent = "🟢 Online";

            status.classList.remove("offline");

        } else {

            status.textContent = "🔴 Offline";

            status.classList.add("offline");

        }

    };

    update();

    window.addEventListener("online", update);

    window.addEventListener("offline", update);

};

/*=========================================================
    WINDOW EVENTS
=========================================================*/

window.addEventListener("scroll", () => {

    LMS.revealOnScroll();

});

window.addEventListener("resize", () => {

    LMS.revealOnScroll();

});

/*=========================================================
    INITIALIZE
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.applySettings();

    LMS.initScrollButton();

    LMS.initHelpButton();

    LMS.updateVisitCounter();

    LMS.updateConnectionStatus();

    LMS.revealOnScroll();

    document
        .querySelector("#themeToggle")
        ?.addEventListener("click", () => {

            LMS.toggleDarkMode();

        });

});

/*=========================================================
    COURSE LEARNING JS
    PART 7
    Calendar • Pomodoro • Study Planner • Session Tracker
=========================================================*/

"use strict";

/*=========================================================
    PRODUCTIVITY MODULE
=========================================================*/

LMS.productivity = {

    pomodoro: {

        minutes: 25,

        seconds: 0,

        timer: null,

        running: false

    },

    sessionStart: null,

    totalStudySeconds:
        Number(localStorage.getItem("totalStudySeconds")) || 0

};

/*=========================================================
    START STUDY SESSION
=========================================================*/

LMS.startStudySession = function () {

    this.productivity.sessionStart = Date.now();

    this.showToast(
        "📚 Study Session",
        "Session Started Successfully"
    );

};

/*=========================================================
    END STUDY SESSION
=========================================================*/

LMS.endStudySession = function () {

    if (!this.productivity.sessionStart) return;

    const elapsed = Math.floor(

        (Date.now() - this.productivity.sessionStart) / 1000

    );

    this.productivity.totalStudySeconds += elapsed;

    localStorage.setItem(

        "totalStudySeconds",

        this.productivity.totalStudySeconds

    );

    this.productivity.sessionStart = null;

    this.updateStudyStatistics();

};

/*=========================================================
    STUDY STATISTICS
=========================================================*/

LMS.updateStudyStatistics = function () {

    const hours = Math.floor(

        this.productivity.totalStudySeconds / 3600

    );

    const minutes = Math.floor(

        (this.productivity.totalStudySeconds % 3600) / 60

    );

    const stat = document.querySelector("#studyStatistics");

    if (stat) {

        stat.textContent =
            `${hours}h ${minutes}m`;

    }

};

/*=========================================================
    POMODORO TIMER
=========================================================*/

LMS.updatePomodoroUI = function () {

    const display =
        document.querySelector("#pomodoroTime");

    if (!display) return;

    display.textContent =
        `${String(this.productivity.pomodoro.minutes).padStart(2,"0")}:${String(this.productivity.pomodoro.seconds).padStart(2,"0")}`;

};

LMS.startPomodoro = function () {

    if (this.productivity.pomodoro.running) return;

    this.productivity.pomodoro.running = true;

    this.productivity.pomodoro.timer = setInterval(() => {

        if (this.productivity.pomodoro.seconds === 0) {

            if (this.productivity.pomodoro.minutes === 0) {

                clearInterval(this.productivity.pomodoro.timer);

                this.productivity.pomodoro.running = false;

                this.showToast(

                    "⏰ Time's Up!",

                    "Take a short break."

                );

                this.playSound("success");

                return;

            }

            this.productivity.pomodoro.minutes--;

            this.productivity.pomodoro.seconds = 59;

        } else {

            this.productivity.pomodoro.seconds--;

        }

        this.updatePomodoroUI();

    }, 1000);

};

LMS.pausePomodoro = function () {

    clearInterval(this.productivity.pomodoro.timer);

    this.productivity.pomodoro.running = false;

};

LMS.resetPomodoro = function () {

    this.pausePomodoro();

    this.productivity.pomodoro.minutes = 25;

    this.productivity.pomodoro.seconds = 0;

    this.updatePomodoroUI();

};

/*=========================================================
    STUDY GOALS
=========================================================*/

LMS.completeStudyGoal = function (goalName) {

    this.addXP(25);

    this.showToast(

        "🎯 Goal Completed",

        goalName

    );

};

/*=========================================================
    CALENDAR
=========================================================*/

LMS.renderCalendar = function () {

    const container =
        document.querySelector("#calendarDays");

    if (!container) return;

    container.innerHTML = "";

    const now = new Date();

    const year = now.getFullYear();

    const month = now.getMonth();

    const totalDays =
        new Date(year, month + 1, 0).getDate();

    for (let day = 1; day <= totalDays; day++) {

        const box =
            document.createElement("div");

        box.className = "calendar-day";

        box.textContent = day;

        if (day === now.getDate()) {

            box.classList.add("today");

        }

        container.appendChild(box);

    }

};

/*=========================================================
    SESSION TIMER
=========================================================*/

LMS.startSessionClock = function () {

    const element =
        document.querySelector("#sessionTimer");

    if (!element) return;

    let seconds = 0;

    setInterval(() => {

        seconds++;

        const h = Math.floor(seconds / 3600);

        const m = Math.floor((seconds % 3600) / 60);

        const s = seconds % 60;

        element.textContent =
            `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;

    }, 1000);

};

/*=========================================================
    EVENTS
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.renderCalendar();

    LMS.updatePomodoroUI();

    LMS.updateStudyStatistics();

    LMS.startSessionClock();

    document.querySelector("#startPomodoro")
        ?.addEventListener("click", () => {

            LMS.startPomodoro();

        });

    document.querySelector("#pausePomodoro")
        ?.addEventListener("click", () => {

            LMS.pausePomodoro();

        });

    document.querySelector("#resetPomodoro")
        ?.addEventListener("click", () => {

            LMS.resetPomodoro();

        });

    document.querySelector("#startSession")
        ?.addEventListener("click", () => {

            LMS.startStudySession();

        });

    document.querySelector("#endSession")
        ?.addEventListener("click", () => {

            LMS.endStudySession();

        });

});

/*=========================================================
    COURSE LEARNING JS
    PART 8 (FINAL)
    Certificate • API Hooks • Confetti • Final Initialization
=========================================================*/

"use strict";

/*=========================================================
    CERTIFICATE MODULE
=========================================================*/

LMS.certificate = {

    unlocked: false,

    downloadEnabled: true

};

/*=========================================================
    CHECK CERTIFICATE
=========================================================*/

LMS.checkCertificateEligibility = function () {

    if (this.progress < 100) return false;

    this.certificate.unlocked = true;

    const btn = document.querySelector("#downloadCertificate");

    if (btn) {

        btn.disabled = false;

        btn.classList.remove("disabled");

    }

    return true;

};

/*=========================================================
    GENERATE CERTIFICATE
=========================================================*/

LMS.generateCertificate = function () {

    if (!this.checkCertificateEligibility()) {

        this.showToast(
            "Course Incomplete",
            "Complete 100% of the course first."
        );

        return;
    }

    const name =
        document.querySelector("#studentName")?.value ||
        "Student";

    document.querySelectorAll(".certificate-name")
        .forEach(item => {

            item.textContent = name;

        });

    this.showToast(
        "Certificate Ready",
        "You can now download it."
    );

};

/*=========================================================
    DOWNLOAD CERTIFICATE
=========================================================*/

LMS.downloadCertificate = function () {

    window.print();

};

/*=========================================================
    SHARE CERTIFICATE
=========================================================*/

LMS.shareCertificate = async function () {

    if (!navigator.share) {

        this.showToast(
            "Share Not Supported",
            "Your browser doesn't support sharing."
        );

        return;
    }

    try {

        await navigator.share({

            title: "Course Certificate",

            text: "I completed my course successfully!",

            url: location.href

        });

    } catch (err) {

        console.log(err);

    }

};

/*=========================================================
    CONFETTI
=========================================================*/

LMS.launchConfetti = function () {

    for (let i = 0; i < 120; i++) {

        const confetti =
            document.createElement("div");

        confetti.className = "confetti";

        confetti.style.left =
            Math.random() * 100 + "%";

        confetti.style.background =
            `hsl(${Math.random() * 360},80%,60%)`;

        confetti.style.animationDuration =
            (Math.random() * 3 + 2) + "s";

        document.body.appendChild(confetti);

        setTimeout(() => {

            confetti.remove();

        }, 5000);

    }

};

/*=========================================================
    EXPORT USER DATA
=========================================================*/

LMS.exportProgress = function () {

    const data = {

        lesson: this.currentLesson,

        progress: this.progress,

        xp: this.gamification.xp,

        level: this.gamification.level,

        streak: this.gamification.streak,

        achievements: this.gamification.achievements,

        studyTime: this.productivity.totalStudySeconds

    };

    const blob = new Blob(

        [JSON.stringify(data, null, 2)],

        { type: "application/json" }

    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;

    link.download = "course_progress.json";

    link.click();

    URL.revokeObjectURL(url);

};

/*=========================================================
    API READY (Flask Integration)
=========================================================*/

LMS.syncProgress = async function () {

    try {

        await fetch("/api/course/progress", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                lesson: this.currentLesson,

                progress: this.progress,

                xp: this.gamification.xp,

                level: this.gamification.level,

                streak: this.gamification.streak

            })

        });

    } catch (err) {

        console.log("Sync Failed:", err);

    }

};

/*=========================================================
    LOAD SERVER DATA
=========================================================*/

LMS.loadServerProgress = async function () {

    try {

        const response =

            await fetch("/api/course/progress");

        if (!response.ok) return;

        const data = await response.json();

        this.currentLesson = data.lesson || 0;

        this.progress = data.progress || 0;

        this.updateProgress();

    } catch (err) {

        console.log(err);

    }

};

/*=========================================================
    AUTO SAVE
=========================================================*/

setInterval(() => {

    LMS.saveProgress();

    LMS.syncProgress();

}, 30000);

/*=========================================================
    BEFORE EXIT
=========================================================*/

window.addEventListener("beforeunload", () => {

    LMS.saveProgress();

});

/*=========================================================
    FINAL INITIALIZATION
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    LMS.loadServerProgress();

    document.querySelector("#downloadCertificate")
        ?.addEventListener("click", () => {

            LMS.generateCertificate();

            LMS.launchConfetti();

            LMS.downloadCertificate();

        });

    document.querySelector("#shareCertificate")
        ?.addEventListener("click", () => {

            LMS.shareCertificate();

        });

    document.querySelector("#exportProgress")
        ?.addEventListener("click", () => {

            LMS.exportProgress();

        });

    console.log(
        "%cCourse Learning System Loaded Successfully",
        "color:#2563eb;font-size:16px;font-weight:bold;"
    );

});

/*=========================================================
    END OF course_learning.js
=========================================================*/
