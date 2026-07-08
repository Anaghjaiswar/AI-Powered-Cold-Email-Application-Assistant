// --- STATE ---
const state = {
    currentTheme: 'dark',
    settings: {
        groq_api_key: '',
        sender_email: '',
        sender_app_password: '',
        email_footer: '',
        preferred_tone: 'professional',
        email_length: 'medium'
    },
    resumes: [],
    selectedResumeId: null,
    isEmailEditMode: false,
    pollTimer: null
};

// --- MARKDOWN RENDERING UTILITY ---
function renderMarkdown(md) {
    if (!md) return "";
    let html = md
        // Escape HTML
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        // Headings
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // Bold with **
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic with *
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Underline with _
        .replace(/_(.*?)_/g, '<u>$1</u>')
        // Links
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: var(--accent-color); font-weight: 600;">$1</a>')
        // Bullet Lists
        .replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>')
        .replace(/^\s*\*\s+(.*$)/gim, '<li>$1</li>')
        // Single backticks code
        .replace(/`(.*?)`/g, '<code style="background: var(--input-bg); padding: 2px 6px; border-radius: 4px; font-family: monospace;">$1</code>')
        // Linebreaks
        .replace(/\n/g, '<br>');
    
    // Wrap lists nicely
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    return html;
}

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialise View
    switchView('welcome');
    
    // 2. Setup Action Listeners
    setupEventListeners();
    
    // 3. Load Theme Preference
    initTheme();
});

// --- THEME MANAGEMENT ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

function setTheme(theme) {
    state.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Synchronize Sun and Moon icons across floating and sidebar theme toggle buttons
    document.querySelectorAll('.theme-icon-sun').forEach(sunIcon => {
        sunIcon.style.display = theme === 'light' ? 'block' : 'none';
    });
    
    document.querySelectorAll('.theme-icon-moon').forEach(moonIcon => {
        moonIcon.style.display = theme === 'light' ? 'none' : 'block';
    });
}

function toggleTheme() {
    const nextTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
}

// --- ROUTER VIEW SWITCHING ---
function switchView(viewName) {
    document.querySelectorAll('.view-container').forEach(view => {
        view.classList.remove('active');
    });
    
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }
}

// --- PASSWORD INPUT TOGGLE ---
function togglePasswordVisibility(id) {
    const input = document.getElementById(id);
    if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
    }
}

// --- TOAST NOTIFICATIONS BANNER ---
function showNotification(message, type = 'success') {
    const banner = document.getElementById('notification-banner');
    const iconSpan = document.getElementById('notification-icon');
    const msgSpan = document.getElementById('notification-message');
    
    banner.className = `notification-banner ${type}`;
    msgSpan.innerText = message;
    
    if (type === 'success') {
        iconSpan.innerHTML = `✅`;
    } else if (type === 'error') {
        iconSpan.innerHTML = `❌`;
    } else {
        iconSpan.innerHTML = `⚠️`;
    }
    
    banner.classList.add('active');
    
    setTimeout(() => {
        banner.classList.remove('active');
    }, 4500);
}

// --- SETTINGS FOOTER EDITOR TABS ---
function switchFooterTab(tab) {
    const editBtn = document.getElementById('footer-edit-tab');
    const previewBtn = document.getElementById('footer-preview-tab');
    const textarea = document.getElementById('email_footer');
    const previewPane = document.getElementById('footer-preview-pane');
    
    if (tab === 'edit') {
        editBtn.classList.add('active');
        previewBtn.classList.remove('active');
        textarea.style.display = 'block';
        previewPane.style.display = 'none';
    } else {
        editBtn.classList.remove('active');
        previewBtn.classList.add('active');
        textarea.style.display = 'none';
        previewPane.style.display = 'block';
        previewPane.innerHTML = renderMarkdown(textarea.value);
    }
}

