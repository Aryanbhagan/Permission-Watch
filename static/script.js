document.addEventListener("DOMContentLoaded", () => {
    const API = {
        stats: "/api/stats",
        events: "/api/events?limit=100",
        analytics: "/api/analytics"
    };

    let riskChart = null;
    let eventChart = null;
    let allEvents = [];

    const $ = (id) => document.getElementById(id);

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[char]);
    }

    async function fetchJSON(url) {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }

        return response.json();
    }

    function updateElement(id, value) {
        const element = $(id);
        if (element) element.textContent = value;
    }

    function formatDate(value) {
        if (!value) return "—";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });
    }

    function getRiskClass(risk) {
        const value = String(risk ?? "").toUpperCase();

        if (value.startsWith("HIGH")) return "high";
        if (value.startsWith("MEDIUM")) return "medium";
        if (value.startsWith("LOW")) return "low";

        return "info";
    }

    function renderEvents(events, targetId) {
        const tbody = $(targetId);
        if (!tbody) return;

        if (!events.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6">No events recorded yet.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = events.map((event) => {
            const risk = event.risk_level || "INFO";
            const oldValue = event.old_value || "—";
            const newValue = event.new_value || "—";

            return `
                <tr>
                    <td>${escapeHTML(formatDate(event.timestamp))}</td>
                    <td>${escapeHTML(event.event_type)}</td>
                    <td class="path-cell" title="${escapeHTML(event.file_path)}">
                        ${escapeHTML(event.file_path)}
                    </td>
                    <td>${escapeHTML(oldValue)}</td>
                    <td>${escapeHTML(newValue)}</td>
                    <td>
                        <span class="risk-badge ${getRiskClass(risk)}">
                            ${escapeHTML(risk)}
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    }

    async function loadStats() {
        const stats = await fetchJSON(API.stats);

        updateElement("total-events", stats.total_events);
        updateElement("high-risk", stats.high_risk);
        updateElement("medium-risk", stats.medium_risk);
        updateElement("permission-events", stats.permission_events);
    }

    async function loadEvents() {
        allEvents = await fetchJSON(API.events);

        renderEvents(allEvents.slice(0, 10), "recent-events");
        renderEvents(allEvents, "event-history");
    }

    async function loadAnalytics() {
        const analytics = await fetchJSON(API.analytics);

        renderRiskChart(analytics.risk_distribution || []);
        renderEventChart(analytics.event_types || []);
    }

    function renderRiskChart(data) {
        const canvas = $("riskChart");

        if (!canvas || typeof Chart === "undefined") return;

        const labels = data.map(item => item.risk);
        const values = data.map(item => item.count);

        if (riskChart) riskChart.destroy();

        riskChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        "#ff5d73",
                        "#ffb454",
                        "#35d49a",
                        "#75839a"
                    ],
                    borderColor: "#111827",
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#cbd5e1",
                            padding: 18
                        }
                    }
                }
            }
        });
    }

    function renderEventChart(data) {
        const canvas = $("eventChart");

        if (!canvas || typeof Chart === "undefined") return;

        const sorted = [...data].sort((a, b) => b.count - a.count);
        const labels = sorted.map(item => item.event_type);
        const values = sorted.map(item => item.count);

        if (eventChart) eventChart.destroy();

        eventChart = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Events",
                    data: values,
                    backgroundColor: "#38bdf8",
                    borderRadius: 5
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { color: "#cbd5e1", precision: 0 },
                        grid: { color: "#263244" }
                    },
                    y: {
                        ticks: { color: "#cbd5e1" },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    function setupSearch() {
        const search = $("event-search");
        if (!search) return;

        search.addEventListener("input", () => {
            const query = search.value.trim().toLowerCase();

            const filtered = allEvents.filter(event => {
                const searchable = [
                    event.event_type,
                    event.file_path,
                    event.old_value,
                    event.new_value,
                    event.risk_level,
                    event.timestamp
                ].join(" ").toLowerCase();

                return searchable.includes(query);
            });

            renderEvents(filtered, "event-history");
        });
    }

    function updateClock() {
        updateElement(
            "current-time",
            new Date().toLocaleTimeString("en-IN")
        );
    }

    async function refreshDashboard() {
        const results = await Promise.allSettled([
            loadStats(),
            loadEvents(),
            loadAnalytics()
        ]);

        const failed = results.some(result => result.status === "rejected");

        updateElement(
            "dashboard-status",
            failed ? "Some data could not be loaded" : "Connected"
        );

        if (failed) {
            console.error("Dashboard refresh error:", results);
        }
    }

    setupSearch();
    updateClock();
    refreshDashboard();

    setInterval(updateClock, 1000);
    setInterval(refreshDashboard, 10000);
});

/* Folder Browser and Monitoring Controls */
(() => {
    const folderList = document.getElementById("folder-list");
    if (!folderList) return;

    const currentPath = document.getElementById("current-folder-path");
    const selectedPath = document.getElementById("selected-folder-path");
    const parentButton = document.getElementById("parent-folder-btn");
    const startButton = document.getElementById("start-monitor-btn");
    const stopButton = document.getElementById("stop-monitor-btn");
    const statusBadge = document.getElementById("monitor-status");
    const message = document.getElementById("monitor-message");

    let browsingPath = "";
    let selectedDirectory = "";
    let monitoring = false;
    let requestPending = false;

    async function requestJSON(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }

        return data;
    }

    function showMessage(text, isError = false) {
        message.textContent = text;
        message.style.color = isError ? "#f87171" : "#94a3b8";
    }

    function updateButtons() {
        startButton.disabled =
            monitoring || requestPending || !selectedDirectory;

        stopButton.disabled =
            !monitoring || requestPending;

        parentButton.disabled =
            !browsingPath || browsingPath === window.permissionWatchHome;
    }

    async function loadFolders(path = "") {
        folderList.replaceChildren();

        const loading = document.createElement("p");
        loading.className = "folder-empty";
        loading.textContent = "Loading folders...";
        folderList.appendChild(loading);

        try {
            const query = path
                ? `?path=${encodeURIComponent(path)}`
                : "";

            const data = await requestJSON(`/api/browse${query}`);

            browsingPath = data.current;
            currentPath.textContent = data.current;
            parentButton.disabled = !data.parent;

            window.permissionWatchHome = window.permissionWatchHome || data.current;

            folderList.replaceChildren();

            if (data.folders.length === 0) {
                const empty = document.createElement("p");
                empty.className = "folder-empty";
                empty.textContent = "No subfolders in this directory.";
                folderList.appendChild(empty);
            }

            data.folders.forEach(folder => {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "folder-item";
                button.textContent = `📁 ${folder.name}`;
                button.title = folder.path;

                if (selectedDirectory === folder.path) {
                    button.classList.add("selected");
                }

                button.addEventListener("click", () => {
                    selectedDirectory = folder.path;
                    selectedPath.textContent = folder.path;

                    folderList.querySelectorAll(".folder-item").forEach(item => {
                        item.classList.remove("selected");
                    });

                    button.classList.add("selected");
                    updateButtons();
                    showMessage("Folder selected. Start monitoring when ready.");
                });

                button.addEventListener("dblclick", () => {
                    loadFolders(folder.path);
                });

                folderList.appendChild(button);
            });

            updateButtons();
        } catch (error) {
            folderList.replaceChildren();

            const errorElement = document.createElement("p");
            errorElement.className = "folder-empty";
            errorElement.textContent = error.message;
            folderList.appendChild(errorElement);

            showMessage(error.message, true);
        }
    }

    parentButton.addEventListener("click", async () => {
        try {
            const data = await requestJSON(
                `/api/browse?path=${encodeURIComponent(browsingPath)}`
            );

            if (data.parent) {
                await loadFolders(data.parent);
            }
        } catch (error) {
            showMessage(error.message, true);
        }
    });

    startButton.addEventListener("click", async () => {
        if (!selectedDirectory || requestPending) return;

        requestPending = true;
        updateButtons();
        showMessage("Starting file and permission monitoring...");

        try {
            await requestJSON("/api/monitor/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path: selectedDirectory })
            });

            await refreshStatus();
            showMessage(`Monitoring requested for ${selectedDirectory}`);
        } catch (error) {
            showMessage(error.message, true);
        } finally {
            requestPending = false;
            updateButtons();
        }
    });

    stopButton.addEventListener("click", async () => {
        if (requestPending) return;

        requestPending = true;
        updateButtons();
        showMessage("Stopping monitoring...");

        try {
            const data = await requestJSON("/api/monitor/stop", {
                method: "POST"
            });

            showMessage(data.message || "Stop requested.");
            await refreshStatus();
        } catch (error) {
            showMessage(error.message, true);
        } finally {
            requestPending = false;
            updateButtons();
        }
    });

    async function refreshStatus() {
        try {
            const data = await requestJSON("/api/monitor/status");

            monitoring = data.active;
            statusBadge.textContent = monitoring ? "● RUNNING" : "● STOPPED";
            statusBadge.classList.toggle("running", monitoring);

            if (data.directory) {
                selectedDirectory = data.directory;
                selectedPath.textContent = data.directory;
            }

            if (data.error) {
                showMessage(`Monitoring error: ${data.error}`, true);
            }

            updateButtons();
        } catch (error) {
            showMessage(error.message, true);
        }
    }

    loadFolders();
    refreshStatus();
    setInterval(refreshStatus, 2000);
})();
