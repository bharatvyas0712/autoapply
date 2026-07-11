// Review Queue Controller for AutoJobApply

class ReviewController {
    constructor() {
        this.apiBase = "http://localhost:5006/api/form";
        this.userId = 1; // Default session mockup user
        this.init();
    }

    async init() {
        injectSidebar('review');
        await this.loadReviewItems();
        await this.loadCoverLetters();
    }

    async loadReviewItems() {
        const container = document.getElementById("review-items-container");
        try {
            const res = await fetch(`${this.apiBase}/review?user_id=${this.userId}`);
            const payload = await res.json();
            
            if (payload.success && payload.data.length > 0) {
                container.innerHTML = payload.data.map(item => `
                    <div class="review-card" id="item-${item.id}">
                        <div class="review-meta">
                            <span class="confidence-badge ${item.confidence < 50 ? 'badge-low' : 'badge-medium'}">
                                Confidence: ${item.confidence}%
                            </span>
                            <span style="font-size: 12px; color: var(--text-muted);">ID: ${item.id}</span>
                        </div>
                        <div class="question-title">${item.question_text}</div>
                        <textarea class="proposed-answer-box" id="ans-${item.id}">${item.proposed_answer || ''}</textarea>
                        <div class="review-actions">
                            <button class="btn btn-primary btn-sm" onclick="reviewController.approveItem(${item.id})">Approve & Save</button>
                            <button class="btn btn-secondary btn-sm" onclick="reviewController.rejectItem(${item.id})">Reject / Skip</button>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `<div style="text-align: center; padding: 24px; color: var(--text-muted);">🎉 All caught up! No questions require review.</div>`;
            }
        } catch (err) {
            container.innerHTML = `<p style="color: var(--status-error-text);">Failed to load review items: ${err.message}</p>`;
        }
    }

    async loadCoverLetters() {
        const container = document.getElementById("cover-letters-container");
        try {
            const res = await fetch(`${this.apiBase}/cover-letters?user_id=${this.userId}`);
            const payload = await res.json();
            
            if (payload.success && payload.data.length > 0) {
                container.innerHTML = payload.data.map(cl => `
                    <div style="border-bottom: 1px solid var(--border-color); padding: 12px 0; font-size: 13px;">
                        <div style="font-weight: 600; margin-bottom: 4px;">${cl.job_title} at ${cl.company_name}</div>
                        <div style="color: var(--text-muted); font-size: 11px; margin-bottom: 8px;">Type: ${cl.letter_type}</div>
                        <textarea style="width:100%; height:80px; font-size:11px; background: rgba(0,0,0,0.1); color: var(--text-muted); border:1px solid var(--border-color); border-radius:4px; padding:6px; resize:none;" readonly>${cl.content}</textarea>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `<p style="color: var(--text-muted);">No cover letters generated yet.</p>`;
            }
        } catch (err) {
            container.innerHTML = `<p style="color: var(--status-error-text);">Failed to load cover letters.</p>`;
        }
    }

    async approveItem(itemId) {
        const answerVal = document.getElementById(`ans-${itemId}`).value;
        try {
            const res = await fetch(`${this.apiBase}/review/${itemId}/approve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_response: answerVal })
            });
            const payload = await res.json();
            if (payload.success) {
                showToast("Question response approved!", "success");
                document.getElementById(`item-${itemId}`).remove();
                if (document.getElementById("review-items-container").children.length === 0) {
                    this.loadReviewItems();
                }
            }
        } catch (err) {
            showToast("Failed to approve item.", "error");
        }
    }

    async rejectItem(itemId) {
        try {
            const res = await fetch(`${this.apiBase}/review/${itemId}/reject`, { method: "POST" });
            const payload = await res.json();
            if (payload.success) {
                showToast("Question rejected/skipped.", "warning");
                document.getElementById(`item-${itemId}`).remove();
                if (document.getElementById("review-items-container").children.length === 0) {
                    this.loadReviewItems();
                }
            }
        } catch (err) {
            showToast("Failed to reject item.", "error");
        }
    }
}

const reviewController = new ReviewController();
window.reviewController = reviewController;
