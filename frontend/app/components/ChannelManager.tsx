// frontend/app/components/ChannelManager.tsx
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
    SimpleGrid,
    Card,
    ActionIcon,
    Tooltip,
    Modal,
    Switch,
    Chip,
    ThemeIcon,
} from "@mantine/core";
import {
    IconPlus,
    IconTrash,
    IconEdit,
    IconBrandYoutube,
    IconBrandTiktok,
    IconBrandInstagram,
    IconTrendingUp,
    IconPalette,
    IconSettings,
} from "@tabler/icons-react";
import { useState } from "react";
import { Channel, ChannelType } from "./workflow/WorkflowTypes";

// 테마/장르 옵션
const THEME_OPTIONS = [
    { value: "martial_arts", label: "⚔️ 무협" },
    { value: "fantasy", label: "🧙 판타지" },
    { value: "scifi", label: "🚀 SF" },
    { value: "romance", label: "💕 로맨스" },
    { value: "horror", label: "👻 호러" },
    { value: "comedy", label: "😂 코미디" },
    { value: "action", label: "💥 액션" },
    { value: "mystery", label: "🔍 미스터리" },
    { value: "slice_of_life", label: "🌸 일상" },
    { value: "historical", label: "🏯 사극" },
];

interface ChannelManagerProps {
    channels: Channel[];
    onAddChannel: (channel: Omit<Channel, 'id' | 'createdAt'>) => void;
    onDeleteChannel: (id: string) => void;
    onEditChannel: (id: string, updates: Partial<Channel>) => void;
}

