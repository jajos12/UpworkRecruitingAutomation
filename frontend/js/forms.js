// Form handling and modal dialogs

// ============================================================================
// Job Creation Form
// ============================================================================

function showCreateJobModal() {
    const modalHTML = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2>Create New Job</h2>
                    <button class="modal-close" onclick="closeModal()">×</button>
                </div>
                
                <form id="createJobForm" onsubmit="handleCreateJob(event)">
                    <div class="form-group">
                        <label for="jobTitle">Job Title *</label>
                        <input type="text" id="jobTitle" required placeholder="e.g., Python Developer for API Integration">
                    </div>
                    
                    <div class="form-group">
                        <label for="jobDescription">Job Description *</label>
                        <textarea id="jobDescription" rows="6" required 
                                  placeholder="Describe the job requirements, tech stack, and project details..."></textarea>
                        <button type="button" class="btn btn-secondary btn-sm" onclick="generateCriteria()" style="margin-top: 0.5rem;">
                            ✨ Auto-Generate Criteria from Description
                        </button>
                    </div>
                    
                    <div class="form-group">
                        <label>Must Have Criteria (one per line)</label>
                        <textarea id="mustHaveCriteria" rows="4" 
                                  placeholder="Job Success Score >= 90%
Total earnings >= $10,000
Skills include Python"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Nice to Have (format: criterion | weight)</label>
                        <textarea id="niceToHaveCriteria" rows="3" 
                                  placeholder="Top Rated or Top Rated Plus | 20
API integration experience | 15"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Red Flags (one per line)</label>
                        <textarea id="redFlagsCriteria" rows="3" 
                                  placeholder="Account less than 6 months old
Generic cover letter"></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Create Job</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.getElementById('modalContainer').innerHTML = modalHTML;
}

