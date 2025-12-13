// frontend/app/components/workflow/SceneConfirmPanel.tsx
"use client";

import {
    Stack,
    Text,
    Paper,
    Group,
    Badge,
    Button,
    Checkbox,
    SimpleGrid,
    Image,
    ActionIcon,
    Tooltip,
    Box,
    Overlay,
    Progress,
} from "@mantine/core";
import {
    IconRefresh,
    IconCheck,
    IconX,
    IconPhoto,
    IconVideo,
    IconZoomIn,
} from "@tabler/icons-react";
import { useState } from "react";
import { SceneOutput } from "./WorkflowTypes";

interface SceneConfirmPanelProps {
    scenes: SceneOutput[];
    nodeType: 'image_gen' | 'video_gen';
    onApprove: (sceneIds: string[]) => void;
    onRegenerate: (sceneIds: string[]) => void;
    onApproveAll: () => void;
}

export function SceneConfirmPanel({
    scenes,
    nodeType,
    onApprove,
    onRegenerate,
    onApproveAll,
}: SceneConfirmPanelProps) {
    const [selectedForRegeneration, setSelectedForRegeneration] = useState<string[]>([]);

    const toggleSelection = (sceneId: string) => {
        setSelectedForRegeneration(prev =>
            prev.includes(sceneId)
                ? prev.filter(id => id !== sceneId)
                : [...prev, sceneId]
        );
    };

    const selectAll = () => {
        setSelectedForRegeneration(scenes.map(s => s.id));
    };

    const deselectAll = () => {
        setSelectedForRegeneration([]);
    };

    const handleRegenerate = () => {
        if (selectedForRegeneration.length > 0) {
            onRegenerate(selectedForRegeneration);
            setSelectedForRegeneration([]);
        }
    };

    const pendingCount = scenes.filter(s => s.status === 'pending').length;
    const generatedCount = scenes.filter(s => s.status === 'generated' || s.status === 'approved').length;

    return (
        <Paper p="lg" radius="md" withBorder>
            <Stack gap="md">
                {/* 헤더 */}
                <Group justify="space-between">
                    <Group gap="xs">
                        {nodeType === 'image_gen' ? (
                            <IconPhoto size={20} className="text-violet-500" />
                        ) : (
                            <IconVideo size={20} className="text-cyan-500" />
                        )}
                        <Text fw={600} size="lg">
                            {nodeType === 'image_gen' ? '🖼️ 이미지 확인' : '🎬 영상 확인'}
                        </Text>
                        <Badge variant="light" color="blue">
                            {generatedCount}/{scenes.length} 생성됨
                        </Badge>
                    </Group>
                    <Group gap="xs">
                        <Button
                            variant="subtle"
                            size="xs"
                            onClick={selectAll}
                        >
                            전체 선택
                        </Button>
                        <Button
                            variant="subtle"
                            size="xs"
                            onClick={deselectAll}
                        >
                            선택 해제
                        </Button>
                    </Group>
                </Group>

                {/* 진행률 */}
                {pendingCount > 0 && (
                    <Progress
                        value={(generatedCount / scenes.length) * 100}
                        size="sm"
                        radius="xl"
                        color="violet"
                        animated
                    />
                )}

                {/* 씬 그리드 */}
                <SimpleGrid cols={{ base: 2, sm: 3, md: 4, lg: 5 }} spacing="sm">
                    {scenes.map((scene) => (
                        <Paper
                            key={scene.id}
                            radius="md"
                            withBorder
                            style={{
                                overflow: 'hidden',
                                position: 'relative',
                                borderColor: selectedForRegeneration.includes(scene.id)
                                    ? 'var(--mantine-color-red-5)'
                                    : scene.status === 'approved'
                                        ? 'var(--mantine-color-green-5)'
                                        : undefined,
                                borderWidth: selectedForRegeneration.includes(scene.id) || scene.status === 'approved' ? 2 : 1,
                            }}
                        >
                            {/* 썸네일 영역 */}
                            <Box
                                style={{
                                    aspectRatio: '9/16',
                                    background: 'linear-gradient(135deg, var(--mantine-color-dark-6), var(--mantine-color-dark-5))',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    position: 'relative',
                                }}
                            >
                                {scene.imageUrl || scene.videoUrl ? (
                                    <Image
                                        src={scene.imageUrl || scene.videoUrl}
                                        alt={`Scene ${scene.sceneNumber}`}
                                        fit="cover"
                                        style={{ width: '100%', height: '100%' }}
                                    />
                                ) : (
                                    <Stack align="center" gap="xs">
                                        {scene.status === 'pending' ? (
                                            <>
                                                <Text size="xl">⏳</Text>
                                                <Text size="xs" c="dimmed">생성 대기</Text>
                                            </>
                                        ) : (
                                            <>
                                                <Text size="xl">{nodeType === 'image_gen' ? '🖼️' : '🎬'}</Text>
                                                <Text size="xs" c="dimmed">미리보기</Text>
                                            </>
                                        )}
                                    </Stack>
                                )}

                                {/* 씬 번호 배지 */}
                                <Badge
                                    style={{ position: 'absolute', top: 8, left: 8 }}
                                    size="sm"
                                    variant="filled"
                                    color="dark"
                                >
                                    #{scene.sceneNumber}
                                </Badge>

                                {/* 체크박스 (재생성 선택용) */}
                                <Checkbox
                                    checked={selectedForRegeneration.includes(scene.id)}
                                    onChange={() => toggleSelection(scene.id)}
                                    style={{ position: 'absolute', top: 8, right: 8 }}
                                    color="red"
                                    size="sm"
                                />

                                {/* 상태 오버레이 */}
                                {scene.status === 'approved' && (
                                    <Box
                                        style={{
                                            position: 'absolute',
                                            bottom: 0,
                                            left: 0,
                                            right: 0,
                                            padding: '4px 8px',
                                            background: 'rgba(34, 197, 94, 0.9)',
                                        }}
                                    >
                                        <Group gap={4} justify="center">
                                            <IconCheck size={12} />
                                            <Text size="xs" fw={500}>승인됨</Text>
                                        </Group>
                                    </Box>
                                )}

                                {scene.needsRegeneration && (
                                    <Box
                                        style={{
                                            position: 'absolute',
                                            bottom: 0,
                                            left: 0,
                                            right: 0,
                                            padding: '4px 8px',
                                            background: 'rgba(239, 68, 68, 0.9)',
                                        }}
                                    >
                                        <Group gap={4} justify="center">
                                            <IconRefresh size={12} />
                                            <Text size="xs" fw={500}>재생성 필요</Text>
                                        </Group>
                                    </Box>
                                )}
                            </Box>

                            {/* 프롬프트 미리보기 */}
                            <Box p="xs">
                                <Text size="xs" c="dimmed" lineClamp={2}>
                                    {scene.prompt || "프롬프트 대기중..."}
                                </Text>
                            </Box>
                        </Paper>
                    ))}
                </SimpleGrid>

                {/* 액션 버튼 */}
                <Group justify="space-between">
                    <Group gap="xs">
                        <Text size="sm" c="dimmed">
                            {selectedForRegeneration.length}개 선택됨
                        </Text>
                    </Group>
                    <Group gap="sm">
                        <Button
                            variant="light"
                            color="red"
                            leftSection={<IconRefresh size={16} />}
                            disabled={selectedForRegeneration.length === 0}
                            onClick={handleRegenerate}
                        >
                            선택 재생성 ({selectedForRegeneration.length})
                        </Button>
                        <Button
                            variant="gradient"
                            gradient={{ from: 'green', to: 'teal' }}
                            leftSection={<IconCheck size={16} />}
                            onClick={onApproveAll}
                        >
                            전체 승인 → 다음 단계
                        </Button>
                    </Group>
                </Group>
            </Stack>
        </Paper>
    );
}
