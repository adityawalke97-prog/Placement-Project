/* ==========================================
   MOCK TEST HISTORY JS
   PART A3.1
   Search + Sorting + Print
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    initializeSearch();

    initializeSorting();

    initializePrint();

});


/* ==========================================
   SEARCH
========================================== */

function initializeSearch() {

    const input = document.getElementById("searchInput");

    if (!input) return;

    input.addEventListener("keyup", function () {

        const filter = this.value.toLowerCase();

        const rows = document.querySelectorAll("#historyTable tbody tr");

        rows.forEach(row => {

            const text = row.innerText.toLowerCase();

            row.style.display = text.includes(filter)
                ? ""
                : "none";

        });

    });

}


/* ==========================================
   SORTING
========================================== */

function initializeSorting() {

    const select = document.getElementById("sortSelect");

    if (!select) return;

    select.addEventListener("change", function () {

        sortTable(this.value);

    });

}


function sortTable(type) {

    const tbody = document.querySelector("#historyTable tbody");

    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll("tr"));

    if (rows.length === 0) return;

    rows.sort((a, b) => {

        if (type === "highest") {

            return getScore(b) - getScore(a);

        }

        if (type === "lowest") {

            return getScore(a) - getScore(b);

        }

        if (type === "percentage") {

            return getPercentage(b) - getPercentage(a);

        }

        if (type === "latest") {

            return getDate(b) - getDate(a);

        }

        return 0;

    });

    rows.forEach(row => tbody.appendChild(row));

}


/* ==========================================
   HELPERS
========================================== */

function getScore(row) {

    const txt = row.cells[2].innerText;

    return parseInt(txt.split("/")[0]);

}

function getPercentage(row) {

    return parseFloat(

        row.cells[3]

        .innerText

        .replace("%", "")

    );

}

function getDate(row) {

    return new Date(

        row.cells[5].innerText

    );

}


/* ==========================================
   PRINT
========================================== */

function initializePrint() {

    const btn = document.getElementById("printHistory");

    if (!btn) return;

    btn.addEventListener("click", () => {

        window.print();

    });

}

/* ==========================================
   MOCK TEST HISTORY JS
   PART A3.2
   Pagination + CSV Export + Statistics
========================================== */

const rowsPerPage = 10;

let currentPage = 1;

let allRows = [];


/* ==========================================
   INITIALIZE
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    const tbody = document.querySelector("#historyTable tbody");

    if(!tbody) return;

    allRows = Array.from(tbody.querySelectorAll("tr"));

    createPagination();

    showPage(1);

    updateStatistics();

    initializeCSVExport();

});


/* ==========================================
   PAGINATION
========================================== */

function showPage(page){

    currentPage = page;

    const start = (page-1)*rowsPerPage;

    const end = start + rowsPerPage;

    allRows.forEach((row,index)=>{

        row.style.display =
            index>=start && index<end
            ? ""
            : "none";

    });

    updatePaginationButtons();

}


function createPagination(){

    const totalPages = Math.ceil(allRows.length/rowsPerPage);

    if(totalPages<=1) return;

    let pagination=document.querySelector(".pagination");

    if(!pagination){

        pagination=document.createElement("div");

        pagination.className="pagination";

        document.querySelector(".history-table-card")
            .after(pagination);

    }

    pagination.innerHTML="";

    for(let i=1;i<=totalPages;i++){

        const btn=document.createElement("button");

        btn.innerHTML=i;

        btn.onclick=()=>showPage(i);

        pagination.appendChild(btn);

    }

}


function updatePaginationButtons(){

    const buttons=document.querySelectorAll(".pagination button");

    buttons.forEach((btn,index)=>{

        btn.classList.remove("active");

        if(index+1===currentPage){

            btn.classList.add("active");

        }

    });

}


/* ==========================================
   CSV EXPORT
========================================== */

function initializeCSVExport(){

    const btn=document.getElementById("exportCSV");

    if(!btn) return;

    btn.addEventListener("click",exportCSV);

}


