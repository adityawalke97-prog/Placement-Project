/* ============================================================
   AI RESUME BUILDER
   resume_builder.js
   ============================================================ */

"use strict";

/* ============================================================
   GLOBAL HELPERS
   ============================================================ */

const $ = (selector, parent = document) =>
    parent.querySelector(selector);

const $$ = (selector, parent = document) =>
    [...parent.querySelectorAll(selector)];

let currentAIAction = null;


/* ============================================================
   DOM READY
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    initializeResumeBuilder();

});


function initializeResumeBuilder() {

    setupCounters();
    setupProgressTracking();
    setupDynamicSections();
    setupSkillButtons();
    setupAnswerButtons();
    setupModalEvents();
    setupPreview();
    setupSaveSystem();
    setupAIButtons();
    setupFinalActions();

    updateResumeProgress();

}


/* ============================================================
   TOAST
   ============================================================ */

function showToast(message, type = "success") {

    const toast = $("#resumeToast");

    if (!toast) return;

    toast.textContent = message;

    toast.className = "resume-toast";

    toast.classList.add(type);

    toast.classList.add("show");

    setTimeout(() => {

        toast.classList.remove("show");

    }, 3000);
}


/* ============================================================
   LOADING
   ============================================================ */

function showLoading(text = "Processing...") {

    const loading = $("#resumeLoading");

    if (!loading) return;

    const title = $("h3", loading);
    const description = $("p", loading);

    if (title) {
        title.textContent = text;
    }

    if (description) {
        description.textContent = "Please wait...";
    }

    loading.classList.add("show");
}


function hideLoading() {

    const loading = $("#resumeLoading");

    if (!loading) return;

    loading.classList.remove("show");

}


/* ============================================================
   TEXTAREA COUNTERS
   ============================================================ */

function setupCounters() {

    const summary = $("#professionalSummary");
    const counter = $("#summaryCounter");

    if (!summary || !counter) return;

    function updateCounter() {

        counter.textContent =
            `${summary.value.length} / 1000`;

    }

    summary.addEventListener("input", updateCounter);

    updateCounter();

}


/* ============================================================
   PROGRESS TRACKING
   ============================================================ */

function setupProgressTracking() {

    document.addEventListener("input", () => {

        updateResumeProgress();

    });

    document.addEventListener("change", () => {

        updateResumeProgress();

    });

}


function updateResumeProgress() {

    const checks = {

        contact:
            !!(
                getValue("#fullName") &&
                getValue("#email")
            ),

        summary:
            getValue("#professionalSummary").length > 20,

        education:
            hasFilledField("input[name='degree[]']"),

        skills:
            hasSkill(),

        projects:
            hasFilledField("input[name='project_name[]']"),

        experience:
            hasFilledField("input[name='job_title[]']")

    };


    updateChecklist("checkContact", checks.contact);
    updateChecklist("checkSummary", checks.summary);
    updateChecklist("checkEducation", checks.education);
    updateChecklist("checkSkills", checks.skills);
    updateChecklist("checkProjects", checks.projects);
    updateChecklist("checkExperience", checks.experience);


    const completed =
        Object.values(checks).filter(Boolean).length;

    const percentage =
        Math.round((completed / 6) * 100);


    const fill = $("#mainProgressFill");
    const text = $("#completionText");
    const score = $("#completionScore");


    if (fill) {

        fill.style.width = `${percentage}%`;

    }

    if (text) {

        text.textContent =
            `${percentage}% Complete`;

    }

    if (score) {

        score.textContent =
            `${percentage}%`;

    }

}


function updateChecklist(id, completed) {

    const element = document.getElementById(id);

    if (!element) return;

    const icon = $("span", element);

    if (completed) {

        element.classList.add("completed");

        if (icon) {
            icon.textContent = "✓";
        }

    } else {

        element.classList.remove("completed");

        if (icon) {
            icon.textContent = "○";
        }

    }

}


function hasFilledField(selector) {

    return $$(selector).some(input =>
        input.value.trim() !== ""
    );

}


