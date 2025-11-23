// State management
let state = {
    simpleIdea: '',
    expandedStory: '',
    promptsData: null,
    selectedScenes: new Set()
};

// DOM elements
const elements = {
    simpleIdea: document.getElementById('simple-idea'),
    expandBtn: document.getElementById('expand-btn'),
    expandLoading: document.getElementById('expand-loading'),
    expandedSection: document.getElementById('expanded-section'),
    expandedStoryText: document.getElementById('expanded-story-text'),
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
            body: JSON.stringify({ expanded_story: state.expandedStory })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '프롬프트 생성 실패');
        }

        state.promptsData = data.prompts_data;
        state.selectedScenes.clear();
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
            body: JSON.stringify({ scenes: scenesToRegenerate })
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

function displayPrompts() {
    const scenes = state.promptsData.scenes || [];
    const totalScenes = scenes.length;
    const estimatedDuration = state.promptsData.estimated_duration || 0;

    // Update summary
    elements.promptsSummary.textContent =
        `총 ${totalScenes}개 장면 | 예상 길이: ${estimatedDuration.toFixed(1)}초`;

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
    card.innerHTML = `
        <div class="scene-header">
            <div class="scene-title">장면 ${scene.scene_number}</div>
            <div class="scene-duration">${scene.duration || 0}초</div>
        </div>

        <div class="scene-content">
            <div class="scene-description">
                <strong>장면 설명:</strong> ${scene.description_kr || 'N/A'}
            </div>

            <div class="scene-prompts">
                <div class="prompt-box">
                    <h4>영어 프롬프트 (Stable Diffusion)</h4>
                    <div class="prompt-text">${scene.prompt_en || 'N/A'}</div>
                </div>

                <div class="prompt-box">
                    <h4>한국어 번역</h4>
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