// --- EVENT LISTENERS REGISTRATION ---
function setupEventListeners() {
    // Theme Toggle (floating)
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // Theme Toggle (sidebar)
    document.getElementById('sidebar-theme-btn').addEventListener('click', toggleTheme);
    
    // Welcome Page button
    document.getElementById('welcome-start-btn').addEventListener('click', async () => {
        showNotification("Checking configuration...", "warning");
        const hasConfig = await fetchUserSettings();
        await fetchAndRenderResumes();
        
        const hasCompletedResumes = state.resumes.some(r => r.status === "completed");
        
        if (hasConfig && hasCompletedResumes) {
            loadDashboard();
        } else if (hasConfig) {
            switchView('resumes-setup');
        } else {
            switchView('settings');
        }
    });
    
    // Settings Form submit
    document.getElementById('settings-form').addEventListener('submit', handleSettingsFormSubmit);
    
    // Settings Reset
    document.getElementById('settings-reset-btn').addEventListener('click', () => {
        document.getElementById('settings-form').reset();
        document.getElementById('email_footer').value = "";
        switchFooterTab('edit');
        showNotification("Fields cleared", "warning");
    });
    
    // Onboarding Finish button
    document.getElementById('onboarding-finish-btn').addEventListener('click', () => {
        loadDashboard();
        showNotification("Welcome to your Outbound Dashboard!", "success");
    });
    
    // Setup drag and drop for onboarding zone
    const onboardingZone = document.getElementById('onboarding-upload-zone');
    
    ['dragenter', 'dragover'].forEach(eventName => {
        onboardingZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            onboardingZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        onboardingZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            onboardingZone.classList.remove('dragover');
        }, false);
    });

    onboardingZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleOnboardingFiles(files);
    });

    // Setup drag and drop for sidebar drawer upload zone
    const drawerZone = document.getElementById('drawer-upload-zone');
    
    ['dragenter', 'dragover'].forEach(eventName => {
        drawerZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            drawerZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        drawerZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            drawerZone.classList.remove('dragover');
        }, false);
    });

    drawerZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleOnboardingFiles(files);
    });

    // Drawer Settings Form submit
    document.getElementById('drawer-settings-form').addEventListener('submit', handleDrawerSettingsFormSubmit);
    
    // Generate email outbound
    document.getElementById('generate-email-btn').addEventListener('click', triggerEmailGeneration);
    
    // Send email outbound
    document.getElementById('send-email-btn').addEventListener('click', triggerEmailSend);
    
    // Update live markdown preview as user types in editor pane
    document.getElementById('email-body-markdown-editor').addEventListener('input', (e) => {
        const previewPane = document.getElementById('email-preview-content');
        previewPane.innerHTML = renderMarkdown(e.target.value);
    });

    // Double-click out of textarea switches back to preview mode
    document.getElementById('email-body-markdown-editor').addEventListener('dblclick', () => {
        toggleEmailEditMode(false);
    });
}

// --- SETTINGS CONTROLLER ACTIONS ---
async function fetchUserSettings() {
    try {
        const res = await fetch(`/api/settings?t=${Date.now()}`);
        if (!res.ok) throw new Error("Could not fetch user configuration.");
        
        const data = await res.json();
        state.settings = data;
        
        // Populate onboarding settings inputs
        document.getElementById('groq_api_key').value = data.groq_api_key || "";
        document.getElementById('sender_email').value = data.sender_email || "";
        document.getElementById('sender_app_password').value = data.sender_app_password || "";
        document.getElementById('email_footer').value = data.email_footer || "";
        document.getElementById('preferred_tone').value = data.preferred_tone || "professional";
        document.getElementById('email_length').value = data.email_length || "medium";
        
        // Populate sidebar drawer settings inputs
        document.getElementById('drawer_groq_api_key').value = data.groq_api_key || "";
        document.getElementById('drawer_sender_email').value = data.sender_email || "";
        document.getElementById('drawer_sender_app_password').value = data.sender_app_password || "";
        document.getElementById('drawer_email_footer').value = data.email_footer || "";
        document.getElementById('drawer_preferred_tone').value = data.preferred_tone || "professional";
        document.getElementById('drawer_email_length').value = data.email_length || "medium";
        
        return !!data.groq_api_key;
    } catch (err) {
        console.error(err);
        showNotification("Failed to fetch settings.", "error");
        return false;
    }
}

