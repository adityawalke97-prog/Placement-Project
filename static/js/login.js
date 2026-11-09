document.addEventListener("DOMContentLoaded", function () {

    const passwordInput = document.getElementById("password");
    const togglePassword = document.getElementById("togglePassword");
    const loginForm = document.getElementById("loginForm");
    const loginButton = document.getElementById("loginButton");


    // SHOW / HIDE PASSWORD

    if (togglePassword && passwordInput) {

        togglePassword.addEventListener("click", function () {

            const isHidden = passwordInput.type === "password";

            passwordInput.type = isHidden ? "text" : "password";

            togglePassword.innerHTML = isHidden
                ? '<i class="fas fa-eye-slash"></i>'
                : '<i class="fas fa-eye"></i>';

            togglePassword.setAttribute(
                "aria-label",
                isHidden ? "Hide password" : "Show password"
            );

        });

    }


    // LOGIN FORM VALIDATION

    if (loginForm) {

        loginForm.addEventListener("submit", function (event) {

            const role = document.getElementById("role");
            const email = document.getElementById("email");

            if (!role.value || !email.value.trim() || !passwordInput.value) {

                event.preventDefault();

                alert("Please fill all required fields.");

                return;
            }

            if (!loginForm.checkValidity()) {
                event.preventDefault();
                loginForm.reportValidity();
                return;
            }

            // Prevent multiple submissions
            if (loginButton) {

                loginButton.disabled = true;

                loginButton.innerHTML = `
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Signing In...</span>
                `;

            }

        });

    }


    // AUTO FOCUS EMAIL

    const emailInput = document.getElementById("email");

    if (emailInput) {
        emailInput.focus();
    }


    // FLASH MESSAGE AUTO HIDE

    const flashMessages = document.querySelectorAll(".flash-message");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.style.transition = "opacity 0.5s ease";
            message.style.opacity = "0";

            setTimeout(function () {
                message.remove();
            }, 500);

        }, 5000);

    });

});