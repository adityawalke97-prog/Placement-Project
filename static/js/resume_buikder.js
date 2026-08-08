/* ============================================================
   AI RESUME BUILDER
   Complete Frontend JavaScript
============================================================ */

"use strict";

document.addEventListener("DOMContentLoaded", () => {

    /* ========================================================
       HELPERS
    ======================================================== */

    const $ = (selector, parent = document) =>
        parent.querySelector(selector);

    const $$ = (selector, parent = document) =>
        [...parent.querySelectorAll(selector)];


    function getValue(id) {

        const element = document.getElementById(id);

        return element
            ? element.value.trim()
            : "";
    }


    function setValue(id, value) {

        const element = document.getElementById(id);

        if (element) {
            element.value = value || "";
        }
    }


    /* ========================================================
       TOAST
    ======================================================== */

    window.showResumeToast = function(message, type = "success") {

        const toast = $("#resumeToast");

        if (!toast) return;

        toast.textContent = message;

        toast.className =
            `resume-toast show ${type}`;

        clearTimeout(window.resumeToastTimer);

        window.resumeToastTimer =
            setTimeout(() => {

                toast.classList.remove("show");

            }, 3500);
    };


    /* ========================================================
       LOADING
    ======================================================== */

    window.showResumeLoading = function() {

        const loader = $("#resumeLoading");

        if (!loader) return;

        loader.classList.add("active");

        loader.style.display = "flex";
    };


    window.hideResumeLoading = function() {

        const loader = $("#resumeLoading");

        if (!loader) return;

        loader.classList.remove("active");

        loader.style.display = "none";
    };


    /* ========================================================
       API CALL
    ======================================================== */

    async function callResumeAI(endpoint, data) {

        showResumeLoading();

        try {

            const response = await fetch(endpoint, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(data)

            });


            let result;

            try {

                result = await response.json();

            } catch {

                throw new Error(
                    "Invalid server response."
                );

            }


            if (!response.ok || !result.success) {

                throw new Error(
                    result.error ||
                    "AI request failed."
                );

            }


            return result;


        } catch (error) {

            console.error(
                "Resume AI Error:",
                error
            );

            showResumeToast(
                error.message ||
                "AI service unavailable.",
                "error"
            );

            return null;


        } finally {

            hideResumeLoading();

        }

    }


    /* ========================================================
       COLLECT RESUME TEXT
    ======================================================== */

    window.collectResumeText = function() {

        const sections = [];

        const fullName = getValue("fullName");

        if (fullName)
            sections.push(`Name: ${fullName}`);


        const title =
            getValue("professionalTitle");

        if (title)
            sections.push(`Title: ${title}`);


        const summary =
            getValue("professionalSummary");

        if (summary)
            sections.push(
                `Professional Summary:\n${summary}`
            );


        /* EDUCATION */

        $$(
            "#educationContainer .education-item"
        ).forEach(item => {

            const values =
                $$("input", item)
                .map(input => input.value.trim())
                .filter(Boolean);

            if (values.length) {

                sections.push(
                    `Education:\n${values.join(" | ")}`
                );

            }

        });


        /* SKILLS */

        const skillInputs =
            $$(".skill-inputs input");

        const skills =
            skillInputs
                .map(input => input.value.trim())
                .filter(Boolean);

        if (skills.length) {

            sections.push(
                `Technical Skills:\n${skills.join(", ")}`
            );

        }


        /* EXPERIENCE */

        $$(
            "#experienceContainer .experience-item"
        ).forEach(item => {

            const values =
                $$("input, textarea", item)
                .map(input => input.value.trim())
                .filter(Boolean);

            if (values.length) {

                sections.push(
                    `Experience:\n${values.join("\n")}`
                );

            }

        });


        /* PROJECTS */

        $$(
            "#projectsContainer .project-item"
        ).forEach(item => {

            const values =
                $$("input, textarea, select", item)
                .map(input => input.value.trim())
                .filter(Boolean);

            if (values.length) {

                sections.push(
                    `Project:\n${values.join("\n")}`
                );

            }

        });


        /* CERTIFICATIONS */

        $$(
            "#certificationContainer .dynamic-item"
        ).forEach(item => {

            const values =
                $$("input", item)
                .map(input => input.value.trim())
                .filter(Boolean);

            if (values.length) {

                sections.push(
                    `Certification:\n${values.join(" | ")}`
                );

            }

        });


        /* ACHIEVEMENTS */

        $$(
            "#achievementContainer .dynamic-item"
        ).forEach(item => {

            const values =
                $$("textarea", item)
                .map(input => input.value.trim())
                .filter(Boolean);

            if (values.length) {

                sections.push(
                    `Achievement:\n${values.join("\n")}`
                );

            }

        });


        /* ADDITIONAL */

        const languages =
            getValue("languages");

        if (languages)
            sections.push(
                `Languages: ${languages}`
            );


        const coursework =
            getValue("coursework");

        if (coursework)
            sections.push(
                `Coursework: ${coursework}`
            );


        const interests =
            getValue("interests");

        if (interests)
            sections.push(
                `Interests: ${interests}`
            );


        return sections.join("\n\n");

    };


    /* ========================================================
       SUMMARY COUNTER
    ======================================================== */

    const summary =
        $("#professionalSummary");

    const summaryCounter =
        $("#summaryCounter");


    function updateSummaryCounter() {

        if (!summary || !summaryCounter)
            return;

        summaryCounter.textContent =
            `${summary.value.length} / 1000`;

    }


    summary?.addEventListener(
        "input",
        updateSummaryCounter
    );


    /* ========================================================
       COMPLETION
    ======================================================== */

    window.updateResumeProgress = function() {

        let completed = 0;

        const total = 6;


        /* CONTACT */

        if (
            getValue("fullName") &&
            getValue("email")
        ) {

            completed++;

            markChecklist(
                "checkContact",
                true
            );

        } else {

            markChecklist(
                "checkContact",
                false
            );

        }


        /* SUMMARY */

        if (
            getValue("professionalSummary")
        ) {

            completed++;

            markChecklist(
                "checkSummary",
                true
            );

        } else {

            markChecklist(
                "checkSummary",
                false
            );

        }


        /* EDUCATION */

        if (
            $$("#educationContainer input")
                .some(input =>
                    input.value.trim()
                )
        ) {

            completed++;

            markChecklist(
                "checkEducation",
                true
            );

        } else {

            markChecklist(
                "checkEducation",
                false
            );

        }


        /* SKILLS */

        if (
            $$(".skill-inputs input")
                .some(input =>
                    input.value.trim()
                )
        ) {

            completed++;

            markChecklist(
                "checkSkills",
                true
            );

        } else {

            markChecklist(
                "checkSkills",
                false
            );

        }


        /* PROJECTS */

        if (
            $$("#projectsContainer input, #projectsContainer textarea")
                .some(input =>
                    input.value.trim()
                )
        ) {

            completed++;

            markChecklist(
                "checkProjects",
                true
            );

        } else {

            markChecklist(
                "checkProjects",
                false
            );

        }


        /* EXPERIENCE */

        if (
            $$("#experienceContainer input, #experienceContainer textarea")
                .some(input =>
                    input.value.trim()
                )
        ) {

            completed++;

            markChecklist(
                "checkExperience",
                true
            );

        } else {

            markChecklist(
                "checkExperience",
                false
            );

        }


        const percentage =
            Math.round(
                (completed / total) * 100
            );


        const progressText =
            $("#completionText");

        if (progressText) {

            progressText.textContent =
                `${percentage}% Complete`;

        }


        const score =
            $("#completionScore");

        if (score) {

            score.textContent =
                `${percentage}%`;

        }


        const fill =
            $("#mainProgressFill");

        if (fill) {

            fill.style.width =
                `${percentage}%`;

        }


        return percentage;

    };


    function markChecklist(id, complete) {

        const item =
            document.getElementById(id);

        if (!item) return;

        item.classList.toggle(
            "completed",
            complete
        );


        const icon =
            $("span", item);

        if (icon) {

            icon.textContent =
                complete ? "✓" : "○";

        }

    }


    /* ========================================================
       AI — IMPROVE SUMMARY
    ======================================================== */

    $("#improveSummaryBtn")
        ?.addEventListener(
            "click",
            async () => {

                const summary =
                    getValue(
                        "professionalSummary"
                    );

                const targetJob =
                    getValue(
                        "targetJobTitle"
                    ) ||
                    "Software Engineer";


                if (!summary) {

                    showResumeToast(
                        "Write your summary first.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/improve-summary",
                        {
                            summary,
                            target_job: targetJob
                        }
                    );


                if (!result)
                    return;


                setValue(
                    "professionalSummary",
                    result.result
                );


                updateSummaryCounter();

                updateResumeProgress();


                showResumeToast(
                    "✨ Summary improved!",
                    "success"
                );

            }
        );


    /* ========================================================
       AI — ANALYZE JOB
    ======================================================== */

    $("#analyzeJobBtn")
        ?.addEventListener(
            "click",
            async () => {

                const jobDescription =
                    getValue(
                        "jobDescription"
                    );


                if (!jobDescription) {

                    showResumeToast(
                        "Paste a job description first.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/analyze-job",
                        {
                            resume_text:
                                collectResumeText(),

                            job_description:
                                jobDescription
                        }
                    );


                if (!result)
                    return;


                showJobAnalysis(result);

            }
        );


    function showJobAnalysis(result) {

        const score =
            result.match_score ?? 0;

        const missing =
            result.missing_keywords || [];

        const strengths =
            result.strengths || [];

        const improvements =
            result.improvements || [];


        console.log(
            "AI JOB ANALYSIS",
            result
        );


        showResumeToast(
            `🎯 Job Match: ${score}%`,
            score >= 70
                ? "success"
                : "warning"
        );


        console.table({
            "Match Score": score,
            "Keyword Score":
                result.keyword_score,
            "Skills Score":
                result.skills_score,
            "Content Score":
                result.content_score
        });


        console.log(
            "Missing Keywords:",
            missing
        );

        console.log(
            "Strengths:",
            strengths
        );

        console.log(
            "Improvements:",
            improvements
        );

    }


    /* ========================================================
       AI — SUGGEST SKILLS
    ======================================================== */

    $("#suggestSkillsBtn")
        ?.addEventListener(
            "click",
            async () => {

                const targetJob =
                    getValue(
                        "targetJobTitle"
                    );

                const jobDescription =
                    getValue(
                        "jobDescription"
                    );


                if (
                    !targetJob &&
                    !jobDescription
                ) {

                    showResumeToast(
                        "Enter target job or job description.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/suggest-skills",
                        {
                            target_job:
                                targetJob,

                            job_description:
                                jobDescription
                        }
                    );


                if (!result)
                    return;


                addSuggestedSkills(
                    result.skills || []
                );

            }
        );


    function addSuggestedSkills(skills) {

        if (!skills.length) {

            showResumeToast(
                "No new skills found.",
                "info"
            );

            return;

        }


        const container =
            $("#programmingSkills");

        if (!container)
            return;


        skills.forEach(skill => {

            if (!skill)
                return;


            const exists =
                $$("input", container)
                    .some(input =>
                        input.value
                            .toLowerCase() ===
                        skill.toLowerCase()
                    );


            if (exists)
                return;


            const input =
                document.createElement(
                    "input"
                );


            input.type = "text";

            input.name =
                "programming_skills[]";

            input.value =
                skill;

            input.placeholder =
                "AI Suggested Skill";


            container.appendChild(
                input
            );

        });


        updateResumeProgress();


        showResumeToast(
            `💡 ${skills.length} skills suggested!`,
            "success"
        );

    }


    /* ========================================================
       AI — IMPROVE EXPERIENCE
    ======================================================== */

    document.addEventListener(
        "click",
        async event => {

            const button =
                event.target.closest(
                    ".improveExperienceBtn"
                );


            if (!button)
                return;


            const item =
                button.closest(
                    ".experience-item"
                );


            if (!item)
                return;


            const textarea =
                $("textarea", item);


            if (!textarea?.value.trim()) {

                showResumeToast(
                    "Enter experience details first.",
                    "error"
                );

                return;

            }


            const result =
                await callResumeAI(
                    "/api/resume/improve-experience",
                    {
                        description:
                            textarea.value,

                        target_job:
                            getValue(
                                "targetJobTitle"
                            ) ||
                            "Software Engineer"
                    }
                );


            if (!result)
                return;


            textarea.value =
                result.result;


            updateResumeProgress();


            showResumeToast(
                "💼 Experience improved!",
                "success"
            );

        }
    );


    /* ========================================================
       AI — IMPROVE PROJECT
    ======================================================== */

    document.addEventListener(
        "click",
        async event => {

            const button =
                event.target.closest(
                    ".improveProjectBtn"
                );


            if (!button)
                return;


            const item =
                button.closest(
                    ".project-item"
                );


            if (!item)
                return;


            const textarea =
                $("textarea", item);


            const inputs =
                $$("input", item);


            if (!textarea?.value.trim()) {

                showResumeToast(
                    "Enter project description first.",
                    "error"
                );

                return;

            }


            const projectName =
                inputs[0]?.value || "";


            const technologies =
                inputs
                    .find(input =>
                        input.name ===
                        "project_technologies[]"
                    )?.value || "";


            const result =
                await callResumeAI(
                    "/api/resume/improve-project",
                    {
                        description:
                            textarea.value,

                        project_name:
                            projectName,

                        technologies:
                            technologies
                    }
                );


            if (!result)
                return;


            textarea.value =
                result.result;


            updateResumeProgress();


            showResumeToast(
                "🚀 Project improved!",
                "success"
            );

        }
    );


    /* ========================================================
       AI — VERIFY RESUME
    ======================================================== */

    $("#verifyResumeBtn")
        ?.addEventListener(
            "click",
            async () => {

                const resumeText =
                    collectResumeText();


                if (!resumeText.trim()) {

                    showResumeToast(
                        "Add resume information first.",
                        "error"
                    );

                    return;

                }


                openModal(
                    "verificationModal"
                );


                const loading =
                    $("#verificationLoading");

                const resultBox =
                    $("#verificationResult");


                if (loading)
                    loading.style.display =
                        "block";


                if (resultBox)
                    resultBox.style.display =
                        "none";


                const result =
                    await callResumeAI(
                        "/api/resume/verify",
                        {
                            resume_text:
                                resumeText,

                            job_description:
                                getValue(
                                    "jobDescription"
                                )
                        }
                    );


                if (!result)
                    return;


                displayVerificationResult(
                    result
                );

            }
        );


    function displayVerificationResult(
        result
    ) {

        const loading =
            $("#verificationLoading");

        const resultBox =
            $("#verificationResult");


        if (loading)
            loading.style.display =
                "none";


        if (resultBox)
            resultBox.style.display =
                "block";


        setText(
            "verificationScore",
            result.score ?? 0
        );


        setText(
            "keywordScore",
            `${result.keyword_score ?? 0}%`
        );


        setText(
            "contentScore",
            `${result.content_score ?? 0}%`
        );


        setText(
            "formatScore",
            `${result.format_score ?? 0}%`
        );


        setText(
            "skillsScore",
            `${result.skills_score ?? 0}%`
        );


        setText(
            "atsScore",
            result.score ?? 0
        );


        const progress =
            $("#atsProgressFill");

        if (progress) {

            progress.style.width =
                `${result.score ?? 0}%`;

        }


        const status =
            $("#atsStatus");

        if (status) {

            const score =
                result.score ?? 0;


            if (score >= 80) {

                status.textContent =
                    "Excellent ATS readiness!";

            } else if (score >= 60) {

                status.textContent =
                    "Good resume. Some improvements recommended.";

            } else {

                status.textContent =
                    "Your resume needs improvement.";

            }

        }


        fillList(
            "strengthsList",
            result.strengths
        );


        fillList(
            "improvementsList",
            result.improvements
        );


        fillKeywords(
            "missingKeywordsList",
            result.missing_keywords
        );

    }


    function setText(id, value) {

        const element =
            document.getElementById(id);

        if (element)
            element.textContent =
                value;

    }


    function fillList(id, items) {

        const list =
            document.getElementById(id);

        if (!list)
            return;


        list.innerHTML = "";


        (items || []).forEach(item => {

            const li =
                document.createElement(
                    "li"
                );

            li.textContent =
                item;

            list.appendChild(li);

        });

    }


    function fillKeywords(id, items) {

        const container =
            document.getElementById(id);

        if (!container)
            return;


        container.innerHTML = "";


        (items || []).forEach(keyword => {

            const tag =
                document.createElement(
                    "span"
                );

            tag.className =
                "keyword-tag";

            tag.textContent =
                keyword;

            container.appendChild(tag);

        });

    }


    /* ========================================================
       AI — TAILOR RESUME
       Uses existing verification endpoint
    ======================================================== */

    $("#tailorResumeBtn")
        ?.addEventListener(
            "click",
            async () => {

                const resumeText =
                    collectResumeText();

                const jobDescription =
                    getValue(
                        "jobDescription"
                    );


                if (!resumeText) {

                    showResumeToast(
                        "Build your resume first.",
                        "error"
                    );

                    return;

                }


                if (!jobDescription) {

                    showResumeToast(
                        "Paste a job description first.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/analyze-job",
                        {
                            resume_text:
                                resumeText,

                            job_description:
                                jobDescription
                        }
                    );


                if (!result)
                    return;


                showJobAnalysis(result);


                showResumeToast(
                    "🎯 Resume tailoring analysis completed!",
                    "success"
                );

            }
        );


    /* ========================================================
       AI — MISSING KEYWORDS
    ======================================================== */

    $("#missingKeywordsBtn")
        ?.addEventListener(
            "click",
            async () => {

                const resumeText =
                    collectResumeText();

                const jobDescription =
                    getValue(
                        "jobDescription"
                    );


                if (!jobDescription) {

                    showResumeToast(
                        "Paste a job description first.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/analyze-job",
                        {
                            resume_text:
                                resumeText,

                            job_description:
                                jobDescription
                        }
                    );


                if (!result)
                    return;


                const missing =
                    result.missing_keywords ||
                    [];


                if (!missing.length) {

                    showResumeToast(
                        "🎉 No major missing keywords found!",
                        "success"
                    );

                    return;

                }


                console.log(
                    "Missing Keywords:",
                    missing
                );


                alert(
                    "Missing Keywords:\n\n" +
                    missing.join(", ")
                );

            }
        );


    /* ========================================================
       AI — GENERATE ACHIEVEMENT
    ======================================================== */

    $("#generateAchievementBtn")
        ?.addEventListener(
            "click",
            async () => {

                const context =
                    collectResumeText();


                if (!context) {

                    showResumeToast(
                        "Add some resume information first.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/generate-achievement",
                        {
                            context
                        }
                    );


                if (!result)
                    return;


                const container =
                    $("#achievementContainer");


                if (!container)
                    return;


                const item =
                    createAchievementItem(
                        result.result
                    );


                container.appendChild(
                    item
                );


                updateResumeProgress();


                showResumeToast(
                    "🏆 Achievement generated!",
                    "success"
                );

            }
        );


    function createAchievementItem(
        text
    ) {

        const wrapper =
            document.createElement(
                "div"
            );


        wrapper.className =
            "dynamic-item";


        wrapper.innerHTML = `

            <div class="form-group">

                <label>
                    AI Generated Achievement
                </label>

                <textarea
                    name="achievement[]"
                    rows="5"></textarea>

            </div>

        `;


        const textarea =
            $("textarea", wrapper);


        if (textarea)
            textarea.value =
                text;


        return wrapper;

    }


    /* ========================================================
       AI — RESUME SUGGESTIONS
    ======================================================== */

    $("#resumeSuggestionsBtn")
        ?.addEventListener(
            "click",
            async () => {

                const resumeText =
                    collectResumeText();


                if (!resumeText) {

                    showResumeToast(
                        "Add resume information first.",
                        "error"
                    );

                    return;

                }


                const result =
                    await callResumeAI(
                        "/api/resume/suggestions",
                        {
                            resume_text:
                                resumeText,

                            target_job:
                                getValue(
                                    "targetJobTitle"
                                )
                        }
                    );


                if (!result)
                    return;


                const suggestions =
                    result.suggestions ||
                    [];


                if (!suggestions.length) {

                    showResumeToast(
                        "No suggestions available.",
                        "info"
                    );

                    return;

                }


                alert(
                    "AI Resume Suggestions\n\n" +
                    suggestions
                        .map(
                            (item, index) =>
                                `${index + 1}. ${item}`
                        )
                        .join("\n\n")
                );

            }
        );


    /* ========================================================
       DYNAMIC EDUCATION
    ======================================================== */

    $("#addEducationBtn")
        ?.addEventListener(
            "click",
            () => {

                const container =
                    $("#educationContainer");

                if (!container)
                    return;


                const item =
                    document.createElement(
                        "div"
                    );


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


                container.appendChild(
                    item
                );

                updateResumeProgress();

            }
        );


    /* ========================================================
       DYNAMIC EXPERIENCE
    ======================================================== */

    $("#addExperienceBtn")
        ?.addEventListener(
            "click",
            () => {

                const container =
                    $("#experienceContainer");

                if (!container)
                    return;


                const item =
                    document.createElement(
                        "div"
                    );


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


                container.appendChild(
                    item
                );

                updateResumeProgress();

            }
        );


    /* ========================================================
       DYNAMIC PROJECT
    ======================================================== */

    $("#addProjectBtn")
        ?.addEventListener(
            "click",
            () => {

                const container =
                    $("#projectsContainer");

                if (!container)
                    return;


                const item =
                    document.createElement(
                        "div"
                    );


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
                                name="project_technologies[]"
                                placeholder="Flask, MySQL, JavaScript">
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


                container.appendChild(
                    item
                );

                updateResumeProgress();

            }
        );


    /* ========================================================
       DYNAMIC CERTIFICATION
    ======================================================== */

    $("#addCertificationBtn")
        ?.addEventListener(
            "click",
            () => {

                const container =
                    $("#certificationContainer");

                if (!container)
                    return;


                const item =
                    document.createElement(
                        "div"
                    );


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
                            <label>Certification Name</label>
                            <input
                                type="text"
                                name="certification_name[]">
                        </div>

                        <div class="form-group">
                            <label>Issuing Organization</label>
                            <input
                                type="text"
                                name="certification_org[]">
                        </div>

                        <div class="form-group">
                            <label>Year</label>
                            <input
                                type="text"
                                name="certification_year[]">
                        </div>

                        <div class="form-group">
                            <label>Credential URL</label>
                            <input
                                type="url"
                                name="certification_url[]">
                        </div>

                    </div>
                `;


                container.appendChild(
                    item
                );

            }
        );


    /* ========================================================
       DYNAMIC ACHIEVEMENT
    ======================================================== */

    $("#addAchievementBtn")
        ?.addEventListener(
            "click",
            () => {

                const container =
                    $("#achievementContainer");

                if (!container)
                    return;


                const item =
                    createAchievementItem(
                        ""
                    );


                container.appendChild(
                    item
                );


                updateResumeProgress();

            }
        );


    /* ========================================================
       REMOVE DYNAMIC ITEMS
    ======================================================== */

    document.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    ".remove-btn"
                );


            if (!button)
                return;


            const item =
                button.closest(
                    ".dynamic-item"
                );


            if (!item)
                return;


            const container =
                item.parentElement;


            const items =
                $$(".dynamic-item", container);


            /* Don't remove last item */

            if (items.length <= 1) {

                $$(
                    "input, textarea, select",
                    item
                ).forEach(field => {

                    field.value = "";

                });

            } else {

                item.remove();

            }


            updateResumeProgress();

        }
    );


    /* ========================================================
       ADD SKILL
    ======================================================== */

    $$(".add-skill-btn")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const category =
                        button.dataset.category;


                    const map = {

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
                            map[category]
                        );


                    if (!container)
                        return;


                    const input =
                        document.createElement(
                            "input"
                        );


                    input.type =
                        "text";


                    const names = {

                        programming:
                            "programming_skills[]",

                        frameworks:
                            "framework_skills[]",

                        database:
                            "database_skills[]",

                        tools:
                            "tool_skills[]"

                    };


                    input.name =
                        names[category];


                    input.placeholder =
                        "Add skill";


                    container.appendChild(
                        input
                    );


                    input.focus();

                }
            );

        });


    /* ========================================================
       LIVE INPUT LISTENER
    ======================================================== */

    document.addEventListener(
        "input",
        event => {

            if (
                event.target.matches(
                    "input, textarea, select"
                )
            ) {

                updateResumeProgress();

            }

        }
    );


    /* ========================================================
       SAVE DRAFT
    ======================================================== */

    function getResumeFormData() {

        const data = {};

        $$(
            "input, textarea, select"
        ).forEach(field => {

            if (!field.name)
                return;


            if (
                field.name.endsWith("[]")
            ) {

                const name =
                    field.name.slice(
                        0,
                        -2
                    );


                if (!data[name])
                    data[name] = [];


                data[name].push(
                    field.value
                );

            } else {

                data[field.name] =
                    field.value;

            }

        });


        return data;

    }


    function saveDraft() {

        const data =
            getResumeFormData();


        localStorage.setItem(
            "ai_resume_draft",
            JSON.stringify(data)
        );


        showResumeToast(
            "💾 Resume draft saved!",
            "success"
        );

    }


    $("#saveDraftBtn")
        ?.addEventListener(
            "click",
            saveDraft
        );


    $("#saveResumeBtn")
        ?.addEventListener(
            "click",
            saveDraft
        );


    /* ========================================================
       LOAD DRAFT
    ======================================================== */

    function loadDraft() {

        const saved =
            localStorage.getItem(
                "ai_resume_draft"
            );


        if (!saved)
            return;


        try {

            const data =
                JSON.parse(saved);


            Object.entries(data)
                .forEach(([name, value]) => {

                    const fields =
                        $$(
                            `[name="${name}"], [name="${name}[]"]`
                        );


                    if (!fields.length)
                        return;


                    if (Array.isArray(value)) {

                        value.forEach(
                            (item, index) => {

                                if (fields[index]) {

                                    fields[index]
                                        .value =
                                        item;

                                }

                            }
                        );

                    } else {

                        fields[0].value =
                            value;

                    }

                });


            updateSummaryCounter();

            updateResumeProgress();


        } catch (error) {

            console.error(
                "Draft loading failed:",
                error
            );

        }

    }


    loadDraft();


    /* ========================================================
       CLEAR RESUME
    ======================================================== */

    $("#clearResumeBtn")
        ?.addEventListener(
            "click",
            () => {

                const confirmed =
                    confirm(
                        "Clear the entire resume?"
                    );


                if (!confirmed)
                    return;


                $$(
                    "input, textarea, select"
                ).forEach(field => {

                    field.value = "";

                });


                localStorage.removeItem(
                    "ai_resume_draft"
                );


                updateSummaryCounter();

                updateResumeProgress();


                showResumeToast(
                    "🗑 Resume cleared.",
                    "success"
                );

            }
        );


    /* ========================================================
       PREVIEW
    ======================================================== */

    $("#previewResumeBtn")
        ?.addEventListener(
            "click",
            () => {

                generatePreview();

                openModal(
                    "previewModal"
                );

            }
        );


    function generatePreview() {

        const preview =
            $("#resumePreview");


        if (!preview)
            return;


        const name =
            getValue("fullName") ||
            "Your Name";


        const title =
            getValue(
                "professionalTitle"
            );


        const email =
            getValue("email");


        const phone =
            getValue("phone");


        const location =
            getValue("location");


        const linkedin =
            getValue("linkedin");


        const github =
            getValue("github");


        const summary =
            getValue(
                "professionalSummary"
            );


        let html = `

            <div class="generated-resume">

                <header>

                    <h1>
                        ${escapeHTML(name)}
                    </h1>

                    ${
                        title
                        ? `<h2>${escapeHTML(title)}</h2>`
                        : ""
                    }

                    <div class="resume-contact">

                        ${
                            email
                            ? escapeHTML(email)
                            : ""
                        }

                        ${
                            phone
                            ? " | " +
                              escapeHTML(phone)
                            : ""
                        }

                        ${
                            location
                            ? " | " +
                              escapeHTML(location)
                            : ""
                        }

                    </div>

                    <div class="resume-links">

                        ${
                            linkedin
                            ? `<a href="${escapeAttribute(linkedin)}" target="_blank">LinkedIn</a>`
                            : ""
                        }

                        ${
                            github
                            ? `<a href="${escapeAttribute(github)}" target="_blank">GitHub</a>`
                            : ""
                        }

                    </div>

                </header>

        `;


        if (summary) {

            html += `

                <section>

                    <h3>
                        PROFESSIONAL SUMMARY
                    </h3>

                    <p>
                        ${escapeHTML(summary)}
                    </p>

                </section>

            `;

        }


        /* SKILLS */

        const skills =
            $$(".skill-inputs input")
                .map(input =>
                    input.value.trim()
                )
                .filter(Boolean);


        if (skills.length) {

            html += `

                <section>

                    <h3>
                        TECHNICAL SKILLS
                    </h3>

                    <p>
                        ${skills
                            .map(escapeHTML)
                            .join(" • ")}
                    </p>

                </section>

            `;

        }


        /* EDUCATION */

        const educationItems =
            $$("#educationContainer .education-item");


        if (educationItems.length) {

            html += `
                <section>
                    <h3>EDUCATION</h3>
            `;


            educationItems.forEach(item => {

                const values =
                    $$(
                        "input",
                        item
                    )
                    .map(
                        input =>
                            input.value.trim()
                    )
                    .filter(Boolean);


                if (values.length) {

                    html += `
                        <div class="preview-item">
                            ${values
                                .map(escapeHTML)
                                .join(" | ")}
                        </div>
                    `;

                }

            });


            html += `</section>`;

        }


        /* EXPERIENCE */

        const experiences =
            $$("#experienceContainer .experience-item");


        if (experiences.length) {

            html += `
                <section>
                    <h3>EXPERIENCE</h3>
            `;


            experiences.forEach(item => {

                const values =
                    $$(
                        "input, textarea",
                        item
                    )
                    .map(
                        field =>
                            field.value.trim()
                    )
                    .filter(Boolean);


                if (values.length) {

                    html += `
                        <div class="preview-item">
                            ${values
                                .map(escapeHTML)
                                .join("<br>")}
                        </div>
                    `;

                }

            });


            html += `</section>`;

        }


        /* PROJECTS */

        const projects =
            $$("#projectsContainer .project-item");


        if (projects.length) {

            html += `
                <section>
                    <h3>PROJECTS</h3>
            `;


            projects.forEach(item => {

                const values =
                    $$(
                        "input, textarea, select",
                        item
                    )
                    .map(
                        field =>
                            field.value.trim()
                    )
                    .filter(Boolean);


                if (values.length) {

                    html += `
                        <div class="preview-item">
                            ${values
                                .map(escapeHTML)
                                .join("<br>")}
                        </div>
                    `;

                }

            });


            html += `</section>`;

        }


        /* CERTIFICATIONS */

        const certifications =
            $$("#certificationContainer .dynamic-item");


        if (certifications.length) {

            html += `
                <section>
                    <h3>CERTIFICATIONS</h3>
            `;


            certifications.forEach(item => {

                const values =
                    $$(
                        "input",
                        item
                    )
                    .map(
                        input =>
                            input.value.trim()
                    )
                    .filter(Boolean);


                if (values.length) {

                    html += `
                        <div class="preview-item">
                            ${values
                                .map(escapeHTML)
                                .join(" | ")}
                        </div>
                    `;

                }

            });


            html += `</section>`;

        }


        /* ACHIEVEMENTS */

        const achievements =
            $$("#achievementContainer textarea")
                .map(
                    textarea =>
                        textarea.value.trim()
                )
                .filter(Boolean);


        if (achievements.length) {

            html += `

                <section>

                    <h3>
                        ACHIEVEMENTS
                    </h3>

                    <ul>

                        ${achievements
                            .map(
                                item =>
                                    `<li>${escapeHTML(item)}</li>`
                            )
                            .join("")}

                    </ul>

                </section>

            `;

        }


        html += `
            </div>
        `;


        preview.innerHTML =
            html;

    }


    /* ========================================================
       GENERATE RESUME
    ======================================================== */

    $("#generateResumeBtn")
        ?.addEventListener(
            "click",
            () => {

                saveDraft();

                generatePreview();

                openModal(
                    "previewModal"
                );

                showResumeToast(
                    "🚀 Resume generated!",
                    "success"
                );

            }
        );


    /* ========================================================
       MODALS
    ======================================================== */

    function openModal(id) {

        const modal =
            document.getElementById(id);


        if (!modal)
            return;


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


        if (!modal)
            return;


        modal.classList.remove(
            "active"
        );

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );

    }


    document.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    "[data-close-modal]"
                );


            if (!button)
                return;


            closeModal(
                button.dataset.closeModal
            );

        }
    );


    document.addEventListener(
        "keydown",
        event => {

            if (event.key !== "Escape")
                return;


            $$(".resume-modal.active")
                .forEach(modal => {

                    closeModal(
                        modal.id
                    );

                });

        }
    );


    /* ========================================================
       PRINT
    ======================================================== */

    $("#printResumeBtn")
        ?.addEventListener(
            "click",
            () => {

                generatePreview();

                window.print();

            }
        );


    $("#downloadResumeBtn")
        ?.addEventListener(
            "click",
            () => {

                generatePreview();

                openModal(
                    "previewModal"
                );


                showResumeToast(
                    "Use Print → Save as PDF to download.",
                    "info"
                );

            }
        );


    /* ========================================================
       SAVE AUTO DRAFT
    ======================================================== */

    let autoSaveTimer;


    document.addEventListener(
        "input",
        () => {

            clearTimeout(
                autoSaveTimer
            );


            autoSaveTimer =
                setTimeout(
                    () => {

                        const data =
                            getResumeFormData();


                        localStorage.setItem(
                            "ai_resume_draft",
                            JSON.stringify(data)
                        );

                    },
                    1500
                );

        }
    );


    /* ========================================================
       ESCAPE HTML
    ======================================================== */

    function escapeHTML(value) {

        return String(value)
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );

    }


    function escapeAttribute(value) {

        return escapeHTML(value);

    }


    /* ========================================================
       INITIALIZE
    ======================================================== */

    updateSummaryCounter();

    updateResumeProgress();

    hideResumeLoading();


    console.log(
        "✅ AI Resume Builder initialized"
    );

});