async function handleSettingsFormSubmit(e) {
    e.preventDefault();
    
    const payload = {
        groq_api_key: document.getElementById('groq_api_key').value.trim(),
        sender_email: document.getElementById('sender_email').value.trim(),
        sender_app_password: document.getElementById('sender_app_password').value.trim(),
        email_footer: document.getElementById('email_footer').value,
        preferred_tone: document.getElementById('preferred_tone').value,
        email_length: document.getElementById('email_length').value
    };
    
    try {
        const res = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error("Update configuration failed.");
        
        showNotification("Outbound configuration saved successfully!");
        // Refresh local memory settings & go to resumes onboarding
        await fetchUserSettings();
        switchView('resumes-setup');
        fetchAndRenderResumes();
    } catch (err) {
        showNotification(err.message, "error");
    }
}

async function handleDrawerSettingsFormSubmit(e) {
    e.preventDefault();
    
    const payload = {
        groq_api_key: document.getElementById('drawer_groq_api_key').value.trim(),
        sender_email: document.getElementById('drawer_sender_email').value.trim(),
        sender_app_password: document.getElementById('drawer_sender_app_password').value.trim(),
        email_footer: document.getElementById('drawer_email_footer').value,
        preferred_tone: document.getElementById('drawer_preferred_tone').value,
        email_length: document.getElementById('drawer_email_length').value
    };
    
    try {
        const res = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error("Update configuration failed.");
        
        showNotification("Sidebar configuration updated successfully!");
        await fetchUserSettings();
        closeDrawer();
    } catch (err) {
        showNotification(err.message, "error");
    }
}

// --- DASHBOARD ACTIONS & VIEW ---
function loadDashboard() {
    switchView('dashboard');
    fetchAndRenderResumes();
}

// --- SIDEBAR DRAWER NAVIGATION CONTROLLERS ---
function showDashboardSection(section) {
    // Reset active status from all sidebar nav elements
    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const drawer = document.getElementById('side-drawer');
    const drawerTitle = document.getElementById('drawer-title');
    
    const resumesTab = document.getElementById('drawer-resumes-tab');
    const settingsTab = document.getElementById('drawer-settings-tab');
    
    if (section === 'workspace') {
        document.getElementById('sidebar-btn-workspace').classList.add('active');
        drawer.classList.remove('active');
    } else if (section === 'resumes') {
        document.getElementById('sidebar-btn-resumes').classList.add('active');
        drawerTitle.innerText = "Resume Manager";
        
        resumesTab.style.display = 'block';
        settingsTab.style.display = 'none';
        
        drawer.classList.add('active');
        fetchAndRenderResumes();
    } else if (section === 'settings') {
        document.getElementById('sidebar-btn-settings').classList.add('active');
        drawerTitle.innerText = "Outbound Settings";
        
        resumesTab.style.display = 'none';
        settingsTab.style.display = 'block';
        
        drawer.classList.add('active');
        fetchUserSettings();
    }
}

function closeDrawer() {
    const drawer = document.getElementById('side-drawer');
    drawer.classList.remove('active');
    
    // Set workspace active by default in the sidebar
    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('sidebar-btn-workspace').classList.add('active');
}

// --- RESUME CONTROLLER ACTIONS ---
async function fetchAndRenderResumes() {
    try {
        const res = await fetch(`/api/resumes?t=${Date.now()}`);
        if (!res.ok) throw new Error("Failed to load resumes list.");
        
        const resumes = await res.json();
        state.resumes = resumes;
        
        renderResumesTray();
        renderOnboardingResumesList();
        
        // Start polling if any resume is in "processing" state
        const isAnyIngesting = resumes.some(r => r.status === "processing");
        if (isAnyIngesting) {
            startResumesPolling();
        } else {
            stopResumesPolling();
        }
    } catch (err) {
        showNotification(err.message, "error");
    }
}

function startResumesPolling() {
    if (state.pollTimer) return;
    state.pollTimer = setInterval(fetchAndRenderResumes, 3000);
}

function stopResumesPolling() {
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
    }
}

