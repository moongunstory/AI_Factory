/**
 * AI Short Factory - Series Studio
 * Main JavaScript Logic
 */

// ============================================================================
// Global State
// ============================================================================
const AppState = {
    mode: null, // 'oneshot' or 'series'
    currentStep: 0,
    activeTab: null,

    // Series mode data
    universeId: null,
    universeName: null,
    seriesId: null,
    seriesName: null,
    episodeNumber: null,

    // Story data
    storyIdea: null,
    expandedStory: null,
    storyBeats: null,
    characterSheets: null,
    theme: 'cinematic_realism',

    // Generated data
    scenes: [],
    generatedImages: [],
    generatedVideos: [],

    // Project ID for save/load
    projectId: null,
    projectPath: null,
    projectName: '',

    // Final assembly
    finalVideoPath: null,
    finalVideoDuration: null,
    finalVideoResolution: null,
    lastSavedAt: null,

    // Suggestions
    suggestions: []
};

const PROJECT_ID_KEY = 'current_project_id';

// Tab IDs for top-level navigation
const Tabs = {
    CINEMATIC_STORY: 'cinematic-story',
    TREND_MEME_META: 'trend-meme'
};

// ============================================================================
// Helper Functions
// ============================================================================

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.step-section').forEach(section => {
        section.classList.add('hidden');
    });

    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function persistProjectId(projectId) {
    if (!projectId) return;
    AppState.projectId = projectId;
}

function loadPersistedProjectId() {
    return null;
}

function clearPersistedProjectId() {
    AppState.projectId = null;
}

function updateProgressBar(step) {
    const progressBar = document.getElementById('progress-bar');
    if (!progressBar) return;

    if (step === 0) {
        progressBar.classList.add('hidden');
        return;
    }

    progressBar.classList.remove('hidden');
    const steps = progressBar.querySelectorAll('.progress-step');

    steps.forEach((stepEl, index) => {
        stepEl.classList.remove('active', 'completed');
        if (index < step) {
            stepEl.classList.add('completed');
        } else if (index === step) {
            stepEl.classList.add('active');
        }
    });
}

function showLoading(loadingId) {
    const loading = document.getElementById(loadingId);
    if (loading) loading.classList.remove('hidden');
}

function hideLoading(loadingId) {
    const loading = document.getElementById(loadingId);
    if (loading) loading.classList.add('hidden');
}

// ============================================================================
// Tab Navigation (Cinematic/Story vs Trend/Meme)
// ============================================================================

function initTabs() {
    AppState.activeTab = Tabs.CINEMATIC_STORY; // Default tab is cinematic/story flow

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // Keyboard shortcuts: switch tabs with 1/2
    document.addEventListener('keydown', (event) => {
        if (event.key === '1') {
            switchTab(Tabs.CINEMATIC_STORY);
        } else if (event.key === '2') {
            switchTab(Tabs.TREND_MEME_META);
        }
    });

    renderTabContent();
}

function switchTab(tabId) {
    if (!Object.values(Tabs).includes(tabId)) return;

    AppState.activeTab = tabId;
    renderTabContent();
}

function renderTabContent() {
    const cinematicContent = document.getElementById('tab-content-cinematic');
    const trendContent = document.getElementById('tab-content-trend');
    const progressBar = document.getElementById('progress-bar');

    document.querySelectorAll('.tab-btn').forEach(btn => {
        const isActive = btn.getAttribute('data-tab') === AppState.activeTab;
        btn.classList.toggle('active', isActive);
        const indicator = btn.querySelector('.tab-indicator');
        if (indicator) {
            indicator.textContent = isActive ? '●' : '○';
        }
    });

    if (AppState.activeTab === Tabs.CINEMATIC_STORY) {
        cinematicContent?.classList.remove('hidden');
        trendContent?.classList.add('hidden');
        showSection('step-0-mode-selection');
        updateProgressBar(AppState.currentStep || 0);
    } else {
        cinematicContent?.classList.add('hidden');
        trendContent?.classList.remove('hidden');
        progressBar?.classList.add('hidden');

        // Show initial view for trend/meme tab
        document.querySelectorAll('#tab-content-trend .step-section').forEach(section => {
            section.classList.remove('hidden');
        });
    }
}

async function apiCall(url, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const projectId = AppState.projectId;

        let payload = data;
        if (method !== 'GET') {
            payload = data ? { ...data } : {};
            if (projectId && !payload.project_id) {
                payload.project_id = projectId;
            }
        }

        if (payload && method !== 'GET') {
            options.body = JSON.stringify(payload);
        }

        const response = await fetch(url, options);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'API 호출에 실패했습니다');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        alert(`오류: ${error.message}`);
        throw error;
    }
}

async function deleteOutputFile(path) {
    if (!path) return false;
    try {
        await apiCall('/api/delete-file', 'POST', { path });
        return true;
    } catch (error) {
        alert(`파일 삭제 실패: ${error.message}`);
        return false;
    }
}

// ===========================================================================
// Project Load / Delete (autosave backend)
// ===========================================================================

let selectedProject = null;

