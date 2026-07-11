// Admin Dashboard Controller for AutoJobApply

class AdminController {
    constructor() {
        this.init();
    }

    init() {
        injectSidebar('admin');
        this.loadMetrics();
    }

    loadMetrics() {
        // Mocking Prometheus/Stats API parameters
        document.getElementById("adm-active-users").textContent = "1,420";
        document.getElementById("adm-workflows").textContent = "18";
        document.getElementById("adm-llm-cost").textContent = "$12.45";
        document.getElementById("adm-success-rate").textContent = "88.5%";
    }
}

const adminController = new AdminController();
window.adminController = adminController;
