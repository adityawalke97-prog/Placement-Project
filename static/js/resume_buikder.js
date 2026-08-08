/* ============================================================
   ADVANCED AI RESUME BUILDER
   Placement Training Portal
   ============================================================ */

"use strict";

document.addEventListener("DOMContentLoaded", () => {

    /* ========================================================
       CONFIG
    ======================================================== */

    const CONFIG = {
        storageKey: "placement_resume_draft_v2",

        maxSkills: 30,
        maxProjects: 10,
        maxExperience: 10,
        maxEducation: 6,

        aiEndpoint: "/api/verify-resume",

        debounceDelay: 250
    };


    /* ========================================================
       HELPERS
    ======================================================== */

    const $ = (selector, parent = document) =>
        parent.querySelector(selector);

    const $$ = (selector, parent = document) =>
        [...parent.querySelectorAll(selector)];


    function escapeHTML(value) {

        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function showToast(message, type = "success") {

        let toast = $("#resumeToast");

        if (!toast) {

            toast = document.createElement("div");

            toast.id = "resumeToast";

            document.body.appendChild(toast);
        }

        toast.className = `resume-toast ${type}`;

        toast.textContent = message;

        toast.classList.add("show");

        clearTimeout(toast.timer);

        toast.timer = setTimeout(() => {
            toast.classList.remove("show");
        }, 3000);
    }


    function debounce(fn, delay = CONFIG.debounceDelay) {

        let timer;

        return (...args) => {

            clearTimeout(timer);

            timer = setTimeout(() => {
                fn(...args);
            }, delay);
        };
    }


    /* ========================================================
       FORM ELEMENTS
       ======================================================== */

    const resumeForm = $("#resumeForm");

    const preview = $("#resumePreview");

    const photoInput = $("#profilePhoto");

    const photoPreview = $("#photoPreview");

    const saveBtn = $("#saveResumeBtn");

    const loadBtn = $("#loadResumeBtn");

    const clearBtn = $("#clearResumeBtn");

    const downloadBtn = $("#downloadResumeBtn");

    const printBtn = $("#printResumeBtn");

    const aiVerifyBtn = $("#aiVerifyBtn");

    const atsScoreElement = $("#atsScore");

    const completenessElement = $("#resumeCompleteness");


    /* ========================================================
       INITIALIZE
       ======================================================== */

    function init() {

        loadDraft();

        setupDynamicSections();

        setupPhotoUpload();

        setupAutoSave();

        setupButtons();

        setupInputListeners();

        updatePreview();

        calculateATSScore();

        calculateCompleteness();
    }


    /* ========================================================
       LIVE INPUT
       ======================================================== */

    function setupInputListeners() {

        if (!resumeForm) {
            return;
        }

        resumeForm.addEventListener("input", debounce(() => {

            updatePreview();

            calculateATSScore();

            calculateCompleteness();

            autoSave();

        }));


        resumeForm.addEventListener("change", () => {

            updatePreview();

            calculateATSScore();

            calculateCompleteness();

            autoSave();
        });
    }


    /* ========================================================
       PHOTO UPLOAD
       ======================================================== */

    function setupPhotoUpload() {

        if (!photoInput) {
            return;
        }

        photoInput.addEventListener("change", event => {

            const file = event.target.files[0];

            if (!file) {
                return;
            }

            if (!file.type.startsWith("image/")) {

                showToast(
                    "Please select a valid image.",
                    "error"
                );

                return;
            }

            if (file.size > 5 * 1024 * 1024) {

                showToast(
                    "Image should be below 5MB.",
                    "error"
                );

                return;
            }

            const reader = new FileReader();

            reader.onload = e => {

                if (photoPreview) {
                    photoPreview.src = e.target.result;
                }

                localStorage.setItem(
                    "resume_profile_photo",
                    e.target.result
                );

                updatePreview();
            };

            reader.readAsDataURL(file);
        });


        const savedPhoto =
            localStorage.getItem("resume_profile_photo");

        if (savedPhoto && photoPreview) {
            photoPreview.src = savedPhoto;
        }
    }


    /* ========================================================
       DYNAMIC SECTION SETUP
       ======================================================== */

    function setupDynamicSections() {

        setupRepeater(
            "#experienceContainer",
            "#addExperienceBtn",
            ".experience-item",
            CONFIG.maxExperience
        );

        setupRepeater(
            "#educationContainer",
            "#addEducationBtn",
            ".education-item",
            CONFIG.maxEducation
        );

        setupRepeater(
            "#projectsContainer",
            "#addProjectBtn",
            ".project-item",
            CONFIG.maxProjects
        );

        setupRepeater(
            "#skillsContainer",
            "#addSkillBtn",
            ".skill-item",
            CONFIG.maxSkills
        );
    }


    function setupRepeater(
        containerSelector,
        addButtonSelector,
        itemSelector,
        maxItems
    ) {

        const container = $(containerSelector);

        const addButton = $(addButtonSelector);

        if (!container || !addButton) {
            return;
        }


        addButton.addEventListener("click", () => {

            const items =
                $$(itemSelector, container);

            if (items.length >= maxItems) {

                showToast(
                    `Maximum ${maxItems} items allowed.`,
                    "warning"
                );

                return;
            }

            const firstItem = items[0];

            if (!firstItem) {
                return;
            }

            const newItem =
                firstItem.cloneNode(true);

            $$("input, textarea, select", newItem)
                .forEach(input => {

                    input.value = "";

                    if (
                        input.type === "checkbox" ||
                        input.type === "radio"
                    ) {
                        input.checked = false;
                    }
                });


            const removeBtn =
                $(".remove-item-btn", newItem);

            if (removeBtn) {

                removeBtn.addEventListener(
                    "click",
                    () => {

                        if (
                            $$(itemSelector, container).length <= 1
                        ) {

                            showToast(
                                "At least one section is required.",
                                "warning"
                            );

                            return;
                        }

                        newItem.remove();

                        updatePreview();

                        calculateATSScore();

                        calculateCompleteness();

                        autoSave();
                    }
                );
            }


            container.appendChild(newItem);

            updatePreview();

            autoSave();
        });


        $$(itemSelector, container)
            .forEach(item => {

                const removeBtn =
                    $(".remove-item-btn", item);

                if (!removeBtn) {
                    return;
                }

                removeBtn.addEventListener(
                    "click",
                    () => {

                        if (
                            $$(itemSelector, container).length <= 1
                        ) {

                            showToast(
                                "At least one section is required.",
                                "warning"
                            );

                            return;
                        }

                        item.remove();

                        updatePreview();

                        calculateATSScore();

                        calculateCompleteness();

                        autoSave();
                    }
                );
            });
    }


    /* ========================================================
       GET FORM DATA
       ======================================================== */

    function getResumeData() {

        if (!resumeForm) {
            return {};
        }

        const data = {};

        const fields =
            $$("[name]", resumeForm);


        fields.forEach(field => {

            if (
                field.type === "checkbox"
            ) {

                data[field.name] =
                    field.checked;

                return;
            }


            if (
                field.type === "radio"
            ) {

                if (field.checked) {
                    data[field.name] =
                        field.value;
                }

                return;
            }


            data[field.name] =
                field.value.trim();
        });


        data.experience =
            collectRepeaterData(
                "#experienceContainer",
                ".experience-item"
            );


        data.education =
            collectRepeaterData(
                "#educationContainer",
                ".education-item"
            );


        data.projects =
            collectRepeaterData(
                "#projectsContainer",
                ".project-item"
            );


        data.skills =
            collectRepeaterData(
                "#skillsContainer",
                ".skill-item"
            );


        return data;
    }


    function collectRepeaterData(
        containerSelector,
        itemSelector
    ) {

        const container =
            $(containerSelector);

        if (!container) {
            return [];
        }

        return $$(itemSelector, container)
            .map(item => {

                const result = {};

                $$("[name]", item)
                    .forEach(field => {

                        result[field.name] =
                            field.value.trim();
                    });

                return result;
            });
    }


    /* ========================================================
       UPDATE PREVIEW
       ======================================================== */

    function updatePreview() {

        if (!preview) {
            return;
        }

        const data =
            getResumeData();


        const setText = (
            selector,
            value,
            fallback = ""
        ) => {

            const element =
                $(selector, preview);

            if (!element) {
                return;
            }

            element.textContent =
                value || fallback;
        };


        /* BASIC INFORMATION */

        setText(
            ".preview-name",
            data.full_name,
            "Your Name"
        );


        setText(
            ".preview-role",
            data.job_title,
            "Software Developer"
        );


        setText(
            ".preview-email",
            data.email
        );


        setText(
            ".preview-phone",
            data.phone
        );


        setText(
            ".preview-location",
            data.location
        );


        setText(
            ".preview-linkedin",
            data.linkedin
        );


        setText(
            ".preview-github",
            data.github
        );


        setText(
            ".preview-summary",
            data.summary
        );


        /* ====================================================
           SKILLS
           ==================================================== */

        const skillsContainer =
            $(".preview-skills", preview);


        if (skillsContainer) {

            skillsContainer.innerHTML = "";

            data.skills.forEach(skill => {

                const value =
                    skill.skill ||
                    skill.name ||
                    skill.skills;

                if (!value) {
                    return;
                }

                const span =
                    document.createElement("span");

                span.className = "preview-skill";

                span.textContent = value;

                skillsContainer.appendChild(span);
            });
        }


        /* ====================================================
           EXPERIENCE
           ==================================================== */

        renderExperience(data.experience);


        /* ====================================================
           EDUCATION
           ==================================================== */

        renderEducation(data.education);


        /* ====================================================
           PROJECTS
           ==================================================== */

        renderProjects(data.projects);
    }


    /* ========================================================
       EXPERIENCE PREVIEW
       ======================================================== */

    function renderExperience(items) {

        const container =
            $(".preview-experience", preview);

        if (!container) {
            return;
        }

        container.innerHTML = "";


        items.forEach(item => {

            const role =
                item.job_title ||
                item.position ||
                item.role;

            const company =
                item.company;

            const start =
                item.start_date ||
                item.start;

            const end =
                item.end_date ||
                item.end ||
                "Present";

            const description =
                item.description;


            if (!role && !company) {
                return;
            }


            const article =
                document.createElement("article");

            article.className =
                "preview-experience-item";


            article.innerHTML = `
                <div class="preview-item-header">

                    <div>
                        <h4>
                            ${escapeHTML(role)}
                        </h4>

                        <strong>
                            ${escapeHTML(company)}
                        </strong>
                    </div>

                    <span>
                        ${escapeHTML(start)}
                        -
                        ${escapeHTML(end)}
                    </span>

                </div>

                ${
                    description
                    ?
                    `<p>
                        ${escapeHTML(description)}
                    </p>`
                    :
                    ""
                }
            `;


            container.appendChild(article);
        });
    }


    /* ========================================================
       EDUCATION PREVIEW
       ======================================================== */

    function renderEducation(items) {

        const container =
            $(".preview-education", preview);

        if (!container) {
            return;
        }

        container.innerHTML = "";


        items.forEach(item => {

            const degree =
                item.degree ||
                item.course;

            const institution =
                item.institution ||
                item.college ||
                item.university;

            const year =
                item.graduation_year ||
                item.year;

            const score =
                item.cgpa ||
                item.percentage;


            if (!degree && !institution) {
                return;
            }


            const article =
                document.createElement("article");

            article.className =
                "preview-education-item";


            article.innerHTML = `
                <div class="preview-item-header">

                    <div>

                        <h4>
                            ${escapeHTML(degree)}
                        </h4>

                        <strong>
                            ${escapeHTML(institution)}
                        </strong>

                    </div>

                    <span>
                        ${escapeHTML(year)}
                    </span>

                </div>

                ${
                    score
                    ?
                    `<p>Score: ${escapeHTML(score)}</p>`
                    :
                    ""
                }
            `;


            container.appendChild(article);
        });
    }


    /* ========================================================
       PROJECT PREVIEW
       ======================================================== */

    function renderProjects(items) {

        const container =
            $(".preview-projects", preview);

        if (!container) {
            return;
        }

        container.innerHTML = "";


        items.forEach(item => {

            const title =
                item.project_name ||
                item.name ||
                item.title;

            const tech =
                item.technologies ||
                item.tech_stack;

            const description =
                item.description;

            const link =
                item.project_link ||
                item.github;


            if (!title) {
                return;
            }


            const article =
                document.createElement("article");

            article.className =
                "preview-project-item";


            article.innerHTML = `
                <h4>
                    ${escapeHTML(title)}
                </h4>

                ${
                    tech
                    ?
                    `<div class="project-tech">
                        ${escapeHTML(tech)}
                    </div>`
                    :
                    ""
                }

                ${
                    description
                    ?
                    `<p>
                        ${escapeHTML(description)}
                    </p>`
                    :
                    ""
                }

                ${
                    link
                    ?
                    `<a
                        href="${escapeHTML(link)}"
                        target="_blank"
                        rel="noopener">
                        Project Link
                    </a>`
                    :
                    ""
                }
            `;


            container.appendChild(article);
        });
    }


    /* ========================================================
       ATS SCORE
       ======================================================== */

    function calculateATSScore() {

        const data =
            getResumeData();


        let score = 0;

        const checks = {

            name:
                Boolean(data.full_name),

            email:
                Boolean(data.email),

            phone:
                Boolean(data.phone),

            location:
                Boolean(data.location),

            summary:
                Boolean(data.summary),

            skills:
                data.skills?.length > 0,

            education:
                data.education?.length > 0,

            experience:
                data.experience?.length > 0,

            projects:
                data.projects?.length > 0,

            linkedin:
                Boolean(data.linkedin),

            github:
                Boolean(data.github)
        };


        const weights = {

            name: 5,
            email: 5,
            phone: 5,
            location: 3,
            summary: 12,
            skills: 15,
            education: 12,
            experience: 15,
            projects: 13,
            linkedin: 5,
            github: 5
        };


        Object.keys(checks)
            .forEach(key => {

                if (checks[key]) {
                    score += weights[key];
                }
            });


        score =
            Math.min(100, Math.round(score));


        if (atsScoreElement) {

            atsScoreElement.textContent =
                `${score}%`;

            atsScoreElement.dataset.score =
                score;


            atsScoreElement.classList.remove(
                "low",
                "medium",
                "good",
                "excellent"
            );


            if (score < 40) {
                atsScoreElement.classList.add("low");
            }
            else if (score < 65) {
                atsScoreElement.classList.add("medium");
            }
            else if (score < 85) {
                atsScoreElement.classList.add("good");
            }
            else {
                atsScoreElement.classList.add("excellent");
            }
        }


        updateATSMessage(score);

        return score;
    }


    function updateATSMessage(score) {

        const element =
            $("#atsMessage");

        if (!element) {
            return;
        }


        if (score < 40) {

            element.textContent =
                "Your resume needs more information.";

        }
        else if (score < 65) {

            element.textContent =
                "Good start. Add more relevant sections.";

        }
        else if (score < 85) {

            element.textContent =
                "Strong resume. A few improvements can help.";

        }
        else {

            element.textContent =
                "Excellent! Your resume is well structured.";
        }
    }


    /* ========================================================
       COMPLETENESS
       ======================================================== */

    function calculateCompleteness() {

        const data =
            getResumeData();


        const required = [

            data.full_name,

            data.email,

            data.phone,

            data.summary,

            data.skills?.length,

            data.education?.length,

            data.projects?.length
        ];


        const completed =
            required.filter(Boolean).length;


        const percentage =
            Math.round(
                (completed / required.length) * 100
            );


        if (completenessElement) {

            completenessElement.textContent =
                `${percentage}%`;
        }


        const progress =
            $("#completenessFill");

        if (progress) {

            progress.style.width =
                `${percentage}%`;
        }


        return percentage;
    }


    /* ========================================================
       KEYWORD ANALYSIS
       ======================================================== */

    function analyzeKeywords() {

        const data =
            getResumeData();


        const text = [

            data.summary,

            ...(data.skills || [])
                .map(x =>
                    x.skill ||
                    x.name ||
                    x.skills ||
                    ""
                ),

            ...(data.projects || [])
                .map(x =>
                    `${x.description || ""}
                     ${x.technologies || ""}
                     ${x.tech_stack || ""}`
                ),

            ...(data.experience || [])
                .map(x =>
                    x.description || ""
                )

        ]
            .join(" ")
            .toLowerCase();


        const keywords = [

            "java",
            "python",
            "javascript",
            "typescript",
            "react",
            "angular",
            "node",
            "node.js",
            "flask",
            "django",
            "spring",
            "sql",
            "mysql",
            "mongodb",
            "git",
            "github",
            "rest api",
            "api",
            "aws",
            "azure",
            "docker",
            "kubernetes",
            "html",
            "css",
            "machine learning",
            "ai",
            "data structures",
            "algorithms",
            "oops",
            "object oriented",
            "communication",
            "problem solving"
        ];


        const found =
            keywords.filter(keyword =>
                text.includes(keyword)
            );


        const missing =
            keywords.filter(keyword =>
                !text.includes(keyword)
            );


        return {
            found,
            missing
        };
    }


    /* ========================================================
       AI RESUME VERIFICATION
       ======================================================== */

    async function verifyWithAI() {

        if (!aiVerifyBtn) {
            return;
        }


        const data =
            getResumeData();


        const atsScore =
            calculateATSScore();


        const completeness =
            calculateCompleteness();


        const keywords =
            analyzeKeywords();


        aiVerifyBtn.disabled = true;

        const oldText =
            aiVerifyBtn.innerHTML;

        aiVerifyBtn.innerHTML =
            "🤖 AI Analyzing...";


        showToast(
            "AI is analyzing your resume...",
            "info"
        );


        try {

            const response =
                await fetch(
                    CONFIG.aiEndpoint,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            resume: data,

                            ats_score:
                                atsScore,

                            completeness:
                                completeness,

                            keywords:
                                keywords
                        })
                    }
                );


            if (!response.ok) {

                throw new Error(
                    `Server error: ${response.status}`
                );
            }


            const result =
                await response.json();


            displayAIResults(result);


            showToast(
                "AI verification completed!",
                "success"
            );


        }
        catch (error) {

            console.error(
                "AI verification error:",
                error
            );


            showToast(
                "AI verification failed. Check backend endpoint.",
                "error"
            );

        }
        finally {

            aiVerifyBtn.disabled =
                false;

            aiVerifyBtn.innerHTML =
                oldText;
        }
    }


    /* ========================================================
       DISPLAY AI RESULTS
       ======================================================== */

    function displayAIResults(result) {

        const panel =
            $("#aiVerificationResult");

        if (!panel) {
            return;
        }


        panel.style.display =
            "block";


        const score =
            result.score ??
            result.ats_score ??
            calculateATSScore();


        const summary =
            result.summary ??
            "Resume analysis completed.";


        const strengths =
            result.strengths || [];


        const weaknesses =
            result.weaknesses ||
            result.improvements ||
            [];


        const keywords =
            result.keywords ||
            result.recommended_keywords ||
            [];


        panel.innerHTML = `

            <div class="ai-result-header">

                <div>

                    <span class="ai-label">
                        🤖 AI Resume Verification
                    </span>

                    <h3>
                        Resume Score:
                        ${escapeHTML(score)}%
                    </h3>

                </div>

            </div>


            <div class="ai-summary">

                <strong>
                    AI Summary
                </strong>

                <p>
                    ${escapeHTML(summary)}
                </p>

            </div>


            ${
                strengths.length
                ?
                `
                <div class="ai-result-section">

                    <h4>
                        ✅ Strengths
                    </h4>

                    <ul>
                        ${
                            strengths
                            .map(item =>
                                `<li>
                                    ${escapeHTML(item)}
                                </li>`
                            )
                            .join("")
                        }
                    </ul>

                </div>
                `
                :
                ""
            }


            ${
                weaknesses.length
                ?
                `
                <div class="ai-result-section">

                    <h4>
                        ⚠️ Improvements
                    </h4>

                    <ul>
                        ${
                            weaknesses
                            .map(item =>
                                `<li>
                                    ${escapeHTML(item)}
                                </li>`
                            )
                            .join("")
                        }
                    </ul>

                </div>
                `
                :
                ""
            }


            ${
                keywords.length
                ?
                `
                <div class="ai-result-section">

                    <h4>
                        🔑 Recommended Keywords
                    </h4>

                    <div class="ai-keywords">

                        ${
                            keywords
                            .map(keyword =>
                                `<span>
                                    ${escapeHTML(keyword)}
                                </span>`
                            )
                            .join("")
                        }

                    </div>

                </div>
                `
                :
                ""
            }

        `;


        panel.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }


    /* ========================================================
       LOCAL STORAGE
       ======================================================== */

    function autoSave() {

        try {

            const data =
                getResumeData();


            localStorage.setItem(
                CONFIG.storageKey,
                JSON.stringify(data)
            );


            updateSaveStatus(
                "Saved automatically"
            );

        }
        catch (error) {

            console.error(
                "Auto-save failed:",
                error
            );
        }
    }


    function saveDraft() {

        try {

            const data =
                getResumeData();


            localStorage.setItem(
                CONFIG.storageKey,
                JSON.stringify(data)
            );


            updateSaveStatus(
                "Saved just now"
            );


            showToast(
                "Resume saved successfully.",
                "success"
            );

        }
        catch (error) {

            showToast(
                "Unable to save resume.",
                "error"
            );
        }
    }


    function loadDraft() {

        try {

            const saved =
                localStorage.getItem(
                    CONFIG.storageKey
                );


            if (!saved) {
                return;
            }


            const data =
                JSON.parse(saved);


            restoreSimpleFields(data);

            restoreRepeater(
                "#experienceContainer",
                ".experience-item",
                data.experience
            );

            restoreRepeater(
                "#educationContainer",
                ".education-item",
                data.education
            );

            restoreRepeater(
                "#projectsContainer",
                ".project-item",
                data.projects
            );

            restoreRepeater(
                "#skillsContainer",
                ".skill-item",
                data.skills
            );


            updateSaveStatus(
                "Draft restored"
            );


        }
        catch (error) {

            console.error(
                "Draft load failed:",
                error
            );
        }
    }


    function restoreSimpleFields(data) {

        if (!resumeForm) {
            return;
        }


        $$("[name]", resumeForm)
            .forEach(field => {

                if (
                    field.closest(
                        ".experience-item, .education-item, .project-item, .skill-item"
                    )
                ) {
                    return;
                }


                if (
                    field.type === "checkbox"
                ) {

                    field.checked =
                        Boolean(data[field.name]);

                }
                else if (
                    field.type !== "file"
                ) {

                    field.value =
                        data[field.name] || "";
                }
            });
    }


    function restoreRepeater(
        containerSelector,
        itemSelector,
        items
    ) {

        if (!items || !items.length) {
            return;
        }


        const container =
            $(containerSelector);


        if (!container) {
            return;
        }


        const template =
            $(itemSelector, container);


        if (!template) {
            return;
        }


        container.innerHTML = "";


        items.forEach(itemData => {

            const item =
                template.cloneNode(true);


            $$("[name]", item)
                .forEach(field => {

                    field.value =
                        itemData[field.name] || "";
                });


            container.appendChild(item);


            const removeBtn =
                $(".remove-item-btn", item);


            if (removeBtn) {

                removeBtn.addEventListener(
                    "click",
                    () => {

                        item.remove();

                        updatePreview();

                        calculateATSScore();

                        calculateCompleteness();

                        autoSave();
                    }
                );
            }
        });
    }


    function updateSaveStatus(message) {

        const status =
            $("#saveStatus");

        if (status) {
            status.textContent =
                message;
        }
    }


    /* ========================================================
       CLEAR DRAFT
       ======================================================== */

    function clearDraft() {

        const confirmed =
            confirm(
                "Are you sure you want to clear your resume draft?"
            );


        if (!confirmed) {
            return;
        }


        localStorage.removeItem(
            CONFIG.storageKey
        );

        localStorage.removeItem(
            "resume_profile_photo"
        );


        if (resumeForm) {
            resumeForm.reset();
        }


        updatePreview();

        calculateATSScore();

        calculateCompleteness();


        showToast(
            "Resume draft cleared.",
            "success"
        );
    }


    /* ========================================================
       DOWNLOAD / PRINT
       ======================================================== */

    function downloadResume() {

        if (!preview) {
            showToast(
                "Resume preview not found.",
                "error"
            );

            return;
        }


        window.print();
    }


    function printResume() {

        if (!preview) {
            return;
        }

        window.print();
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    function setupButtons() {

        if (saveBtn) {

            saveBtn.addEventListener(
                "click",
                saveDraft
            );
        }


        if (loadBtn) {

            loadBtn.addEventListener(
                "click",
                () => {

                    loadDraft();

                    updatePreview();

                    calculateATSScore();

                    calculateCompleteness();

                    showToast(
                        "Saved resume loaded.",
                        "success"
                    );
                }
            );
        }


        if (clearBtn) {

            clearBtn.addEventListener(
                "click",
                clearDraft
            );
        }


        if (downloadBtn) {

            downloadBtn.addEventListener(
                "click",
                downloadResume
            );
        }


        if (printBtn) {

            printBtn.addEventListener(
                "click",
                printResume
            );
        }


        if (aiVerifyBtn) {

            aiVerifyBtn.addEventListener(
                "click",
                verifyWithAI
            );
        }
    }


    /* ========================================================
       COPY RESUME TEXT
       ======================================================== */

    const copyResumeBtn =
        $("#copyResumeBtn");


    if (copyResumeBtn) {

        copyResumeBtn.addEventListener(
            "click",
            async () => {

                const data =
                    getResumeData();


                const text = buildPlainText(data);


                try {

                    await navigator.clipboard.writeText(
                        text
                    );


                    showToast(
                        "Resume copied to clipboard.",
                        "success"
                    );

                }
                catch {

                    showToast(
                        "Copy failed.",
                        "error"
                    );
                }
            }
        );
    }


    function buildPlainText(data) {

        const sections = [];


        sections.push(
            data.full_name || ""
        );


        sections.push(
            data.job_title || ""
        );


        sections.push(
            [
                data.email,
                data.phone,
                data.location,
                data.linkedin,
                data.github
            ]
            .filter(Boolean)
            .join(" | ")
        );


        if (data.summary) {

            sections.push(
                `SUMMARY\n${data.summary}`
            );
        }


        if (data.skills?.length) {

            sections.push(
                `SKILLS\n${
                    data.skills
                    .map(x =>
                        x.skill ||
                        x.name ||
                        x.skills ||
                        ""
                    )
                    .filter(Boolean)
                    .join(", ")
                }`
            );
        }


        if (data.experience?.length) {

            const experience =
                data.experience
                    .map(item => {

                        return [

                            item.job_title ||
                            item.position ||
                            item.role,

                            item.company,

                            item.start_date,

                            item.end_date,

                            item.description

                        ]
                        .filter(Boolean)
                        .join("\n");
                    })
                    .join("\n\n");


            sections.push(
                `EXPERIENCE\n${experience}`
            );
        }


        if (data.projects?.length) {

            const projects =
                data.projects
                    .map(item => {

                        return [

                            item.project_name ||
                            item.name ||
                            item.title,

                            item.technologies ||
                            item.tech_stack,

                            item.description,

                            item.project_link ||
                            item.github

                        ]
                        .filter(Boolean)
                        .join("\n");
                    })
                    .join("\n\n");


            sections.push(
                `PROJECTS\n${projects}`
            );
        }


        if (data.education?.length) {

            const education =
                data.education
                    .map(item => {

                        return [

                            item.degree ||
                            item.course,

                            item.institution ||
                            item.college,

                            item.graduation_year ||
                            item.year,

                            item.cgpa ||
                            item.percentage

                        ]
                        .filter(Boolean)
                        .join("\n");
                    })
                    .join("\n\n");


            sections.push(
                `EDUCATION\n${education}`
            );
        }


        return sections
            .filter(Boolean)
            .join("\n\n");
    }


    /* ========================================================
       KEYBOARD SHORTCUTS
       ======================================================== */

    document.addEventListener(
        "keydown",
        event => {

            if (
                (event.ctrlKey || event.metaKey) &&
                event.key.toLowerCase() === "s"
            ) {

                event.preventDefault();

                saveDraft();
            }


            if (
                (event.ctrlKey || event.metaKey) &&
                event.key.toLowerCase() === "p"
            ) {

                event.preventDefault();

                printResume();
            }
        }
    );


    /* ========================================================
       SECTION TOGGLE
       ======================================================== */

    $$(".section-toggle")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const target =
                        button.dataset.target;


                    if (!target) {
                        return;
                    }


                    const section =
                        $(target);


                    if (!section) {
                        return;
                    }


                    section.classList.toggle(
                        "collapsed"
                    );


                    button.classList.toggle(
                        "active"
                    );
                }
            );
        });


    /* ========================================================
       CHARACTER COUNTERS
       ======================================================== */

    $$("[data-maxlength]")
        .forEach(input => {

            const counter =
                document.querySelector(
                    `[data-counter="${input.id}"]`
                );


            if (!counter) {
                return;
            }


            const updateCounter = () => {

                const max =
                    Number(
                        input.dataset.maxlength
                    );


                const current =
                    input.value.length;


                counter.textContent =
                    `${current}/${max}`;


                counter.classList.toggle(
                    "limit-warning",
                    current > max * 0.85
                );
            };


            input.addEventListener(
                "input",
                updateCounter
            );


            updateCounter();
        });


    /* ========================================================
       URL VALIDATION
       ======================================================== */

    $$(
        'input[type="url"]'
    )
    .forEach(input => {

        input.addEventListener(
            "blur",
            () => {

                if (
                    input.value &&
                    !isValidURL(input.value)
                ) {

                    input.classList.add(
                        "input-error"
                    );

                    showToast(
                        "Please enter a valid URL.",
                        "warning"
                    );

                }
                else {

                    input.classList.remove(
                        "input-error"
                    );
                }
            }
        );
    });


    function isValidURL(value) {

        try {

            new URL(value);

            return true;

        }
        catch {

            return false;
        }
    }


    /* ========================================================
       EMAIL VALIDATION
       ======================================================== */

    const emailInput =
        $('input[name="email"]');


    if (emailInput) {

        emailInput.addEventListener(
            "blur",
            () => {

                const email =
                    emailInput.value.trim();


                if (
                    email &&
                    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/
                        .test(email)
                ) {

                    emailInput.classList.add(
                        "input-error"
                    );

                    showToast(
                        "Please enter a valid email.",
                        "warning"
                    );

                }
                else {

                    emailInput.classList.remove(
                        "input-error"
                    );
                }
            }
        );
    }


    /* ========================================================
       PHONE VALIDATION
       ======================================================== */

    const phoneInput =
        $('input[name="phone"]');


    if (phoneInput) {

        phoneInput.addEventListener(
            "input",
            () => {

                phoneInput.value =
                    phoneInput.value
                        .replace(/[^\d+\-\s()]/g, "")
                        .slice(0, 20);
            }
        );
    }


    /* ========================================================
       INITIAL RUN
       ======================================================== */

    init();

});