async function fetchProjectList() {
    const loadingEl = document.getElementById('load-project-loading');
    const listEl = document.getElementById('project-list');
    const emptyEl = document.getElementById('no-project-message');
    const filterEl = document.getElementById('project-mode-filter');
    const sortEl = document.getElementById('project-sort-order');

    if (loadingEl) loadingEl.classList.remove('hidden');
    listEl?.classList.add('hidden');
    emptyEl?.classList.add('hidden');

    try {
        const modeFilter = filterEl?.value === 'all' ? '' : filterEl?.value;
        const query = modeFilter ? `?mode=${modeFilter}` : '';
        const result = await apiCall(`/api/list-projects${query}`);
        const projects = result.projects || [];

        if (projects.length === 0) {
            emptyEl?.classList.remove('hidden');
            listEl?.classList.add('hidden');
            return;
        }

        const sortOrder = sortEl?.value || 'newest';
        renderProjectList(projects, sortOrder);
    } catch (error) {
        console.error('Failed to fetch project list:', error);
    } finally {
        if (loadingEl) loadingEl.classList.add('hidden');
    }
}

function renderProjectList(projects, sortOrder = 'newest') {
    const listEl = document.getElementById('project-list');
    const confirmBtn = document.getElementById('confirm-load-btn');

    if (!listEl) return;

    listEl.innerHTML = '';
    selectedProject = null;
    if (confirmBtn) {
        confirmBtn.disabled = true;
        delete confirmBtn.dataset.selectedProject;
    }

    const sorted = [...projects];

    sorted.sort((a, b) => {
        if (sortOrder === 'oldest') {
            return (a.created_at || '').localeCompare(b.created_at || '');
        }
        if (sortOrder === 'title') {
            return (a.project_title || '').localeCompare(b.project_title || '');
        }
        return (b.created_at || '').localeCompare(a.created_at || '');
    });

    sorted.forEach(project => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.dataset.projectId = project.project_id;
        card.dataset.projectMode = project.mode || 'oneshot';

        const created = project.created_at ? project.created_at : '시간 정보 없음';
        const step = project.current_step ? `진행 단계: Step ${project.current_step}` : '진행 정보 없음';

        card.innerHTML = `
            <div class="title">${project.project_title || project.project_id}</div>
            <div class="meta">생성: ${created} | 모드: ${project.mode || 'N/A'}</div>
            <div class="meta">${step}</div>
            <div class="tag">${project.theme || '기본 테마'}</div>
            <button class="btn btn-small btn-danger project-delete-btn" type="button">삭제</button>
        `;

        card.addEventListener('click', () => {
            document.querySelectorAll('.project-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedProject = project;

            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.dataset.selectedProject = project.project_id;
                confirmBtn.dataset.projectMode = project.mode || 'oneshot';
            }
        });

        const deleteBtn = card.querySelector('.project-delete-btn');
        deleteBtn.addEventListener('click', async (event) => {
            event.stopPropagation();
            if (!confirm('프로젝트를 삭제할까요? 삭제하면 복구할 수 없습니다.')) return;
            await apiCall('/api/delete-project', 'POST', {
                project_id: project.project_id,
                mode: project.mode || 'oneshot'
            });
            if (AppState.projectId === project.project_id) {
                clearPersistedProjectId();
            }
            fetchProjectList();
        });

        listEl.appendChild(card);
    });

    listEl.classList.remove('hidden');
}

function openLoadModal() {
    const modal = document.getElementById('load-project-modal');
    if (!modal) return;

    modal.classList.remove('hidden');
    fetchProjectList();
}

function closeLoadModal() {
    const modal = document.getElementById('load-project-modal');
    const confirmBtn = document.getElementById('confirm-load-btn');

    if (modal) modal.classList.add('hidden');
    if (confirmBtn) {
        confirmBtn.disabled = true;
        delete confirmBtn.dataset.selectedProject;
        delete confirmBtn.dataset.projectMode;
    }
}

async function handleProjectLoad() {
    const confirmBtn = document.getElementById('confirm-load-btn');
    const projectId = confirmBtn?.dataset.selectedProject;
    const projectMode = confirmBtn?.dataset.projectMode || 'oneshot';

    if (!projectId) return;

    confirmBtn.disabled = true;

    try {
        const result = await apiCall('/api/load-project', 'POST', { project_id: projectId, mode: projectMode });
        applyLoadedProject(result.project);
        closeLoadModal();
        alert('프로젝트를 불러왔습니다.');
    } catch (error) {
        alert(`프로젝트 불러오기 실패: ${error.message}`);
    } finally {
        confirmBtn.disabled = false;
    }
}

