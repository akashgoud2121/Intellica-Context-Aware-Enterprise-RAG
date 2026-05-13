const API_BASE = "https://intellica-context-aware-enterprise-rag.onrender.com/api/v1";

let currentUserPersona = "ceo_alice";

const personaMeta = {
    "ceo_alice": { role: "Executive", dept: "Management", silos: "finance, hr, engineering, compliance, public", clearance: "Top Secret" },
    "lead_bob": { role: "Engineering", dept: "Engineering", silos: "engineering, public", clearance: "Confidential" },
    "hr_clara": { role: "HR", dept: "Human Resources", silos: "hr, public", clearance: "Restricted" },
    "fin_david": { role: "Finance", dept: "Finance", silos: "finance, public", clearance: "Secret" },
    "comp_eve": { role: "Compliance", dept: "Legal", silos: "compliance, hr, finance, public", clearance: "Secret" },
    "guest_frank": { role: "Guest", dept: "Contractor", silos: "public", clearance: "Unclassified" }
};

function switchPersona(username) {
    currentUserPersona = username;
    const meta = personaMeta[username];
    
    document.getElementById("clearanceBadge").innerText = meta.clearance;
    document.getElementById("infoRole").innerText = meta.role;
    document.getElementById("infoDept").innerText = meta.dept;
    
    // Dynamically inject beautiful silo pills
    const silosArr = meta.silos.split(', ');
    document.getElementById("infoSilos").innerHTML = silosArr.map(s => `<span class="silo-pill">${s}</span>`).join('');
    
    document.getElementById("queryResultsArea").classList.add("hidden");
    
    if (document.getElementById("analyticsTab").classList.contains("active")) {
        loadAnalytics();
    }
}