function exportCSV(){

    let csv=[];

    const rows=document.querySelectorAll("#historyTable tr");

    rows.forEach(row=>{

        const cols=row.querySelectorAll("th,td");

        const data=[];

        cols.forEach(col=>{

            data.push(
                '"' +
                col.innerText.replace(/"/g,'""')
                + '"'
            );

        });

        csv.push(data.join(","));

    });

    const csvFile=new Blob(
        [csv.join("\n")],
        {type:"text/csv"}
    );

    const download=document.createElement("a");

    download.download="mock_test_history.csv";

    download.href=
        window.URL.createObjectURL(csvFile);

    download.style.display="none";

    document.body.appendChild(download);

    download.click();

    document.body.removeChild(download);

}


/* ==========================================
   UPDATE STATISTICS
========================================== */

function updateStatistics(){

    const rows=document.querySelectorAll("#historyTable tbody tr");

    let total=0;

    let passed=0;

    let failed=0;

    let totalPercentage=0;

    rows.forEach(row=>{

        if(row.classList.contains("no-data"))
            return;

        total++;

        const percentage=parseFloat(
            row.cells[3].innerText
                .replace("%","")
        );

        totalPercentage+=percentage;

        if(percentage>=40){

            passed++;

        }else{

            failed++;

        }

    });

    console.log({
        total,
        passed,
        failed,
        average:
            total
            ? (totalPercentage/total).toFixed(2)
            : 0
    });

}


/* ==========================================
   ROW HOVER EFFECT
========================================== */

document.addEventListener("mouseover",(e)=>{

    const row=e.target.closest("tbody tr");

    if(!row) return;

    row.style.transition=".3s";

    row.style.transform="scale(1.01)";

});


document.addEventListener("mouseout",(e)=>{

    const row=e.target.closest("tbody tr");

    if(!row) return;

    row.style.transform="scale(1)";

});

/* ==========================================
   MOCK TEST HISTORY JS
   PART A3.3.1
   Toast Notification + Delete Confirmation
========================================== */


/* ===========================
   TOAST NOTIFICATION
=========================== */

function showToast(message, type = "success") {

    let toast = document.createElement("div");

    toast.className = "toast-message " + type;

    toast.innerHTML = `
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("show");
    }, 100);

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => {

            toast.remove();

        }, 300);

    }, 3000);

}



/* ===========================
   BUTTON EVENTS
=========================== */

document.addEventListener("DOMContentLoaded", () => {

    showSuccessMessage();

    initializeDeleteButtons();

});



/* ===========================
   SUCCESS MESSAGE
=========================== */

function showSuccessMessage(){

    const table=document.getElementById("historyTable");

    if(table){

        showToast("History Loaded Successfully");

    }

}



/* ===========================
   DELETE BUTTON
=========================== */

function initializeDeleteButtons(){

    const buttons=document.querySelectorAll(".btn-delete");

    buttons.forEach(button=>{

        button.addEventListener("click",function(e){

            e.preventDefault();

            const url=this.getAttribute("href");

            confirmDelete(url);

        });

    });

}



/* ===========================
   DELETE CONFIRMATION
=========================== */

function confirmDelete(url){

    const confirmBox=document.createElement("div");

    confirmBox.className="delete-overlay";

    confirmBox.innerHTML=`

    <div class="delete-modal">

        <h2>🗑 Delete History</h2>

        <p>

            Are you sure you want to delete this history?

        </p>

        <div class="delete-buttons">

            <button class="cancel-btn">

                Cancel

            </button>

            <button class="delete-btn">

                Delete

            </button>

        </div>

    </div>

    `;

    document.body.appendChild(confirmBox);



    confirmBox.querySelector(".cancel-btn")

    .onclick=()=>{

        confirmBox.remove();

    };



    confirmBox.querySelector(".delete-btn")

    .onclick=()=>{

        showToast("History Deleted","success");

        window.location.href=url;

    };

}



/* ===========================
   ESC CLOSE
=========================== */

document.addEventListener("keydown",(e)=>{

    if(e.key==="Escape"){

        const overlay=document.querySelector(".delete-overlay");

        if(overlay){

            overlay.remove();

        }

    }

});
/* ==========================================
   MOCK TEST HISTORY JS
   PART A3.3.2a
   Loading Overlay + Refresh + Animations
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    initializeLoading();

    initializeRefreshButton();

    animateCards();

});


/* ==========================================
   LOADING OVERLAY
========================================== */

function initializeLoading(){

    const loader=document.createElement("div");

    loader.id="pageLoader";

    loader.innerHTML=`
        <div class="loader-box">
            <div class="loader-circle"></div>
            <p>Loading History...</p>
        </div>
    `;

    document.body.appendChild(loader);

    setTimeout(()=>{

        loader.classList.add("hide");

        setTimeout(()=>{

            loader.remove();

        },500);

    },900);

}


/* ==========================================
   REFRESH BUTTON
========================================== */

function initializeRefreshButton(){

    const btn=document.getElementById("refreshHistory");

    if(!btn) return;

    btn.addEventListener("click",()=>{

        showLoading();

        setTimeout(()=>{

            location.reload();

        },800);

    });

}


/* ==========================================
   SHOW LOADER
========================================== */

function showLoading(){

    const loader=document.createElement("div");

    loader.className="loading-overlay";

    loader.innerHTML=`
        <div class="loader-box">
            <div class="loader-circle"></div>
            <p>Please wait...</p>
        </div>
    `;

    document.body.appendChild(loader);

}


/* ==========================================
   CARD ANIMATION
========================================== */

function animateCards(){

    const cards=document.querySelectorAll(".stat-card");

    cards.forEach((card,index)=>{

        card.style.opacity="0";

        card.style.transform="translateY(40px)";

        setTimeout(()=>{

            card.style.transition=".6s ease";

            card.style.opacity="1";

            card.style.transform="translateY(0)";

        },index*120);

    });

}


/* ==========================================
   TABLE ANIMATION
========================================== */

window.addEventListener("load",()=>{

    const rows=document.querySelectorAll("#historyTable tbody tr");

    rows.forEach((row,index)=>{

        row.style.opacity="0";

        row.style.transform="translateX(-20px)";

        setTimeout(()=>{

            row.style.transition=".4s ease";

            row.style.opacity="1";

            row.style.transform="translateX(0)";

        },index*40);

    });

});


/* ==========================================
   SCROLL TO TOP
========================================== */

const scrollButton=document.createElement("button");

scrollButton.innerHTML="⬆";

scrollButton.id="scrollTopBtn";

document.body.appendChild(scrollButton);

window.addEventListener("scroll",()=>{

    if(window.scrollY>250){

        scrollButton.style.display="flex";

    }else{

        scrollButton.style.display="none";

    }

});

scrollButton.onclick=()=>{

    window.scrollTo({

        top:0,

        behavior:"smooth"

    });

};
/* ==========================================
   MOCK TEST HISTORY JS
   PART A3.3.2b
   Keyboard Shortcuts + Utilities
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    initializeKeyboardShortcuts();

    initializeTooltips();

    focusSearchBox();

});


/* ==========================================
   KEYBOARD SHORTCUTS
========================================== */

function initializeKeyboardShortcuts(){

    document.addEventListener("keydown",(e)=>{

        // Ignore shortcuts while typing
        const tag=document.activeElement.tagName;

        if(tag==="INPUT" || tag==="TEXTAREA")
            return;

        switch(e.key.toLowerCase()){

            case "/":

                e.preventDefault();

                document.getElementById("searchInput")?.focus();

                break;

            case "p":

                e.preventDefault();

                document.getElementById("printHistory")?.click();

                break;

            case "e":

                e.preventDefault();

                document.getElementById("exportCSV")?.click();

                break;

            case "r":

                e.preventDefault();

                document.getElementById("refreshHistory")?.click();

                break;

            case "home":

                window.scrollTo({
                    top:0,
                    behavior:"smooth"
                });

                break;

            case "end":

                window.scrollTo({
                    top:document.body.scrollHeight,
                    behavior:"smooth"
                });

                break;

        }

    });

}


/* ==========================================
   AUTO FOCUS
========================================== */

function focusSearchBox(){

    const input=document.getElementById("searchInput");

    if(!input) return;

    setTimeout(()=>{

        input.focus();

    },500);

}


/* ==========================================
   TOOLTIP
========================================== */

function initializeTooltips(){

    document.querySelectorAll("[title]").forEach(item=>{

        item.addEventListener("mouseenter",()=>{

            item.style.cursor="pointer";

        });

    });

}


/* ==========================================
   COPY TEXT
========================================== */

function copyText(text){

    navigator.clipboard.writeText(text);

    if(typeof showToast==="function"){

        showToast("Copied Successfully");

    }

}


/* ==========================================
   DOWNLOAD FILE
========================================== */

function downloadFile(filename,content,type){

    const blob=new Blob([content],{type:type});

    const a=document.createElement("a");

    a.href=URL.createObjectURL(blob);

    a.download=filename;

    a.click();

}


/* ==========================================
   FORMAT DATE
========================================== */

function formatDate(date){

    const d=new Date(date);

    return d.toLocaleDateString("en-IN",{

        day:"2-digit",

        month:"short",

        year:"numeric"

    });

}


/* ==========================================
   LOADING BUTTON
========================================== */

function buttonLoading(button,text="Loading..."){

    if(!button) return;

    button.dataset.original=button.innerHTML;

    button.disabled=true;

    button.innerHTML=`
        ⏳ ${text}
    `;

}


function resetButton(button){

    if(!button) return;

    button.disabled=false;

    button.innerHTML=button.dataset.original;

}


/* ==========================================
   SMOOTH FADE
========================================== */

function fadeIn(element){

    element.style.opacity=0;

    element.style.display="block";

    let opacity=0;

    const timer=setInterval(()=>{

        opacity+=0.1;

        element.style.opacity=opacity;

        if(opacity>=1){

            clearInterval(timer);

        }

    },30);

}


/* ==========================================
   ELEMENT SHOW/HIDE
========================================== */

function hideElement(id){

    const el=document.getElementById(id);

    if(el){

        el.style.display="none";

    }

}


function showElement(id){

    const el=document.getElementById(id);

    if(el){

        el.style.display="block";

    }

}


/* ==========================================
   PAGE READY
========================================== */

window.addEventListener("load",()=>{

    console.log("✅ Mock Test History Loaded");

    if(typeof showToast==="function"){

        showToast("Welcome Back!");

    }

});
