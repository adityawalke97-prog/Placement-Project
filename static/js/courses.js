// ========================================
// SEARCH COURSE
// ========================================

const searchInput = document.getElementById("searchCourse");
const levelFilter = document.getElementById("levelFilter");
const cards = document.querySelectorAll(".course-card");

function filterCourses() {

    const search = searchInput.value.toLowerCase();
    const level = levelFilter.value.toLowerCase();

    cards.forEach(card => {

        const title = card.querySelector("h2").innerText.toLowerCase();

        const courseLevel =
            card.dataset.level.toLowerCase();

        const searchMatch =
            title.includes(search);

        const levelMatch =
            level === "all" ||
            courseLevel.includes(level);

        if (searchMatch && levelMatch) {

            card.style.display = "block";

        } else {

            card.style.display = "none";

        }

    });

}

searchInput.addEventListener(
    "keyup",
    filterCourses
);

levelFilter.addEventListener(
    "change",
    filterCourses
);


// ========================================
// PROGRESS ANIMATION
// ========================================

const progressBars =
document.querySelectorAll(".progress-fill");

window.addEventListener("load",()=>{

    progressBars.forEach(bar=>{

        const width =
        bar.style.width;

        bar.style.width="0";

        setTimeout(()=>{

            bar.style.width=width;

        },300);

    });

});


// ========================================
// CARD ANIMATION
// ========================================

const observer =
new IntersectionObserver(entries=>{

    entries.forEach(entry=>{

        if(entry.isIntersecting){

            entry.target.style.opacity="1";

            entry.target.style.transform=
            "translateY(0px)";

        }

    });

});

cards.forEach(card=>{

    card.style.opacity="0";

    card.style.transform=
    "translateY(40px)";

    card.style.transition=
    ".5s ease";

    observer.observe(card);

});


// ========================================
// BUTTON RIPPLE EFFECT
// ========================================

document.querySelectorAll(".start-btn")
.forEach(btn=>{

btn.addEventListener("click",function(e){

const circle=
document.createElement("span");

circle.style.position="absolute";
circle.style.borderRadius="50%";
circle.style.background=
"rgba(255,255,255,.4)";
circle.style.width="15px";
circle.style.height="15px";

circle.style.left=
e.offsetX+"px";

circle.style.top=
e.offsetY+"px";

circle.style.animation=
"ripple .7s linear";

this.appendChild(circle);

setTimeout(()=>{

circle.remove();

},700);

});

});


// ========================================
// COUNTER ANIMATION
// ========================================

document.querySelectorAll(".stat-card h2")
.forEach(counter=>{

let target=
counter.innerText.replace(/\D/g,'');

if(target==="") return;

let count=0;

const update=()=>{

count+=Math.ceil(target/40);

if(count>=target){

counter.innerText=
counter.innerText
.replace(/\d+/,target);

return;

}

counter.innerText=
counter.innerText
.replace(/\d+/,count);

requestAnimationFrame(update);

}

update();

});
