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

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'API call failed');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        alert(`Error: ${error.message}`);
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
            alert('Please enter a universe name');
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
            alert('Please select a universe');
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
            alert('Please select a series');
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
            <div class="suggestion-focus">Focus: ${suggestion.focus}</div>
        `;

        card.addEventListener('click', () => {
            selectSuggestion(index);
        });

        container.appendChild(card);
    });
}

function getSuggestionTypeLabel(type) {
    const labels = {
        'conflict': 'Conflict-driven',
        'character': 'Character growth',
        'event': 'Event-driven',
        'emotion': 'Emotion/Relationship',
        'dark': 'Dark route'
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
        alert('Please enter a story idea');
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
                <div class="character-detail"><strong>Appearance:</strong> ${physical}</div>
                <div class="character-detail"><strong>Costume:</strong> ${costume}</div>
                ${equipment ? `<div class="character-detail"><strong>Equipment:</strong> ${equipment}</div>` : ''}
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
        <h3>📊 Prompt generation complete</h3>
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">${AppState.scenes.length}</div>
                <div class="stat-label">Total scenes</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Math.round(AppState.scenes.reduce((sum, s) => sum + (s.duration || 0), 0))}s</div>
                <div class="stat-label">Estimated length</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${AppState.characterSheets.characters.length}</div>
                <div class="stat-label">Characters</div>
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
                    <span>Select to regenerate</span>
                </label>
                <button class="btn btn-small btn-secondary" onclick="copyPrompt(${index})">Copy</button>
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
        alert('Prompt copied!');
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

    document.getElementById('save-and-finish-btn').addEventListener('click', () => {
        alert('Saved! (Implement persistence in backend to store data.)');
    });

    document.getElementById('start-new-btn').addEventListener('click', () => {
        if (confirm('Start a new project? Current work may not be saved.')) {
            location.reload();
        }
    });

    // Generate images button
    document.getElementById('generate-images-btn').addEventListener('click', async () => {
        try {
            showLoading('image-generation-loading');

            const result = await apiCall('/api/generate-images', 'POST', {
                prompts_data: {
                    scenes: AppState.scenes
                }
            });

            AppState.generatedImages = result.images;
            displayImages();

            hideLoading('image-generation-loading');
        } catch (error) {
            hideLoading('image-generation-loading');
            alert(`Image generation failed: ${error.message}\n\nPlease ensure the ComfyUI server is running.`);
        }
    });

    // Regenerate images button
    document.getElementById('regenerate-images-btn').addEventListener('click', async () => {
        const checked = document.querySelectorAll('.image-checkbox:checked');
        if (checked.length === 0) {
            alert('Please select images to regenerate.');
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
                scenes: scenesToRegenerate
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
            alert(`${result.images.length}images were regenerated!`);
        } catch (error) {
            hideLoading('image-regenerate-loading');
            alert(`Image regeneration failed: ${error.message}`);
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
        <h3>🎨 Image generation complete</h3>
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">${successCount}</div>
                <div class="stat-label">Succeeded</div>
            </div>
            ${failedCount > 0 ? `
            <div class="stat-item">
                <div class="stat-value">${failedCount}</div>
                <div class="stat-label">Failed</div>
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
                    <div class="image-title">Scene ${image.scene_number}</div>
                    <label class="image-checkbox-label">
                        <input type="checkbox" class="image-checkbox" data-image="${index}">
                        Regenerate
                    </label>
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
                    <div class="image-title">Scene ${image.scene_number}</div>
                    <label class="image-checkbox-label">
                        <input type="checkbox" class="image-checkbox" data-image="${index}">
                        Regenerate
                    </label>
                </div>
                <div class="image-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">${image.error || 'Image failed'}</div>
                </div>
                <div class="image-info">
                    <div class="image-description">${image.description || ''}</div>
                </div>
            `;
        }

        container.appendChild(imageEl);
    });

    // Enable regenerate button when checkboxes are selected
    const checkboxes = document.querySelectorAll('.image-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateImageRegenerateButton);
    });

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