function hasSkill() {

    return $$(
        ".skill-inputs input"
    ).some(input =>
        input.value.trim() !== ""
    );

}


/* ============================================================
   GET VALUE
   ============================================================ */

function getValue(selector) {

    const element = $(selector);

    return element
        ? element.value.trim()
        : "";

}


/* ============================================================
   DYNAMIC EDUCATION / EXPERIENCE / PROJECTS
   ============================================================ */

function setupDynamicSections() {

    const educationBtn =
        $("#addEducationBtn");

    const experienceBtn =
        $("#addExperienceBtn");

    const projectBtn =
        $("#addProjectBtn");

    const certificationBtn =
        $("#addCertificationBtn");

    const achievementBtn =
        $("#addAchievementBtn");


    if (educationBtn) {

        educationBtn.addEventListener(
            "click",
            addEducation
        );

    }


    if (experienceBtn) {

        experienceBtn.addEventListener(
            "click",
            addExperience
        );

    }


    if (projectBtn) {

        projectBtn.addEventListener(
            "click",
            addProject
        );

    }


    if (certificationBtn) {

        certificationBtn.addEventListener(
            "click",
            addCertification
        );

    }


    if (achievementBtn) {

        achievementBtn.addEventListener(
            "click",
            addAchievement
        );

    }


    document.addEventListener(
        "click",
        handleRemove
    );

}


/* ============================================================
   EDUCATION
   ============================================================ */

function addEducation() {

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


/* ============================================================
   EXPERIENCE
   ============================================================ */

function addExperience() {

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
                    placeholder="Describe your responsibilities and achievements..."></textarea>

            </div>

        </div>

        <button
            type="button"
            class="ai-bullet-btn improveExperienceBtn">

            ✨ Improve Experience Bullets

        </button>
    `;

    container.appendChild(item);

    updateResumeProgress();

}


/* ============================================================
   PROJECT
   ============================================================ */

function addProject() {

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

                <label>Project Name</label>

                <input
                    type="text"
                    name="project_name[]"
                    placeholder="Project Name">

            </div>

            <div class="form-group">

                <label>Project Type</label>

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

                <label>GitHub URL</label>

                <input
                    type="url"
                    name="project_github[]"
                    placeholder="https://github.com/...">

            </div>

            <div class="form-group">

                <label>Live Demo</label>

                <input
                    type="url"
                    name="project_demo[]"
                    placeholder="https://...">

            </div>

            <div class="form-group full">

                <label>Technologies</label>

                <input
                    type="text"
                    name="project_technologies[]"
                    placeholder="Flask, MySQL, JavaScript">

            </div>

            <div class="form-group full">

                <label>Project Description</label>

                <textarea
                    name="project_description[]"
                    rows="6"
                    placeholder="Describe your project..."></textarea>

            </div>

        </div>

        <button
            type="button"
            class="ai-bullet-btn improveProjectBtn">

            ✨ Improve Project Description

        </button>
    `;

    container.appendChild(item);

    updateResumeProgress();

}


/* ============================================================
   CERTIFICATION
   ============================================================ */

function addCertification() {

    const container =
        $("#certificationContainer");

    if (!container) return;

    const item =
        document.createElement("div");

    item.className =
        "dynamic-item";

    item.innerHTML = `

        <div class="dynamic-item-header">

            <strong>
                Certification
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
                    Certification Name
                </label>

                <input
                    type="text"
                    name="certification_name[]"
                    placeholder="Certification">

            </div>

            <div class="form-group">

                <label>
                    Issuing Organization
                </label>

                <input
                    type="text"
                    name="certification_org[]"
                    placeholder="Organization">

            </div>

            <div class="form-group">

                <label>
                    Year
                </label>

                <input
                    type="text"
                    name="certification_year[]"
                    placeholder="2026">

            </div>

            <div class="form-group">

                <label>
                    Credential URL
                </label>

                <input
                    type="url"
                    name="certification_url[]"
                    placeholder="https://...">

            </div>

        </div>
    `;

    container.appendChild(item);

}


/* ============================================================
   ACHIEVEMENT
   ============================================================ */

function addAchievement() {

    const container =
        $("#achievementContainer");

    if (!container) return;

    const item =
        document.createElement("div");

    item.className =
        "dynamic-item";

    item.innerHTML = `

        <div class="dynamic-item-header">

            <strong>
                Achievement
            </strong>

            <button
                type="button"
                class="remove-btn">

                🗑

            </button>

        </div>

        <div class="form-group">

            <label>
                Achievement
            </label>

            <textarea
                name="achievement[]"
                rows="3"
                placeholder="Describe your achievement..."></textarea>

        </div>
    `;

    container.appendChild(item);

}


/* ============================================================
   REMOVE DYNAMIC ITEMS
   ============================================================ */

function handleRemove(event) {

    const button =
        event.target.closest(".remove-btn");

    if (!button) return;

    const item =
        button.closest(".dynamic-item");

    if (!item) return;

    const container =
        item.parentElement;

    const items =
        container.querySelectorAll(
            ".dynamic-item"
        );

    /*
       Keep first item.
       Additional items can be removed.
    */

    if (items.length <= 1) {

        item.querySelectorAll("input, textarea")
            .forEach(input => {
                input.value = "";
            });

        return;
    }

    item.remove();

    updateResumeProgress();

}


/* ============================================================
   SKILLS
   ============================================================ */

function setupSkillButtons() {

    $$(".add-skill-btn")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => addSkill(button)
            );

        });

}