async function generateCriteria() {
    const description = document.getElementById('jobDescription').value;
    if (!description || description.length < 20) {
        showToast('Please enter a longer job description first', 'warning');
        return;
    }

    const btn = document.querySelector('button[onclick="generateCriteria()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '✨ Generating...';
    btn.disabled = true;

    try {
        const criteria = await API.generateCriteria(description);
        
        // Populate fields
        if (criteria.must_have) {
            document.getElementById('mustHaveCriteria').value = criteria.must_have.join('\n');
        }
        
        if (criteria.nice_to_have) {
            document.getElementById('niceToHaveCriteria').value = criteria.nice_to_have
                .map(item => `${item.text} | ${item.weight || 'Medium'}`)
                .join('\n');
        }
        
        if (criteria.red_flags) {
            document.getElementById('redFlagsCriteria').value = criteria.red_flags.join('\n');
        }
        
        showToast('Criteria generated successfully!', 'success');
    } catch (error) {
        showToast('Failed to generate criteria: ' + error.message, 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function handleCreateJob(event) {
    event.preventDefault();

    const title = document.getElementById('jobTitle').value;
    const description = document.getElementById('jobDescription').value;
    const mustHaveText = document.getElementById('mustHaveCriteria').value;
    const niceToHaveText = document.getElementById('niceToHaveCriteria').value;
    const redFlagsText = document.getElementById('redFlagsCriteria').value;

    // Parse criteria
    const must_have = mustHaveText.split('\n').filter(line => line.trim());

    const nice_to_have = niceToHaveText.split('\n')
        .filter(line => line.trim())
        .map(line => {
            const [criterion, weight] = line.split('|').map(s => s.trim());
            return { criterion, weight: parseInt(weight) || 10 };
        });

    const red_flags = redFlagsText.split('\n').filter(line => line.trim());

    const jobData = {
        title,
        description,
        criteria: {
            must_have,
            nice_to_have,
            red_flags
        }
    };

    try {
        await API.createJob(jobData);
        showToast('Job created successfully!', 'success');
        closeModal();
        await loadJobs();
        await updateDashboardStats();
    } catch (error) {
        showToast('Failed to create job: ' + error.message, 'error');
    }
}

// ============================================================================
// Job Editing Form
// ============================================================================

async function showEditJobModal(jobId) {
    try {
        const job = await API.getJob(jobId);
        
        let niceToHaveText = '';
        if (job.criteria && job.criteria.nice_to_have) {
            niceToHaveText = job.criteria.nice_to_have
                .map(item => `${item.text || item.criterion} | ${item.weight}`)
                .join('\n');
        }

        const modalHTML = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h2>Edit Job Criteria</h2>
                        <button class="modal-close" onclick="closeModal()">×</button>
                    </div>
                    
                    <form id="editJobForm" onsubmit="handleEditJob(event, '${jobId}')">
                        <div class="form-group">
                            <label for="jobTitle">Job Title</label>
                            <input type="text" id="jobTitle" required value="${escapeHtml(job.title)}">
                        </div>
                        
                        <div class="form-group">
                            <label for="jobDescription">Job Description</label>
                            <textarea id="jobDescription" rows="6" required>${escapeHtml(job.description)}</textarea>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="generateCriteria()" style="margin-top: 0.5rem;">
                                ✨ Re-Generate Criteria
                            </button>
                        </div>
                        
                        <div class="form-group">
                            <label>Must Have Criteria (one per line)</label>
                            <textarea id="mustHaveCriteria" rows="4">${job.criteria?.must_have?.join('\n') || ''}</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>Nice to Have (format: criterion | weight)</label>
                            <textarea id="niceToHaveCriteria" rows="3">${niceToHaveText}</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>Red Flags (one per line)</label>
                            <textarea id="redFlagsCriteria" rows="3">${job.criteria?.red_flags?.join('\n') || ''}</textarea>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                            <button type="submit" class="btn btn-primary">Save Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('modalContainer').innerHTML = modalHTML;
    } catch (error) {
        showToast('Failed to load job details: ' + error.message, 'error');
    }
}

async function handleEditJob(event, jobId) {
    event.preventDefault();

    const title = document.getElementById('jobTitle').value;
    const description = document.getElementById('jobDescription').value;
    const mustHaveText = document.getElementById('mustHaveCriteria').value;
    const niceToHaveText = document.getElementById('niceToHaveCriteria').value;
    const redFlagsText = document.getElementById('redFlagsCriteria').value;

    // Parse criteria
    const must_have = mustHaveText.split('\n').filter(line => line.trim());

    const nice_to_have = niceToHaveText.split('\n')
        .filter(line => line.trim())
        .map(line => {
            const [criterion, weight] = line.split('|').map(s => s.trim());
            return { text: criterion, weight: isNaN(parseInt(weight)) ? weight : parseInt(weight) };
        });

    const red_flags = redFlagsText.split('\n').filter(line => line.trim());

    const jobData = {
        title,
        description,
        criteria: {
            must_have,
            nice_to_have,
            red_flags
        }
    };

    try {
        await API.updateJob(jobId, jobData);
        showToast('Job updated successfully!', 'success');
        closeModal();
        
        // Ask to re-analyze
        if (confirm('Job criteria updated. Do you want to re-analyze all candidates?')) {
            await API.analyzeJobProposals(jobId, true);
            showToast('Re-analysis started...', 'info');
        }
        
        await loadJobs();
    } catch (error) {
        showToast('Failed to update job: ' + error.message, 'error');
    }
}

// ============================================================================
// Proposal Creation Form
// ============================================================================

function showCreateProposalModal(preselectedJobId = null) {
    // We'll need to load jobs first
    API.getJobs().then(jobs => {
        const jobOptions = jobs.map(job =>
            `<option value="${job.job_id}" ${job.job_id === preselectedJobId ? 'selected' : ''}>
                ${escapeHtml(job.title)}
            </option>`
        ).join('');

        const modalHTML = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content large-modal" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h2>Add Proposal</h2>
                        <button class="modal-close" onclick="closeModal()">×</button>
                    </div>
                    
                    <form id="createProposalForm" onsubmit="handleCreateProposal(event)">
                        <div class="form-group">
                            <label for="proposalJobId">Job *</label>
                            <select id="proposalJobId" required>
                                <option value="">Select a job...</option>
                                ${jobOptions}
                            </select>
                        </div>
                        
                        <h3>Freelancer Profile</h3>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="freelancerName">Name *</label>
                                <input type="text" id="freelancerName" required>
                            </div>
                            <div class="form-group">
                                <label for="freelancerTitle">Title *</label>
                                <input type="text" id="freelancerTitle" required placeholder="e.g., Senior Python Developer">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="hourlyRate">Hourly Rate ($)</label>
                                <input type="number" id="hourlyRate" min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="jobSuccessScore">Job Success Score (%)</label>
                                <input type="number" id="jobSuccessScore" min="0" max="100">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="totalEarnings">Total Earnings ($)</label>
                                <input type="number" id="totalEarnings" min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="topRatedStatus">Top Rated Status</label>
                                <select id="topRatedStatus">
                                    <option value="">None</option>
                                    <option value="Top Rated">Top Rated</option>
                                    <option value="Top Rated Plus">Top Rated Plus</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="skills">Skills (comma separated)</label>
                            <input type="text" id="skills" placeholder="Python, FastAPI, PostgreSQL, AWS">
                        </div>
                        
                        <div class="form-group">
                            <label for="workHistory">Work History Summary</label>
                            <textarea id="workHistory" rows="2" placeholder="Brief summary of experience..."></textarea>
                        </div>
                        
                        <h3>Proposal Details</h3>
                        
                        <div class="form-group">
                            <label for="coverLetter">Cover Letter *</label>
                            <textarea id="coverLetter" rows="6" required 
                                      placeholder="Write the freelancer's cover letter..."></textarea>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="bidAmount">Bid Amount ($) *</label>
                                <input type="number" id="bidAmount" required min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="estimatedDuration">Estimated Duration</label>
                                <input type="text" id="estimatedDuration" placeholder="e.g., 2-3 weeks">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="screeningAnswers">Screening Questions Answers</label>
                            <textarea id="screeningAnswers" rows="3" 
                                      placeholder="Answers to screening questions..."></textarea>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                            <button type="submit" class="btn btn-primary">Add Proposal</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('modalContainer').innerHTML = modalHTML;
    });
}

async function handleCreateProposal(event) {
    event.preventDefault();

    const jobId = document.getElementById('proposalJobId').value;
    const freelancerId = 'freelancer_' + Math.random().toString(36).substr(2, 9);

    const proposalData = {
        job_id: jobId,
        freelancer: {
            freelancer_id: freelancerId,
            name: document.getElementById('freelancerName').value,
            title: document.getElementById('freelancerTitle').value,
            hourly_rate: parseFloat(document.getElementById('hourlyRate').value) || null,
            job_success_score: parseInt(document.getElementById('jobSuccessScore').value) || null,
            total_earnings: parseFloat(document.getElementById('totalEarnings').value) || null,
            top_rated_status: document.getElementById('topRatedStatus').value || null,
            skills: document.getElementById('skills').value.split(',').map(s => s.trim()).filter(Boolean),
            work_history_summary: document.getElementById('workHistory').value || null,
            profile_url: `https://upwork.com/freelancers/${freelancerId}`
        },
        cover_letter: document.getElementById('coverLetter').value,
        bid_amount: parseFloat(document.getElementById('bidAmount').value),
        estimated_duration: document.getElementById('estimatedDuration').value || null,
        screening_answers: document.getElementById('screeningAnswers').value || null
    };

    try {
        await API.createProposal(proposalData);
        showToast('Proposal added successfully!', 'success');
        closeModal();
        await loadProposals();
        await loadJobs(); // Refresh to update counts
        await updateDashboardStats();
    } catch (error) {
        showToast('Failed to add proposal: ' + error.message, 'error');
    }
}

// ============================================================================
// Modal Utilities
// ============================================================================

function closeModal() {
    document.getElementById('modalContainer').innerHTML = '';
}

// Add CSS for modal and forms
const modalCSS = `
<style>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn var(--transition-fast);
}

.modal-content {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-glass-border);
    border-radius: var(--radius-xl);
    padding: var(--spacing-xl);
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: var(--shadow-xl);
}

.modal-content.large-modal {
    max-width: 800px;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--color-glass-border);
}

.modal-header h2 {
    font-size: var(--font-size-2xl);
    font-weight: 700;
}

.modal-close {
    background: none;
    border: none;
    color: var(--color-text-secondary);
    font-size: 2rem;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
}

.modal-close:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
}

.form-group {
    margin-bottom: var(--spacing-lg);
}

.form-group label {
    display: block;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
    color: var(--color-text-secondary);
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-glass-border);
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    font-size: var(--font-size-base);
    font-family: var(--font-family);
    transition: all var(--transition-fast);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--color-brand-primary);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-md);
}

.form-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--color-glass-border);
}

.modal-content h3 {
    font-size: var(--font-size-lg);
    font-weight: 700;
    margin: var(--spacing-lg) 0 var(--spacing-md) 0;
    color: var(--color-brand-primary);
}
</style>
`;

// Inject modal CSS
document.head.insertAdjacentHTML('beforeend', modalCSS);