// Render Dashboard Tray List
function renderResumesTray() {
    const tray = document.getElementById('resumes-tray-list');
    if (!tray) return;
    
    // Clear dynamic cards, keeping the upload button
    const uploadCard = tray.querySelector('.add-resume-card');
    tray.innerHTML = "";
    tray.appendChild(uploadCard);
    
    state.resumes.forEach(resume => {
        const card = document.createElement('div');
        card.className = `resume-card ${state.selectedResumeId === resume.id ? 'selected' : ''}`;
        card.onclick = () => selectResumeForAttachment(resume.id);
        
        let badgeClass = 'processing';
        let badgeText = 'Processing...';
        if (resume.status === 'completed') {
            badgeClass = 'completed';
            badgeText = 'Index Ready';
        } else if (resume.status === 'failed') {
            badgeClass = 'failed';
            badgeText = 'Ingest Failed';
        }
        
        card.innerHTML = `
            <button class="delete-resume-btn" onclick="event.stopPropagation(); deleteResume(${resume.id})" title="Delete PDF">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
            </button>
            <span class="resume-filename" title="${resume.filename}">${resume.filename}</span>
            <div class="status-badge ${badgeClass}">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"></circle></svg>
                ${badgeText}
            </div>
        `;
        
        tray.insertBefore(card, uploadCard);
    });
    
    updateAttachmentLabel();
}

// Render Onboarding setup list AND Drawer list
function renderOnboardingResumesList() {
    const listContainer = document.getElementById('onboarding-resumes-list');
    const drawerList = document.getElementById('drawer-resumes-list');
    
    // Render onboarding list
    if (listContainer) {
        if (state.resumes.length === 0) {
            listContainer.innerHTML = `<p style="color: var(--text-secondary); font-style: italic; text-align: center; padding: 20px;">No resumes uploaded yet.</p>`;
        } else {
            listContainer.innerHTML = "";
            state.resumes.forEach(resume => {
                const item = document.createElement('div');
                item.className = 'onboarding-resume-item';
                
                let badgeClass = 'processing';
                let badgeText = 'Processing...';
                if (resume.status === 'completed') {
                    badgeClass = 'completed';
                    badgeText = 'Completed';
                } else if (resume.status === 'failed') {
                    badgeClass = 'failed';
                    badgeText = `Failed: ${resume.error_message || 'Unknown error'}`;
                }
                
                item.innerHTML = `
                    <div class="onboarding-resume-info" style="max-width: 80%;">
                        <span class="onboarding-resume-name" style="word-break: break-all;" title="${resume.filename}">${resume.filename}</span>
                        <span class="status-badge ${badgeClass}" style="margin-top: 3px;">${badgeText}</span>
                    </div>
                    <button class="icon-btn" onclick="deleteResume(${resume.id})" style="color: var(--error-color); border-color: transparent;" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                    </button>
                `;
                listContainer.appendChild(item);
            });
        }
    }
    
    // Render drawer list
    if (drawerList) {
        if (state.resumes.length === 0) {
            drawerList.innerHTML = `<p style="color: var(--text-secondary); font-style: italic; font-size: 0.85rem; text-align: center;">No resumes uploaded.</p>`;
        } else {
            drawerList.innerHTML = "";
            state.resumes.forEach(resume => {
                const item = document.createElement('div');
                item.className = 'onboarding-resume-item';
                
                let badgeClass = 'processing';
                let badgeText = 'Processing...';
                if (resume.status === 'completed') {
                    badgeClass = 'completed';
                    badgeText = 'Completed';
                } else if (resume.status === 'failed') {
                    badgeClass = 'failed';
                    badgeText = 'Failed';
                }
                
                item.innerHTML = `
                    <div class="onboarding-resume-info" style="max-width: 80%;">
                        <span class="onboarding-resume-name" style="word-break: break-all;" title="${resume.filename}">${resume.filename}</span>
                        <span class="status-badge ${badgeClass}" style="margin-top: 3px;">${badgeText}</span>
                    </div>
                    <button class="icon-btn" onclick="deleteResume(${resume.id})" style="color: var(--error-color); border-color: transparent;" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                    </button>
                `;
                drawerList.appendChild(item);
            });
        }
    }
}

