// UI Components generators

// ============================================================================
// Job Card Component
// ============================================================================

function createJobCard(job) {
    return `
        <div class="job-card" data-job-id="${job.job_id}">
            <div class="job-card-header">
                <div>
                    <h3 class="job-title">${escapeHtml(job.title)}</h3>
                    <div class="job-meta">
                        <span>📋 ${job.proposal_count} proposals</span>
                        <span>🕒 ${formatDate(job.created_at)}</span>
                    </div>
                </div>
                <div class="tier-badges">
                    ${job.tier1_count > 0 ? `<span class="tier-badge tier-badge-1">T1: ${job.tier1_count}</span>` : ''}
                    ${job.tier2_count > 0 ? `<span class="tier-badge tier-badge-2">T2: ${job.tier2_count}</span>` : ''}
                    ${job.tier3_count > 0 ? `<span class="tier-badge tier-badge-3">T3: ${job.tier3_count}</span>` : ''}
                </div>
            </div>
            
            <p class="job-description">${escapeHtml(job.description.substring(0, 200))}${job.description.length > 200 ? '...' : ''}</p>
            
            <div class="job-actions">
                <button class="btn btn-primary" onclick="viewJobProposals('${job.job_id}')">
                    View Proposals
                </button>
                <button class="btn btn-success" onclick="analyzeJob('${job.job_id}')">
                    ▶️ Analyze
                </button>
                <button class="btn btn-secondary" onclick="addProposalToJob('${job.job_id}')">
                    ➕ Add Proposal
                </button>
                <button class="btn btn-danger" onclick="deleteJob('${job.job_id}')">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `;
}

// ============================================================================
// Proposal Card Component
// ============================================================================

function createProposalCard(proposal) {
    const tierClass = proposal.ai_tier ? `tier-${proposal.ai_tier}` : '';
    const tierIndicator = proposal.ai_tier ?
        `<div class="proposal-tier-indicator ${tierClass}"></div>` : '';

    return `
        <div class="proposal-card" data-proposal-id="${proposal.proposal_id}">
            ${tierIndicator}
            
            <div class="freelancer-info">
                <h3 class="freelancer-name">${escapeHtml(proposal.freelancer.name)}</h3>
                <p class="freelancer-title">${escapeHtml(proposal.freelancer.title)}</p>
            </div>
            
            <div class="proposal-stats">
                <div class="proposal-stat">
                    <div class="proposal-stat-label">JSS</div>
                    <div class="proposal-stat-value">${proposal.freelancer.job_success_score || 'N/A'}%</div>
                </div>
                <div class="proposal-stat">
                    <div class="proposal-stat-label">Earnings</div>
                    <div class="proposal-stat-value">$${formatNumber(proposal.freelancer.total_earnings || 0)}</div>
                </div>
                <div class="proposal-stat">
                    <div class="proposal-stat-label">Rate</div>
                    <div class="proposal-stat-value">$${proposal.freelancer.hourly_rate || 0}/hr</div>
                </div>
                <div class="proposal-stat">
                    <div class="proposal-stat-label">Bid</div>
                    <div class="proposal-stat-value">$${formatNumber(proposal.bid_amount)}</div>
                </div>
            </div>
            
            ${proposal.freelancer.top_rated_status ?
            `<div class="top-rated-badge">⭐ ${proposal.freelancer.top_rated_status}</div>` : ''}
            
            <div class="cover-letter-preview">
                ${escapeHtml(proposal.cover_letter.substring(0, 150))}${proposal.cover_letter.length > 150 ? '...' : ''}
            </div>
            
            ${proposal.ai_score !== null ? `
                <div class="ai-score">
                    <div>
                        <div class="score-label">AI Score</div>
                        <div class="score-value" style="color: ${getTierColor(proposal.ai_tier)}">${proposal.ai_score}/100</div>
                    </div>
                    <div>
                        <span class="tier-badge tier-badge-${proposal.ai_tier}">Tier ${proposal.ai_tier}</span>
                    </div>
                </div>
            ` : `
                <button class="btn btn-success" style="width: 100%; margin-top: 1rem;" 
                        onclick="analyzeSingleProposal('${proposal.proposal_id}')">
                    🤖 Analyze with AI
                </button>
            `}
            
            <div class="proposal-actions" style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                <button class="btn btn-secondary" onclick="viewProposalDetails('${proposal.proposal_id}')">
                    👁️ Details
                </button>
                <button class="btn btn-danger" onclick="deleteProposal('${proposal.proposal_id}')">
                    🗑️
                </button>
            </div>
        </div>
    `;
}

// ============================================================================
// Activity Item Component
// ============================================================================

function createActivityItem(activity) {
    const time = formatRelativeTime(activity.timestamp);
    const icon = getActivityIcon(activity.event_type);

    return `
        <div class="activity-item">
            <div class="activity-time">${time}</div>
            <div class="activity-message">
                ${icon} ${escapeHtml(activity.message)}
            </div>
        </div>
    `;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getTierColor(tier) {
    switch (tier) {
        case 1: return 'var(--color-tier1)';
        case 2: return 'var(--color-tier2)';
        case 3: return 'var(--color-tier3)';
        default: return 'var(--color-text-secondary)';
    }
}

function getActivityIcon(eventType) {
    const icons = {
        'job_created': '📋',
        'proposal_created': '📝',
        'analysis_started': '🔍',
        'analysis_complete': '✅',
        'data_seeded': '🎲',
        'data_cleared': '🗑️',
        'error': '❌',
        'progress': '⏳'
    };
    return icons[eventType] || '📌';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatRelativeTime(dateString) {
    if (!dateString) return 'just now';

    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function formatNumber(num) {
    if (typeof num !== 'number') return '0';
    return num.toLocaleString('en-US');
}

// ============================================================================
// Toast Notifications
// ============================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, CONFIG.TOAST_DURATION);
}
