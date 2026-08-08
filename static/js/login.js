document.addEventListener("DOMContentLoaded", function () {

    console.log("Resume Builder JS Loaded ✅");


    // =====================================================
    // ELEMENTS
    // =====================================================

    const saveResumeBtn = document.getElementById("saveResumeBtn");
    const saveDraftBtn = document.getElementById("saveDraftBtn");
    const previewResumeBtn = document.getElementById("previewResumeBtn");
    const downloadResumeBtn = document.getElementById("downloadResumeBtn");
    const clearResumeBtn = document.getElementById("clearResumeBtn");
    const generateResumeBtn = document.getElementById("generateResumeBtn");

    const addEducationBtn = document.getElementById("addEducationBtn");
    const addExperienceBtn = document.getElementById("addExperienceBtn");
    const addProjectBtn = document.getElementById("addProjectBtn");
    const addCertificationBtn = document.getElementById("addCertificationBtn");
    const addAchievementBtn = document.getElementById("addAchievementBtn");

    const verifyResumeBtn = document.getElementById("verifyResumeBtn");

    const improveSummaryBtn =
        document.getElementById("improveSummaryBtn");

    const suggestSkillsBtn =
        document.getElementById("suggestSkillsBtn");

    const analyzeJobBtn =
        document.getElementById("analyzeJobBtn");


    // =====================================================
    // SAVE / DRAFT
    // =====================================================

    function collectResumeData() {

        const data = {};

        document.querySelectorAll("input, textarea, select").forEach(
            function (element) {

                if (element.name && element.name.endsWith("[]")) {

                    if (!data[element.name]) {
                        data[element.name] = [];
                    }

                    data[element.name].push(element.value);

                } else if (element.id) {

                    data[element.id] = element.value;

                } else if (element.name) {

                    data[element.name] = element.value;
                }

            }
        );

        return data;
    }


    function saveToLocalStorage() {

        const data = collectResumeData();

        localStorage.setItem(
            "ai_resume_builder",
            JSON.stringify(data)
        );

        showMessage("Resume saved successfully ✅");

    }


    function loadFromLocalStorage() {

        const saved =
            localStorage.getItem("ai_resume_builder");

        if (!saved) {
            return;
        }

        try {

            const data = JSON.parse(saved);

            Object.keys(data).forEach(function (key) {

                const value = data[key];

                const element =
                    document.getElementById(key);

                if (element && !Array.isArray(value)) {
                    element.value = value;
                }

            });

            updateCompletion();

            console.log("Resume loaded ✅");

        } catch (error) {

            console.error(
                "Resume loading error:",
                error
            );

        }
    }


    // =====================================================
    // MESSAGE
    // =====================================================

    function showMessage(message) {

        alert(message);

    }


    // =====================================================
    // SAVE BUTTONS
    // =====================================================

    if (saveResumeBtn) {

        saveResumeBtn.addEventListener(
            "click",
            saveToLocalStorage
        );

    }


    if (saveDraftBtn) {

        saveDraftBtn.addEventListener(
            "click",
            saveToLocalStorage
        );

    }


    // =====================================================
    // CLEAR
    // =====================================================

    if (clearResumeBtn) {

        clearResumeBtn.addEventListener(
            "click",
            function () {

                const confirmClear =
                    confirm(
                        "Are you sure you want to clear the resume?"
                    );

                if (!confirmClear) {
                    return;
                }

                document.querySelectorAll(
                    "input, textarea, select"
                ).forEach(function (element) {

                    element.value = "";

                });

                localStorage.removeItem(
                    "ai_resume_builder"
                );

                updateCompletion();

                showMessage(
                    "Resume cleared successfully."
                );

            }
        );

    }


    // =====================================================
    // PREVIEW
    // =====================================================

    if (previewResumeBtn) {

        previewResumeBtn.addEventListener(
            "click",
            function () {

                generatePreview();

                openModal("previewModal");

            }
        );

    }


    // =====================================================
    // PRINT
    // =====================================================

    const printResumeBtn =
        document.getElementById("printResumeBtn");

    if (printResumeBtn) {

        printResumeBtn.addEventListener(
            "click",
            function () {

                window.print();

            }
        );

    }


    // =====================================================
    // DYNAMIC EDUCATION
    // =====================================================

    if (addEducationBtn) {

        addEducationBtn.addEventListener(
            "click",
            function () {

                const container =
                    document.getElementById(
                        "educationContainer"
                    );

                const item =
                    document.createElement("div");

                item.className =
                    "dynamic-item education-item";

                item.innerHTML = `
                    <div class="dynamic-item-header">

                        <strong>
                            Education
                        </strong>

                        <button
                            type="button"
                            class="remove-btn">
                            🗑
                        </button>

                    </div>

                    <div class="form-grid">

                        <div class="form-group">
                            <label>Degree</label>
                            <input
                                type="text"
                                name="degree[]"
                                placeholder="B.Sc Computer Science">
                        </div>

                        <div class="form-group">
                            <label>Institution</label>
                            <input
                                type="text"
                                name="institution[]"
                                placeholder="College / University">
                        </div>

                        <div class="form-group">
                            <label>Start Year</label>
                            <input
                                type="text"
                                name="education_start[]">
                        </div>

                        <div class="form-group">
                            <label>End Year</label>
                            <input
                                type="text"
                                name="education_end[]">
                        </div>

                        <div class="form-group">
                            <label>CGPA / Percentage</label>
                            <input
                                type="text"
                                name="grade[]">
                        </div>

                        <div class="form-group">
                            <label>Location</label>
                            <input
                                type="text"
                                name="education_location[]">
                        </div>

                    </div>
                `;

                container.appendChild(item);

            }
        );

    }


    // =====================================================
    // DYNAMIC EXPERIENCE
    // =====================================================

    if (addExperienceBtn) {

        addExperienceBtn.addEventListener(
            "click",
            function () {

                const container =
                    document.getElementById(
                        "experienceContainer"
                    );

                const item =
                    document.createElement("div");

                item.className =
                    "dynamic-item experience-item";

                item.innerHTML = `
                    <div class="dynamic-item-header">

                        <strong>
                            Work Experience
                        </strong>

                        <button
                            type="button"
                            class="remove-btn">
                            🗑
                        </button>

                    </div>

                    <div class="form-grid">

                        <div class="form-group">
                            <label>Job Title</label>
                            <input
                                type="text"
                                name="job_title[]">
                        </div>

                        <div class="form-group">
                            <label>Company</label>
                            <input
                                type="text"
                                name="company[]">
                        </div>

                        <div class="form-group">
                            <label>Start Date</label>
                            <input
                                type="month"
                                name="experience_start[]">
                        </div>

                        <div class="form-group">
                            <label>End Date</label>
                            <input
                                type="month"
                                name="experience_end[]">
                        </div>

                        <div class="form-group full">
                            <label>
                                Responsibilities & Achievements
                            </label>

                            <textarea
                                name="experience_description[]"
                                rows="6">
                            </textarea>
                        </div>

                    </div>
                `;

                container.appendChild(item);

            }
        );

    }


    // =====================================================
    // DYNAMIC PROJECT
    // =====================================================

    if (addProjectBtn) {

        addProjectBtn.addEventListener(
            "click",
            function () {

                const container =
                    document.getElementById(
                        "projectsContainer"
                    );

                const item =
                    document.createElement("div");

                item.className =
                    "dynamic-item project-item";

                item.innerHTML = `
                    <div class="dynamic-item-header">

                        <strong>
                            Project
                        </strong>

                        <button
                            type="button"
                            class="remove-btn">
                            🗑
                        </button>

                    </div>

                    <div class="form-grid">

                        <div class="form-group">
                            <label>Project Name</label>
                            <input
                                type="text"
                                name="project_name[]">
                        </div>

                        <div class="form-group">
                            <label>Project Type</label>

                            <select name="project_type[]">

                                <option value="">
                                    Select Type
                                </option>

                                <option>
                                    Academic
                                </option>

                                <option>
                                    Personal
                                </option>

                                <option>
                                    Internship
                                </option>

                                <option>
                                    Freelance
                                </option>

                            </select>

                        </div>

                        <div class="form-group">
                            <label>GitHub URL</label>
                            <input
                                type="url"
                                name="project_github[]">
                        </div>

                        <div class="form-group">
                            <label>Live Demo</label>
                            <input
                                type="url"
                                name="project_demo[]">
                        </div>

                        <div class="form-group full">
                            <label>Technologies</label>
                            <input
                                type="text"
                                name="project_technologies[]">
                        </div>

                        <div class="form-group full">

                            <label>
                                Project Description
                            </label>

                            <textarea
                                name="project_description[]"
                                rows="6">
                            </textarea>

                        </div>

                    </div>
                `;

                container.appendChild(item);

            }
        );

    }


    // =====================================================
    // REMOVE DYNAMIC ITEMS
    // =====================================================

    document.addEventListener(
        "click",
        function (event) {

            const removeBtn =
                event.target.closest(".remove-btn");

            if (!removeBtn) {
                return;
            }

            const item =
                removeBtn.closest(".dynamic-item");

            if (item) {
                item.remove();
                updateCompletion();
            }

        }
    );


    // =====================================================
    // ADD SKILL
    // =====================================================

    document.querySelectorAll(
        ".add-skill-btn"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const category =
                    button.dataset.category;

                const containerMap = {

                    programming:
                        "programmingSkills",

                    frameworks:
                        "frameworkSkills",

                    database:
                        "databaseSkills",

                    tools:
                        "toolSkills"

                };

                const container =
                    document.getElementById(
                        containerMap[category]
                    );

                if (!container) {
                    return;
                }

                const input =
                    document.createElement("input");

                input.type = "text";

                input.name =
                    category + "_skills[]";

                input.placeholder =
                    "Add skill";

                container.appendChild(input);

            }
        );

    });


    // =====================================================
    // SUMMARY COUNTER
    // =====================================================

    const summary =
        document.getElementById(
            "professionalSummary"
        );

    const summaryCounter =
        document.getElementById(
            "summaryCounter"
        );

    if (summary && summaryCounter) {

        function updateSummaryCounter() {

            summaryCounter.textContent =
                summary.value.length +
                " / " +
                summary.maxLength;

        }

        summary.addEventListener(
            "input",
            updateSummaryCounter
        );

        updateSummaryCounter();

    }


    // =====================================================
    // COMPLETION
    // =====================================================

    function updateCompletion() {

        const fields = [

            "fullName",
            "professionalTitle",
            "email",
            "professionalSummary",
            "targetJobTitle",
            "targetIndustry",
            "languages"

        ];

        let completed = 0;

        fields.forEach(function (id) {

            const element =
                document.getElementById(id);

            if (
                element &&
                element.value.trim()
            ) {
                completed++;
            }

        });

        const percentage =
            Math.round(
                (completed / fields.length) * 100
            );

        const text =
            document.getElementById(
                "completionText"
            );

        const score =
            document.getElementById(
                "completionScore"
            );

        const fill =
            document.getElementById(
                "mainProgressFill"
            );

        if (text) {
            text.textContent =
                percentage + "% Complete";
        }

        if (score) {
            score.textContent =
                percentage + "%";
        }

        if (fill) {
            fill.style.width =
                percentage + "%";
        }

    }


    document.addEventListener(
        "input",
        updateCompletion
    );


    // =====================================================
    // MODAL
    // =====================================================

    function openModal(id) {

        const modal =
            document.getElementById(id);

        if (!modal) {
            console.warn(
                "Modal not found:",
                id
            );
            return;
        }

        modal.style.display = "flex";

    }


    function closeModal(id) {

        const modal =
            document.getElementById(id);

        if (!modal) {
            return;
        }

        modal.style.display = "none";

    }


    document.addEventListener(
        "click",
        function (event) {

            const closeButton =
                event.target.closest(
                    "[data-close-modal]"
                );

            if (!closeButton) {
                return;
            }

            closeModal(
                closeButton.dataset.closeModal
            );

        }
    );


    // =====================================================
    // PREVIEW
    // =====================================================

    function generatePreview() {

        const preview =
            document.getElementById(
                "resumePreview"
            );

        if (!preview) {
            return;
        }

        const name =
            document.getElementById(
                "fullName"
            )?.value || "Your Name";

        const title =
            document.getElementById(
                "professionalTitle"
            )?.value || "";

        const email =
            document.getElementById(
                "email"
            )?.value || "";

        const phone =
            document.getElementById(
                "phone"
            )?.value || "";

        const summary =
            document.getElementById(
                "professionalSummary"
            )?.value || "";

        preview.innerHTML = `

            <div class="generated-resume">

                <header>

                    <h1>${escapeHTML(name)}</h1>

                    <h3>
                        ${escapeHTML(title)}
                    </h3>

                    <p>
                        ${escapeHTML(email)}
                        ${email && phone ? " | " : ""}
                        ${escapeHTML(phone)}
                    </p>

                </header>

                ${
                    summary
                    ? `
                        <section>
                            <h2>Professional Summary</h2>
                            <p>
                                ${escapeHTML(summary)}
                            </p>
                        </section>
                    `
                    : ""
                }

            </div>
        `;

    }


    // =====================================================
    // HTML ESCAPE
    // =====================================================

    function escapeHTML(value) {

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    }


    // =====================================================
    // DOWNLOAD
    // =====================================================

    if (downloadResumeBtn) {

        downloadResumeBtn.addEventListener(
            "click",
            function () {

                generatePreview();

                window.print();

            }
        );

    }


    // =====================================================
    // GENERATE RESUME
    // =====================================================

    if (generateResumeBtn) {

        generateResumeBtn.addEventListener(
            "click",
            function () {

                saveToLocalStorage();

                generatePreview();

                openModal("previewModal");

            }
        );

    }


    // =====================================================
    // VERIFY RESUME
    // =====================================================

    if (verifyResumeBtn) {

        verifyResumeBtn.addEventListener(
            "click",
            function () {

                openModal("verificationModal");

                const loading =
                    document.getElementById(
                        "verificationLoading"
                    );

                const result =
                    document.getElementById(
                        "verificationResult"
                    );

                if (loading) {
                    loading.style.display = "block";
                }

                if (result) {
                    result.style.display = "none";
                }

                // Temporary local ATS calculation
                setTimeout(function () {

                    const score =
                        calculateLocalATS();

                    const scoreElement =
                        document.getElementById(
                            "verificationScore"
                        );

                    const atsScore =
                        document.getElementById(
                            "atsScore"
                        );

                    const atsProgress =
                        document.getElementById(
                            "atsProgressFill"
                        );

                    if (scoreElement) {
                        scoreElement.textContent =
                            score;
                    }

                    if (atsScore) {
                        atsScore.textContent =
                            score;
                    }

                    if (atsProgress) {
                        atsProgress.style.width =
                            score + "%";
                    }

                    if (loading) {
                        loading.style.display =
                            "none";
                    }

                    if (result) {
                        result.style.display =
                            "block";
                    }

                }, 1000);

            }
        );

    }


    // =====================================================
    // LOCAL ATS SCORE
    // =====================================================

    function calculateLocalATS() {

        let score = 0;

        const fields = [

            "fullName",
            "email",
            "phone",
            "professionalTitle",
            "professionalSummary",
            "targetJobTitle",
            "jobDescription"

        ];

        fields.forEach(function (id) {

            const element =
                document.getElementById(id);

            if (
                element &&
                element.value.trim()
            ) {

                score += 10;

            }

        });

        const skills =
            document.querySelectorAll(
                'input[name$="_skills[]"]'
            );

        if (skills.length > 0) {
            score += 10;
        }

        const projects =
            document.querySelectorAll(
                'input[name="project_name[]"]'
            );

        if (projects.length > 0 &&
            projects[0].value.trim()) {

            score += 10;

        }

        return Math.min(score, 100);

    }


    // =====================================================
    // AI BUTTON PLACEHOLDER
    // =====================================================

    if (improveSummaryBtn) {

        improveSummaryBtn.addEventListener(
            "click",
            function () {

                const summary =
                    document.getElementById(
                        "professionalSummary"
                    );

                if (!summary.value.trim()) {

                    alert(
                        "Pehle professional summary likho."
                    );

                    return;
                }

                alert(
                    "AI API next step me connect karenge."
                );

            }
        );

    }


    if (suggestSkillsBtn) {

        suggestSkillsBtn.addEventListener(
            "click",
            function () {

                alert(
                    "AI Skills Suggestion API next step me connect karenge."
                );

            }
        );

    }


    if (analyzeJobBtn) {

        analyzeJobBtn.addEventListener(
            "click",
            function () {

                const job =
                    document.getElementById(
                        "jobDescription"
                    );

                if (!job || !job.value.trim()) {

                    alert(
                        "Pehle Job Description paste karo."
                    );

                    return;
                }

                alert(
                    "AI Job Analyzer next step me connect karenge."
                );

            }
        );

    }


    // =====================================================
    // INITIALIZE
    // =====================================================

    loadFromLocalStorage();
    updateCompletion();

});
