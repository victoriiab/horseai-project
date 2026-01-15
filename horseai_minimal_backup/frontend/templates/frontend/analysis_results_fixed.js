async function loadAnalyses() {
    try {
        // Используем новый API
        const response = await fetch('/api/analysis/user/');
        const data = await response.json();

        if (data.success) {
            allAnalyses = data.analyses.sort((a, b) => {
                return new Date(b.analysis_date || 0) - new Date(a.analysis_date || 0);
            });
            
            updateStatistics();
            renderAnalyses();
        } else {
            showEmptyState();
        }
    } catch (error) {
        console.error('Ошибка загрузки анализов:', error);
        showEmptyState();
    }
}

function viewAnalysisDetail(analysisId) {
    window.location.href = `/analysis/${analysisId}/`;
}