function addSkill(button) {

    const category =
        button.dataset.category;

    const map = {

        programming:
            "#programmingSkills",

        frameworks:
            "#frameworkSkills",

        database:
            "#databaseSkills",

        tools:
            "#toolSkills"

    };

    const container =
        $(map[category]);

    if (!container) return;

    const input =
        document.createElement("input");

    input.type = "text";

    input.name =
        `${getSkillName(category)}[]`;

    input.placeholder =
        "Add skill";

    container.appendChild(input);

    input.focus();

    updateResumeProgress();

}


function getSkillName(category) {

    const names = {

        programming:
            "programming_skills",

        frameworks:
            "framework_skills",

        database:
            "database_skills",

        tools:
            "tool_skills"

    };

    return names[category] || "skills";

}


/* ============================================================
   AI BUTTON SETUP
   ============================================================ */

function setupAIButtons() {

    const improveSummaryBtn =
        $("#improveSummaryBtn");

    const analyzeJobBtn =
        $("#analyzeJobBtn");

    const suggestSkillsBtn =
        $("#suggestSkillsBtn");

    const verifyBtn =
        $("#verifyResumeBtn");

    const tailorBtn =
        $("#tailorResumeBtn");

    const missingKeywordsBtn =
        $("#missingKeywordsBtn");

    const achievementBtn =
        $("#generateAchievementBtn");

    const suggestionsBtn =
        $("#resumeSuggestionsBtn");


    if (improveSummaryBtn) {

        improveSummaryBtn.addEventListener(
            "click",
            improveSummary
        );

    }


    if (analyzeJobBtn) {

        analyzeJobBtn.addEventListener(
            "click",
            analyzeJob
        );

    }


    if (suggestSkillsBtn) {

        suggestSkillsBtn.addEventListener(
            "click",
            suggestSkills
        );

    }


    if (verifyBtn) {

        verifyBtn.addEventListener(
            "click",
            verifyResume
        );

    }


    if (tailorBtn) {

        tailorBtn.addEventListener(
            "click",
            tailorResume
        );

    }


    if (missingKeywordsBtn) {

        missingKeywordsBtn.addEventListener(
            "click",
            findMissingKeywords
        );

    }


    if (achievementBtn) {

        achievementBtn.addEventListener(
            "click",
            generateAchievement
        );

    }


    if (suggestionsBtn) {

        suggestionsBtn.addEventListener(
            "click",
            getResumeSuggestions
        );


    }


    document.addEventListener(
        "click",
        handleDynamicAIButtons
    );

}


