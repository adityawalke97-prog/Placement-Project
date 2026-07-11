javascript id="z0rxsw"
// Confirm Logout
function confirmLogout() {
    return confirm("Are you sure you want to logout?");
}

// Auto Hide Flash Messages
setTimeout(function () {
    const flash = document.querySelector(".flash");

    if (flash) {
        flash.style.display = "none";
    }
}, 3000);

// Resume Form Validation
function validateResume() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;

    if (name === "" || email === "") {
        alert("Please fill all required fields.");
        return false;
    }

    return true;
}
