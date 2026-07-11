// Memory Dashboard Controller for AutoJobApply

class MemoryController {
    constructor() {
        this.apiBase = "http://localhost:5008/api/memory";
        this.userId = 1;
        this.init();
    }

    async init() {
        injectSidebar('memory');
        await this.loadStats();
        await this.loadRecommendations();
        await this.loadResumes();
        await this.loadTimelines();
    }

    async loadStats() {
        try {
            // Load base statistics
            const res = await fetch(`${this.apiBase}/statistics?user_id=${this.userId}`);
            const data = await res.json();
            if (data.success && data.data) {
                const s = data.data;
                document.getElementById("stat-interview-rate").textContent = `${s.interview_rate.toFixed(1)}%`;
                document.getElementById("stat-memories-count").textContent = s.memories_count ?? 0;
                document.getElementById("stat-companies-count").textContent = s.companies_count ?? 0;
                document.getElementById("stat-resumes-count").textContent = s.resumes_count ?? 0;
            }
        } catch (err) {
            console.error("Error loading stats:", err);
        }
    }

    async loadRecommendations() {
        const container = document.getElementById("recommendations-container");
        try {
            const res = await fetch(`${this.apiBase}/recommendations?user_id=${this.userId}`);
            const data = await res.json();
            if (data.success && data.data.length > 0) {
                container.innerHTML = data.data.map(rec => `
                    <div class="recommendation-item">
                        <span class="recommendation-icon">💡</span>
                        <span style="font-size:13px; font-weight:500;">${rec}</span>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `<p style="color: var(--text-muted);">No recommendations calculated yet.</p>`;
            }
        } catch (err) {
            container.innerHTML = `<p style="color: var(--status-error-text);">Failed to load recommendations.</p>`;
        }
    }

    async loadResumes() {
        const container = document.getElementById("resumes-container");
        try {
            const res = await fetch(`${this.apiBase}/resumes?user_id=${this.userId}`);
            const data = await res.json();
            if (data.success && data.data.length > 0) {
                container.innerHTML = data.data.map(rv => `
                    <div style="border-bottom: 1px solid var(--border-color); padding: 12px 0;">
                        <div style="font-weight: 600; font-size:13px;">${rv.version_label}</div>
                        <div style="font-size:11px; color: var(--text-muted); margin-top:4px;">
                            Applications: ${rv.applications_count} | Interviews: ${rv.interviews_count}
                        </div>
                    </div>
                `).join('');
            } else {
                // Mock versions fallback
                container.innerHTML = `
                    <div style="border-bottom: 1px solid var(--border-color); padding: 12px 0;">
                        <div style="font-weight: 600; font-size:13px;">Resume_v1_Backend.pdf</div>
                        <div style="font-size:11px; color: var(--text-muted); margin-top:4px;">
                            Applications: 12 | Interviews: 2
                        </div>
                    </div>
                    <div style="border-bottom: 1px solid var(--border-color); padding: 12px 0;">
                        <div style="font-weight: 600; font-size:13px;">Resume_v2_Fullstack.pdf</div>
                        <div style="font-size:11px; color: var(--text-muted); margin-top:4px;">
                            Applications: 24 | Interviews: 6
                        </div>
                    </div>
                `;
            }
        } catch (err) {
            container.innerHTML = `<p style="color: var(--status-error-text);">Failed to load resume versions.</p>`;
        }
    }

    async loadTimelines() {
        const appContainer = document.getElementById("application-timeline");
        const compContainer = document.getElementById("companies-timeline");
        
        try {
            // Load application history
            const res = await fetch(`${this.apiBase}/application-history?user_id=${this.userId}`);
            const data = await res.json();
            
            if (data.success && data.data.length > 0) {
                appContainer.innerHTML = data.data.map(app => `
                    <div class="timeline-node">
                        <div class="timeline-time">${new Date(app.created_at).toLocaleDateString()}</div>
                        <div class="timeline-content">Applied as ${app.job_title} at ${app.company_name}</div>
                        <div style="font-size:11px; font-weight: bold; color: ${app.outcome === 'rejected' ? '#ef4444' : '#10b981'}">${app.outcome.toUpperCase()}</div>
                    </div>
                `).join('');
            } else {
                appContainer.innerHTML = `
                    <div class="timeline-node">
                        <div class="timeline-time">Today</div>
                        <div class="timeline-content">Applied for Backend Engineer at Stripe</div>
                        <div style="font-size:11px; font-weight: bold; color: #f59e0b">INTERVIEWING</div>
                    </div>
                    <div class="timeline-node">
                        <div class="timeline-time">Yesterday</div>
                        <div class="timeline-content">Applied for Python Developer at Vercel</div>
                        <div style="font-size:11px; font-weight: bold; color: #ef4444">REJECTED</div>
                    </div>
                `;
            }
            
            // Mock company histories
            compContainer.innerHTML = `
                <div class="timeline-node">
                    <div class="timeline-time">Stripe</div>
                    <div class="timeline-content">Last contact: Recruiter Jane Doe. Note: Prefers hands-on coding challenges over trivia.</div>
                </div>
                <div class="timeline-node">
                    <div class="timeline-time">Vercel</div>
                    <div class="timeline-content">Last contact: Automatic rejection portal. Note: Required 5+ years React experience.</div>
                </div>
            `;
            
        } catch (err) {
            appContainer.innerHTML = `<p style="color: var(--status-error-text);">Failed to load timelines.</p>`;
        }
    }
}

const memoryController = new MemoryController();
window.memoryController = memoryController;