/* ============================================================
   DYNAMIC AI BUTTONS
   ============================================================ */

function handleDynamicAIButtons(event) {

    const experienceBtn =
        event.target.closest(
            ".improveExperienceBtn"
        );

    const projectBtn =
        event.target.closest(
            ".improveProjectBtn"
        );


    if (experienceBtn) {

        improveExperience(
            experienceBtn
        );

    }


    if (projectBtn) {

        improveProject(
            projectBtn
        );

    }

}


/* ============================================================
   COLLECT RESUME DATA
   ============================================================ */

function collectResumeData() {

    const education = $$(
        ".education-item"
    ).map(item => ({

        degree:
            getItemValue(
                item,
                "input[name='degree[]']"
            ),

        institution:
            getItemValue(
                item,
                "input[name='institution[]']"
            ),

        start:
            getItemValue(
                item,
                "input[name='education_start[]']"
            ),

        end:
            getItemValue(
                item,
                "input[name='education_end[]']"
            ),

        grade:
            getItemValue(
                item,
                "input[name='grade[]']"
            ),

        location:
            getItemValue(
                item,
                "input[name='education_location[]']"
            )

    }));


    const experience = $$(
        ".experience-item"
    ).map(item => ({

        job_title:
            getItemValue(
                item,
                "input[name='job_title[]']"
            ),

        company:
            getItemValue(
                item,
                "input[name='company[]']"
            ),

        start:
            getItemValue(
                item,
                "input[name='experience_start[]']"
            ),

        end:
            getItemValue(
                item,
                "input[name='experience_end[]']"
            ),

        description:
            getItemValue(
                item,
                "textarea[name='experience_description[]']"
            )

    }));


    const projects = $$(
        ".project-item"
    ).map(item => ({

        name:
            getItemValue(
                item,
                "input[name='project_name[]']"
            ),

        type:
            getItemValue(
                item,
                "select[name='project_type[]']"
            ),

        github:
            getItemValue(
                item,
                "input[name='project_github[]']"
            ),

        demo:
            getItemValue(
                item,
                "input[name='project_demo[]']"
            ),

        technologies:
            getItemValue(
                item,
                "input[name='project_technologies[]']"
            ),

        description:
            getItemValue(
                item,
                "textarea[name='project_description[]']"
            )

    }));


    const certifications =
        $$(
            "#certificationContainer .dynamic-item"
        ).map(item => ({

            name:
                getItemValue(
                    item,
                    "input[name='certification_name[]']"
                ),

            organization:
                getItemValue(
                    item,
                    "input[name='certification_org[]']"
                ),

            year:
                getItemValue(
                    item,
                    "input[name='certification_year[]']"
                ),

            url:
                getItemValue(
                    item,
                    "input[name='certification_url[]']"
                )

        }));


    const achievements =
        $$(
            "#achievementContainer textarea[name='achievement[]']"
        ).map(
            textarea =>
                textarea.value.trim()
        );


    const skills = {

        programming:
            getValues(
                "input[name='programming_skills[]']"
            ),

        frameworks:
            getValues(
                "input[name='framework_skills[]']"
            ),

        database:
            getValues(
                "input[name='database_skills[]']"
            ),

        tools:
            getValues(
                "input[name='tool_skills[]']"
            )

    };


    return {

        personal: {

            full_name:
                getValue("#fullName"),

            professional_title:
                getValue("#professionalTitle"),

            location:
                getValue("#location"),

            email:
                getValue("#email"),

            phone:
                getValue("#phone"),

            linkedin:
                getValue("#linkedin"),

            github:
                getValue("#github"),

            portfolio:
                getValue("#portfolio")

        },

        summary:
            getValue("#professionalSummary"),

        target_job: {

            title:
                getValue("#targetJobTitle"),

            industry:
                getValue("#targetIndustry"),

            description:
                getValue("#jobDescription")

        },

        education,

        skills,

        experience,

        projects,

        certifications,

        achievements,

        additional: {

            languages:
                getValue("#languages"),

            coursework:
                getValue("#coursework"),

            interests:
                getValue("#interests")

        }

    };

}


