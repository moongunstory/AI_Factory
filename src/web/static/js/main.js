// State management
let state = {
    simpleIdea: '',
    expandedStory: '',
    selectedTheme: 'cinematic_realism',
    promptsData: null,
    storyBeats: null,
    characterSheets: null,
    selectedScenes: new Set()
};

// Theme descriptions
const themeDescriptions = {
    'cinematic_realism': '자연스러운 색감과 현실적인 조명으로 영화 같은 사실적인 분위기를 연출합니다.',
    'dark_fantasy': '깊은 보라색, 피 같은 붉은색, 어두운 그림자로 신비롭고 장엄한 다크 판타지 세계를 표현합니다.',
    'anime': '선명한 색상과 역동적인 앵글로 일본 애니메이션 스타일을 구현합니다.',
    'disney': '따뜻하고 생동감 있는 색채로 디즈니/픽사의 마법 같은 애니메이션 스타일을 재현합니다.',
    'game_cinematic': '언리얼 엔진 5 퀄리티의 게임 시네마틱으로 영웅적이고 웅장한 분위기를 연출합니다.',
    'cyber_fantasy': '네온 블루, 핫 핑크, 홀로그램 효과로 미래적이고 디스토피아적인 사이버펑크 세계를 표현합니다.',
    'horror': '불안정한 조명과 불안한 구도로 공포스럽고 긴장감 넘치는 분위기를 조성합니다.',
    'fantasy_adventure': '풍부한 색감과 장대한 카메라 워크로 판타지 모험의 경이로움을 담아냅니다.',
    'sci_fi': '차갑고 깨끗한 미래적 디자인으로 첨단 과학 기술의 세계를 표현합니다.',
    'retro_synthwave': '80년대 네온과 그라데이션으로 향수를 불러일으키는 신스웨이브 분위기를 연출합니다.'
};

// DOM elements
const elements = {
    simpleIdea: document.getElementById('simple-idea'),
    themeSelect: document.getElementById('theme-select'),
    themeDescription: document.getElementById('theme-description'),
    expandBtn: document.getElementById('expand-btn'),
    expandLoading: document.getElementById('expand-loading'),
    expandedSection: document.getElementById('expanded-section'),
    expandedStoryText: document.getElementById('expanded-story-text'),
    storyBeatsBox: document.getElementById('story-beats-box'),
    storyBeatsContent: document.getElementById('story-beats-content'),
    characterSheetsBox: document.getElementById('character-sheets-box'),
    characterSheetsContent: document.getElementById('character-sheets-content'),
    confirmBtn: document.getElementById('confirm-btn'),
    retryStoryBtn: document.getElementById('retry-story-btn'),
    generateLoading: document.getElementById('generate-loading'),
    promptsSection: document.getElementById('prompts-section'),
    promptsSummary: document.getElementById('prompts-summary'),
    scenesContainer: document.getElementById('scenes-container'),
    regenerateControls: document.getElementById('regenerate-controls'),
    regenerateBtn: document.getElementById('regenerate-btn'),
    regenerateLoading: document.getElementById('regenerate-loading'),
    regenerateInfo: document.getElementById('regenerate-info')
};

// Event listeners
elements.simpleIdea.addEventListener('input', (e) => {
    state.simpleIdea = e.target.value.trim();
    elements.expandBtn.disabled = !state.simpleIdea;
});

elements.themeSelect.addEventListener('change', (e) => {
    state.selectedTheme = e.target.value;
    elements.themeDescription.textContent = themeDescriptions[state.selectedTheme] || '';
});

elements.expandBtn.addEventListener('click', expandStory);
elements.retryStoryBtn.addEventListener('click', expandStory);
elements.confirmBtn.addEventListener('click', generatePrompts);
elements.regenerateBtn.addEventListener('click', regenerateSelectedScenes);

