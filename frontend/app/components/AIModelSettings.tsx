// frontend/app/components/AIModelSettings.tsx
"use client";

import {
    Stack,
    Text,
    Paper,
    Group,
    Badge,
    Button,
    TextInput,
    Select,
    Tabs,
    Card,
    ActionIcon,
    Tooltip,
    Switch,
    PasswordInput,
    Divider,
    Alert,
    ThemeIcon,
    SimpleGrid,
    Collapse,
} from "@mantine/core";
import {
    IconBrain,
    IconPhoto,
    IconVideo,
    IconMicrophone,
    IconKey,
    IconCheck,
    IconX,
    IconExternalLink,
    IconInfoCircle,
    IconServer,
    IconCloud,
    IconChevronDown,
    IconChevronUp,
} from "@tabler/icons-react";
import { useState } from "react";
import { AI_PROVIDERS, AIProvider, AIModelConfig } from "./workflow/WorkflowTypes";

interface AIModelSettingsProps {
    configs: Record<string, AIModelConfig>;
    onConfigChange: (category: string, config: AIModelConfig) => void;
    onTestConnection: (category: string) => Promise<boolean>;
}

export function AIModelSettings({
    configs,
    onConfigChange,
    onTestConnection,
}: AIModelSettingsProps) {
    const [expandedCategory, setExpandedCategory] = useState<string | null>("llm");
    const [testingCategory, setTestingCategory] = useState<string | null>(null);
    const [testResults, setTestResults] = useState<Record<string, boolean | null>>({});

    const categories = [
        { id: "llm", label: "LLM (텍스트)", icon: <IconBrain size={18} />, color: "blue" },
        { id: "image", label: "이미지 생성", icon: <IconPhoto size={18} />, color: "violet" },
        { id: "video", label: "영상 생성", icon: <IconVideo size={18} />, color: "cyan" },
        { id: "audio", label: "오디오/TTS", icon: <IconMicrophone size={18} />, color: "green" },
    ];

    const handleTest = async (category: string) => {
        setTestingCategory(category);
        try {
            const result = await onTestConnection(category);
            setTestResults(prev => ({ ...prev, [category]: result }));
        } catch {
            setTestResults(prev => ({ ...prev, [category]: false }));
        }
        setTestingCategory(null);
    };

    const getProviders = (category: string) => {
        return AI_PROVIDERS.filter(p => p.category === category);
    };

    return (
        <Stack gap="lg">
            {/* 헤더 */}
            <Stack gap="xs">
                <Text fw={700} size="xl">⚙️ AI 모델 설정</Text>
                <Text size="sm" c="dimmed">
                    각 단계에서 사용할 AI 모델을 설정하세요. 로컬 모델 또는 API 서비스를 선택할 수 있습니다.
                </Text>
            </Stack>

            {/* 통합 API 안내 */}
            <Alert
                variant="light"
                color="blue"
                icon={<IconInfoCircle size={18} />}
                title="통합 API 서비스"
            >
                <Stack gap="xs">
                    <Text size="sm">
                        <strong>OpenRouter</strong> 같은 통합 API 서비스를 사용하면 하나의 API 키로 여러 모델을 사용할 수 있습니다.
                    </Text>
                    <Group gap="xs">
                        <Button
                            variant="subtle"
                            size="xs"
                            rightSection={<IconExternalLink size={14} />}
                            component="a"
                            href="https://openrouter.ai"
                            target="_blank"
                        >
                            OpenRouter
                        </Button>
                        <Button
                            variant="subtle"
                            size="xs"
                            rightSection={<IconExternalLink size={14} />}
                            component="a"
                            href="https://replicate.com"
                            target="_blank"
                        >
                            Replicate
                        </Button>
                    </Group>
                </Stack>
            </Alert>

            {/* 카테고리별 설정 */}
            <Stack gap="md">
                {categories.map((category) => {
                    const providers = getProviders(category.id);
                    const localProviders = providers.filter(p => p.type === 'local');
                    const apiProviders = providers.filter(p => p.type === 'api');
                    const currentConfig = configs[category.id] || { modelType: 'local', autoConfirm: false };
                    const isExpanded = expandedCategory === category.id;

                    return (
                        <Card key={category.id} padding={0} radius="md" withBorder>
                            {/* 카테고리 헤더 */}
                            <Paper
                                p="md"
                                style={{ cursor: 'pointer' }}
                                onClick={() => setExpandedCategory(isExpanded ? null : category.id)}
                            >
                                <Group justify="space-between">
                                    <Group gap="sm">
                                        <ThemeIcon size="lg" radius="md" variant="light" color={category.color}>
                                            {category.icon}
                                        </ThemeIcon>
                                        <Stack gap={2}>
                                            <Text fw={600}>{category.label}</Text>
                                            <Text size="xs" c="dimmed">
                                                {currentConfig.modelType === 'local' ? '🖥️ 로컬 모델' : `☁️ ${currentConfig.provider || 'API'}`}
                                            </Text>
                                        </Stack>
                                    </Group>
                                    <Group gap="sm">
                                        {testResults[category.id] !== undefined && (
                                            <Badge
                                                color={testResults[category.id] ? "green" : "red"}
                                                variant="light"
                                                leftSection={testResults[category.id] ? <IconCheck size={12} /> : <IconX size={12} />}
                                            >
                                                {testResults[category.id] ? "연결됨" : "연결 실패"}
                                            </Badge>
                                        )}
                                        <ActionIcon variant="subtle">
                                            {isExpanded ? <IconChevronUp size={18} /> : <IconChevronDown size={18} />}
                                        </ActionIcon>
                                    </Group>
                                </Group>
                            </Paper>

                            {/* 확장 영역 */}
                            <Collapse in={isExpanded}>
                                <Divider />
                                <Stack p="md" gap="md">
                                    {/* 모델 타입 선택 */}
                                    <SimpleGrid cols={2}>
                                        <Paper
                                            p="md"
                                            radius="md"
                                            withBorder
                                            style={{
                                                cursor: 'pointer',
                                                borderColor: currentConfig.modelType === 'local'
                                                    ? `var(--mantine-color-${category.color}-5)`
                                                    : undefined,
                                                background: currentConfig.modelType === 'local'
                                                    ? `var(--mantine-color-${category.color}-light)`
                                                    : undefined,
                                            }}
                                            onClick={() => onConfigChange(category.id, { ...currentConfig, modelType: 'local' })}
                                        >
                                            <Stack align="center" gap="xs">
                                                <IconServer size={24} />
                                                <Text fw={500}>로컬 모델</Text>
                                                <Text size="xs" c="dimmed" ta="center">
                                                    내 컴퓨터에서 실행<br />무료, GPU 필요
                                                </Text>
                                            </Stack>
                                        </Paper>

                                        <Paper
                                            p="md"
                                            radius="md"
                                            withBorder
                                            style={{
                                                cursor: 'pointer',
                                                borderColor: currentConfig.modelType === 'api'
                                                    ? `var(--mantine-color-${category.color}-5)`
                                                    : undefined,
                                                background: currentConfig.modelType === 'api'
                                                    ? `var(--mantine-color-${category.color}-light)`
                                                    : undefined,
                                            }}
                                            onClick={() => onConfigChange(category.id, { ...currentConfig, modelType: 'api' })}
                                        >
                                            <Stack align="center" gap="xs">
                                                <IconCloud size={24} />
                                                <Text fw={500}>API 서비스</Text>
                                                <Text size="xs" c="dimmed" ta="center">
                                                    클라우드 서비스 사용<br />유료, 고품질
                                                </Text>
                                            </Stack>
                                        </Paper>
                                    </SimpleGrid>

                                    {/* 로컬 모델 설정 */}
                                    {currentConfig.modelType === 'local' && (
                                        <Stack gap="sm">
                                            <Text size="sm" fw={500}>로컬 모델 선택</Text>
                                            <Select
                                                placeholder="모델 선택"
                                                data={localProviders.flatMap(p =>
                                                    p.models.map(m => ({
                                                        value: `${p.id}:${m}`,
                                                        label: `${p.name} - ${m}`
                                                    }))
                                                )}
                                                value={currentConfig.model}
                                                onChange={(v) => onConfigChange(category.id, { ...currentConfig, model: v || undefined })}
                                            />
                                        </Stack>
                                    )}

                                    {/* API 설정 */}
                                    {currentConfig.modelType === 'api' && (
                                        <Stack gap="sm">
                                            <Select
                                                label="API 제공자"
                                                placeholder="선택하세요"
                                                data={apiProviders.map(p => ({ value: p.id, label: p.name }))}
                                                value={currentConfig.provider}
                                                onChange={(v) => onConfigChange(category.id, { ...currentConfig, provider: v || undefined })}
                                            />

                                            {currentConfig.provider && (
                                                <>
                                                    <Select
                                                        label="모델"
                                                        placeholder="선택하세요"
                                                        data={
                                                            apiProviders
                                                                .find(p => p.id === currentConfig.provider)
                                                                ?.models.map(m => ({ value: m, label: m })) || []
                                                        }
                                                        value={currentConfig.model}
                                                        onChange={(v) => onConfigChange(category.id, { ...currentConfig, model: v || undefined })}
                                                    />

                                                    <PasswordInput
                                                        label="API 키"
                                                        placeholder="sk-..."
                                                        leftSection={<IconKey size={16} />}
                                                        value={currentConfig.apiKey || ""}
                                                        onChange={(e) => onConfigChange(category.id, {
                                                            ...currentConfig,
                                                            apiKey: e.currentTarget.value
                                                        })}
                                                    />
                                                </>
                                            )}
                                        </Stack>
                                    )}

                                    {/* 테스트 버튼 */}
                                    <Group justify="flex-end">
                                        <Button
                                            variant="light"
                                            color={category.color}
                                            loading={testingCategory === category.id}
                                            onClick={() => handleTest(category.id)}
                                        >
                                            연결 테스트
                                        </Button>
                                    </Group>
                                </Stack>
                            </Collapse>
                        </Card>
                    );
                })}
            </Stack>

            {/* 저장 버튼 */}
            <Group justify="flex-end">
                <Button
                    variant="gradient"
                    gradient={{ from: "violet", to: "cyan" }}
                    size="md"
                >
                    설정 저장
                </Button>
            </Group>
        </Stack>
    );
}