export function ChannelManager({
    channels,
    onAddChannel,
    onDeleteChannel,
    onEditChannel,
}: ChannelManagerProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingChannel, setEditingChannel] = useState<Channel | null>(null);

    // 새 채널 폼 상태
    const [newChannelName, setNewChannelName] = useState("");
    const [newChannelType, setNewChannelType] = useState<ChannelType>("theme");
    const [newChannelTheme, setNewChannelTheme] = useState<string | null>(null);
    const [newChannelPlatforms, setNewChannelPlatforms] = useState<string[]>(["youtube"]);
    const [newChannelAutoUpload, setNewChannelAutoUpload] = useState(false);

    const resetForm = () => {
        setNewChannelName("");
        setNewChannelType("theme");
        setNewChannelTheme(null);
        setNewChannelPlatforms(["youtube"]);
        setNewChannelAutoUpload(false);
        setEditingChannel(null);
    };

    const handleSubmit = () => {
        if (!newChannelName.trim()) return;

        onAddChannel({
            name: newChannelName,
            type: newChannelType,
            theme: newChannelType === 'theme' ? newChannelTheme || undefined : undefined,
            platforms: newChannelPlatforms as Channel['platforms'],
            autoUpload: newChannelAutoUpload,
        });

        resetForm();
        setIsModalOpen(false);
    };

    const getPlatformIcon = (platform: string) => {
        switch (platform) {
            case "youtube": return <IconBrandYoutube size={14} />;
            case "tiktok": return <IconBrandTiktok size={14} />;
            case "instagram": return <IconBrandInstagram size={14} />;
            default: return null;
        }
    };

    const getThemeLabel = (themeValue: string) => {
        return THEME_OPTIONS.find(t => t.value === themeValue)?.label || themeValue;
    };

    const trendChannels = channels.filter(c => c.type === 'trend');
    const themeChannels = channels.filter(c => c.type === 'theme');

    return (
        <Stack gap="lg">
            {/* 헤더 */}
            <Group justify="space-between">
                <Stack gap={4}>
                    <Text fw={700} size="xl">📺 채널 관리</Text>
                    <Text size="sm" c="dimmed">테마별, 트렌드 채널을 관리하세요</Text>
                </Stack>
                <Button
                    variant="gradient"
                    gradient={{ from: "violet", to: "cyan" }}
                    leftSection={<IconPlus size={16} />}
                    onClick={() => setIsModalOpen(true)}
                >
                    채널 추가
                </Button>
            </Group>

            {/* 트렌드 채널 섹션 */}
            <Paper p="md" radius="md" withBorder>
                <Stack gap="md">
                    <Group gap="xs">
                        <IconTrendingUp size={20} className="text-orange-500" />
                        <Text fw={600}>🔥 트렌드 분석 채널</Text>
                        <Badge color="orange" variant="light">{trendChannels.length}개</Badge>
                    </Group>

                    {trendChannels.length === 0 ? (
                        <Paper p="lg" radius="md" withBorder style={{ borderStyle: 'dashed' }}>
                            <Stack align="center" gap="sm">
                                <Text size="xl">📊</Text>
                                <Text c="dimmed" ta="center">
                                    트렌드 분석 채널이 없습니다
                                </Text>
                                <Button
                                    variant="light"
                                    size="xs"
                                    onClick={() => {
                                        setNewChannelType('trend');
                                        setIsModalOpen(true);
                                    }}
                                >
                                    트렌드 채널 추가
                                </Button>
                            </Stack>
                        </Paper>
                    ) : (
                        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
                            {trendChannels.map((channel) => (
                                <ChannelCard
                                    key={channel.id}
                                    channel={channel}
                                    onDelete={() => onDeleteChannel(channel.id)}
                                    onEdit={() => {
                                        setEditingChannel(channel);
                                        setIsModalOpen(true);
                                    }}
                                    getPlatformIcon={getPlatformIcon}
                                />
                            ))}
                        </SimpleGrid>
                    )}
                </Stack>
            </Paper>

            {/* 테마 채널 섹션 */}
            <Paper p="md" radius="md" withBorder>
                <Stack gap="md">
                    <Group gap="xs">
                        <IconPalette size={20} className="text-violet-500" />
                        <Text fw={600}>🎨 테마별 채널</Text>
                        <Badge color="violet" variant="light">{themeChannels.length}개</Badge>
                    </Group>

                    {themeChannels.length === 0 ? (
                        <Paper p="lg" radius="md" withBorder style={{ borderStyle: 'dashed' }}>
                            <Stack align="center" gap="sm">
                                <Text size="xl">🎬</Text>
                                <Text c="dimmed" ta="center">
                                    테마 채널이 없습니다.<br />
                                    무협, 판타지, SF 등 장르별 채널을 추가하세요
                                </Text>
                                <Button
                                    variant="light"
                                    size="xs"
                                    onClick={() => {
                                        setNewChannelType('theme');
                                        setIsModalOpen(true);
                                    }}
                                >
                                    테마 채널 추가
                                </Button>
                            </Stack>
                        </Paper>
                    ) : (
                        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
                            {themeChannels.map((channel) => (
                                <ChannelCard
                                    key={channel.id}
                                    channel={channel}
                                    onDelete={() => onDeleteChannel(channel.id)}
                                    onEdit={() => {
                                        setEditingChannel(channel);
                                        setIsModalOpen(true);
                                    }}
                                    getPlatformIcon={getPlatformIcon}
                                    getThemeLabel={getThemeLabel}
                                />
                            ))}
                        </SimpleGrid>
                    )}
                </Stack>
            </Paper>

            {/* 채널 추가/수정 모달 */}
            <Modal
                opened={isModalOpen}
                onClose={() => {
                    setIsModalOpen(false);
                    resetForm();
                }}
                title={
                    <Group gap="xs">
                        <IconPlus size={20} />
                        <Text fw={600}>{editingChannel ? "채널 수정" : "새 채널 추가"}</Text>
                    </Group>
                }
                size="md"
            >
                <Stack gap="md">
                    <TextInput
                        label="채널 이름"
                        placeholder="예: 무협 스토리 채널"
                        value={newChannelName}
                        onChange={(e) => setNewChannelName(e.currentTarget.value)}
                        required
                    />

                    <Select
                        label="채널 유형"
                        data={[
                            { value: "theme", label: "🎨 테마/장르 기반" },
                            { value: "trend", label: "🔥 트렌드 분석" },
                        ]}
                        value={newChannelType}
                        onChange={(v) => setNewChannelType(v as ChannelType)}
                    />

                    {newChannelType === "theme" && (
                        <Select
                            label="테마/장르"
                            placeholder="선택하세요"
                            data={THEME_OPTIONS}
                            value={newChannelTheme}
                            onChange={setNewChannelTheme}
                            searchable
                        />
                    )}

                    <Stack gap="xs">
                        <Text size="sm" fw={500}>업로드 플랫폼</Text>
                        <Chip.Group multiple value={newChannelPlatforms} onChange={setNewChannelPlatforms}>
                            <Group>
                                <Chip value="youtube" color="red">
                                    <Group gap={4}><IconBrandYoutube size={14} /> YouTube</Group>
                                </Chip>
                                <Chip value="tiktok" color="dark">
                                    <Group gap={4}><IconBrandTiktok size={14} /> TikTok</Group>
                                </Chip>
                                <Chip value="instagram" color="grape">
                                    <Group gap={4}><IconBrandInstagram size={14} /> Instagram</Group>
                                </Chip>
                            </Group>
                        </Chip.Group>
                    </Stack>

                    <Switch
                        label="자동 업로드"
                        description="영상 생성 완료 시 자동으로 업로드"
                        checked={newChannelAutoUpload}
                        onChange={(e) => setNewChannelAutoUpload(e.currentTarget.checked)}
                    />

                    <Group justify="flex-end" mt="md">
                        <Button variant="subtle" onClick={() => {
                            setIsModalOpen(false);
                            resetForm();
                        }}>
                            취소
                        </Button>
                        <Button
                            variant="gradient"
                            gradient={{ from: "violet", to: "cyan" }}
                            onClick={handleSubmit}
                            disabled={!newChannelName.trim()}
                        >
                            {editingChannel ? "저장" : "추가"}
                        </Button>
                    </Group>
                </Stack>
            </Modal>
        </Stack>
    );
}