// API calls
async function expandStory() {
    try {
        showLoading(elements.expandLoading);
        elements.expandBtn.disabled = true;

        const response = await fetch('/api/expand-story', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ simple_idea: state.simpleIdea })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '이야기 확장 실패');
        }

        state.expandedStory = data.expanded_story;
        displayExpandedStory();

        // Hide prompts section when regenerating story
        elements.promptsSection.classList.add('hidden');

        // Hide story beats and character sheets until new prompts are generated
        elements.storyBeatsBox.classList.add('hidden');
        elements.characterSheetsBox.classList.add('hidden');

    } catch (error) {
        alert(`오류: ${error.message}`);
        console.error('Expand story error:', error);
    } finally {
        hideLoading(elements.expandLoading);
        elements.expandBtn.disabled = false;
    }
}

async function generatePrompts() {
    try {
        showLoading(elements.generateLoading);
        elements.confirmBtn.disabled = true;

        const response = await fetch('/api/generate-prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                expanded_story: state.expandedStory,
                theme: state.selectedTheme
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '프롬프트 생성 실패');
        }

        state.promptsData = data.prompts_data;
        state.storyBeats = data.story_beats;
        state.characterSheets = data.character_sheets;
        state.selectedScenes.clear();

        displayStoryBeats();
        displayCharacterSheets();
        displayPrompts();

    } catch (error) {
        alert(`오류: ${error.message}`);
        console.error('Generate prompts error:', error);
    } finally {
        hideLoading(elements.generateLoading);
        elements.confirmBtn.disabled = false;
    }
}

async function regenerateSelectedScenes() {
    if (state.selectedScenes.size === 0) return;

    try {
        showLoading(elements.regenerateLoading);
        elements.regenerateBtn.disabled = true;

        // Prepare scenes data
        const scenesToRegenerate = [];
        state.promptsData.scenes.forEach(scene => {
            if (state.selectedScenes.has(scene.scene_number)) {
                scenesToRegenerate.push({
                    scene_number: scene.scene_number,
                    scene_description: scene.description_kr || ''
                });
            }
        });

        const response = await fetch('/api/regenerate-scenes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenes: scenesToRegenerate,
                theme: state.selectedTheme
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '장면 재생성 실패');
        }

        // Update scenes in promptsData
        data.scenes.forEach(newScene => {
            const sceneIndex = state.promptsData.scenes.findIndex(
                s => s.scene_number === newScene.scene_number
            );
            if (sceneIndex !== -1) {
                state.promptsData.scenes[sceneIndex] = newScene;
            }
        });

        state.selectedScenes.clear();
        displayPrompts();

    } catch (error) {
        alert(`오류: ${error.message}`);
        console.error('Regenerate scenes error:', error);
    } finally {
        hideLoading(elements.regenerateLoading);
        elements.regenerateBtn.disabled = false;
    }
}

