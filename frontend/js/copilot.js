// Career Copilot UI Controller for AutoJobApply

class CopilotController {
    constructor() {
        this.apiBase = "http://localhost:5010/api/copilot";
        this.userId = 1;
        this.init();
    }

    init() {
        injectSidebar('copilot');
    }

    async optimizeResume() {
        const kws = document.getElementById("res-keywords").value.split(",");
        const resumeText = document.getElementById("res-text").value;
        const box = document.getElementById("res-result");
        box.style.display = "block";

        if (!resumeText.trim()) {
            box.innerHTML = "Please paste your resume text first.";
            return;
        }

        box.innerHTML = "<span class='spinner'></span> Optimizing bullet points...";

        try {
            const res = await fetch(`${this.apiBase}/resume-optimize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: this.userId,
                    resume_text: resumeText,
                    keywords: kws
                })
            });
            const payload = await res.json();
            if (payload.success && payload.data) {
                const data = payload.data;
                box.innerHTML = `
                    <div style="font-weight:bold; color:#10b981; margin-bottom:8px;">✅ Resume Analysis Complete</div>
                    <div style="font-weight: 600;">Suggestions:</div>
                    <ul style="margin-left:16px; margin-top:4px;">
                        ${data.suggestions.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                `;
            }
        } catch (err) {
            box.textContent = "Failed to run optimizer.";
        }
    }

    async checkAts() {
        const desc = document.getElementById("ats-job-desc").value;
        const resumeText = document.getElementById("ats-resume-text").value;
        const box = document.getElementById("ats-result");
        box.style.display = "block";

        if (!resumeText.trim() || !desc.trim()) {
            box.innerHTML = "Please paste both your resume text and the job description.";
            return;
        }

        box.innerHTML = "<span class='spinner'></span> Analyzing keyword densities...";

        try {
            const res = await fetch(`${this.apiBase}/ats-score`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    resume_text: resumeText,
                    job_description: desc
                })
            });
            const payload = await res.json();
            if (payload.success && payload.data) {
                const data = payload.data;
                box.innerHTML = `
                    <div style="font-weight:bold; color:#3b82f6; margin-bottom:6px; font-size:14px;">ATS Score: ${data.ats_score}/100</div>
                    <div style="font-size:12px; color:var(--text-muted);">Keyword Match: ${data.keyword_match_rate}% | Readability: ${data.readability_score}%</div>
                    <div style="font-weight:600; margin-top:8px;">Improvement Checklist:</div>
                    <ul style="margin-left:16px; margin-top:4px;">
                        ${data.improvement_areas.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                `;
            }
        } catch (err) {
            box.textContent = "Failed to calculate ATS score.";
        }
    }

    async startInterview() {
        const type = document.getElementById("int-type").value;
        const box = document.getElementById("int-result");
        box.style.display = "block";
        box.innerHTML = "<span class='spinner'></span> Fetching simulation room QAs...";

        try {
            const res = await fetch(`${this.apiBase}/mock-interview`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: this.userId,
                    interview_type: type
                })
            });
            const payload = await res.json();
            if (payload.success && payload.data) {
                const questions = payload.data.questions;
                box.innerHTML = `
                    <div style="font-weight:bold; color:#f59e0b; margin-bottom:6px;">Mock Session Started</div>
                    ${questions.map((q, idx) => `
                        <div style="margin-bottom:8px;">
                            <div style="font-weight:600;">Q${idx+1}: ${q.question}</div>
                            <input type="text" class="form-control" style="margin-top:4px;" placeholder="Type your answer here...">
                        </div>
                    `).join('')}
                    <button class="btn btn-secondary btn-sm" onclick="showToast('Answers saved! Evaluation compiled.', 'success')">Submit Answers</button>
                `;
            }
        } catch (err) {
            box.textContent = "Failed to start interview.";
        }
    }

    async predictSalary() {
        const role = document.getElementById("sal-role").value;
        const loc = document.getElementById("sal-loc").value;
        const box = document.getElementById("sal-result");
        box.style.display = "block";
        box.innerHTML = "<span class='spinner'></span> Estimating market levels...";

        try {
            const res = await fetch(`${this.apiBase}/salary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: this.userId,
                    role: role,
                    location: loc
                })
            });
            const payload = await res.json();
            if (payload.success && payload.data) {
                const d = payload.data;
                box.innerHTML = `
                    <div style="font-weight:bold; color:#10b981; font-size:14px;">Estimated Compensation:</div>
                    <div style="font-weight:600; font-size:16px; margin-top:4px;">${d.currency_symbol || d.currency || '$'}${d.predicted_min.toLocaleString()} - ${d.currency_symbol || d.currency || '$'}${d.predicted_max.toLocaleString()} ${d.currency}</div>
                    <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Calculated using locations: ${loc}</div>
                `;
            }
        } catch (err) {
            box.textContent = "Failed to calculate prediction.";
        }
    }

    async generateRoadmap() {
        const target = document.getElementById("map-target").value;
        const current = document.getElementById("map-current").value || "Software Developer";
        const box = document.getElementById("map-result");
        box.style.display = "block";
        box.innerHTML = "<span class='spinner'></span> Compiling milestone timelines...";

        try {
            const res = await fetch(`${this.apiBase}/career-roadmap`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: this.userId,
                    current_role: current,
                    target_role: target
                })
            });
            const payload = await res.json();
            if (payload.success && payload.data) {
                const d = payload.data;
                box.innerHTML = `
                    <div style="font-weight:bold; color:#3b82f6; margin-bottom:8px;">Milestone Roadmap for ${target}</div>
                    <div style="margin-bottom:8px;">
                        <span style="font-weight:bold; color:#10b981;">6 Months:</span>
                        <ul style="margin-left:16px;">${d.roadmap_6m.map(item => `<li>${item}</li>`).join('')}</ul>
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="font-weight:bold; color:#10b981;">12 Months:</span>
                        <ul style="margin-left:16px;">${d.roadmap_12m.map(item => `<li>${item}</li>`).join('')}</ul>
                    </div>
                    <div>
                        <span style="font-weight:bold; color:#10b981;">24 Months:</span>
                        <ul style="margin-left:16px;">${d.roadmap_24m.map(item => `<li>${item}</li>`).join('')}</ul>
                    </div>
                `;
            }
        } catch (err) {
            box.textContent = "Failed to generate roadmap.";
        }
    }
}

const copilotController = new CopilotController();
window.copilotController = copilotController;