function applyLoadedProject(projectEnvelope) {
    if (!projectEnvelope) return;

    const { metadata, story, prompts, images, final_video: finalVideo } = projectEnvelope;

    if (metadata?.project_id) {
        persistProjectId(metadata.project_id);
    }

    AppState.projectId = metadata?.project_id || null;
    AppState.projectName = metadata?.project_title || '';
    AppState.mode = metadata?.mode || AppState.mode;
    AppState.theme = prompts?.theme || AppState.theme;
    AppState.storyIdea = story?.simple_idea || '';
    AppState.expandedStory = story?.expanded_story || '';
    AppState.characterSheets = story?.character_sheets || { characters: [] };
    AppState.scenes = prompts?.scenes || [];
    AppState.generatedImages = images || [];
    AppState.generatedVideos = projectEnvelope?.videos || [];
    AppState.finalVideoPath = finalVideo?.path || null;
    AppState.finalVideoDuration = finalVideo?.duration || null;
    AppState.finalVideoResolution = finalVideo?.resolution || null;

    const storyInput = document.getElementById('story-idea-input');
    if (storyInput) storyInput.value = AppState.storyIdea || '';

    const themeSelect = document.getElementById('theme-select');
    if (themeSelect && AppState.theme) {
        themeSelect.value = AppState.theme;
    }

    document.querySelectorAll('.mode-card').forEach(card => card.classList.remove('selected'));
    if (AppState.mode === 'series') {
        document.getElementById('mode-series')?.classList.add('selected');
    } else if (AppState.mode === 'oneshot') {
        document.getElementById('mode-oneshot')?.classList.add('selected');
    }

    updateModeUiState();

    let step = metadata?.current_step || 1;

    if (AppState.expandedStory) {
        displayExpandedStory();
    }

    if (AppState.scenes && AppState.scenes.length > 0) {
        displayScenes();
    }

    if (AppState.generatedImages && AppState.generatedImages.length > 0) {
        displayImages();
    }

    if (AppState.generatedVideos && AppState.generatedVideos.length > 0) {
        displayVideos();
    }

    if (AppState.finalVideoPath) {
        displayFinalVideoResult();
    }

    let targetSection = 'step-1-story-input';
    if (step >= 5 && AppState.finalVideoPath) {
        targetSection = 'step-5-final-assembly';
    } else if (step >= 4 && AppState.generatedImages?.length) {
        targetSection = 'step-4-video-generation';
    } else if (step >= 3 && AppState.scenes?.length) {
        targetSection = 'step-3-prompts';
    } else if (step >= 2 && AppState.expandedStory) {
        targetSection = 'step-2-story-expanded';
    }

    showSection(targetSection);

    AppState.currentStep = step;
    updateProgressBar(step);
}

async function autoResumeProject() {
    const storedId = loadPersistedProjectId();
    if (!storedId) return;

    try {
        const result = await apiCall('/api/load-project', 'POST', { project_id: storedId });
        applyLoadedProject(result.project);
        alert('저장된 프로젝트를 자동으로 불러왔습니다.');
    } catch (error) {
        console.warn('자동 불러오기 실패', error);
        clearPersistedProjectId();
    }
}

function initProjectControls() {
    const loadBtn = document.getElementById('load-project-btn');
    const oneshotLoadBtn = document.getElementById('oneshot-load-btn');
    const closeModalBtn = document.getElementById('close-load-modal');
    const refreshBtn = document.getElementById('refresh-project-list-btn');
    const confirmLoadBtn = document.getElementById('confirm-load-btn');
    const modal = document.getElementById('load-project-modal');
    const filterEl = document.getElementById('project-mode-filter');
    const sortEl = document.getElementById('project-sort-order');

    loadBtn?.addEventListener('click', () => openLoadModal());
    oneshotLoadBtn?.addEventListener('click', () => openLoadModal());
    closeModalBtn?.addEventListener('click', () => closeLoadModal());
    refreshBtn?.addEventListener('click', () => fetchProjectList());
    confirmLoadBtn?.addEventListener('click', () => handleProjectLoad());
    filterEl?.addEventListener('change', () => fetchProjectList());
    sortEl?.addEventListener('change', () => fetchProjectList());

    modal?.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeLoadModal();
        }
    });
}

// ============================================================================
// Step 0: Mode Selection
// ============================================================================

function updateModeUiState() {
    const resumePanel = document.getElementById('oneshot-resume-panel');
    if (resumePanel) {
        resumePanel.classList.toggle('hidden', AppState.mode !== 'oneshot');
    }
}

function initModeSelection() {
    const modeButtons = document.querySelectorAll('.mode-select-btn');

    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-mode');
            selectMode(mode);
        });
    });
}

function selectMode(mode) {
    AppState.mode = mode;
    AppState.currentStep = 1;
    updateModeUiState();

    if (mode === 'oneshot') {
        // Skip series setup, go directly to story input
        showSection('step-1-story-input');
        updateProgressBar(1);
        // Hide suggestions for oneshot
        document.getElementById('next-episode-suggestions').classList.add('hidden');
    } else if (mode === 'series') {
        // Go to series setup
        showSection('step-0-5-series-setup');
        loadUniverses();
    }
}

// ============================================================================
// Trend · Meme Meta Mode (new tab)
// ============================================================================

function initTrendMemeMode() {
    const trendButtons = document.querySelectorAll('.trend-select-btn');

    trendButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const source = btn.getAttribute('data-source');
            handleTrendModeMenuSelection(source);
        });
    });
}

function handleTrendModeMenuSelection(source) {
    // Connect follow-up flow based on selected meta source
    runTrendMemeMode(source);
}

function runTrendMemeMode(source) {
    // TODO: Wire in latest meta auto-research logic here.
    // - Add crawl/API integration points per source.
    // - Hook in meme pattern extraction, clip analysis, and prompt automation.
    // - Connect preset/template storage for repeat production.

    const labelMap = {
        'live_feed': '🕒 Live feed',
        'ranking': '📊 Ranking / trending',
        'custom_pattern': '🧬 Custom pattern preset'
    };

    const selectionText = labelMap[source] || source;
    const resultBox = document.getElementById('trend-selection-result');

    if (resultBox) {
        resultBox.classList.remove('hidden');
        resultBox.innerHTML = `
            <strong>Selection:</strong> ${selectionText}<br>
            TODO: Connect meta analysis and meme-pattern prompt generation logic here.<br>
            • Collect live/ranking signals → analyze formats → recommend shoot/subtitle/audio prompts<br>
            • Planned: connect template/preset storage for repeat production
        `;
    }

    console.log(`[Trend/Meme] Selected source: ${selectionText}`);
}

// ============================================================================
// Step 0.5: Series Setup
// ============================================================================

