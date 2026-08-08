/* =========================================================
   AI RESUME BUILDER
   Complete Frontend Controller
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    "use strict";

    /* =====================================================
       HELPERS
    ===================================================== */

    const $ = (selector, parent = document) =>
        parent.querySelector(selector);

    const $$ = (selector, parent = document) =>
        [...parent.querySelectorAll(selector)];

    function value(id) {
        const el = document.getElementById(id);
        return el ? el.value.trim() : "";
    }

    function showToast(message, type = "success") {

        const toast = $("#resumeToast");

        if (!toast) return;

        toast.textContent = message;

        toast.className = `resume-toast show ${type}`;

        setTimeout(() => {
            toast.classList.remove("show");
        }, 3000);
    }


    function showLoading(message = "Processing...") {

        const loader = $("#resumeLoading");

        if (!loader) return;

        const title = $("h3", loader);

        if (title) {
            title.textContent = message;
        }

        loader.classList.add("active");
    }


    function hideLoading() {

        const loader = $("#resumeLoading");

        if (!loader) return;

        loader.classList.remove("active");
    }


    /* =====================================================
       COLLECT RESUME DATA
    ===================================================== */

    function collectResumeData() {

        const data = {

            personal: {
                full_name: value("fullName"),
                professional_title: value("professionalTitle"),
                location: value("location"),
                email: value("email"),
                phone: value("phone"),
                linkedin: value("linkedin"),
                github: value("github"),
                portfolio: value("portfolio")
            },

            summary: value("professionalSummary"),

            target_job: {
                title: value("targetJobTitle"),
                industry: value("targetIndustry"),
                description: value("jobDescription")
            },

            education: [],

            skills: {
                programming: [],
                frameworks: [],
                databases: [],
                tools: []
            },

            experience: [],

            projects: [],

            certifications: [],

            achievements: [],

            additional: {
                languages: value("languages"),
                coursework: value("coursework"),
                interests: value("interests")
            }
        };


        /* EDUCATION */

        $$(".education-item").forEach(item => {

            const inputs = $$("input", item);

            data.education.push({
                degree: inputs[0]?.value.trim() || "",
                institution: inputs[1]?.value.trim() || "",
                start_year: inputs[2]?.value.trim() || "",
                end_year: inputs[3]?.value.trim() || "",
                grade: inputs[4]?.value.trim() || "",
                location: inputs[5]?.value.trim() || ""
            });

        });


        /* SKILLS */

        $$('input[name="programming_skills[]"]')
            .forEach(input => {
                if (input.value.trim())
                    data.skills.programming.push(input.value.trim());
            });


        $$('input[name="framework_skills[]"]')
            .forEach(input => {
                if (input.value.trim())
                    data.skills.frameworks.push(input.value.trim());
            });


        $$('input[name="database_skills[]"]')
            .forEach(input => {
                if (input.value.trim())
                    data.skills.databases.push(input.value.trim());
            });


        $$('input[name="tool_skills[]"]')
            .forEach(input => {
                if (input.value.trim())
                    data.skills.tools.push(input.value.trim());
            });


        /* EXPERIENCE */

        $$(".experience-item").forEach(item => {

            const inputs = $$("input", item);
            const textarea = $("textarea", item);

            data.experience.push({

                job_title: inputs[0]?.value.trim() || "",

                company: inputs[1]?.value.trim() || "",

                start_date: inputs[2]?.value || "",

                end_date: inputs[3]?.value || "",

                description: textarea?.value.trim() || ""

            });

        });


        /* PROJECTS */

        $$(".project-item").forEach(item => {

            const inputs = $$("input", item);

            const select = $("select", item);

            const textarea = $("textarea", item);

            data.projects.push({

                name: inputs[0]?.value.trim() || "",

                type: select?.value || "",

                github: inputs[1]?.value.trim() || "",

                demo: inputs[2]?.value.trim() || "",

                technologies: inputs[3]?.value.trim() || "",

                description: textarea?.value.trim() || ""

            });

        });


        /* CERTIFICATIONS */

        $$("#certificationContainer .dynamic-item")
            .forEach(item => {

                const inputs = $$("input", item);

                data.certifications.push({

                    name: inputs[0]?.value.trim() || "",

                    organization: inputs[1]?.value.trim() || "",

                    year: inputs[2]?.value.trim() || "",

                    url: inputs[3]?.value.trim() || ""

                });

            });


        /* ACHIEVEMENTS */

        $$('textarea[name="achievement[]"]')
            .forEach(textarea => {

                if (textarea.value.trim()) {

                    data.achievements.push(
                        textarea.value.trim()
                    );

                }

            });


        return data;
    }


    /* =====================================================
       AI API CALL
    ===================================================== */

    async function callAI(action, extraData = {}) {

        try {

            showLoading("AI is working...");

            const resume = collectResumeData();

            const response = await fetch("/api/resume/ai", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({

                    action: action,

                    resume: resume,

                    ...extraData

                })

            });


            const result = await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error ||
                    "AI request failed."
                );

            }


            return result;

        }

        catch (error) {

            console.error("AI ERROR:", error);

            showToast(
                error.message || "AI service failed.",
                "error"
            );

            return null;

        }

        finally {

            hideLoading();

        }

    }


    /* =====================================================
       IMPROVE SUMMARY
    ===================================================== */

    const improveSummaryBtn =
        $("#improveSummaryBtn");

    if (improveSummaryBtn) {

        improveSummaryBtn.addEventListener(
            "click",
            async () => {

                const summary =
                    value("professionalSummary");

                const job =
                    value("targetJobTitle");

                if (!summary) {

                    showToast(
                        "Please write a summary first.",
                        "error"
                    );

                    return;
                }


                const result = await callAI(
                    "improve_summary",
                    {
                        text: summary,
                        target_job: job
                    }
                );


                if (
                    result &&
                    result.success &&
                    result.content
                ) {

                    $("#professionalSummary").value =
                        result.content;

                    updateSummaryCounter();

                    updateResumeProgress();

                    showToast(
                        "✨ Summary improved successfully!"
                    );

                }

            }
        );

    }


    /* =====================================================
       ANALYZE JOB
    ===================================================== */

    const analyzeJobBtn =
        $("#analyzeJobBtn");

    if (analyzeJobBtn) {

        analyzeJobBtn.addEventListener(
            "click",
            async () => {

                const jobDescription =
                    value("jobDescription");

                if (!jobDescription) {

                    showToast(
                        "Paste a job description first.",
                        "error"
                    );

                    return;
                }


                const result = await callAI(
                    "analyze_job",
                    {
                        job_description:
                            jobDescription
                    }
                );


                if (result && result.success) {

                    showAIAnalysis(result);

                    showToast(
                        "🎯 Job analysis completed!"
                    );

                }

            }
        );

    }


    /* =====================================================
       SUGGEST SKILLS
    ===================================================== */

    const suggestSkillsBtn =
        $("#suggestSkillsBtn");

    if (suggestSkillsBtn) {

        suggestSkillsBtn.addEventListener(
            "click",
            async () => {

                const result = await callAI(
                    "suggest_skills",
                    {
                        target_job:
                            value("targetJobTitle"),

                        job_description:
                            value("jobDescription")
                    }
                );


                if (
                    result &&
                    result.success
                ) {

                    showSkillSuggestions(
                        result
                    );

                }

            }
        );

    }


    /* =====================================================
       IMPROVE EXPERIENCE
    ===================================================== */

    $$(".improveExperienceBtn")
        .forEach(button => {

            button.addEventListener(
                "click",
                async () => {

                    const item =
                        button.closest(
                            ".experience-item"
                        );

                    if (!item) return;


                    const textarea =
                        $("textarea", item);

                    if (
                        !textarea ||
                        !textarea.value.trim()
                    ) {

                        showToast(
                            "Enter your experience first.",
                            "error"
                        );

                        return;
                    }


                    const result =
                        await callAI(
                            "improve_experience",
                            {
                                text:
                                    textarea.value,

                                target_job:
                                    value(
                                        "targetJobTitle"
                                    )
                            }
                        );


                    if (
                        result &&
                        result.success &&
                        result.content
                    ) {

                        textarea.value =
                            result.content;

                        updateResumeProgress();

                        showToast(
                            "✨ Experience improved!"
                        );

                    }

                }
            );

        });


    /* =====================================================
       IMPROVE PROJECT
    ===================================================== */

    $$(".improveProjectBtn")
        .forEach(button => {

            button.addEventListener(
                "click",
                async () => {

                    const item =
                        button.closest(
                            ".project-item"
                        );

                    if (!item) return;


                    const textarea =
                        $("textarea", item);

                    if (
                        !textarea ||
                        !textarea.value.trim()
                    ) {

                        showToast(
                            "Enter project description first.",
                            "error"
                        );

                        return;
                    }


                    const result =
                        await callAI(
                            "improve_project",
                            {
                                text:
                                    textarea.value,

                                technologies:
                                    $("input[name='project_technologies[]']", item)
                                    ?.value || ""
                            }
                        );


                    if (
                        result &&
                        result.success &&
                        result.content
                    ) {

                        textarea.value =
                            result.content;

                        updateResumeProgress();

                        showToast(
                            "🚀 Project improved!"
                        );

                    }

                }
            );

        });


    /* =====================================================
       VERIFY RESUME
    ===================================================== */

    const verifyResumeBtn =
        $("#verifyResumeBtn");

    if (verifyResumeBtn) {

        verifyResumeBtn.addEventListener(
            "click",
            async () => {

                openModal(
                    "verificationModal"
                );

                showVerificationLoading();


                const result =
                    await callAI(
                        "verify_resume",
                        {
                            job_description:
                                value(
                                    "jobDescription"
                                )
                        }
                    );


                if (
                    result &&
                    result.success
                ) {

                    displayVerification(
                        result
                    );

                }

            }
        );

    }


    /* =====================================================
       TAILOR RESUME
    ===================================================== */

    const tailorResumeBtn =
        $("#tailorResumeBtn");

    if (tailorResumeBtn) {

        tailorResumeBtn.addEventListener(
            "click",
            async () => {

                if (!value("jobDescription")) {

                    showToast(
                        "Add a job description first.",
                        "error"
                    );

                    return;
                }


                const result =
                    await callAI(
                        "tailor_resume",
                        {
                            job_description:
                                value(
                                    "jobDescription"
                                )
                        }
                    );


                if (
                    result &&
                    result.success
                ) {

                    showAIResultModal(
                        "🎯 Resume Tailoring",
                        result
                    );

                }

            }
        );

    }


    /* =====================================================
       MISSING KEYWORDS
    ===================================================== */

    const missingKeywordsBtn =
        $("#missingKeywordsBtn");

    if (missingKeywordsBtn) {

        missingKeywordsBtn.addEventListener(
            "click",
            async () => {

                if (!value("jobDescription")) {

                    showToast(
                        "Add a job description first.",
                        "error"
                    );

                    return;
                }


                const result =
                    await callAI(
                        "missing_keywords",
                        {
                            job_description:
                                value(
                                    "jobDescription"
                                )
                        }
                    );


                if (
                    result &&
                    result.success
                ) {

                    showAIResultModal(
                        "🔍 Missing Keywords",
                        result
                    );

                }

            }
        );

    }


    /* =====================================================
       RESUME SUGGESTIONS
    ===================================================== */

    const resumeSuggestionsBtn =
        $("#resumeSuggestionsBtn");

    if (resumeSuggestionsBtn) {

        resumeSuggestionsBtn.addEventListener(
            "click",
            async () => {

                const result =
                    await callAI(
                        "resume_suggestions"
                    );


                if (
                    result &&
                    result.success
                ) {

                    showAIResultModal(
                        "💡 Resume Suggestions",
                        result
                    );

                }

            }
        );

    }


    /* =====================================================
       GENERATE ACHIEVEMENT
    ===================================================== */

    const generateAchievementBtn =
        $("#generateAchievementBtn");

    if (generateAchievementBtn) {

        generateAchievementBtn.addEventListener(
            "click",
            async () => {

                const result =
                    await callAI(
                        "generate_achievement",
                        {
                            target_job:
                                value(
                                    "targetJobTitle"
                                )
                        }
                    );


                if (
                    result &&
                    result.success &&
                    result.content
                ) {

                    const container =
                        $("#achievementContainer");

                    if (container) {

                        const item =
                            document.createElement(
                                "div"
                            );

                        item.className =
                            "dynamic-item";

                        item.innerHTML = `

                            <div class="form-group">

                                <label>
                                    AI Generated Achievement
                                </label>

                                <textarea
                                    name="achievement[]"
                                    rows="3">${escapeHTML(
                                        result.content
                                    )}</textarea>

                            </div>

                        `;

                        container.appendChild(item);

                        updateResumeProgress();

                        showToast(
                            "🏆 Achievement generated!"
                        );

                    }

                }

            }
        );

    }


    /* =====================================================
       SUMMARY COUNTER
    ===================================================== */

    function updateSummaryCounter() {

        const textarea =
            $("#professionalSummary");

        const counter =
            $("#summaryCounter");

        if (!textarea || !counter) return;

        counter.textContent =
            `${textarea.value.length} / 1000`;

    }


    const summaryTextarea =
        $("#professionalSummary");

    if (summaryTextarea) {

        summaryTextarea.addEventListener(
            "input",
            () => {

                updateSummaryCounter();

                updateResumeProgress();

            }
        );

    }


    /* =====================================================
       DYNAMIC EDUCATION
    ===================================================== */

    const addEducationBtn =
        $("#addEducationBtn");

    if (addEducationBtn) {

        addEducationBtn.addEventListener(
            "click",
            () => {

                const container =
                    $("#educationContainer");

                if (!container) return;

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
                                name="education_start[]"
                                placeholder="2024">
                        </div>

                        <div class="form-group">
                            <label>End Year</label>
                            <input
                                type="text"
                                name="education_end[]"
                                placeholder="2027">
                        </div>

                        <div class="form-group">
                            <label>CGPA / Percentage</label>
                            <input
                                type="text"
                                name="grade[]"
                                placeholder="8.5 CGPA">
                        </div>

                        <div class="form-group">
                            <label>Location</label>
                            <input
                                type="text"
                                name="education_location[]"
                                placeholder="Pune">
                        </div>

                    </div>

                `;

                container.appendChild(item);

                updateResumeProgress();

            }
        );

    }


    /* =====================================================
       DYNAMIC EXPERIENCE
    ===================================================== */

    const addExperienceBtn =
        $("#addExperienceBtn");

    if (addExperienceBtn) {

        addExperienceBtn.addEventListener(
            "click",
            () => {

                const container =
                    $("#experienceContainer");

                if (!container) return;

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
                                name="job_title[]"
                                placeholder="Software Developer Intern">

                        </div>

                        <div class="form-group">

                            <label>Company</label>

                            <input
                                type="text"
                                name="company[]"
                                placeholder="Company Name">

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
                                rows="6"
                                placeholder="Describe your work..."></textarea>

                        </div>

                    </div>

                    <button
                        type="button"
                        class="ai-bullet-btn improveExperienceBtn">

                        ✨ Improve Experience Bullets

                    </button>

                `;

                container.appendChild(item);

                attachExperienceAI(item);

            }
        );

    }


    function attachExperienceAI(item) {

        const button =
            $(".improveExperienceBtn", item);

        if (!button) return;

        button.addEventListener(
            "click",
            async () => {

                const textarea =
                    $("textarea", item);

                if (
                    !textarea ||
                    !textarea.value.trim()
                ) {

                    showToast(
                        "Enter experience first.",
                        "error"
                    );

                    return;
                }


                const result =
                    await callAI(
                        "improve_experience",
                        {
                            text:
                                textarea.value,

                            target_job:
                                value(
                                    "targetJobTitle"
                                )
                        }
                    );


                if (
                    result &&
                    result.success
                ) {

                    textarea.value =
                        result.content;

                    showToast(
                        "✨ Experience improved!"
                    );

                }

            }
        );

    }


    /* =====================================================
       DYNAMIC PROJECTS
    ===================================================== */

    const addProjectBtn =
        $("#addProjectBtn");

    if (addProjectBtn) {

        addProjectBtn.addEventListener(
            "click",
            () => {

                const container =
                    $("#projectsContainer");

                if (!container) return;

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

                            <label>
                                Project Name
                            </label>

                            <input
                                type="text"
                                name="project_name[]">

                        </div>

                        <div class="form-group">

                            <label>
                                Project Type
                            </label>

                            <select name="project_type[]">

                                <option value="">
                                    Select Type
                                </option>

                                <option>Academic</option>
                                <option>Personal</option>
                                <option>Internship</option>
                                <option>Freelance</option>

                            </select>

                        </div>

                        <div class="form-group">

                            <label>
                                GitHub URL
                            </label>

                            <input
                                type="url"
                                name="project_github[]">

                        </div>

                        <div class="form-group">

                            <label>
                                Live Demo
                            </label>

                            <input
                                type="url"
                                name="project_demo[]">

                        </div>

                        <div class="form-group full">

                            <label>
                                Technologies
                            </label>

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
                                rows="6"></textarea>

                        </div>

                    </div>

                    <button
                        type="button"
                        class="ai-bullet-btn improveProjectBtn">

                        ✨ Improve Project Description

                    </button>

                `;

                container.appendChild(item);

                attachProjectAI(item);

            }
        );

    }


    function attachProjectAI(item) {

        const button =
            $(".improveProjectBtn", item);

        if (!button) return;

        button.addEventListener(
            "click",
            async () => {

                const textarea =
                    $("textarea", item);

                if (
                    !textarea ||
                    !textarea.value.trim()
                ) {

                    showToast(
                        "Enter project description first.",
                        "error"
                    );

                    return;
                }


                const tech =
                    $("input[name='project_technologies[]']", item);


                const result =
                    await callAI(
                        "improve_project",
                        {
                            text:
                                textarea.value,

                            technologies:
                                tech?.value || ""
                        }
                    );


                if (
                    result &&
                    result.success
                ) {

                    textarea.value =
                        result.content;

                    showToast(
                        "🚀 Project improved!"
                    );

                }

            }
        );

    }


    /* =====================================================
       ADD SKILL
    ===================================================== */

    $$(".add-skill-btn")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const category =
                        button.dataset.category;

                    let containerId = "";

                    let name = "";

                    let placeholder = "";


                    if (category === "programming") {

                        containerId =
                            "programmingSkills";

                        name =
                            "programming_skills[]";

                        placeholder =
                            "JavaScript";

                    }

                    else if (category === "frameworks") {

                        containerId =
                            "frameworkSkills";

                        name =
                            "framework_skills[]";

                        placeholder =
                            "React";

                    }

                    else if (category === "database") {

                        containerId =
                            "databaseSkills";

                        name =
                            "database_skills[]";

                        placeholder =
                            "PostgreSQL";

                    }

                    else {

                        containerId =
                            "toolSkills";

                        name =
                            "tool_skills[]";

                        placeholder =
                            "Docker";

                    }


                    const container =
                        document.getElementById(
                            containerId
                        );

                    if (!container) return;


                    const input =
                        document.createElement(
                            "input"
                        );

                    input.type = "text";

                    input.name = name;

                    input.placeholder =
                        placeholder;


                    container.appendChild(
                        input
                    );


                    input.focus();

                    updateResumeProgress();

                }
            );

        });


    /* =====================================================
       REMOVE DYNAMIC ITEM
    ===================================================== */

    document.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    ".remove-btn"
                );

            if (!button) return;


            const item =
                button.closest(
                    ".dynamic-item"
                );

            if (!item) return;


            const parent =
                item.parentElement;


            const items =
                parent.querySelectorAll(
                    ".dynamic-item"
                );


            if (items.length <= 1) {

                showToast(
                    "At least one item should remain.",
                    "error"
                );

                return;

            }


            item.remove();

            updateResumeProgress();

        }
    );


    /* =====================================================
       PROGRESS
    ===================================================== */

    function updateResumeProgress() {

        const fields = [

            value("fullName"),

            value("email"),

            value("professionalSummary"),

            value("targetJobTitle"),

            value("location")

        ];


        const hasEducation =
            $$(".education-item input")
            .some(input =>
                input.value.trim()
            );


        const hasSkills =
            $$(
                'input[name$="_skills[]"]'
            )
            .some(input =>
                input.value.trim()
            );


        const hasProjects =
            $$(".project-item input, .project-item textarea")
            .some(el =>
                el.value.trim()
            );


        const hasExperience =
            $$(".experience-item input, .experience-item textarea")
            .some(el =>
                el.value.trim()
            );


        let completed = 0;

        const total = 8;


        completed += fields[0] ? 1 : 0;

        completed += fields[1] ? 1 : 0;

        completed += fields[2] ? 1 : 0;

        completed += hasEducation ? 1 : 0;

        completed += hasSkills ? 1 : 0;

        completed += hasProjects ? 1 : 0;

        completed += hasExperience ? 1 : 0;

        completed += fields[3] ? 1 : 0;


        const percentage =
            Math.round(
                (completed / total) * 100
            );


        const text =
            $("#completionText");

        const score =
            $("#completionScore");

        const fill =
            $("#mainProgressFill");


        if (text)
            text.textContent =
                `${percentage}% Complete`;

        if (score)
            score.textContent =
                `${percentage}%`;

        if (fill)
            fill.style.width =
                `${percentage}%`;


        updateChecklist();

    }


    /* =====================================================
       CHECKLIST
    ===================================================== */

    function updateChecklist() {

        setCheck(
            "checkContact",
            value("fullName") &&
            value("email")
        );


        setCheck(
            "checkSummary",
            value("professionalSummary")
        );


        setCheck(
            "checkEducation",
            $$(".education-item input")
                .some(el =>
                    el.value.trim()
                )
        );


        setCheck(
            "checkSkills",
            $$(
                'input[name$="_skills[]"]'
            )
            .some(el =>
                el.value.trim()
            )
        );


        setCheck(
            "checkProjects",
            $$(".project-item input, .project-item textarea")
                .some(el =>
                    el.value.trim()
                )
        );


        setCheck(
            "checkExperience",
            $$(".experience-item input, .experience-item textarea")
                .some(el =>
                    el.value.trim()
                )
        );

    }


    function setCheck(id, complete) {

        const element =
            document.getElementById(id);

        if (!element) return;


        const icon =
            $("span", element);


        if (complete) {

            element.classList.add(
                "completed"
            );

            if (icon)
                icon.textContent = "✓";

        }

        else {

            element.classList.remove(
                "completed"
            );

            if (icon)
                icon.textContent = "○";

        }

    }


    /* =====================================================
       VERIFY DISPLAY
    ===================================================== */

    function showVerificationLoading() {

        const loading =
            $("#verificationLoading");

        const result =
            $("#verificationResult");


        if (loading)
            loading.style.display =
                "block";

        if (result)
            result.style.display =
                "none";

    }


    function displayVerification(data) {

        const loading =
            $("#verificationLoading");

        const result =
            $("#verificationResult");


        if (loading)
            loading.style.display =
                "none";

        if (result)
            result.style.display =
                "block";


        const score =
            data.score ??
            data.ats_score ??
            0;


        setText(
            "verificationScore",
            score
        );


        setText(
            "atsScore",
            score
        );


        setText(
            "keywordScore",
            `${data.keyword_score ?? 0}%`
        );


        setText(
            "contentScore",
            `${data.content_score ?? 0}%`
        );


        setText(
            "formatScore",
            `${data.format_score ?? 0}%`
        );


        setText(
            "skillsScore",
            `${data.skills_score ?? 0}%`
        );


        fillATS(score);


        renderList(
            "strengthsList",
            data.strengths || []
        );


        renderList(
            "improvementsList",
            data.improvements || []
        );


        renderKeywords(
            data.missing_keywords || []
        );

    }


    function fillATS(score) {

        const fill =
            $("#atsProgressFill");

        if (fill)
            fill.style.width =
                `${Math.min(
                    100,
                    Math.max(0, score)
                )}%`;

    }


    /* =====================================================
       AI ANALYSIS
    ===================================================== */

    function showAIAnalysis(data) {

        let message = "";

        if (data.summary)
            message +=
                `${data.summary}\n\n`;

        if (data.missing_keywords?.length)
            message +=
                "Missing keywords:\n" +
                data.missing_keywords.join(
                    ", "
                );


        alert(
            message ||
            "Job analysis completed."
        );

    }


    function showSkillSuggestions(data) {

        const skills =
            data.skills ||
            data.suggested_skills ||
            [];


        if (!skills.length) {

            showToast(
                "No additional skills found."
            );

            return;

        }


        const formatted =
            skills.join(", ");


        showToast(
            `💡 Suggested: ${formatted}`
        );

    }


    /* =====================================================
       RESULT MODAL
    ===================================================== */

    function showAIResultModal(title, data) {

        let content =
            data.content ||
            data.message ||
            data.summary ||
            "";


        if (
            typeof content !== "string"
        ) {

            content =
                JSON.stringify(
                    content,
                    null,
                    2
                );

        }


        const modal =
            document.createElement(
                "div"
            );

        modal.className =
            "resume-modal active";


        modal.innerHTML = `

            <div class="modal-overlay"></div>

            <div class="modal-container">

                <div class="modal-header">

                    <div>

                        <span class="modal-label">
                            AI ASSISTANT
                        </span>

                        <h2>
                            ${escapeHTML(title)}
                        </h2>

                    </div>

                    <button
                        type="button"
                        class="modal-close">
                        ✕
                    </button>

                </div>

                <div
                    style="
                        padding:25px;
                        white-space:pre-wrap;
                        line-height:1.7;
                    "
                >
                    ${escapeHTML(content)}
                </div>

            </div>

        `;


        document.body.appendChild(
            modal
        );


        const close = () => {
            modal.remove();
        };


        $(".modal-close", modal)
            ?.addEventListener(
                "click",
                close
            );


        $(".modal-overlay", modal)
            ?.addEventListener(
                "click",
                close
            );

    }


    /* =====================================================
       MODALS
    ===================================================== */

    function openModal(id) {

        const modal =
            document.getElementById(id);

        if (!modal) return;

        modal.classList.add("active");

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "modal-open"
        );

    }


    function closeModal(id) {

        const modal =
            document.getElementById(id);

        if (!modal) return;

        modal.classList.remove("active");

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );

    }


    $$("[data-close-modal]")
        .forEach(element => {

            element.addEventListener(
                "click",
                () => {

                    closeModal(
                        element.dataset.closeModal
                    );

                }
            );

        });


    /* =====================================================
       PREVIEW
    ===================================================== */

    const previewResumeBtn =
        $("#previewResumeBtn");

    if (previewResumeBtn) {

        previewResumeBtn.addEventListener(
            "click",
            () => {

                generatePreview();

                openModal(
                    "previewModal"
                );

            }
        );

    }


    function generatePreview() {

        const preview =
            $("#resumePreview");

        if (!preview) return;


        const data =
            collectResumeData();


        preview.innerHTML = `

            <div class="resume-paper">

                <header class="preview-personal">

                    <h1>
                        ${escapeHTML(
                            data.personal.full_name ||
                            "Your Name"
                        )}
                    </h1>

                    <h3>
                        ${escapeHTML(
                            data.personal.professional_title ||
                            ""
                        )}
                    </h3>

                    <p>
                        ${escapeHTML(
                            data.personal.email
                        )}
                        ${data.personal.phone
                            ? " • " +
                              escapeHTML(
                                data.personal.phone
                              )
                            : ""}
                        ${data.personal.location
                            ? " • " +
                              escapeHTML(
                                data.personal.location
                              )
                            : ""}
                    </p>

                </header>


                ${
                    data.summary
                    ? `
                    <section>

                        <h2>
                            PROFESSIONAL SUMMARY
                        </h2>

                        <p>
                            ${escapeHTML(
                                data.summary
                            )}
                        </p>

                    </section>
                    `
                    : ""
                }


                ${
                    data.skills.programming.length ||
                    data.skills.frameworks.length ||
                    data.skills.databases.length ||
                    data.skills.tools.length
                    ? `
                    <section>

                        <h2>
                            TECHNICAL SKILLS
                        </h2>

                        <p>
                            ${escapeHTML(
                                [
                                    ...data.skills.programming,
                                    ...data.skills.frameworks,
                                    ...data.skills.databases,
                                    ...data.skills.tools
                                ].join(", ")
                            )}
                        </p>

                    </section>
                    `
                    : ""
                }


                ${
                    data.education.length
                    ? `
                    <section>

                        <h2>
                            EDUCATION
                        </h2>

                        ${data.education.map(
                            edu => `
                                <div>

                                    <strong>
                                        ${escapeHTML(
                                            edu.degree
                                        )}
                                    </strong>

                                    <p>
                                        ${escapeHTML(
                                            edu.institution
                                        )}
                                    </p>

                                </div>
                            `
                        ).join("")}

                    </section>
                    `
                    : ""
                }


                ${
                    data.experience.some(
                        x =>
                            x.job_title ||
                            x.company ||
                            x.description
                    )
                    ? `
                    <section>

                        <h2>
                            EXPERIENCE
                        </h2>

                        ${data.experience.map(
                            exp => `
                                <div>

                                    <h3>
                                        ${escapeHTML(
                                            exp.job_title
                                        )}
                                    </h3>

                                    <strong>
                                        ${escapeHTML(
                                            exp.company
                                        )}
                                    </strong>

                                    <p>
                                        ${escapeHTML(
                                            exp.description
                                        )}
                                    </p>

                                </div>
                            `
                        ).join("")}

                    </section>
                    `
                    : ""
                }


                ${
                    data.projects.some(
                        x =>
                            x.name ||
                            x.description
                    )
                    ? `
                    <section>

                        <h2>
                            PROJECTS
                        </h2>

                        ${data.projects.map(
                            project => `
                                <div>

                                    <h3>
                                        ${escapeHTML(
                                            project.name
                                        )}
                                    </h3>

                                    <p>
                                        ${escapeHTML(
                                            project.description
                                        )}
                                    </p>

                                    <small>
                                        ${escapeHTML(
                                            project.technologies
                                        )}
                                    </small>

                                </div>
                            `
                        ).join("")}

                    </section>
                    `
                    : ""
                }

            </div>

        `;

    }


    /* =====================================================
       PRINT
    ===================================================== */

    const printResumeBtn =
        $("#printResumeBtn");

    if (printResumeBtn) {

        printResumeBtn.addEventListener(
            "click",
            () => {

                window.print();

            }
        );

    }


    /* =====================================================
       CLEAR
    ===================================================== */

    const clearResumeBtn =
        $("#clearResumeBtn");

    if (clearResumeBtn) {

        clearResumeBtn.addEventListener(
            "click",
            () => {

                const confirmClear =
                    confirm(
                        "Clear your complete resume?"
                    );


                if (!confirmClear)
                    return;


                $$(
                    ".resume-builder-page input, " +
                    ".resume-builder-page textarea"
                )
                .forEach(el => {

                    el.value = "";

                });


                $$(
                    ".resume-builder-page select"
                )
                .forEach(el => {

                    el.selectedIndex = 0;

                });


                updateResumeProgress();

                updateSummaryCounter();

                showToast(
                    "Resume cleared."
                );

            }
        );

    }


    /* =====================================================
       SAVE DRAFT LOCAL STORAGE
    ===================================================== */

    const saveDraftBtn =
        $("#saveDraftBtn");

    if (saveDraftBtn) {

        saveDraftBtn.addEventListener(
            "click",
            () => {

                const data =
                    collectResumeData();


                localStorage.setItem(
                    "ai_resume_draft",
                    JSON.stringify(data)
                );


                showToast(
                    "💾 Draft saved successfully!"
                );

            }
        );

    }


    const saveResumeBtn =
        $("#saveResumeBtn");

    if (saveResumeBtn) {

        saveResumeBtn.addEventListener(
            "click",
            () => {

                const data =
                    collectResumeData();


                localStorage.setItem(
                    "ai_resume_draft",
                    JSON.stringify(data)
                );


                showToast(
                    "💾 Resume saved!"
                );

            }
        );

    }


    /* =====================================================
       LOAD DRAFT
    ===================================================== */

    function loadDraft() {

        const saved =
            localStorage.getItem(
                "ai_resume_draft"
            );


        if (!saved) return;


        try {

            const data =
                JSON.parse(saved);


            if (
                data.personal
            ) {

                setValue(
                    "fullName",
                    data.personal.full_name
                );

                setValue(
                    "professionalTitle",
                    data.personal.professional_title
                );

                setValue(
                    "location",
                    data.personal.location
                );

                setValue(
                    "email",
                    data.personal.email
                );

                setValue(
                    "phone",
                    data.personal.phone
                );

                setValue(
                    "linkedin",
                    data.personal.linkedin
                );

                setValue(
                    "github",
                    data.personal.github
                );

                setValue(
                    "portfolio",
                    data.personal.portfolio
                );

            }


            setValue(
                "professionalSummary",
                data.summary
            );


            setValue(
                "targetJobTitle",
                data.target_job?.title
            );

            setValue(
                "targetIndustry",
                data.target_job?.industry
            );

            setValue(
                "jobDescription",
                data.target_job?.description
            );


            setValue(
                "languages",
                data.additional?.languages
            );

            setValue(
                "coursework",
                data.additional?.coursework
            );

            setValue(
                "interests",
                data.additional?.interests
            );


            updateSummaryCounter();

            updateResumeProgress();


        }

        catch(error) {

            console.error(
                "Draft loading error:",
                error
            );

        }

    }


    /* =====================================================
       DOWNLOAD
    ===================================================== */

    const downloadResumeBtn =
        $("#downloadResumeBtn");

    if (downloadResumeBtn) {

        downloadResumeBtn.addEventListener(
            "click",
            () => {

                generatePreview();

                setTimeout(
                    () => {
                        window.print();
                    },
                    200
                );

            }
        );

    }


    /* =====================================================
       UTILITIES
    ===================================================== */

    function setText(id, text) {

        const el =
            document.getElementById(id);

        if (el)
            el.textContent =
                text;

    }


    function setValue(id, value) {

        const el =
            document.getElementById(id);

        if (
            el &&
            value !== undefined &&
            value !== null
        ) {

            el.value = value;

        }

    }


    function renderList(id, items) {

        const list =
            document.getElementById(id);

        if (!list) return;


        list.innerHTML = "";


        items.forEach(item => {

            const li =
                document.createElement(
                    "li"
                );

            li.textContent =
                item;

            list.appendChild(li);

        });

    }


    function renderKeywords(items) {

        const container =
            $("#missingKeywordsList");

        if (!container) return;


        container.innerHTML = "";


        items.forEach(keyword => {

            const span =
                document.createElement(
                    "span"
                );

            span.className =
                "keyword-tag";

            span.textContent =
                keyword;

            container.appendChild(
                span
            );

        });

    }


    function escapeHTML(text) {

        const div =
            document.createElement(
                "div"
            );

        div.textContent =
            text || "";

        return div.innerHTML;

    }


    /* =====================================================
       INPUT LISTENERS
    ===================================================== */

    document.addEventListener(
        "input",
        event => {

            if (
                event.target.matches(
                    ".resume-builder-page input, " +
                    ".resume-builder-page textarea"
                )
            ) {

                updateResumeProgress();

            }

        }
    );


    /* =====================================================
       INITIALIZE
    ===================================================== */

    loadDraft();

    updateSummaryCounter();

    updateResumeProgress();


    console.log(
        "✅ AI Resume Builder initialized"
    );

});
