// ===============================
// Show / Hide Password
// ===============================

function togglePassword() {

    const password = document.getElementById("password");
    const icon = document.querySelector(".toggle-password");

    if(password.type === "password"){

        password.type = "text";

        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");

    }
    else{

        password.type = "password";

        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");

    }

}

// ===============================
// Login Button Loading
// ===============================

const loginForm = document.querySelector("form");

if(loginForm){

loginForm.addEventListener("submit",function(){

    const btn = document.querySelector(".login-btn");

    btn.classList.add("loading");

    btn.innerHTML="";

});

}

// ===============================
// Input Focus Animation
// ===============================

document.querySelectorAll("input").forEach(input=>{

    input.addEventListener("focus",()=>{

        input.parentElement.style.transform="scale(1.02)";

    });

    input.addEventListener("blur",()=>{

        input.parentElement.style.transform="scale(1)";

    });

});

// ===============================
// Card Animation
// ===============================

window.addEventListener("load",()=>{

    document.querySelector(".login-card")
        .classList.add("fade-up");

});

// ===============================
// Button Hover Sound (Optional)
// ===============================

// document.querySelector(".login-btn").addEventListener(
// "mouseenter",
// ()=>{
// new Audio("/static/audio/click.mp3").play();
// });


// ===============================
// Email Validation
// ===============================

const emailInput=document.querySelector("input[name='email']");

if(emailInput){

emailInput.addEventListener("input",()=>{

    const email=emailInput.value;

    if(email.includes("@")){

        emailInput.style.border="2px solid #22c55e";

    }

    else{

        emailInput.style.border="2px solid #ef4444";

    }

});

}

// ===============================
// Password Strength
// ===============================

const passwordInput=document.getElementById("password");

if(passwordInput){

passwordInput.addEventListener("input",()=>{

    if(passwordInput.value.length>=8){

        passwordInput.style.border="2px solid #22c55e";

    }

    else{

        passwordInput.style.border="2px solid #f59e0b";

    }

});

}

// ===============================
// Google Button Animation
// ===============================

const googleBtn=document.querySelector(".google-btn");

if(googleBtn){

googleBtn.addEventListener("mouseenter",()=>{

    googleBtn.style.transform="translateY(-4px) scale(1.02)";

});

googleBtn.addEventListener("mouseleave",()=>{

    googleBtn.style.transform="translateY(0px) scale(1)";

});

}

// ===============================
// Floating Background
// ===============================

document.addEventListener("mousemove",(e)=>{

    document.body.style.backgroundPosition=
        (e.clientX/40)+"px "+(e.clientY/40)+"px";

});

// ===============================
// Enter Key Animation
// ===============================

document.addEventListener("keydown",(e)=>{

    if(e.key==="Enter"){

        const btn=document.querySelector(".login-btn");

        btn.style.transform="scale(.96)";

        setTimeout(()=>{

            btn.style.transform="scale(1)";

        },150);

    }

});

// ===============================
// Welcome Effect
// ===============================

setTimeout(()=>{

console.log(
"Welcome to Placement Training Portal 🚀"
);

},500);

// ===============================
// Disable Right Click (Optional)
// ===============================

// document.addEventListener("contextmenu",
// e=>e.preventDefault());


// ===============================
// Disable Ctrl+U (Optional)
// ===============================

// document.addEventListener("keydown",(e)=>{

// if(e.ctrlKey && e.key==="u"){
// e.preventDefault();
// }

// });