async function loadUniverses() {
    try {
        const result = await apiCall('/api/universes');
        const select = document.getElementById('existing-universe-select');

        select.innerHTML = '<option value="">Select a universe</option>';

        result.universes.forEach(universe => {
            const option = document.createElement('option');
            option.value = universe.id;
            option.textContent = `${universe.name} (${universe.genre})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load universes:', error);
    }
}

function initSeriesSetup() {
    // Universe type radio buttons
    const universeTypeRadios = document.querySelectorAll('input[name="universe-type"]');
    universeTypeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'new') {
                document.getElementById('new-universe-form').classList.remove('hidden');
                document.getElementById('existing-universe-form').classList.add('hidden');
            } else {
                document.getElementById('new-universe-form').classList.add('hidden');
                document.getElementById('existing-universe-form').classList.remove('hidden');
            }
        });
    });

    // Series type radio buttons
    const seriesTypeRadios = document.querySelectorAll('input[name="series-type"]');
    seriesTypeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'new') {
                document.getElementById('new-series-form').classList.remove('hidden');
                document.getElementById('existing-series-form').classList.add('hidden');
            } else {
                document.getElementById('new-series-form').classList.add('hidden');
                document.getElementById('existing-series-form').classList.remove('hidden');
            }
        });
    });

    // Next button
    document.getElementById('series-setup-next-btn').addEventListener('click', async () => {
        await proceedFromSeriesSetup();
    });

    // Back button
    document.getElementById('series-setup-back-btn').addEventListener('click', () => {
        showSection('step-0-mode-selection');
        AppState.mode = null;
    });
}

async function proceedFromSeriesSetup() {
    const universeType = document.querySelector('input[name="universe-type"]:checked').value;

    if (universeType === 'new') {
        // Create new universe
        const name = document.getElementById('new-universe-name').value.trim();
        const genre = document.getElementById('new-universe-genre').value;
        const background = document.getElementById('new-universe-background').value.trim();
        const styleLock = document.getElementById('new-universe-style-lock').checked;

        if (!name) {
            alert('유니버스 이름을 입력하세요');
            return;
        }

        try {
            const universeId = name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
            const result = await apiCall('/api/universes', 'POST', {
                universe_id: universeId,
                name,
                genre,
                background,
                rules: {},
                style_lock: styleLock ? { theme: genre, locked: true } : null
            });

            AppState.universeId = result.universe.id;
            AppState.universeName = result.universe.name;
        } catch (error) {
            return;
        }
    } else {
        // Use existing universe
        const universeId = document.getElementById('existing-universe-select').value;
        if (!universeId) {
            alert('유니버스를 선택하세요');
            return;
        }
        AppState.universeId = universeId;
    }

    // Handle series
    const seriesType = document.querySelector('input[name="series-type"]:checked').value;

    if (seriesType === 'new') {
        const seriesName = document.getElementById('new-series-name').value.trim() || 'Season 1';
        const seriesId = `series_${Date.now()}`;

        try {
            await apiCall(`/api/universes/${AppState.universeId}/series`, 'POST', {
                series_id: seriesId,
                name: seriesName,
                description: ''
            });

            AppState.seriesId = seriesId;
            AppState.seriesName = seriesName;
            AppState.episodeNumber = 1;
        } catch (error) {
            return;
        }
    } else {
        const seriesId = document.getElementById('existing-series-select').value;
        if (!seriesId) {
            alert('시리즈를 선택하세요');
            return;
        }
        AppState.seriesId = seriesId;
        // TODO: Get next episode number
        AppState.episodeNumber = 1;
    }

    // Proceed to story input with suggestions
    showSection('step-1-story-input');
    updateProgressBar(1);
    await loadNextEpisodeSuggestions();
}

// ============================================================================
// Step 1: Story Input & Suggestions
// ============================================================================

async function loadNextEpisodeSuggestions() {
    if (AppState.mode !== 'series') return;

    const suggestionsSection = document.getElementById('next-episode-suggestions');
    suggestionsSection.classList.remove('hidden');

    showLoading('suggestions-loading');

    try {
        const result = await apiCall('/api/series/next-suggestions', 'POST', {
            universe_id: AppState.universeId,
            series_id: AppState.seriesId
        });

        AppState.suggestions = result.suggestions;
        displaySuggestions(result.suggestions);
    } catch (error) {
        console.error('Failed to load suggestions:', error);
    } finally {
        hideLoading('suggestions-loading');
    }
}

function displaySuggestions(suggestions) {
    const container = document.getElementById('suggestions-container');
    container.innerHTML = '';

    suggestions.forEach((suggestion, index) => {
        const card = document.createElement('div');
        card.className = 'suggestion-card';
        card.innerHTML = `
            <span class="suggestion-type">${getSuggestionTypeLabel(suggestion.type)}</span>
            <div class="suggestion-title">${suggestion.title}</div>
            <div class="suggestion-idea">${suggestion.idea}</div>
            <div class="suggestion-focus">초점: ${suggestion.focus}</div>
        `;

        card.addEventListener('click', () => {
            selectSuggestion(index);
        });

        container.appendChild(card);
    });
}

function getSuggestionTypeLabel(type) {
    const labels = {
        'conflict': '갈등 중심',
        'character': '캐릭터 성장',
        'event': '사건 중심',
        'emotion': '감정/관계',
        'dark': '다크 루트'
    };
    return labels[type] || type;
}

function selectSuggestion(index) {
    // Deselect all
    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Select clicked
    document.querySelectorAll('.suggestion-card')[index].classList.add('selected');

    // Fill story input
    const suggestion = AppState.suggestions[index];
    document.getElementById('story-idea-input').value = suggestion.idea;
}

function initStoryInput() {
    // Enable expand button when text is entered
    const storyInput = document.getElementById('story-idea-input');
    storyInput.addEventListener('input', () => {
        const expandBtn = document.getElementById('expand-story-btn');
        expandBtn.disabled = storyInput.value.trim().length === 0;
    });

    // Expand story button
    document.getElementById('expand-story-btn').addEventListener('click', async () => {
        await expandStory();
    });

    // Back button
    document.getElementById('story-back-btn').addEventListener('click', () => {
        if (AppState.mode === 'series') {
            showSection('step-0-5-series-setup');
        } else {
            showSection('step-0-mode-selection');
        }
    });

    // Custom story button
    const customBtn = document.getElementById('use-custom-story-btn');
    if (customBtn) {
        customBtn.addEventListener('click', () => {
            document.getElementById('next-episode-suggestions').classList.add('hidden');
        });
    }
}

async function expandStory() {
    const storyIdea = document.getElementById('story-idea-input').value.trim();
    if (!storyIdea) {
        alert('스토리 아이디어를 입력하세요');
        return;
    }

    AppState.storyIdea = storyIdea;
    AppState.theme = document.getElementById('theme-select').value;

    showLoading('expand-loading');

    try {
        // Step 1: Expand story
        const expandResult = await apiCall('/api/expand-story', 'POST', {
            simple_idea: storyIdea,
            mode: AppState.mode || 'oneshot',
            project_id: AppState.projectId
        });

        if (expandResult.project_id) {
            persistProjectId(expandResult.project_id);
        }

        AppState.expandedStory = expandResult.expanded_story;

        // Step 2: Generate prompts (this includes story beats and characters)
        const promptsResult = await apiCall('/api/generate-prompts', 'POST', {
            expanded_story: AppState.expandedStory,
            theme: AppState.theme,
            project_id: AppState.projectId,
            mode: AppState.mode || 'oneshot'
        });

        if (promptsResult.project_id) {
            persistProjectId(promptsResult.project_id);
        }

        AppState.storyBeats = promptsResult.story_beats;
        AppState.characterSheets = promptsResult.character_sheets;
        AppState.scenes = promptsResult.prompts_data.scenes;

        // Display results
        displayExpandedStory();

        // Move to next step
        AppState.currentStep = 2;
        showSection('step-2-story-expanded');
        updateProgressBar(2);

    } catch (error) {
        console.error('Story expansion failed:', error);
    } finally {
        hideLoading('expand-loading');
    }
}

function displayExpandedStory() {
    // Display expanded story
    document.getElementById('expanded-story-text').textContent = AppState.expandedStory;

    // Display story beats
    const beatsContainer = document.getElementById('story-beats-content');
    beatsContainer.innerHTML = '';

    if (AppState.storyBeats && AppState.storyBeats.beats) {
        AppState.storyBeats.beats.forEach(beat => {
            const beatEl = document.createElement('div');
            beatEl.className = 'beat-item';
            const description = beat.description_en || beat.description || '';
            beatEl.innerHTML = `
                <span class="beat-number">비트 ${beat.beat_number}</span>
                <span class="beat-description">${description}</span>
                <div class="beat-function">${beat.narrative_function}</div>
            `;
            beatsContainer.appendChild(beatEl);
        });
    }

    // Display characters
    const charactersContainer = document.getElementById('character-sheets-content');
    charactersContainer.innerHTML = '';

    if (AppState.characterSheets && AppState.characterSheets.characters) {
        AppState.characterSheets.characters.forEach(char => {
            const charEl = document.createElement('div');
            charEl.className = 'character-card';
            
            const name = char.name_en || char.name || 'Unknown';
            const physical = char.physical_en || char.physical || '';
            const costume = char.costume_en || char.costume || '';
            const equipment = char.equipment_en || char.equipment || '';

            charEl.innerHTML = `
                <div class="character-name">${name}</div>
                <span class="character-role">${char.role}</span>
                <div class="character-detail"><strong>외형:</strong> ${physical}</div>
                <div class="character-detail"><strong>복장:</strong> ${costume}</div>
                ${equipment ? `<div class="character-detail"><strong>장비:</strong> ${equipment}</div>` : ''}
            `;
            charactersContainer.appendChild(charEl);
        });
    }
}

// ============================================================================
// Step 2: Confirm and Generate
// ============================================================================

function initStoryExpanded() {
    document.getElementById('confirm-generate-btn').addEventListener('click', () => {
        // Scenes are already generated, just move to display
        AppState.currentStep = 3;
        displayScenes();
        showSection('step-3-prompts');
        updateProgressBar(3);
    });

    document.getElementById('story-retry-btn').addEventListener('click', async () => {
        // Go back to Step 1 and regenerate
        showSection('step-1-story-input');
        updateProgressBar(1);
    });

    document.getElementById('story-expanded-back-btn').addEventListener('click', () => {
        // Go back to Step 1 without clearing data
        showSection('step-1-story-input');
        updateProgressBar(1);
    });
}

// ============================================================================
// Step 3: Display Prompts
// ============================================================================

function displayScenes() {
    // Summary
    const summary = document.getElementById('prompts-summary');
    summary.innerHTML = `
        <h3>📊 프롬프트 생성 완료</h3>
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">${AppState.scenes.length}</div>
                <div class="stat-label">총 장면 수</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Math.round(AppState.scenes.reduce((sum, s) => sum + (s.duration || 0), 0))}s</div>
                <div class="stat-label">예상 길이</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${AppState.characterSheets.characters.length}</div>
                <div class="stat-label">등장 캐릭터</div>
            </div>
        </div>
    `;

    // Scenes
    const container = document.getElementById('scenes-container');
    container.innerHTML = '';

    AppState.scenes.forEach((scene, index) => {
        const sceneEl = document.createElement('div');
        sceneEl.className = 'scene-card';
        // Only show scene number, no title
        sceneEl.innerHTML = `
            <div class="scene-header">
                <div class="scene-title">${scene.scene_number}</div>
                <span class="scene-duration">${scene.duration}s</span>
            </div>
            <div class="scene-prompt">
                <div class="prompt-text">${scene.prompt_en}</div>
            </div>
            <div class="scene-actions">
                <label>
                    <input type="checkbox" class="scene-checkbox" data-scene="${index}">
                    <span>재생성 선택</span>
                </label>
                <button class="btn btn-small btn-secondary" onclick="copyPrompt(${index})">복사</button>
            </div>
        `;
        container.appendChild(sceneEl);
    });

    // Enable regenerate button when checkboxes are selected
    const checkboxes = document.querySelectorAll('.scene-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateRegenerateButton);
    });
}

function updateRegenerateButton() {
    const checked = document.querySelectorAll('.scene-checkbox:checked');
    const controls = document.getElementById('regenerate-controls');

    if (checked.length > 0) {
        controls.classList.remove('hidden');
    } else {
        controls.classList.add('hidden');
    }
}

window.copyPrompt = function(index) {
    const scene = AppState.scenes[index];
    const text = scene.prompt_en;

    navigator.clipboard.writeText(text).then(() => {
        alert('프롬프트를 복사했습니다!');
    }).catch(err => {
        console.error('Copy failed:', err);
    });
};

function initPromptsDisplay() {
    // Back button to Step 2 (preserving state)
    document.getElementById('prompts-back-btn').addEventListener('click', () => {
        AppState.currentStep = 2;
        showSection('step-2-story-expanded');
        updateProgressBar(2);
    });

    // Generate images button
    document.getElementById('generate-images-btn').addEventListener('click', async () => {
        try {
            showLoading('image-generation-loading');

            const result = await apiCall('/api/generate-images', 'POST', {
                prompts_data: {
                    scenes: AppState.scenes
                },
                mode: AppState.mode || 'oneshot'
            });

            AppState.generatedImages = result.images;
            displayImages();

            hideLoading('image-generation-loading');
        } catch (error) {
            hideLoading('image-generation-loading');
            alert(`이미지 생성 실패: ${error.message}\n\nComfyUI 서버가 실행 중인지 확인하세요.`);
        }
    });

    // Regenerate images button
    document.getElementById('regenerate-images-btn').addEventListener('click', async () => {
        const checked = document.querySelectorAll('.image-checkbox:checked');
        if (checked.length === 0) {
            alert('재생성할 이미지를 선택하세요.');
            return;
        }

        const scenesToRegenerate = [];
        checked.forEach(cb => {
            const index = parseInt(cb.dataset.image);
            const image = AppState.generatedImages[index];
            scenesToRegenerate.push({
                scene_number: image.scene_number,
                prompt: image.prompt,
                description: image.description,
                duration: image.duration
            });
        });

        try {
            showLoading('image-regenerate-loading');

            const result = await apiCall('/api/regenerate-images', 'POST', {
                scenes: scenesToRegenerate,
                mode: AppState.mode || 'oneshot'
            });

            // Update images in AppState
            result.images.forEach(newImage => {
                const index = AppState.generatedImages.findIndex(
                    img => img.scene_number === newImage.scene_number
                );
                if (index !== -1) {
                    AppState.generatedImages[index] = newImage;
                }
            });

            displayImages();
            hideLoading('image-regenerate-loading');
            alert(`${result.images.length}개의 이미지가 재생성되었습니다!`);
        } catch (error) {
            hideLoading('image-regenerate-loading');
            alert(`이미지 재생성 실패: ${error.message}`);
        }
    });
}

function displayImages() {
    const step4 = document.getElementById('step-4-images');
    step4.classList.remove('hidden');

    // Summary
    const summary = document.getElementById('images-summary');
    const successCount = AppState.generatedImages.filter(img => img.image_path).length;
    const failedCount = AppState.generatedImages.length - successCount;

    summary.innerHTML = `
        <h3>🎨 이미지 생성 완료</h3>
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">${successCount}</div>
                <div class="stat-label">성공</div>
            </div>
            ${failedCount > 0 ? `
            <div class="stat-item">
                <div class="stat-value">${failedCount}</div>
                <div class="stat-label">실패</div>
            </div>
            ` : ''}
        </div>
    `;

    // Images grid
    const container = document.getElementById('images-container');
    container.innerHTML = '';

    AppState.generatedImages.forEach((image, index) => {
        const imageEl = document.createElement('div');
        imageEl.className = 'image-card';

        if (image.image_path) {
            imageEl.innerHTML = `
                <div class="image-header">
                    <div class="image-title">장면 ${image.scene_number}</div>
                    <label class="image-checkbox-label">
                        <input type="checkbox" class="image-checkbox" data-image="${index}">
                        재생성
                    </label>
                    <button class="btn btn-danger btn-small image-delete" data-image="${index}">🗑️ 삭제</button>
                </div>
                <div class="image-preview">
                    <img src="/${image.image_path}" alt="Scene ${image.scene_number}"
                         onclick="openImageModal('${image.image_path}')">
                </div>
                <div class="image-info">
                    <div class="image-description">${image.description || ''}</div>
                    <div class="image-prompt">${image.prompt.substring(0, 100)}...</div>
                </div>
            `;
        } else {
            imageEl.innerHTML = `
                <div class="image-header">
                    <div class="image-title">장면 ${image.scene_number}</div>
                    <label class="image-checkbox-label">
                        <input type="checkbox" class="image-checkbox" data-image="${index}">
                        재생성
                    </label>
                </div>
                <div class="image-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">${image.error || '이미지 생성 실패'}</div>
                </div>
                <div class="image-info">
                    <div class="image-description">${image.description || ''}</div>
                </div>
            `;
        }

        container.appendChild(imageEl);
    });

    const deleteButtons = document.querySelectorAll('.image-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const idx = Number(btn.dataset.image);
            const target = AppState.generatedImages[idx];
            if (!target?.image_path) return;
            if (!confirm('이 이미지를 삭제할까요?')) return;
            const deleted = await deleteOutputFile(target.image_path);
            if (deleted) {
                AppState.generatedImages[idx].image_path = null;
                displayImages();
            }
        });
    });

    // Enable regenerate button when checkboxes are selected
    const checkboxes = document.querySelectorAll('.image-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateImageRegenerateButton);
    });

    // Show video generation button when all images are generated
    if (successCount > 0) {
        document.getElementById('start-video-generation-btn').classList.remove('hidden');
    }

    // Scroll to images
    step4.scrollIntoView({ behavior: 'smooth' });
}

function updateImageRegenerateButton() {
    const checked = document.querySelectorAll('.image-checkbox:checked');
    const controls = document.getElementById('image-regenerate-controls');

    if (checked.length > 0) {
        controls.classList.remove('hidden');
    } else {
        controls.classList.add('hidden');
    }
}

window.openImageModal = function(imagePath) {
    // Simple modal for full-size image viewing
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="this.parentElement.remove()"></div>
        <div class="modal-content">
            <img src="/${imagePath}" alt="Full size image">
            <button class="modal-close" onclick="this.parentElement.parentElement.remove()">✕</button>
        </div>
    `;
    document.body.appendChild(modal);
};

// ============================================================================
// Step 4: Video Generation
// ============================================================================

function initVideoGeneration() {
    document.getElementById('start-video-generation-btn').addEventListener('click', async () => {
        await startVideoGeneration();
    });

    document.getElementById('video-back-btn').addEventListener('click', () => {
        showSection('step-3-prompts');
        updateProgressBar(3);
    });

    document.getElementById('proceed-to-assembly-btn').addEventListener('click', () => {
        AppState.currentStep = 5;
        showSection('step-5-final-assembly');
        updateProgressBar(5);
    });
}

async function startVideoGeneration() {
    AppState.currentStep = 4;
    showSection('step-4-video-generation');
    updateProgressBar(4);

    // Summary
    const summary = document.getElementById('video-generation-summary');
    summary.innerHTML = `
        <h3>🎬 영상 생성 중</h3>
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">${AppState.generatedImages.filter(img => img.image_path).length}</div>
                <div class="stat-label">생성할 영상</div>
            </div>
        </div>
    `;

    try {
        // Use default values - AI will automatically configure video parameters
        const defaultDuration = 2.5;
        const defaultCamera = 'cinematic movement';
        const defaultFps = 24;

        // Call video generation API
        const validImages = AppState.generatedImages.filter(img => img.image_path);
        const videoRequests = validImages.map(img => {
            const scene = AppState.scenes.find(s => s.scene_number === img.scene_number);
            return {
                scene_number: img.scene_number,
                image_path: img.image_path,
                video_prompt: scene?.video_prompt || scene?.description || defaultCamera,
                duration: scene?.duration || img.duration || defaultDuration,
                fps: defaultFps,
                scene_description: scene?.description || ''
            };
        });

        // Update progress
        document.getElementById('video-progress-status').textContent = '영상 생성 중...';

        const result = await apiCall('/api/generate-videos', 'POST', {
            videos: videoRequests,
            mode: AppState.mode || 'oneshot',
            options: {
                duration: defaultDuration,
                camera: defaultCamera,
                fps: defaultFps
            }
        });

        if (result.project_id) {
            persistProjectId(result.project_id);
        }

        AppState.generatedVideos = result.videos;
        displayVideos();

        // Show proceed button
        document.getElementById('proceed-to-assembly-btn').classList.remove('hidden');

    } catch (error) {
        alert(`영상 생성 실패: ${error.message}\n\nComfyUI 서버와 WAN2.2 워크플로 템플릿을 확인하세요.`);
        document.getElementById('video-progress-status').textContent = '영상 생성 실패';
    }
}

function displayVideos() {
    const container = document.getElementById('videos-container');
    container.innerHTML = '';

    const totalVideos = AppState.generatedVideos.length;
    const successCount = AppState.generatedVideos.filter(v => v.video_path).length;

    // Update progress
    document.getElementById('video-progress-status').textContent = `완료: ${successCount}/${totalVideos}`;
    const progress = totalVideos > 0 ? (successCount / totalVideos) * 100 : 0;
    document.getElementById('video-progress-bar').style.width = `${progress}%`;

    AppState.generatedVideos.forEach((video, index) => {
        const videoEl = document.createElement('div');
        videoEl.className = 'video-card';

        if (video.video_path) {
            videoEl.innerHTML = `
                <div class="video-header">
                    <div class="video-title">장면 ${video.scene_number}</div>
                    <span class="video-duration">${video.duration}s</span>
                    <button class="btn btn-danger btn-small video-delete" data-video="${index}">🗑️ 삭제</button>
                </div>
                <div class="video-preview">
                    <video src="/${video.video_path}" controls></video>
                </div>
                <div class="video-info">
                    <div class="video-prompt">${video.video_prompt || ''}</div>
                </div>
            `;
        } else {
            videoEl.innerHTML = `
                <div class="video-header">
                    <div class="video-title">장면 ${video.scene_number}</div>
                </div>
                <div class="video-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">${video.error || '영상 생성 실패'}</div>
                </div>
            `;
        }

        container.appendChild(videoEl);
    });

    const deleteButtons = document.querySelectorAll('.video-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const idx = Number(btn.dataset.video);
            const target = AppState.generatedVideos[idx];
            if (!target?.video_path) return;
            if (!confirm('이 영상을 삭제할까요?')) return;
            const deleted = await deleteOutputFile(target.video_path);
            if (deleted) {
                AppState.generatedVideos[idx].video_path = null;
                displayVideos();
            }
        });
    });
}