function switchTab(tabId) {
    document.querySelectorAll(".view-panel").forEach(p => p.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    
    document.getElementById(tabId).classList.remove("hidden");
    event.currentTarget.classList.add("active");
    
    if (tabId === "analyticsTab") {
        loadAnalytics();
    }
}

function setQuery(text) {
    document.getElementById("ragQueryInput").value = text;
    executeQuery();
}

async function executeQuery() {
    const qInput = document.getElementById("ragQueryInput");
    const query = qInput.value.trim();
    if (!query) return;
    
    const silo = document.getElementById("siloFilterSelect").value;
    const resArea = document.getElementById("queryResultsArea");
    const ansContent = document.getElementById("ragAnswerContent");
    const citesGrid = document.getElementById("ragCitationsGrid");
    
    resArea.classList.remove("hidden");
    ansContent.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Contacting Enterprise RAG engine...';
    citesGrid.innerHTML = '';
    
    let url = `${API_BASE}/query?query=${encodeURIComponent(query)}`;
    if (silo) url += `&silo_filter=${encodeURIComponent(silo)}`;
    
    try {
        const res = await fetch(url, {
            headers: { "x-username": currentUserPersona }
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            ansContent.innerHTML = `<span style="color: var(--danger-red)"><i class="fa-solid fa-triangle-exclamation"></i> Error: ${data.detail || 'Unknown error'}</span>`;
            return;
        }
        
        document.getElementById("pillIntent").innerHTML = `<i class="fa-solid fa-route"></i> Intent: ${data.routed_intent}`;
        document.getElementById("pillTime").innerHTML = `<i class="fa-solid fa-stopwatch"></i> Latency: ${data.execution_time_ms}ms`;
        
        const resp = data.response;
        const confPerc = Math.round(resp.confidence_score * 100);
        document.getElementById("confidenceVal").innerText = `${confPerc}% (${resp.uncertainty_indicator})`;
        document.getElementById("confidenceBar").style.width = `${confPerc}%`;
        
        ansContent.innerText = resp.answer;
        
        if (resp.citations && resp.citations.length > 0) {
            resp.citations.forEach(c => {
                const div = document.createElement("div");
                div.className = "citation-card";
                div.innerHTML = `
                    <div class="citation-meta">
                        <span>Source: ${c.filename}</span>
                        <span class="silo-tag">[Silo: ${c.data_silo}]</span>
                    </div>
                    <div class="snippet">"${c.text_snippet}"</div>
                `;
                citesGrid.appendChild(div);
            });
        } else {
            citesGrid.innerHTML = '<p style="color: var(--text-muted)">No specific citations mapped for this query response.</p>';
        }
        
    } catch (err) {
        ansContent.innerHTML = `<span style="color: var(--danger-red)"><i class="fa-solid fa-server"></i> Connection Error: Ensure backend is running at ${API_BASE}</span>`;
    }
}

let selectedFile = null;
function handleFileSelect(e) {
    selectedFile = e.target.files[0];
    if (selectedFile) {
        document.getElementById("selectedFileName").innerText = `Selected: ${selectedFile.name}`;
        
        const ext = selectedFile.name.split('.').pop().toLowerCase();
        const typeSelect = document.getElementById("ingestDocType");
        if (ext === "pptx") typeSelect.value = "pptx";
        else if (ext === "docx") typeSelect.value = "docx";
        else if (ext === "pdf") typeSelect.value = "pdf";
        else if (ext === "json") typeSelect.value = "json_log";
        else if (ext === "csv") typeSelect.value = "csv";
    }
}

async function uploadDocument() {
    if (!selectedFile) {
        alert("Please select a file first.");
        return;
    }
    
    const silo = document.getElementById("ingestSilo").value;
    const docType = document.getElementById("ingestDocType").value;
    const statusDiv = document.getElementById("uploadStatus");
    
    statusDiv.style.color = "var(--accent-indigo)";
    statusDiv.innerText = "Encrypting and ingesting document into vector DB...";
    
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("data_silo", silo);
    formData.append("doc_type", docType);
    
    try {
        const res = await fetch(`${API_BASE}/ingest`, {
            method: "POST",
            headers: { "x-username": currentUserPersona },
            body: formData
        });
        
        const data = await res.json();
        if (res.ok) {
            statusDiv.style.color = "var(--accent-green)";
            statusDiv.innerText = `Success: ${data.message} (Took ${data.execution_time_ms}ms)`;
            selectedFile = null;
            document.getElementById("selectedFileName").innerText = "";
            document.getElementById("fileInput").value = "";
        } else {
            statusDiv.style.color = "var(--danger-red)";
            statusDiv.innerText = `Upload Failed: ${data.detail || 'RBAC Unauthorized'}`;
        }
    } catch (err) {
        statusDiv.style.color = "var(--danger-red)";
        statusDiv.innerText = "Error connecting to ingestion endpoint.";
    }
}

async function loadAnalytics() {
    const container = document.getElementById("analyticsContent");
    container.innerHTML = '<div style="padding: 3rem; text-align: center;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i> Loading Audit Trail & Metrics...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/analytics`, {
            headers: { "x-username": currentUserPersona }
        });
        
        if (!res.ok) {
            const errData = await res.json();
            container.innerHTML = `
                <div class="glass-card" style="border-color: var(--danger-red)">
                    <h3 style="color: var(--danger-red)"><i class="fa-solid fa-lock"></i> RBAC Security Lockout</h3>
                    <p style="margin-top: 1rem;">${errData.detail || 'Access Denied.'}</p>
                    <p style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted)">Tip: Switch to CEO Alice or Compliance Eve persona to view enterprise audit logs.</p>
                </div>
            `;
            return;
        }
        
        const data = await res.json();
        const perf = data.performance_metrics;
        const health = data.system_health;
        
        let auditRows = data.audit_trail.map(a => `
            <tr style="background: ${a.action === 'UNAUTHORIZED_ACCESS' ? 'rgba(220, 38, 38, 0.05)' : 'transparent'}">
                <td>${a.timestamp.replace('T', ' ')}</td>
                <td><strong>${a.username}</strong> (${a.role})</td>
                <td><span class="pill ${a.action === 'UNAUTHORIZED_ACCESS' ? 'status-badge' : 'intent-pill'}">${a.action}</span></td>
                <td>${a.silo_accessed || 'N/A'}</td>
                <td>${a.execution_time_ms}ms</td>
                <td>${a.success ? '<i class="fa-solid fa-circle-check" style="color:var(--accent-green)"></i>' : '<i class="fa-solid fa-circle-xmark" style="color:var(--danger-red)"></i>'}</td>
            </tr>
        `).join('');
        
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-label">Total Queries Served</span>
                    <span class="stat-value" style="color: var(--accent-indigo)">${perf.total_queries_served}</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">Avg Response Latency</span>
                    <span class="stat-value" style="color: var(--accent-purple)">${perf.average_response_time_ms}ms</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">System Throughput</span>
                    <span class="stat-value" style="color: var(--accent-green)">${perf.system_throughput_qpm} QPM</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">RBAC Violations Blocked</span>
                    <span class="stat-value" style="color: var(--danger-red)">${perf.rbac_unauthorized_attempts}</span>
                </div>
            </div>

            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1.5rem;">
                    <h3><i class="fa-solid fa-shield-halved"></i> Enterprise Security Audit Log</h3>
                    <span style="font-size:0.85rem; color:var(--text-muted)">Real-time Policy Enforcement Engine</span>
                </div>
                <div class="audit-table-wrapper">
                    <table class="audit-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>User Context</th>
                                <th>Action</th>
                                <th>Target Silo</th>
                                <th>Latency</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${auditRows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
    } catch (err) {
        container.innerHTML = `<div class="glass-card"><span style="color: var(--danger-red)">Error loading analytics data.</span></div>`;
    }
}
