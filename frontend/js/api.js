// API Client for backend communication

const API = {
    // ========================================================================
    // Jobs
    // ========================================================================

    async createJob(jobData) {
        const response = await fetch(apiUrl('/jobs'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        if (!response.ok) throw new Error('Failed to create job');
        return await response.json();
    },

    async getJobs() {
        const response = await fetch(apiUrl('/jobs'));
        if (!response.ok) throw new Error('Failed to fetch jobs');
        return await response.json();
    },

    async getJob(jobId) {
        const response = await fetch(apiUrl(`/jobs/${jobId}`));
        if (!response.ok) throw new Error('Failed to fetch job');
        return await response.json();
    },

    async deleteJob(jobId) {
        const response = await fetch(apiUrl(`/jobs/${jobId}`), {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete job');
        return await response.json();
    },

    // ========================================================================
    // Proposals
    // ========================================================================

    async createProposal(proposalData) {
        const response = await fetch(apiUrl('/proposals'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(proposalData)
        });
        if (!response.ok) throw new Error('Failed to create proposal');
        return await response.json();
    },

    async getProposals(jobId = null) {
        const url = jobId ? apiUrl(`/proposals?job_id=${jobId}`) : apiUrl('/proposals');
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch proposals');
        return await response.json();
    },

    async getProposal(proposalId) {
        const response = await fetch(apiUrl(`/proposals/${proposalId}`));
        if (!response.ok) throw new Error('Failed to fetch proposal');
        return await response.json();
    },

    async deleteProposal(proposalId) {
        const response = await fetch(apiUrl(`/proposals/${proposalId}`), {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete proposal');
        return await response.json();
    },

    // ========================================================================
    // Analysis
    // ========================================================================

    async analyzeProposal(proposalId) {
        const response = await fetch(apiUrl(`/analyze/${proposalId}`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze proposal');
        }
        return await response.json();
    },

    async analyzeJobProposals(jobId) {
        const response = await fetch(apiUrl(`/analyze/job/${jobId}`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze job proposals');
        }
        return await response.json();
    },

    // ========================================================================
    // Stats & Data
    // ========================================================================

    async getStats() {
        const response = await fetch(apiUrl('/stats'));
        if (!response.ok) throw new Error('Failed to fetch stats');
        return await response.json();
    },

    async seedMockData() {
        const response = await fetch(apiUrl('/seed-data'), {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to seed data');
        return await response.json();
    },

    async clearAllData() {
        const response = await fetch(apiUrl('/clear-data'), {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to clear data');
        return await response.json();
    },

    // AI Configuration
    async getAIProviders() {
        const response = await fetch(apiUrl('/ai/providers'));
        if (!response.ok) throw new Error('Failed to fetch AI providers');
        return await response.json();
    },

    async switchAIProvider(provider, model) {
        const response = await fetch(apiUrl('/ai/switch'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, model })
        });
        if (!response.ok) throw new Error('Failed to switch AI provider');
        return await response.json();
    }
};