// ============================================================================
// Step 5: Final Assembly
// ============================================================================

function initFinalAssembly() {
    // BGM checkbox toggle
    document.getElementById('add-bgm').addEventListener('change', (e) => {
        const bgmOptions = document.getElementById('bgm-options');
        if (e.target.checked) {
            bgmOptions.style.display = 'block';
        } else {
            bgmOptions.style.display = 'none';
        }
    });

    // Subtitle checkbox toggle
    document.getElementById('add-subtitles').addEventListener('change', (e) => {
        const subtitleOptions = document.getElementById('subtitle-options');
        if (e.target.checked) {
            subtitleOptions.style.display = 'block';
        } else {
            subtitleOptions.style.display = 'none';
        }
    });

    document.getElementById('start-assembly-btn').addEventListener('click', async () => {
        await startFinalAssembly();
    });

    document.getElementById('assembly-back-btn').addEventListener('click', () => {
        showSection('step-4-video-generation');
        updateProgressBar(4);
    });

    document.getElementById('download-final-video-btn').addEventListener('click', () => {
        const videoPath = document.getElementById('final-video-path').textContent;
        window.open(`/${videoPath}`, '_blank');
    });

    document.getElementById('start-new-project-btn').addEventListener('click', () => {
        if (confirm('새 프로젝트를 시작할까요?')) {
            location.reload();
        }
    });
}

