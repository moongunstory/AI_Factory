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

    // Suggestions
    suggestions: []
};

// 탭 ID 정의 (상단 탭 UI용)
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
    AppState.activeTab = Tabs.CINEMATIC_STORY; // 기본 탭은 기존 시네마틱/스토리 플로우

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // 키보드 단축키: 1/2로 탭 전환
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

        // 트렌드/밈 탭 초기 화면 표시
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

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'API 호출 실패');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        alert(`오류: ${error.message}`);
        throw error;
    }
}

// ============================================================================
// Step 0: Mode Selection
// ============================================================================

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
// Trend · Meme Meta Mode (신규 탭)
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
    // 선택된 메타 소스를 바탕으로 후속 흐름 연결
    runTrendMemeMode(source);
}

function runTrendMemeMode(source) {
    // TODO: 여기서 최신 메타 자동 조사 로직을 연결합니다.
    // - 실시간 피드/랭킹/커스텀 패턴별로 크롤링·API 연동 지점 추가
    // - 밈 패턴 추출, 클립 구조 분석, 프롬프트 자동화 파이프라인 삽입
    // - 반복 제작용 프리셋/템플릿 저장 및 불러오기 연계

    const labelMap = {
        'live_feed': '🕒 실시간 피드',
        'ranking': '📊 랭킹 / 인기 탭',
        'custom_pattern': '🧬 커스텀 패턴 프리셋'
    };

    const selectionText = labelMap[source] || source;
    const resultBox = document.getElementById('trend-selection-result');

    if (resultBox) {
        resultBox.classList.remove('hidden');
        resultBox.innerHTML = `
            <strong>선택:</strong> ${selectionText}<br>
            TODO: 메타 분석 및 밈 패턴 기반 프롬프트 생성 로직을 여기에 연결합니다.<br>
            • 실시간/랭킹 신호 수집 → 포맷 분석 → 촬영/자막/오디오 프롬프트 추천<br>
            • 반복 제작용 템플릿/프리셋 저장소와 연동 예정
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

        select.innerHTML = '<option value="">세계관을 선택하세요</option>';

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
            alert('세계관 이름을 입력해주세요');
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
            alert('세계관을 선택해주세요');
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
            alert('시리즈를 선택해주세요');
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
        alert('이야기 아이디어를 입력해주세요');
        return;
    }

    AppState.storyIdea = storyIdea;
    AppState.theme = document.getElementById('theme-select').value;

    showLoading('expand-loading');

    try {
        // Step 1: Expand story
        const expandResult = await apiCall('/api/expand-story', 'POST', {
            simple_idea: storyIdea
        });

        AppState.expandedStory = expandResult.expanded_story;

        // Step 2: Generate prompts (this includes story beats and characters)
        const promptsResult = await apiCall('/api/generate-prompts', 'POST', {
            expanded_story: AppState.expandedStory,
            theme: AppState.theme
        });

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
            const description = beat.description_ko || beat.description_en || beat.description || '';
            beatEl.innerHTML = `
                <span class="beat-number">Beat ${beat.beat_number}</span>
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
            
            const name = char.name_ko || char.name_en || char.name || 'Unknown';
            const physical = char.physical_ko || char.physical_en || char.physical || '';
            const costume = char.costume_ko || char.costume_en || char.costume || '';
            const equipment = char.equipment_ko || char.equipment_en || char.equipment || '';

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

    document.getElementById('story-retry-btn').addEventListener('click', () => {
        showSection('step-1-story-input');
        updateProgressBar(1);
    });

    document.getElementById('story-expanded-back-btn').addEventListener('click', () => {
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
                <div class="stat-value">${Math.round(AppState.scenes.reduce((sum, s) => sum + (s.duration || 0), 0))}초</div>
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
        sceneEl.innerHTML = `
            <div class="scene-header">
                <div class="scene-title">Scene ${scene.scene_number}</div>
                <span class="scene-duration">${scene.duration}초</span>
            </div>
            <div class="scene-description">${scene.description || scene.description_kr || ''}</div>
            <div class="scene-prompt">
                <span class="prompt-label">프롬프트 (EN):</span>
                <div class="prompt-text">${scene.prompt_en}</div>
            </div>
            ${scene.prompt_kr ? `
                <div class="scene-prompt">
                    <span class="prompt-label">프롬프트 (KR):</span>
                    <div class="prompt-text">${scene.prompt_kr}</div>
                </div>
            ` : ''}
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
        alert('프롬프트가 복사되었습니다!');
    }).catch(err => {
        console.error('Copy failed:', err);
    });
};

function initPromptsDisplay() {
    document.getElementById('save-and-finish-btn').addEventListener('click', () => {
        alert('저장되었습니다! (실제 저장 기능은 백엔드 추가 필요)');
    });

    document.getElementById('start-new-btn').addEventListener('click', () => {
        if (confirm('새 프로젝트를 시작하시겠습니까? 현재 작업이 저장되지 않을 수 있습니다.')) {
            location.reload();
        }
    });
}

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    // Initialize all sections
    initModeSelection();
    initSeriesSetup();
    initStoryInput();
    initStoryExpanded();
    initPromptsDisplay();
    initTrendMemeMode();

    // Show initial section
    showSection('step-0-mode-selection');
    updateProgressBar(0);

    console.log('AI Short Factory - Series Studio initialized');
});