// Display functions
function displayExpandedStory() {
    elements.expandedStoryText.textContent = state.expandedStory;
    elements.expandedSection.classList.remove('hidden');
    elements.expandedSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayStoryBeats() {
    if (!state.storyBeats || !state.storyBeats.beats) {
        return;
    }

    const beats = state.storyBeats.beats;
    const summary = state.storyBeats.story_summary || '';

    let html = '';
    if (summary) {
        html += `<div class="beats-summary"><strong>전체 스토리 요약:</strong> ${summary}</div>`;
    }

    html += '<div class="beats-list">';
    beats.forEach(beat => {
        html += `
            <div class="beat-item">
                <div class="beat-number">비트 ${beat.beat_number}</div>
                <div class="beat-content">
                    <div class="beat-description">${beat.description}</div>
                    <div class="beat-function">${beat.narrative_function}</div>
                </div>
            </div>
        `;
    });
    html += '</div>';

    elements.storyBeatsContent.innerHTML = html;
    elements.storyBeatsBox.classList.remove('hidden');
}

function displayCharacterSheets() {
    if (!state.characterSheets || !state.characterSheets.characters) {
        return;
    }

    const characters = state.characterSheets.characters;

    let html = '';
    characters.forEach(char => {
        html += `
            <div class="character-card">
                <div class="character-name">${char.name}</div>
                <div class="character-role">${char.role}</div>
                <div class="character-details">
                    <div class="character-field">
                        <strong>외형:</strong> ${char.physical}
                    </div>
                    <div class="character-field">
                        <strong>의상:</strong> ${char.costume}
                    </div>
                    ${char.equipment ? `
                    <div class="character-field">
                        <strong>장비:</strong> ${char.equipment}
                    </div>
                    ` : ''}
                    <div class="character-field">
                        <strong>시각적 특징:</strong> ${char.personality_visual}
                    </div>
                </div>
            </div>
        `;
    });

    elements.characterSheetsContent.innerHTML = html;
    elements.characterSheetsBox.classList.remove('hidden');
}

function displayPrompts() {
    const scenes = state.promptsData.scenes || [];
    const totalScenes = scenes.length;
    const estimatedDuration = state.promptsData.estimated_duration || 0;

    // Update summary with more details
    elements.promptsSummary.innerHTML = `
        <div class="summary-stats">
            <div class="stat-item">
                <span class="stat-label">총 장면 수:</span>
                <span class="stat-value">${totalScenes}개</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">예상 영상 길이:</span>
                <span class="stat-value">${estimatedDuration.toFixed(1)}초 (${Math.floor(estimatedDuration / 60)}분 ${Math.floor(estimatedDuration % 60)}초)</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">선택된 테마:</span>
                <span class="stat-value">${themeDescriptions[state.selectedTheme]?.split('.')[0] || state.selectedTheme}</span>
            </div>
        </div>
    `;

    // Clear and render scenes
    elements.scenesContainer.innerHTML = '';
    scenes.forEach(scene => {
        const sceneCard = createSceneCard(scene);
        elements.scenesContainer.appendChild(sceneCard);
    });

    // Show prompts section
    elements.promptsSection.classList.remove('hidden');
    elements.promptsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Update regenerate controls
    updateRegenerateControls();
}

function createSceneCard(scene) {
    const card = document.createElement('div');
    card.className = 'scene-card';

    const duration = scene.duration || 0;
    const durationDisplay = duration ? `${duration.toFixed(1)}초` : '미정';

    card.innerHTML = `
        <div class="scene-header">
            <div class="scene-title">
                <span class="scene-number-badge">장면 ${scene.scene_number}</span>
                <span class="scene-duration-badge">${durationDisplay}</span>
            </div>
        </div>

        <div class="scene-content">
            <div class="scene-description">
                <strong>📝 장면 설명:</strong> ${scene.description_kr || 'N/A'}
            </div>

            <div class="scene-prompts">
                <div class="prompt-box">
                    <h4>🎨 영어 프롬프트 (Stable Diffusion)</h4>
                    <div class="prompt-text">${scene.prompt_en || 'N/A'}</div>
                </div>

                <div class="prompt-box">
                    <h4>🇰🇷 한국어 번역</h4>
                    <div class="prompt-text">${scene.prompt_kr || '번역 중...'}</div>
                </div>
            </div>

            <div class="scene-checkbox">
                <input
                    type="checkbox"
                    id="scene-${scene.scene_number}"
                    ${state.selectedScenes.has(scene.scene_number) ? 'checked' : ''}
                    onchange="handleSceneSelection(${scene.scene_number}, this.checked)"
                >
                <label for="scene-${scene.scene_number}">이 장면 재생성 선택</label>
            </div>
        </div>
    `;
    return card;
}

function handleSceneSelection(sceneNumber, isChecked) {
    if (isChecked) {
        state.selectedScenes.add(sceneNumber);
    } else {
        state.selectedScenes.delete(sceneNumber);
    }
    updateRegenerateControls();
}

function updateRegenerateControls() {
    const selectedCount = state.selectedScenes.size;

    if (selectedCount > 0) {
        elements.regenerateControls.classList.remove('hidden');
        elements.regenerateInfo.classList.add('hidden');
        elements.regenerateBtn.textContent = `선택한 ${selectedCount}개 장면 재생성`;
    } else {
        elements.regenerateControls.classList.add('hidden');
        elements.regenerateInfo.classList.remove('hidden');
    }
}

// Utility functions
function showLoading(element) {
    element.classList.remove('hidden');
}

function hideLoading(element) {
    element.classList.add('hidden');
}

// Make handleSceneSelection available globally
window.handleSceneSelection = handleSceneSelection;
