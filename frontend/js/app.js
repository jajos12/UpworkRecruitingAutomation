// Main application logic and event handlers

// ============================================================================
// State Management
// ============================================================================

let currentPage = 'dashboard';
let allJobs = [];
let allProposals = [];
let activityItems = [];
let currentAIConfig = {
    provider: 'claude',
    model: 'default',
    available: false
};

// ============================================================================
// Page Navigation
// ============================================================================

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateToPage(page);
        });
    });
}

function navigateToPage(pageName) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // Update pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`page-${pageName}`).classList.add('active');

    currentPage = pageName;

    // Load page data
    switch (pageName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'jobs':
            loadJobs();
            break;
        case 'proposals':
            loadProposals();
            break;
        case 'activity':
            // Activity feed is always live via WebSocket
            break;
    }
}

// ============================================================================
// Dashboard
// ============================================================================

async function loadDashboard() {
    await updateDashboardStats();
    await loadRecentJobs();
}

async function updateDashboardStats() {
    try {
        const stats = await API.getStats();

        document.getElementById('statTotalJobs').textContent = stats.total_jobs;
        document.getElementById('statTotalProposals').textContent = stats.total_proposals;
        document.getElementById('statTier1').textContent = stats.tier1_count;
        document.getElementById('statTier2').textContent = stats.tier2_count;
        document.getElementById('statTier3').textContent = stats.tier3_count;
        document.getElementById('statPending').textContent = stats.pending_count;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadRecentJobs() {
    try {
        allJobs = await API.getJobs();
        const recentJobs = allJobs.slice(0, 5);

        const container = document.getElementById('recentJobs');
        if (recentJobs.length === 0) {
            container.innerHTML = '<p class="empty-state">No jobs yet. Create one to get started!</p>';
        } else {
            container.innerHTML = recentJobs.map(job => createJobCard(job)).join('');
        }
    } catch (error) {
        console.error('Failed to load jobs:', error);
    }
}

// ============================================================================
// Jobs Page
// ============================================================================

async function loadJobs() {
    try {
        allJobs = await API.getJobs();

        const container = document.getElementById('jobsList');
        if (allJobs.length === 0) {
            container.innerHTML = '<p class="empty-state">No jobs available</p>';
        } else {
            container.innerHTML = allJobs.map(job => createJobCard(job)).join('');
        }

        // Update proposal job filter if on proposals page
        updateProposalJobFilter();
    } catch (error) {
        console.error('Failed to load jobs:', error);
        showToast('Failed to load jobs', 'error');
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job and all its proposals?')) return;

    try {
        await API.deleteJob(jobId);
        showToast('Job deleted', 'success');
        await loadJobs();
        await updateDashboardStats();
    } catch (error) {
        showToast('Failed to delete job: ' + error.message, 'error');
    }
}

async function analyzeJob(jobId) {
    try {
        showToast('Starting AI analysis...', 'info');
        const result = await API.analyzeJobProposals(jobId);
        showToast(result.message, 'success');
        await loadJobs();
        await loadProposals();
        await updateDashboardStats();
    } catch (error) {
        showToast('Analysis failed: ' + error.message, 'error');
    }
}

function addProposalToJob(jobId) {
    showCreateProposalModal(jobId);
}

function viewJobProposals(jobId) {
    navigateToPage('proposals');
    setTimeout(() => {
        document.getElementById('proposalJobFilter').value = jobId;
        filterProposals();
    }, 100);
}

// ============================================================================
// Proposals Page
// ============================================================================

async function loadProposals(jobId = null) {
    try {
        allProposals = await API.getProposals(jobId);

        const container = document.getElementById('proposalsList');
        if (allProposals.length === 0) {
            container.innerHTML = '<p class="empty-state">No proposals available</p>';
        } else {
            container.innerHTML = allProposals.map(proposal => createProposalCard(proposal)).join('');
        }
    } catch (error) {
        console.error('Failed to load proposals:', error);
        showToast('Failed to load proposals', 'error');
    }
}

function updateProposalJobFilter() {
    const filterEl = document.getElementById('proposalJobFilter');
    if (!filterEl) return;

    const currentValue = filterEl.value;
    filterEl.innerHTML = '<option value="">All Jobs</option>';

    allJobs.forEach(job => {
        const option = document.createElement('option');
        option.value = job.job_id;
        option.textContent = job.title;
        if (job.job_id === currentValue) option.selected = true;
        filterEl.appendChild(option);
    });
}

function filterProposals() {
    const jobId = document.getElementById('proposalJobFilter').value;
    loadProposals(jobId || null);
}

async function deleteProposal(proposalId) {
    if (!confirm('Delete this proposal?')) return;

    try {
        await API.deleteProposal(proposalId);
        showToast('Proposal deleted', 'success');
        await loadProposals();
        await loadJobs();
        await updateDashboardStats();
    } catch (error) {
        showToast('Failed to delete proposal: ' + error.message, 'error');
    }
}

async function analyzeSingleProposal(proposalId) {
    try {
        showToast('Analyzing proposal...', 'info');
        await API.analyzeProposal(proposalId);
        showToast('Analysis complete!', 'success');
        await loadProposals();
        await loadJobs();
        await updateDashboardStats();
    } catch (error) {
        showToast('Analysis failed: ' + error.message, 'error');
    }
}

function viewProposalDetails(proposalId) {
    // TODO: Implement detailed proposal view modal
    const proposal = allProposals.find(p => p.proposal_id === proposalId);
    if (proposal) {
        alert(`Proposal from ${proposal.freelancer.name}\n\nScore: ${proposal.ai_score || 'Not analyzed'}\nTier: ${proposal.ai_tier || 'N/A'}\n\n${proposal.ai_reasoning || 'No analysis available'}`);
    }
}

// ============================================================================
// Activity Feed
// ============================================================================

function addActivityItem(activity) {
    activityItems.unshift(activity);

    // Limit to max items
    if (activityItems.length > CONFIG.ACTIVITY_FEED_MAX_ITEMS) {
        activityItems = activityItems.slice(0, CONFIG.ACTIVITY_FEED_MAX_ITEMS);
    }

    const feedContainer = document.getElementById('activityFeed');
    if (!feedContainer) return;

    // Add new item at the top
    const itemHTML = createActivityItem(activity);
    feedContainer.insertAdjacentHTML('afterbegin', itemHTML);

    // Remove excess items
    const items = feedContainer.querySelectorAll('.activity-item');
    if (items.length > CONFIG.ACTIVITY_FEED_MAX_ITEMS) {
        items[items.length - 1].remove();
    }
}

function clearActivityFeed() {
    activityItems = [];
    const feedContainer = document.getElementById('activityFeed');
    if (feedContainer) {
        feedContainer.innerHTML = '<div class="activity-item"><div class="activity-time">Just now</div><div class="activity-message">Activity feed cleared</div></div>';
    }
}

// ============================================================================
// Quick Actions
// ============================================================================

async function seedMockData() {
    if (!confirm('This will create 3 sample jobs with proposals. Continue?')) return;

    try {
        showToast('Seeding mock data...', 'info');
        const result = await API.seedMockData();
        showToast(result.message, 'success');

        // Refresh all views
        await loadDashboard();
        await loadJobs();
        await loadProposals();
    } catch (error) {
        showToast('Failed to seed data: ' + error.message, 'error');
    }
}

async function clearAllData() {
    if (!confirm('This will delete ALL jobs and proposals. This cannot be undone. Continue?')) return;

    try {
        await API.clearAllData();
        showToast('All data cleared', 'success');

        // Refresh all views
        await loadDashboard();
        await loadJobs();
        await loadProposals();
    } catch (error) {
        showToast('Failed to clear data: ' + error.message, 'error');
    }
}

async function analyzeAllJobs() {
    if (!allJobs.length) {
        showToast('No jobs to analyze', 'info');
        return;
    }

    if (!confirm(`Analyze all proposals across ${allJobs.length} jobs?`)) return;

    try {
        showToast('Starting analysis...', 'info');

        for (const job of allJobs) {
            await API.analyzeJobProposals(job.job_id);
        }

        showToast('All jobs analyzed!', 'success');
        await loadJobs();
        await loadProposals();
        await updateDashboardStats();
    } catch (error) {
        showToast('Analysis failed: ' + error.message, 'error');
    }
}

// ============================================================================
// AI Configuration
// ============================================================================

async function initAIConfig() {
    try {
        const config = await API.getAIProviders();
        currentAIConfig = {
            provider: config.current,
            model: config.current_model === 'default' ? '' : config.current_model,
            available: config.available && config.available.length > 0
        };

        // Update UI
        const providerSelect = document.getElementById('aiProviderSelect');
        const modelInput = document.getElementById('aiModelInput');

        if (providerSelect) providerSelect.value = currentAIConfig.provider;
        if (modelInput) modelInput.value = currentAIConfig.model;

        updateAIStatusBadge();
    } catch (error) {
        console.error('Failed to load AI config:', error);
    }
}

async function handleAIProviderChange() {
    const provider = document.getElementById('aiProviderSelect').value;
    const model = document.getElementById('aiModelInput').value;

    // Only switch if actually changed
    if (provider === currentAIConfig.provider && model === currentAIConfig.model) return;

    try {
        showToast(`Switching to ${provider}...`, 'info');
        const result = await API.switchAIProvider(provider, model);

        currentAIConfig.provider = result.provider;
        currentAIConfig.model = result.model === 'default' ? '' : result.model;

        showToast(`Switched to ${provider}`, 'success');
        updateAIStatusBadge();
    } catch (error) {
        showToast('Failed to switch provider: ' + error.message, 'error');
        // Reset UI to current state
        initAIConfig();
    }
}

function updateAIStatusBadge() {
    const badge = document.getElementById('aiStatusBadge');
    if (!badge) return;

    if (currentAIConfig.provider) {
        badge.textContent = `Using ${currentAIConfig.provider.toUpperCase()}`;
        badge.className = 'ai-status-badge available';
    } else {
        badge.textContent = 'AI Unavailable';
        badge.className = 'ai-status-badge unavailable';
    }
}

// ============================================================================
// WebSocket Event Handlers (called from websocket.js)
// ============================================================================

function updateStats(stats) {
    // Update stats display
    if (document.getElementById('statTotalJobs')) {
        document.getElementById('statTotalJobs').textContent = stats.total_jobs;
        document.getElementById('statTotalProposals').textContent = stats.total_proposals;
        document.getElementById('statTier1').textContent = stats.tier1_count;
        document.getElementById('statTier2').textContent = stats.tier2_count;
        document.getElementById('statTier3').textContent = stats.tier3_count;
        document.getElementById('statPending').textContent = stats.pending_count;
    }

    // Reload current page data
    if (currentPage === 'jobs') {
        loadJobs();
    } else if (currentPage === 'proposals') {
        filterProposals();
    }
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 UpworkHireBot UI initialized');

    // Initialize navigation
    initializeNavigation();

    // Load initial AI config
    initAIConfig();

    // Load initial dashboard
    loadDashboard();

    // Add initial activity
    addActivityItem({
        timestamp: new Date().toISOString(),
        event_type: 'startup',
        message: 'Application started'
    });
});
