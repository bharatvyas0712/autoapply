// Browser Status Widget for AutoJobApply
// Dynamically creates and injects a modern, floating browser execution tracking widget.

class BrowserStatusWidget {
    constructor() {
        this.apiBase = "http://localhost:5005/api/browser";
        this.pollInterval = null;
        this.activeJobId = null;
        this.createWidget();
    }

    createWidget() {
        // CSS Styles
        const style = document.createElement("style");
        style.textContent = `
            .browser-widget-container {
                position: fixed;
                bottom: 24px;
                right: 24px;
                width: 360px;
                background: rgba(30, 30, 38, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
                color: #fff;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                z-index: 10000;
                overflow: hidden;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                display: none;
            }
            .browser-widget-header {
                padding: 16px;
                background: rgba(255, 255, 255, 0.03);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .browser-widget-title {
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .browser-widget-close {
                background: none;
                border: none;
                color: rgba(255, 255, 255, 0.6);
                cursor: pointer;
                font-size: 16px;
            }
            .browser-widget-close:hover {
                color: #fff;
            }
            .browser-widget-body {
                padding: 16px;
            }
            .browser-widget-info {
                margin-bottom: 12px;
            }
            .browser-widget-label {
                font-size: 11px;
                color: rgba(255, 255, 255, 0.5);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }
            .browser-widget-value {
                font-size: 13px;
                font-weight: 500;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .browser-widget-progress {
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                overflow: hidden;
                margin: 12px 0;
            }
            .browser-widget-progress-bar {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #3b82f6, #60a5fa);
                transition: width 0.3s ease;
            }
            .browser-widget-controls {
                display: flex;
                gap: 8px;
                margin-top: 16px;
            }
            .browser-btn {
                flex: 1;
                padding: 8px 12px;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }
            .browser-btn-primary {
                background: #3b82f6;
                color: white;
            }
            .browser-btn-primary:hover {
                background: #2563eb;
            }
            .browser-btn-secondary {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            .browser-btn-secondary:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            .browser-widget-pulse {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10b981;
                box-shadow: 0 0 8px #10b981;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(0.9); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.5; }
                100% { transform: scale(0.9); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Widget HTML structure
        this.container = document.createElement("div");
        this.container.className = "browser-widget-container";
        this.container.innerHTML = `
            <div class="browser-widget-header">
                <div class="browser-widget-title">
                    <div class="browser-widget-pulse"></div>
                    Autonomous Apply Agent
                </div>
                <button class="browser-widget-close" onclick="this.parentElement.parentElement.style.display='none'">✕</button>
            </div>
            <div class="browser-widget-body">
                <div class="browser-widget-info">
                    <div class="browser-widget-label">Target Page</div>
                    <div class="browser-widget-value" id="bw-page">Initiating...</div>
                </div>
                <div class="browser-widget-info">
                    <div class="browser-widget-label">Current Action</div>
                    <div class="browser-widget-value" id="bw-action">Detecting form inputs...</div>
                </div>
                <div class="browser-widget-progress">
                    <div class="browser-widget-progress-bar" id="bw-progress"></div>
                </div>
                <div class="browser-widget-info">
                    <div class="browser-widget-label">Status</div>
                    <div class="browser-widget-value" id="bw-status" style="font-weight: bold; color: #10b981;">Running</div>
                </div>
                <div class="browser-widget-controls">
                    <button class="browser-btn browser-btn-primary" id="bw-pause-btn">⏸ Pause</button>
                    <button class="browser-btn browser-btn-secondary" id="bw-resume-btn" style="display:none;">▶ Resume</button>
                </div>
            </div>
        `;
        document.body.appendChild(this.container);

        // Bind events
        this.container.querySelector("#bw-pause-btn").addEventListener("click", () => this.pauseApply());
        this.container.querySelector("#bw-resume-btn").addEventListener("click", () => this.resumeApply());
    }

    show(jobId) {
        this.activeJobId = jobId;
        this.container.style.display = "block";
        this.startPolling();
    }

    startPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        this.pollInterval = setInterval(() => this.pollStatus(), 2000);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    async pollStatus() {
        if (!this.activeJobId) return;
        try {
            const res = await fetch(`${this.apiBase}/status?job_id=${this.activeJobId}`);
            const payload = await res.json();
            if (payload.success && payload.data) {
                const data = payload.data;
                document.getElementById("bw-page").textContent = data.current_page || "N/A";
                document.getElementById("bw-action").textContent = `Step: ${data.current_step}`;
                
                // Update progress percentage
                const total = data.completed_steps.length + data.pending_steps.length;
                const percent = total > 0 ? (data.completed_steps.length / total) * 100 : 0;
                document.getElementById("bw-progress").style.width = `${percent}%`;

                // Update Status text
                const statusEl = document.getElementById("bw-status");
                statusEl.textContent = data.status.toUpperCase();
                
                const pauseBtn = document.getElementById("bw-pause-btn");
                const resumeBtn = document.getElementById("bw-resume-btn");

                if (data.status.startsWith("paused")) {
                    statusEl.style.color = "#f59e0b"; // yellow
                    pauseBtn.style.display = "none";
                    resumeBtn.style.display = "flex";
                } else if (data.status === "failed") {
                    statusEl.style.color = "#ef4444"; // red
                    this.stopPolling();
                } else if (data.status === "submitted") {
                    statusEl.style.color = "#10b981"; // green
                    this.stopPolling();
                } else {
                    statusEl.style.color = "#10b981";
                    pauseBtn.style.display = "flex";
                    resumeBtn.style.display = "none";
                }
            }
        } catch (err) {
            console.error("Error polling browser status:", err);
        }
    }

    async pauseApply() {
        if (!this.activeJobId) return;
        await fetch(`${this.apiBase}/pause/${this.activeJobId}?reason=manual`, { method: "POST" });
        this.pollStatus();
    }

    async resumeApply() {
        if (!this.activeJobId) return;
        await fetch(`${this.apiBase}/resume/${this.activeJobId}`, { method: "POST" });
        this.pollStatus();
    }
}

// Instantiate on window load
window.addEventListener("DOMContentLoaded", () => {
    window.browserStatusWidget = new BrowserStatusWidget();
});
