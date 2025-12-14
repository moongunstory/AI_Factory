"use client";

import React from 'react';
import {
    Paper,
    Text,
    Stack,
    Group,
    Button,
    Select,
    Textarea,
    Title,
    CloseButton,
    Divider,
    Badge,
    SimpleGrid,
    Image,
    Checkbox,
    ScrollArea,
    ThemeIcon,
    Alert
} from '@mantine/core';
import {
    IconDeviceFloppy,
    IconRefresh,
    IconPlayerPlay,
    IconCheck,
    IconPhoto,
    IconMovie,
    IconBrandOpenai,
    IconBrandGoogle,
    IconServer,
    IconBrain
} from '@tabler/icons-react';
import { WorkflowNode, AIModelConfig } from './WorkflowTypes';

interface NodeControlPanelProps {
    node: WorkflowNode;
    onClose: () => void;
    onUpdate: (updatedNode: WorkflowNode) => void;
    onRegenerate: () => void;
}

export function NodeControlPanel({ node, onClose, onUpdate, onRegenerate }: NodeControlPanelProps) {

    // Mock Data Helpers
    const getModelOptions = () => {
        if (['user_input', 'edit', 'upload'].includes(node.type)) return [];
        if (['llm_expand', 'prompt_gen', 'storyboard'].includes(node.type)) {
            return [
                { value: 'chatgpt', label: 'ChatGPT-4o' },
                { value: 'gemini', label: 'Gemini Pro' },
                { value: 'claude', label: 'Claude 3' },
            ];
        }
        if (['image_gen', 'video_gen'].includes(node.type)) {
            return [
                { value: 'local', label: 'Local Model (SDXL/CogVideo)' },
                { value: 'meta', label: 'Meta Emu' },
                { value: 'grok', label: 'Grok Vision' },
            ];
        }
        return [];
    };

    const handleModelChange = (value: string | null) => {
        if (!value) return;
        onUpdate({
            ...node,
            config: { ...node.config, provider: value }
        });
    };

    // Render Content based on Node Type
    const renderContent = () => {
        switch (node.type) {
            case 'user_input':
                return (
                    <Stack>
                        <Alert variant="light" color="blue" title="초기 아이디어">
                            자유롭게 상상하는 이야기를 적어주세요. 입력 후 엔터를 누르면 자동으로 GPT 확장이 시작됩니다.
                        </Alert>
                        <Textarea
                            label="이야기 입력"
                            placeholder="예: 네온 비 속에서 명상하는 사이버네틱 사무라이, 도시의 불빛이 반사되는 가운데 내면의 평화를 찾는다..."
                            minRows={6}
                            value={node.data?.input || ""}
                            onChange={(e) => {
                                const updatedNode = {
                                    ...node,
                                    data: { ...node.data, input: e.currentTarget.value }
                                };
                                onUpdate(updatedNode);
                            }}
                            onKeyDown={async (e) => {
                                if (e.key === 'Enter' && e.ctrlKey) {
                                    // Ctrl+Enter로 GPT 확장 자동 실행
                                    const input = node.data?.input;
                                    if (!input || !input.trim()) {
                                        alert("이야기를 먼저 입력해주세요!");
                                        return;
                                    }

                                    // 다음 노드(llm_expand)를 processing 상태로 변경
                                    alert(`GPT 확장을 시작합니다...\n(내용: ${input.substring(0, 30)}...)`);

                                    try {
                                        const response = await fetch('http://localhost:8000/api/automation/expand-story', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ story: input })
                                        });

                                        if (!response.ok) {
                                            const errorHttp = await response.json();
                                            throw new Error(errorHttp.detail || 'Automation failed');
                                        }

                                        const data = await response.json();

                                        // 현재 노드를 완료 상태로 변경
                                        onUpdate({
                                            ...node,
                                            status: 'completed',
                                            data: { ...node.data, input }
                                        });

                                        alert("확장 완료! 다음 노드를 확인하세요.");
                                    } catch (e) {
                                        console.error(e);
                                        alert("오류 발생: " + e + "\n\n백엔드 서버가 켜져있는지 확인해주세요.");
                                    }
                                }
                            }}
                        />
                        <Text size="xs" c="dimmed">💡 Ctrl+Enter를 누르면 바로 GPT 확장이 시작됩니다.</Text>
                    </Stack>
                );

            case 'llm_expand':
            case 'storyboard':
            case 'prompt_gen':
                return (
                    <Stack>
                        <Textarea
                            label={
                                node.type === 'llm_expand' ? "확장된 이야기" :
                                node.type === 'storyboard' ? "스토리보드" :
                                "생성된 프롬프트"
                            }
                            minRows={10}
                            value={node.data?.output || ""}
                            onChange={(e) => onUpdate({ ...node, data: { ...node.data, output: e.currentTarget.value } })}
                            placeholder={
                                node.type === 'llm_expand' ? "GPT 확장을 실행하면 이야기가 여기에 표시됩니다." :
                                node.type === 'storyboard' ? "스토리보드가 여기에 표시됩니다." :
                                "프롬프트가 여기에 표시됩니다."
                            }
                            readOnly={node.status === 'completed'}
                        />
                        {node.status === 'pending' && (
                            <Alert variant="light" color="yellow" icon={<IconBrain size={16} />}>
                                이전 단계를 완료하면 이 노드가 활성화됩니다.
                            </Alert>
                        )}
                        {node.status === 'completed' && (
                            <Alert variant="light" color="green" icon={<IconCheck size={16} />}>
                                ✅ 작업이 완료되었습니다. 필요시 수정하거나 다음 단계로 진행하세요.
                            </Alert>
                        )}
                    </Stack>
                );

            case 'image_gen':
                return (
                    <Stack>
                        <Text size="sm" fw={500}>생성된 이미지 (4장)</Text>
                        <SimpleGrid cols={2}>
                            {[1, 2, 3, 4].map((i) => (
                                <Paper key={i} withBorder p={4} style={{ cursor: 'pointer', position: 'relative' }}>
                                    <Image
                                        src="https://placehold.co/300x200/2C2E33/FFF?text=Image+Gen"
                                        radius="sm"
                                    />
                                    <Checkbox
                                        color="violet"
                                        styles={{ input: { cursor: 'pointer' } }}
                                        style={{ position: 'absolute', top: 8, right: 8 }}
                                    />
                                </Paper>
                            ))}
                        </SimpleGrid>
                        <Text size="xs" c="dimmed">마음에 들지 않는 이미지를 선택하고 재생성을 누르세요.</Text>
                    </Stack>
                );

            case 'video_gen':
                return (
                    <Stack>
                        <Paper withBorder p="md" bg="dark.8">
                            <Stack align="center" justify="center" h={200}>
                                <IconMovie size={40} opacity={0.5} />
                                <Text size="sm" c="dimmed">Video Preview Area</Text>
                            </Stack>
                        </Paper>
                        <Alert color="yellow" icon={<IconRefresh size={16} />}>
                            영상이 마음에 들지 않으면 설정을 변경하고 재생성하세요.
                        </Alert>
                    </Stack>
                );

            default:
                return <Text c="dimmed">이 노드는 별도의 설정이 없습니다.</Text>;
        }
    };

    const handleAction = async () => {
        if (node.type === 'llm_expand') {
            try {
                // [FIX] 사용자 입력 스토리 가져오기
                const storyPrompt = node.data?.input;

                if (!storyPrompt) {
                    alert("입력된 스토리가 없습니다. '이야기 입력' 단계를 먼저 완료해주세요.");
                    return;
                }

                alert(`브라우저를 열고 Fable Forge GPT에게 이야기를 전달합니다.\n(내용: ${storyPrompt.substring(0, 30)}...)\n\n* 브라우저가 열리면 로그인이 되어있는지 확인해주세요.`);

                const response = await fetch('http://localhost:8000/api/automation/expand-story', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ story: storyPrompt })
                });

                if (!response.ok) {
                    const errorHttp = await response.json();
                    throw new Error(errorHttp.detail || 'Automation failed');
                }

                const data = await response.json();

                // Update the node with the response
                console.log("GPT Response:", data.expanded_story);

                // [FIX] 부모 컴포넌트에 업데이트 요청 (결과 저장)
                onUpdate({
                    ...node,
                    status: 'completed',
                    data: { ...node.data, output: data.expanded_story }
                });

                alert("확장 완료! 결과를 텍스트 영역에 표시합니다.");

            } catch (e) {
                console.error(e);
                alert("오류 발생 (Backend Connection Failed): " + e + "\n\n백엔드 서버(port 8000)가 켜져있는지 확인해주세요.");
            }
        } else {
            onRegenerate();
        }
    };

    return (
        <Paper
            w={400}
            h="100%"
            p="md"
            radius={0}
            style={{
                borderLeft: '1px solid var(--mantine-color-dark-4)',
                background: 'var(--mantine-color-dark-8)',
                display: 'flex',
                flexDirection: 'column'
            }}
        >
            <Group justify="space-between" mb="xl">
                <Group gap="xs">
                    <ThemeIcon size="lg" radius="md" variant="light" color="violet">
                        <Text>{node.icon}</Text>
                    </ThemeIcon>
                    <Stack gap={0}>
                        <Title order={4}>{node.label}</Title>
                        <Badge variant="dot" size="xs" color={node.status === 'completed' ? 'green' : 'yellow'}>
                            {node.status}
                        </Badge>
                    </Stack>
                </Group>
                <CloseButton onClick={onClose} />
            </Group>

            <ScrollArea flex={1} mb="md">
                <Stack gap="xl">
                    {/* Model Select (if applicable) */}
                    {getModelOptions().length > 0 && (
                        <Select
                            label="AI 모델 선택"
                            data={getModelOptions()}
                            defaultValue={node.config.provider || 'local'}
                            onChange={handleModelChange}
                            leftSection={<IconServer size={16} />}
                        />
                    )}

                    <Divider label="작업 내용" labelPosition="left" />

                    {renderContent()}
                </Stack>
            </ScrollArea>

            <Divider my="md" />

            <Group grow>
                <Button
                    variant="light"
                    color="red"
                    leftSection={<IconRefresh size={18} />}
                    onClick={handleAction}
                >
                    {node.type === 'llm_expand' ? 'GPT 확장 실행' : '재생성'}
                </Button>
                <Button
                    variant="filled"
                    color="violet"
                    leftSection={<IconDeviceFloppy size={18} />}
                    onClick={onClose}
                >
                    저장 및 완료
                </Button>
            </Group>
        </Paper>
    );
}