function getItemValue(item, selector) {

    const element =
        $(selector, item);

    return element
        ? element.value.trim()
        : "";

}


function getValues(selector) {

    return $$(selector)
        .map(input => input.value.trim())
        .filter(Boolean);

}


/* ============================================================
   GENERIC AI REQUEST
   ============================================================ */

async function callAI(endpoint, payload) {

    showLoading("AI is working...");

    try {

        const response =
            await fetch(endpoint, {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json",

                    "Accept":
                        "application/json"

                },

                body:
                    JSON.stringify(payload)

            });


        let data;

        try {

            data =
                await response.json();

        } catch {

            throw new Error(
                "Server returned an invalid response."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                "AI request failed."
            );

        }


        return data;

    } catch (error) {

        console.error(
            "AI Error:",
            error
        );

        showToast(
            error.message ||
            "AI service unavailable.",
            "error"
        );

        return null;

    } finally {

        hideLoading();

    }

}


/* ============================================================
   IMPROVE SUMMARY
   ============================================================ */

async function improveSummary() {

    const summary =
        getValue("#professionalSummary");

    const job =
        getValue("#targetJobTitle");

    const description =
        getValue("#jobDescription");


    if (!summary) {

        showToast(
            "First write your summary.",
            "warning"
        );

        return;

    }


    const result =
        await callAI(
            "/api/resume/improve-summary",
            {

                summary,

                target_job: job,

                job_description:
                    description

            }
        );


    if (!result) return;


    const improved =
        result.improved_summary ||
        result.summary ||
        result.result;


    if (improved) {

        $("#professionalSummary").value =
            improved;

        $("#professionalSummary")
            .dispatchEvent(
                new Event("input")
            );

        showToast(
            "✨ Summary improved successfully!"
        );

    }

}


/* ============================================================
   ANALYZE JOB
   ============================================================ */

async function analyzeJob() {

    const jobDescription =
        getValue("#jobDescription");


    if (!jobDescription) {

        showToast(
            "Paste the job description first.",
            "warning"
        );

        return;

    }


    const result =
        await callAI(
            "/api/resume/analyze-job",
            {

                job_title:
                    getValue("#targetJobTitle"),

                job_description:
                    jobDescription,

                resume:
                    collectResumeData()

            }
        );


    if (!result) return;


    displayJobAnalysis(result);

}


function displayJobAnalysis(result) {

    const keywords =
        result.keywords ||
        result.required_skills ||
        [];

    const message = [

        `Keywords: ${keywords.join(", ")}`,

        result.summary
            ? `\n\n${result.summary}`
            : "",

        result.experience
            ? `\n\nExperience: ${result.experience}`
            : ""

    ].join("");


    showAIResult(
        "🎯 Job Analysis",
        message
    );

}


/* ============================================================
   SUGGEST SKILLS
   ============================================================ */

async function suggestSkills() {

    const job =
        getValue("#targetJobTitle");

    const industry =
        getValue("#targetIndustry");


    if (!job) {

        showToast(
            "Enter your target job title first.",
            "warning"
        );

        return;

    }


    const result =
        await callAI(
            "/api/resume/suggest-skills",
            {

                target_job:
                    job,

                industry,

                resume:
                    collectResumeData()

            }
        );


    if (!result) return;


    const skills =
        result.skills ||
        result.suggestions ||
        [];


    showAIResult(
        "💡 AI Skill Suggestions",
        Array.isArray(skills)
            ? skills.join("\n")
            : String(skills)
    );

}


/* ============================================================
   IMPROVE EXPERIENCE
   ============================================================ */

async function improveExperience(button) {

    const item =
        button.closest(
            ".experience-item"
        );

    if (!item) return;


    const description =
        getItemValue(
