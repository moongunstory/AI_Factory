// frontend/app/components/workflow/WorkflowTypes.ts

export type WorkflowNodeType =
    | 'user_input'      // 유저 간단 인풋
    | 'llm_expand'      // LLM 이야기 확장
    | 'storyboard'      // 스토리보드 프롬프트 생성
    | 'prompt_gen'      // [NEW] 프롬프트 생성 (이미지/영상용)
    | 'image_gen'       // 이미지 생성
    | 'video_gen'       // 영상 생성
    | 'audio'           // 오디오 추가
    | 'edit'            // 영상 편집
    | 'upload';         // SNS 업로드

export type NodeStatus = 'pending' | 'processing' | 'completed' | 'error' | 'waiting_confirm';

export type ModelType = 'local' | 'api';

export interface AIModelConfig {
    modelType: ModelType;
    provider?: string;
    model?: string;
    apiKey?: string;
}

export interface SceneOutput {
    id: string;
    sceneNumber: number;
    prompt: string;
    imageUrl?: string;
    videoUrl?: string;
    status: 'pending' | 'generated' | 'approved' | 'rejected';
    needsRegeneration: boolean;
}

export interface WorkflowNode {
    id: string;
    type: WorkflowNodeType;
    label: string;
    icon: string;
    status: NodeStatus;
    config: {
        modelType: ModelType;
        provider?: string;
        autoConfirm: boolean;
    };
    outputs?: SceneOutput[];
    error?: string;
    // React Flow specific properties
    position: { x: number; y: number };
    data?: any; // For custom node data
}

export interface WorkflowState {
    nodes: WorkflowNode[];
    currentNodeIndex: number;
    isAutoMode: boolean;
    isRunning: boolean;
}

// 기본 워크플로우 노드 템플릿
export const DEFAULT_WORKFLOW_NODES: Omit<WorkflowNode, 'id'>[] = [
    {
        type: 'user_input',
        label: '이야기 인풋',
        icon: '✏️',
        status: 'pending',
        config: { modelType: 'local', autoConfirm: true },
        position: { x: 0, y: 100 },
    },
    {
        type: 'llm_expand',
        label: '이야기 확장',
        icon: '🧠',
        status: 'pending',
        config: { modelType: 'api', provider: 'chatgpt', autoConfirm: false },
        position: { x: 200, y: 100 },
    },
    {
        type: 'storyboard',
        label: '스토리보드 작성',
        icon: '📝',
        status: 'pending',
        config: { modelType: 'api', provider: 'gemini', autoConfirm: false },
        position: { x: 400, y: 100 },
    },
    {
        type: 'prompt_gen',
        label: '프롬프트 생성',
        icon: '🔡',
        status: 'pending',
        config: { modelType: 'api', provider: 'chatgpt', autoConfirm: false },
        position: { x: 600, y: 100 },
    },
    {
        type: 'image_gen',
        label: '이미지 생성',
        icon: '🖼️',
        status: 'pending',
        config: { modelType: 'local', autoConfirm: false },
        position: { x: 800, y: 100 },
    },
    {
        type: 'video_gen',
        label: '영상 생성',
        icon: '🎬',
        status: 'pending',
        config: { modelType: 'api', provider: 'meta', autoConfirm: false },
        position: { x: 1000, y: 100 },
    },
    {
        type: 'audio',
        label: '오디오 생성',
        icon: '🔊',
        status: 'pending',
        config: { modelType: 'local', autoConfirm: false },
        position: { x: 1200, y: 100 },
    },
    {
        type: 'edit',
        label: '편집',
        icon: '✂️',
        status: 'pending',
        config: { modelType: 'local', autoConfirm: true },
        position: { x: 1400, y: 100 },
    },
    {
        type: 'upload',
        label: '업로드',
        icon: '📤',
        status: 'pending',
        config: { modelType: 'local', autoConfirm: false },
        position: { x: 1600, y: 100 },
    },
];

// 채널 관련 타입
export type ChannelType = 'theme' | 'trend';

export interface Channel {
    id: string;
    name: string;
    type: ChannelType;
    theme?: string; // 무협, 판타지, SF 등 (theme 타입일 때)
    platforms: ('youtube' | 'tiktok' | 'instagram')[];
    autoUpload: boolean;
    createdAt: Date;
}

// AI 모델 제공자
export interface AIProvider {
    id: string;
    name: string;
    category: 'llm' | 'image' | 'video' | 'audio';
    type: 'local' | 'api';
    models: string[];
}

export const AI_PROVIDERS: AIProvider[] = [
    // LLM
    { id: 'ollama', name: 'Ollama (로컬)', category: 'llm', type: 'local', models: ['llama3', 'mistral', 'codellama'] },
    { id: 'openai', name: 'OpenAI', category: 'llm', type: 'api', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'] },
    { id: 'anthropic', name: 'Anthropic', category: 'llm', type: 'api', models: ['claude-3-opus', 'claude-3-sonnet'] },
    { id: 'openrouter', name: 'OpenRouter (통합)', category: 'llm', type: 'api', models: ['auto'] },

    // Image
    { id: 'sd-local', name: 'Stable Diffusion (로컬)', category: 'image', type: 'local', models: ['sdxl', 'sd1.5'] },
    { id: 'dalle', name: 'DALL-E', category: 'image', type: 'api', models: ['dall-e-3', 'dall-e-2'] },
    { id: 'midjourney', name: 'Midjourney', category: 'image', type: 'api', models: ['v6', 'v5.2'] },

    // Video
    { id: 'cogvideo', name: 'CogVideoX (로컬)', category: 'video', type: 'local', models: ['cogvideox-5b'] },
    { id: 'runway', name: 'Runway', category: 'video', type: 'api', models: ['gen-3', 'gen-2'] },
    { id: 'pika', name: 'Pika', category: 'video', type: 'api', models: ['pika-1.0'] },

    // Audio
    { id: 'bark', name: 'Bark (로컬)', category: 'audio', type: 'local', models: ['bark'] },
    { id: 'elevenlabs', name: 'ElevenLabs', category: 'audio', type: 'api', models: ['eleven_multilingual_v2'] },
];