function displayFinalVideoResult() {
    if (!AppState.finalVideoPath) return;

    const finalContainer = document.getElementById('final-video-result');
    finalContainer?.classList.remove('hidden');

    document.getElementById('final-video-player').src = `/${AppState.finalVideoPath}`;
    document.getElementById('final-video-path').textContent = AppState.finalVideoPath;

    if (AppState.finalVideoDuration) {
        document.getElementById('final-video-duration').textContent = `${AppState.finalVideoDuration}s`;
    }

    if (AppState.finalVideoResolution) {
        document.getElementById('final-video-resolution').textContent = AppState.finalVideoResolution;
    }
}

async function startFinalAssembly() {
    showLoading('assembly-loading');
    document.getElementById('assembly-progress').classList.remove('hidden');

    const addBGM = document.getElementById('add-bgm').checked;
    const bgmStyle = document.getElementById('bgm-select').value;
    const addSubtitles = document.getElementById('add-subtitles').checked;
    const subtitleStyle = document.getElementById('subtitle-style').value;

    try {
        const validVideos = AppState.generatedVideos.filter(v => v.video_path);

        const result = await apiCall('/api/assemble-final-video', 'POST', {
            videos: validVideos,
            options: {
                add_bgm: addBGM,
                bgm_style: bgmStyle,
                add_subtitles: addSubtitles,
                subtitle_style: subtitleStyle,
                theme: AppState.theme,
                story: AppState.expandedStory,
                project_title: AppState.projectName
            },
            mode: AppState.mode || 'oneshot'
        });

        if (result.project_id) {
            persistProjectId(result.project_id);
        }

        // Show final result
        document.getElementById('final-video-result').classList.remove('hidden');
        document.getElementById('final-video-player').src = `/${result.final_video_path}`;
        document.getElementById('final-video-path').textContent = result.final_video_path;
        document.getElementById('final-video-duration').textContent = `${result.duration}s`;
        document.getElementById('final-video-resolution').textContent = result.resolution || '768x1365';

        AppState.finalVideoPath = result.final_video_path;
        AppState.finalVideoDuration = result.duration;
        AppState.finalVideoResolution = result.resolution || '768x1365';
        AppState.currentStep = 5;
        updateProgressBar(5);

        // Update progress
        document.getElementById('assembly-progress-status').textContent = '완료!';
        document.getElementById('assembly-progress-bar').style.width = '100%';

        hideLoading('assembly-loading');

    } catch (error) {
        hideLoading('assembly-loading');
        alert(`최종 합성 실패: ${error.message}`);
        document.getElementById('assembly-progress-status').textContent = '합성 실패';
    }
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    // Initialize all sections
    initProjectControls();
    initModeSelection();
    initSeriesSetup();
    initStoryInput();
    initStoryExpanded();
    initPromptsDisplay();
    initVideoGeneration();
    initFinalAssembly();
    initTrendMemeMode();

    // Show initial section
    showSection('step-0-mode-selection');
    updateProgressBar(0);

    autoResumeProject();

    console.log('AI Short Factory - Series Studio initialized');
});