// 채널 카드 컴포넌트
function ChannelCard({
    channel,
    onDelete,
    onEdit,
    getPlatformIcon,
    getThemeLabel,
}: {
    channel: Channel;
    onDelete: () => void;
    onEdit: () => void;
    getPlatformIcon: (platform: string) => React.ReactNode;
    getThemeLabel?: (theme: string) => string;
}) {
    return (
        <Card padding="md" radius="md" withBorder className="channel-card">
            <Stack gap="sm">
                <Group justify="space-between">
                    <Group gap="xs">
                        <ThemeIcon
                            size="md"
                            radius="md"
                            variant="gradient"
                            gradient={
                                channel.type === 'trend'
                                    ? { from: "orange", to: "red" }
                                    : { from: "violet", to: "cyan" }
                            }
                        >
                            {channel.type === 'trend' ? <IconTrendingUp size={14} /> : <IconPalette size={14} />}
                        </ThemeIcon>
                        <Text fw={600} size="sm" lineClamp={1}>{channel.name}</Text>
                    </Group>
                    <Group gap={4}>
                        <Tooltip label="설정">
                            <ActionIcon variant="subtle" size="sm" onClick={onEdit}>
                                <IconEdit size={14} />
                            </ActionIcon>
                        </Tooltip>
                        <Tooltip label="삭제">
                            <ActionIcon variant="subtle" color="red" size="sm" onClick={onDelete}>
                                <IconTrash size={14} />
                            </ActionIcon>
                        </Tooltip>
                    </Group>
                </Group>

                {channel.type === 'theme' && channel.theme && getThemeLabel && (
                    <Badge variant="light" color="violet" size="sm">
                        {getThemeLabel(channel.theme)}
                    </Badge>
                )}

                <Group gap={4}>
                    {channel.platforms.map((platform) => (
                        <Badge
                            key={platform}
                            variant="outline"
                            size="xs"
                            leftSection={getPlatformIcon(platform)}
                        >
                            {platform}
                        </Badge>
                    ))}
                </Group>

                {channel.autoUpload && (
                    <Badge variant="dot" color="green" size="xs">자동 업로드</Badge>
                )}
            </Stack>
        </Card>
    );
}