function selectResumeForAttachment(id) {
    const resume = state.resumes.find(r => r.id === id);
    if (!resume) return;
    
    if (resume.status !== 'completed') {
        showNotification("You can only attach resumes that have completed ingestion.", "warning");
        return;
    }
    
    if (state.selectedResumeId === id) {
        state.selectedResumeId = null;
    } else {
        state.selectedResumeId = id;
    }
    
    renderResumesTray();
}

function updateAttachmentLabel() {
    const label = document.getElementById('attached-resume-status');
    if (!label) return;
    
    if (state.selectedResumeId) {
        const resume = state.resumes.find(r => r.id === state.selectedResumeId);
        label.innerText = `Attachment: ${resume ? resume.filename : 'Ready'}`;
        label.style.color = 'var(--success-color)';
    } else {
        label.innerText = "Attachment: None";
        label.style.color = 'var(--text-secondary)';
    }
}

// --- RESUME UPLOAD FLOW HANDLERS ---
function triggerResumeUpload() {
    document.getElementById('resume-file-selector').click();
}

function triggerOnboardingResumeUpload() {
    document.getElementById('onboarding-resume-selector').click();
}

function triggerDrawerResumeUpload() {
    document.getElementById('drawer-resume-selector').click();
}

async function handleResumeFileSelected(event) {
    const file = event.target.files[0];
    if (!file) return;
    uploadSingleResumeFile(file);
    event.target.value = "";
}

async function handleOnboardingResumeSelected(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    await handleOnboardingFiles(files);
    event.target.value = "";
}

async function handleDrawerResumeSelected(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    await handleOnboardingFiles(files);
    event.target.value = "";
}

async function handleOnboardingFiles(files) {
    showNotification(`Uploading ${files.length} resume(s)...`, "warning");
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.type !== "application/pdf") {
            showNotification(`File "${file.name}" is not a PDF and was skipped.`, "error");
            continue;
        }
        await uploadSingleResumeFile(file, false);
    }
    showNotification("All files queued for indexing!", "success");
    fetchAndRenderResumes();
}

async function uploadSingleResumeFile(file, triggerRefresh = true) {
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const res = await fetch('/api/resumes', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || `Upload of ${file.name} failed.`);
        }
        
        if (triggerRefresh) {
            showNotification(`Resume "${file.name}" uploaded successfully!`, "success");
            fetchAndRenderResumes();
        }
    } catch (err) {
        showNotification(err.message, "error");
    }
}

async function deleteResume(id) {
    if (!confirm("Are you sure you want to delete this resume? All stored vector embeddings will be erased.")) return;
    
    try {
        const res = await fetch(`/api/resumes/${id}`, {
            method: 'DELETE'
        });
        
        if (!res.ok) throw new Error("Could not delete resume.");
        
        showNotification("Resume and vector index deleted successfully.");
        if (state.selectedResumeId === id) {
            state.selectedResumeId = null;
        }
        fetchAndRenderResumes();
    } catch (err) {
        showNotification(err.message, "error");
    }
}

// --- EMAIL GENERATION & STREAMING TYPEWRITER ---
async function triggerEmailGeneration() {
    const jobDescription = document.getElementById('job_description').value.trim();
    const companyDescription = document.getElementById('company_description').value.trim();
    
    if (!jobDescription) {
        showNotification("Please paste a Job Description first.", "error");
        return;
    }
    
    const completedResumes = state.resumes.filter(r => r.status === "completed");
    if (completedResumes.length === 0) {
        showNotification("You must upload at least one successfully processed resume first.", "error");
        return;
    }
    
    // Check settings
    if (!state.settings.groq_api_key) {
        const hasConfig = await fetchUserSettings();
        if (!hasConfig) {
            showNotification("Please configure your Settings (Groq API Key) first.", "error");
            switchView('settings');
            return;
        }
    }
    
    // Overlay loading
    const overlay = document.getElementById('editor-loading-overlay');
    overlay.style.display = 'flex';
    
    const payload = {
        job_description: jobDescription,
        company_description: companyDescription
    };
    
    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || "Failed to generate email.");
        }
        
        const data = await res.json();
        overlay.style.display = 'none';
        
        // Enable send button
        document.getElementById('send-email-btn').removeAttribute('disabled');
        
        // Stream output to fields
        await streamEmailResponse(data.subject, data.body);
        
    } catch (err) {
        overlay.style.display = 'none';
        showNotification(err.message, "error");
    }
}

