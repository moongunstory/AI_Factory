// frontend/app/components/workflow/WorkflowSidebar.tsx
"use client";

import {
    Stack,
    Text,
    Paper,
    Group,
    Badge,
    Progress,
    Switch,
    ActionIcon,
    Tooltip,
    Divider,
    ScrollArea,
    Box,
    ThemeIcon,
    UnstyledButton,
} from "@mantine/core";
import {
    IconChevronLeft,
    IconChevronRight,
    IconPlayerPlay,
    IconPlayerPause,
    IconRefresh,
    IconSettings,
} from "@tabler/icons-react";
import { WorkflowNode, NodeStatus } from "./WorkflowTypes";

interface WorkflowSidebarProps {
    nodes: WorkflowNode[];
    currentNodeIndex: number;
    isAutoMode: boolean;
    isRunning: boolean;
    isOpen: boolean;
    onToggle: () => void;
    onAutoModeChange: (auto: boolean) => void;
    onNodeClick: (index: number) => void;
    onStart: () => void;
    onPause: () => void;
    onReset: () => void;
}

const getStatusColor = (status: NodeStatus): string => {
    switch (status) {
        case 'completed': return 'green';
        case 'processing': return 'blue';
        case 'waiting_confirm': return 'yellow';
        case 'error': return 'red';
        default: return 'gray';
    }
};

const getStatusLabel = (status: NodeStatus): string => {
    switch (status) {
        case 'completed': return '완료';
        case 'processing': return '처리중';
        case 'waiting_confirm': return '확인 대기';
        case 'error': return '오류';
        default: return '대기';
    }
};

export function WorkflowSidebar({
    nodes,
    currentNodeIndex,
    isAutoMode,
    isRunning,
    isOpen,
    onToggle,
    onAutoModeChange,
    onNodeClick,
    onStart,
    onPause,
    onReset,
}: WorkflowSidebarProps) {
    const completedCount = nodes.filter(n => n.status === 'completed').length;
    const progressPercent = (completedCount / nodes.length) * 100;

    if (!isOpen) {
        return (
            <Box
                style={{
                    position: 'fixed',
                    left: 0,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    zIndex: 100,
                }}
            >
                <Tooltip label="워크플로우 열기" position="right">
                    <ActionIcon
                        variant="filled"
                        size="xl"
                        radius="0 md md 0"
                        onClick={onToggle}
                        style={{
                            background: 'linear-gradient(135deg, var(--mantine-color-violet-6), var(--mantine-color-cyan-6))',
                        }}
                    >
                        <IconChevronRight size={20} />
                    </ActionIcon>
                </Tooltip>
            </Box>
        );
    }

    return (
        <Paper
            shadow="xl"
            p="md"
            style={{
                height: '100%',
                background: 'rgba(26, 27, 30, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRight: '1px solid var(--mantine-color-dark-4)',
            }}
        >
            <Stack gap="md" h="100%">
                {/* 헤더 */}
                <Group justify="space-between">
                    <Group gap="xs">
                        <Text size="lg" fw={700} variant="gradient" gradient={{ from: 'violet', to: 'cyan' }}>
                            워크플로우
                        </Text>
                    </Group>
                    <ActionIcon variant="subtle" onClick={onToggle}>
                        <IconChevronLeft size={18} />
                    </ActionIcon>
                </Group>

                {/* 진행률 */}
                <Paper p="sm" radius="md" withBorder>
                    <Stack gap="xs">
                        <Group justify="space-between">
                            <Text size="sm" c="dimmed">진행률</Text>
                            <Text size="sm" fw={600}>{completedCount}/{nodes.length}</Text>
                        </Group>
                        <Progress
                            value={progressPercent}
                            size="md"
                            radius="xl"
                            color="violet"
                            animated={isRunning}
                        />
                    </Stack>
                </Paper>

                {/* 컨트롤 */}
                <Paper p="sm" radius="md" withBorder>
                    <Stack gap="sm">
                        <Group justify="space-between">
                            <Text size="sm" fw={500}>자동 모드</Text>
                            <Switch
                                checked={isAutoMode}
                                onChange={(e) => onAutoModeChange(e.currentTarget.checked)}
                                color="violet"
                                size="sm"
                            />
                        </Group>
                        <Text size="xs" c="dimmed">
                            {isAutoMode ? "각 단계 자동 진행" : "단계별 확인 필요"}
                        </Text>
                        <Divider />
                        <Group grow>
                            <Tooltip label={isRunning ? "일시정지" : "시작"}>
                                <ActionIcon
                                    variant="light"
                                    color={isRunning ? "yellow" : "green"}
                                    size="lg"
                                    onClick={isRunning ? onPause : onStart}
                                >
                                    {isRunning ? <IconPlayerPause size={18} /> : <IconPlayerPlay size={18} />}
                                </ActionIcon>
                            </Tooltip>
                            <Tooltip label="초기화">
                                <ActionIcon variant="light" color="red" size="lg" onClick={onReset}>
                                    <IconRefresh size={18} />
                                </ActionIcon>
                            </Tooltip>
                        </Group>
                    </Stack>
                </Paper>

                <Divider label="노드" labelPosition="center" />

                {/* 노드 목록 */}
                <ScrollArea flex={1}>
                    <Stack gap="xs">
                        {nodes.map((node, index) => (
                            <UnstyledButton
                                key={node.id}
                                onClick={() => onNodeClick(index)}
                                style={{ width: '100%' }}
                            >
                                <Paper
                                    p="sm"
                                    radius="md"
                                    withBorder
                                    style={{
                                        borderColor: currentNodeIndex === index
                                            ? 'var(--mantine-color-violet-5)'
                                            : undefined,
                                        background: currentNodeIndex === index
                                            ? 'var(--mantine-color-violet-light)'
                                            : undefined,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                    }}
                                >
                                    <Group justify="space-between" wrap="nowrap">
                                        <Group gap="sm" wrap="nowrap">
                                            <ThemeIcon
                                                size="md"
                                                radius="md"
                                                variant="light"
                                                color={getStatusColor(node.status)}
                                            >
                                                <Text size="sm">{node.icon}</Text>
                                            </ThemeIcon>
                                            <Stack gap={2}>
                                                <Text size="sm" fw={500} lineClamp={1}>{node.label}</Text>
                                                <Text size="xs" c="dimmed">
                                                    {node.config.modelType === 'local' ? '로컬' : node.config.provider}
                                                </Text>
                                            </Stack>
                                        </Group>
                                        <Badge
                                            size="xs"
                                            color={getStatusColor(node.status)}
                                            variant="light"
                                        >
                                            {getStatusLabel(node.status)}
                                        </Badge>
                                    </Group>
                                </Paper>
                            </UnstyledButton>
                        ))}
                    </Stack>
                </ScrollArea>

                {/* 설정 버튼 */}
                <Tooltip label="AI 모델 설정">
                    <ActionIcon variant="light" size="lg" radius="xl" w="100%">
                        <IconSettings size={18} />
                    </ActionIcon>
                </Tooltip>
            </Stack>
        </Paper>
    );
}
