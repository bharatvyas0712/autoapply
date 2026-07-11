// AI Chat & Tool Inspector Controller for AutoJobApply

class ChatController {
    constructor() {
        this.apiBase = "http://localhost:5009/api";
        this.conversationId = 1;
        this.init();
    }

    async init() {
        injectSidebar('chat');
        await this.loadTools();
    }

    async loadTools() {
        const box = document.getElementById("tool-box");
        try {
            const res = await fetch(`${this.apiBase}/tools`);
            const payload = await res.json();
            if (payload.success && payload.tools.length > 0) {
                box.innerHTML = payload.tools.map(tool => `
                    <div class="tool-item">
                        <div class="tool-name-lbl">🛠 ${tool.name}</div>
                        <div style="color: var(--text-muted); font-size:11px; margin-bottom:6px;">${tool.description}</div>
                        <pre style="background:rgba(0,0,0,0.1); border-radius:4px; padding:6px; font-size:10px; overflow-x:auto;">${JSON.stringify(tool.parameters, null, 2)}</pre>
                    </div>
                `).join('');
            } else {
                box.innerHTML = `<p style="color: var(--text-muted); padding:10px;">No tools discovered.</p>`;
            }
        } catch (err) {
            box.innerHTML = `<p style="color: var(--status-error-text); padding:10px;">Failed to load MCP tools.</p>`;
        }
    }

    async sendMessage() {
        const input = document.getElementById("chat-input");
        const prompt = input.value.trim();
        if (!prompt) return;

        input.value = "";
        this.appendMessage("user", prompt);

        const chatBox = document.getElementById("chat-box");
        const loadingMsg = this.appendMessage("assistant", "<span class='spinner'></span> Analyzing request and matching tools...");

        try {
            const res = await fetch(`${this.apiBase}/llm/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    conversation_id: this.conversationId,
                    message: prompt,
                    stream: false
                })
            });
            const payload = await res.json();
            loadingMsg.remove();

            if (payload.success && payload.response) {
                const r = payload.response;
                if (r.content && r.content.trim()) {
                    this.appendMessage("assistant", r.content);
                }
            }
        } catch (err) {
            loadingMsg.remove();
            this.appendMessage("assistant", "Sorry, I encountered an error coordinating tool selection.");
        }
    }

    appendMessage(role, content) {
        const chatBox = document.getElementById("chat-box");
        const div = document.createElement("div");
        div.className = `msg ${role}`;
        div.innerHTML = content;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
        return div;
    }
}

const chatController = new ChatController();
window.chatController = chatController;