// Typewriter Streaming Simulation
async function streamEmailResponse(subjectText, bodyText) {
    const subjectInput = document.getElementById('email-subject-input');
    const editorTextarea = document.getElementById('email-body-markdown-editor');
    const previewContent = document.getElementById('email-preview-content');
    
    // Force preview view mode during stream
    toggleEmailEditMode(false);
    
    // Write subject line instantly
    subjectInput.value = subjectText;
    
    // Stream body text word-by-word
    editorTextarea.value = "";
    previewContent.innerHTML = "";
    
    const words = bodyText.split(" ");
    let currentText = "";
    
    for (let i = 0; i < words.length; i++) {
        currentText += (i === 0 ? "" : " ") + words[i];
        editorTextarea.value = currentText;
        previewContent.innerHTML = renderMarkdown(currentText);
        
        previewContent.scrollTop = previewContent.scrollHeight;
        
        await new Promise(r => setTimeout(r, 18));
    }
    
    showNotification("Email draft generated successfully!", "success");
}

// --- OUTBOUND EMAIL SMTP TRANSMISSION ---
async function triggerEmailSend() {
    const recipientEmail = document.getElementById('recipient_email_input').value.trim();
    const subject = document.getElementById('email-subject-input').value.trim();
    const body = document.getElementById('email-body-markdown-editor').value.trim();
    
    if (!recipientEmail) {
        showNotification("Please input a recipient outbound email address.", "error");
        return;
    }
    if (!subject || !body) {
        showNotification("Please generate or write an email first.", "error");
        return;
    }
    
    const sendBtn = document.getElementById('send-email-btn');
    sendBtn.disabled = true;
    sendBtn.innerText = "Queueing...";
    
    const payload = {
        recipient_email: recipientEmail,
        subject: subject,
        body: body,
        resume_id: state.selectedResumeId
    };
    
    try {
        const res = await fetch('/api/send-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || "Failed to dispatch email.");
        }
        
        showNotification("Email has been securely queued and is sending in the background!", "success");
    } catch (err) {
        showNotification(err.message, "error");
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            Send Email
        `;
    }
}

// --- DOUBLE CLICK / EDIT MODE TOGGLE ---
function toggleEmailEditMode(isEdit) {
    state.isEmailEditMode = isEdit;
    
    const container = document.getElementById('email-editor-container');
    const previewPanel = document.getElementById('email-preview-panel-view');
    const editorPanel = document.getElementById('email-editor-panel-view');
    const modeIndicator = document.getElementById('panel-mode-indicator');
    const hintText = document.getElementById('editor-toggle-hint');
    const textarea = document.getElementById('email-body-markdown-editor');
    
    if (isEdit) {
        container.classList.add('is-editing');
        previewPanel.classList.remove('active');
        editorPanel.classList.add('active');
        modeIndicator.innerText = "EDIT MODE (MARKDOWN)";
        modeIndicator.style.background = "var(--accent-color)";
        modeIndicator.style.color = "#ffffff";
        hintText.innerText = "Double click inside or click out to return to Preview";
        
        textarea.focus();
    } else {
        container.classList.remove('is-editing');
        previewPanel.classList.add('active');
        editorPanel.classList.remove('active');
        modeIndicator.innerText = "PREVIEW MODE";
        modeIndicator.style.background = "var(--border-color)";
        modeIndicator.style.color = "var(--text-secondary)";
        hintText.innerText = "Double click here to edit raw Markdown code";
        
        const previewContent = document.getElementById('email-preview-content');
        previewContent.innerHTML = renderMarkdown(textarea.value);
    }
}
