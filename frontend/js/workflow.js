// Multi-Agent Workflow Controller for AutoJobApply

class WorkflowController {
    constructor() {
        this.apiBase = "http://localhost:5007/api/orchestrator";
        this.userId = 1;
        this.activeSessionId = null;
        this.pollInterval = null;
        this.init();
    }

    init() {
        injectSidebar('workflow');
    }

    async startWorkflow() {
        try {
            const res = await fetch(`${this.apiBase}/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: this.userId })
            });
            const data = await res.json();
            if (data.success) {
                this.activeSessionId = data.session_id;
                showToast("LangGraph Workflow Started!", "success");
                
                document.getElementById("ctrl-pause-btn").disabled = false;
                document.getElementById("ctrl-stop-btn").disabled = false;
                
                this.startPolling();
            }
        } catch (err) {
            showToast("Failed to initiate Multi-Agent Orchestration.", "error");
        }
    }

    startPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        this.pollInterval = setInterval(() => this.pollState(), 1500);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    async pollState() {
        if (!this.activeSessionId) return;
        try {
            const res = await fetch(`${this.apiBase}/state?session_id=${this.activeSessionId}`);
            const data = await res.json();
            
            if (data.success && data.state) {
                const state = data.state;
                document.getElementById("state-json").textContent = JSON.stringify(state, null, 2);
                
                this.updateTimeline(state);
                
                // Toggle play/pause buttons based on state status
                const pauseBtn = document.getElementById("ctrl-pause-btn");
                const resumeBtn = document.getElementById("ctrl-resume-btn");
                
                if (state.status.startsWith("paused")) {
                    pauseBtn.style.display = "none";
                    resumeBtn.style.display = "flex";
                } else {
                    pauseBtn.style.display = "flex";
                    resumeBtn.style.display = "none";
                }
                
                if (state.status === "completed" || state.status === "failed" || state.status === "stopped") {
                    this.stopPolling();
                    pauseBtn.disabled = true;
                    document.getElementById("ctrl-stop-btn").disabled = true;
                    showToast(`Workflow execution finished with status: ${state.status}`, "info");
                }
            }
        } catch (err) {
            console.error("Error polling orchestrator state:", err);
        }
    }

    updateTimeline(state) {
        const timeline = document.getElementById("timeline");
        const steps = [
            { key: "resume_intelligence", name: "Resume Intelligence", icon: "📄" },
            { key: "job_search", name: "Job Search", icon: "🔍" },
            { key: "job_matching", name: "Job Match Evaluator", icon: "🧠" },
            { key: "browser_automation", name: "Browser Automation Form Filling", icon: "🌐" }
        ];

        let reachedActive = false;
        
        timeline.innerHTML = steps.map(step => {
            let statusClass = "";
            let statusText = "Waiting...";
            
            if (state.current_page && step.key === "browser_automation") {
                statusClass = "active";
                statusText = "Filling forms...";
                reachedActive = true;
            } else if (state.resume_summary && step.key === "resume_intelligence") {
                statusClass = "completed";
                statusText = "Completed";
            } else if (state.search_results.length > 0 && step.key === "job_search") {
                statusClass = "completed";
                statusText = "Completed";
            } else if (state.matched_jobs.length > 0 && step.key === "job_matching") {
                statusClass = "completed";
                statusText = "Completed";
            } else if (!reachedActive) {
                statusClass = "active";
                statusText = "Running...";
                reachedActive = true;
            }
            
            return `
                <div class="timeline-item ${statusClass}">
                    <div class="timeline-icon">${step.icon}</div>
                    <div class="timeline-details">
                        <div class="timeline-name">${step.name}</div>
                        <div class="timeline-status">${statusText}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async pauseWorkflow() {
        if (!this.activeSessionId) return;
        await fetch(`${this.apiBase}/pause?session_id=${this.activeSessionId}&reason=manual`, { method: "POST" });
        showToast("Workflow pause requested", "warning");
        this.pollState();
    }

    async resumeWorkflow() {
        if (!this.activeSessionId) return;
        await fetch(`${this.apiBase}/resume?session_id=${this.activeSessionId}`, { method: "POST" });
        showToast("Workflow resuming...", "success");
        this.startPolling();
    }

    async stopWorkflow() {
        if (!this.activeSessionId) return;
        await fetch(`${this.apiBase}/stop?session_id=${this.activeSessionId}`, { method: "POST" });
        showToast("Workflow stopped", "error");
        this.pollState();
    }
}

const workflowController = new WorkflowController();
window.workflowController = workflowController;
