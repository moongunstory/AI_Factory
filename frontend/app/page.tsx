// frontend/app/page.tsx
"use client";

import {
  AppShell,
  Container,
  Title,
  Text,
  TextInput,
  Button,
  Group,
  Stack,
  Card,
  Badge,
  Grid,
  ThemeIcon,
  rem,
  Tabs,
  Textarea,
  NumberInput,
  Select,
  Divider,
  SegmentedControl,
  ActionIcon,
  Paper,
  SimpleGrid,
  Chip,
  Accordion,
  Tooltip,
  Drawer,
  Progress,
  RingProgress,
  ScrollArea,
  UnstyledButton,
  Box,
  Loader,
  Alert,
} from "@mantine/core";
import {
  IconVideo,
  IconMovie,
  IconFlame,
  IconSparkles,
  IconSearch,
  IconUpload,
  IconDeviceFloppy,
  IconPalette,
  IconUsers,
  IconWorld,
  IconSettings,
  IconBrandYoutube,
  IconBrandTiktok,
  IconBrandInstagram,
  IconBrandX,
  IconTrendingUp,
  IconChartLine,
  IconMoodSmile,
  IconPlayerPlay,
  IconEye,
  IconHeart,
  IconShare,
  IconPlus,
  IconTrash,
  IconChevronRight,
  IconFilter,
  IconMapPin,
  IconWand,
  IconBrain,
  IconLayoutSidebar,
  IconBroadcast,
} from "@tabler/icons-react";
import { useState, useCallback } from "react";

// 컴포넌트 임포트
import { WorkflowEditor } from "./components/workflow/WorkflowEditor";
import { SceneConfirmPanel } from "./components/workflow/SceneConfirmPanel";

import { AIModelSettings } from "./components/AIModelSettings";
import {
  WorkflowNode,
  DEFAULT_WORKFLOW_NODES,
  Channel,
  AIModelConfig,
  SceneOutput,
} from "./components/workflow/WorkflowTypes";

// 테마 데이터
const VIDEO_THEMES = [
  { id: "cinematic", emoji: "🎬", label: "시네마틱", color: "blue" },
  { id: "cyberpunk", emoji: "🌆", label: "사이버펑크", color: "violet" },
  { id: "nature", emoji: "🌿", label: "자연/힐링", color: "green" },
  { id: "dramatic", emoji: "🎭", label: "드라마틱", color: "red" },
  { id: "scifi", emoji: "🚀", label: "SF/미래", color: "cyan" },
  { id: "fantasy", emoji: "⚔️", label: "판타지", color: "grape" },
  { id: "artistic", emoji: "🎨", label: "아트", color: "pink" },
  { id: "storybook", emoji: "📖", label: "동화", color: "orange" },
];

// 카테고리 데이터
const TREND_CATEGORIES = [
  { value: "entertainment", label: "🎬 엔터테인먼트" },
  { value: "gaming", label: "🎮 게임" },
  { value: "education", label: "📚 교육" },
  { value: "music", label: "🎵 음악" },
  { value: "meme", label: "😂 밈" },
  { value: "news", label: "📰 뉴스" },
  { value: "tech", label: "💻 기술" },
  { value: "lifestyle", label: "✨ 라이프스타일" },
];

// Mock 트렌딩 데이터
const MOCK_TRENDING = [
  { id: 1, title: "AI가 그린 미래 도시", platform: "youtube", views: "1.2M", likes: "89K", rise: 523, thumbnail: "🏙️" },
  { id: 2, title: "이게 진짜 실화냐", platform: "tiktok", views: "4.5M", likes: "320K", rise: 890, thumbnail: "😱" },
  { id: 3, title: "요즘 유행하는 댄스 챌린지", platform: "instagram", views: "890K", likes: "156K", rise: 234, thumbnail: "💃" },
  { id: 4, title: "개발자 브이로그", platform: "youtube", views: "560K", likes: "45K", rise: 156, thumbnail: "💻" },
  { id: 5, title: "고양이 vs 레이저", platform: "tiktok", views: "8.9M", likes: "1.2M", rise: 1200, thumbnail: "🐱" },
  { id: 6, title: "신기한 과학 실험", platform: "instagram", views: "2.3M", likes: "189K", rise: 445, thumbnail: "🔬" },
];

// Mock 밈 데이터
const MOCK_MEMES = [
  { id: 1, title: "어쩔티비", category: "유머", popularity: 95 },
  { id: 2, title: "점심 뭐 먹지", category: "일상", popularity: 88 },
  { id: 3, title: "월요병", category: "직장", popularity: 92 },
  { id: 4, title: "이게 맞아?", category: "반응", popularity: 78 },
];

type TabType = "create" | "channels" | "trending" | "settings";
type ModeType = "short" | "series";

interface Character {
  id: string;
  name: string;
  appearance: string;
  personality: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>("create");
  const [viewMode, setViewMode] = useState<"dashboard" | "workflow">("dashboard");
  const [mode, setMode] = useState<ModeType>("short");
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [story, setStory] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // GPT 워크플로우 결과 상태
  const [workflowResults, setWorkflowResults] = useState<{
    expanded_story: string;
    storyboard: string;
    prompts: string;
  } | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  // 워크플로우 상태
  const [workflowOpen, setWorkflowOpen] = useState(false);
  const [workflowNodes, setWorkflowNodes] = useState<WorkflowNode[]>(
    DEFAULT_WORKFLOW_NODES.map((node, index) => ({
      ...node,
      id: `node-${index}`,
    }))
  );
  const [currentNodeIndex, setCurrentNodeIndex] = useState(0);
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false);

  // 시리즈 상태 - 개선된 자유형 입력
  const [seriesTitle, setSeriesTitle] = useState("");
  const [episodeCount, setEpisodeCount] = useState<number | "">(3);
  const [characters, setCharacters] = useState<Character[]>([]);

  // 자유로운 세계관 입력 (개선됨)
  const [worldviewInput, setWorldviewInput] = useState(""); // 간단 인풋
  const [expandedWorldview, setExpandedWorldview] = useState(""); // LLM 확장 결과
  const [isExpandingWorldview, setIsExpandingWorldview] = useState(false);



  // AI 모델 설정 상태
  const [aiConfigs, setAiConfigs] = useState<Record<string, AIModelConfig>>({
    llm: { modelType: "api", provider: "openai" },
    image: { modelType: "local" },
    video: { modelType: "local" },
    audio: { modelType: "api", provider: "elevenlabs" },
  });

  // 씬 확인 상태 (이미지/영상 생성 후)
  const [showSceneConfirm, setShowSceneConfirm] = useState(false);
  const [mockScenes, setMockScenes] = useState<SceneOutput[]>([]);

  // 트렌드 상태
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["youtube", "tiktok"]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [timePeriod, setTimePeriod] = useState("week");
  const [trendKeyword, setTrendKeyword] = useState("");
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [selectedTrend, setSelectedTrend] = useState<typeof MOCK_TRENDING[0] | null>(null);

  // 세계관 LLM 확장 핸들러
  const handleExpandWorldview = async () => {
    if (!worldviewInput.trim()) {
      alert("세계관 아이디어를 먼저 입력해주세요!");
      return;
    }

    setIsExpandingWorldview(true);

    // Mock LLM 확장 (실제로는 API 호출)
    setTimeout(() => {
      const mockExpanded = `# ${seriesTitle || "무제"} 세계관

## 배경 설정
${worldviewInput}

## 확장된 세계관

### 시대와 장소
이 이야기는 먼 미래, 인류가 우주로 진출한 시대를 배경으로 합니다. 지구는 환경 오염으로 인해 거대 돔 도시에서만 생존이 가능하며, 부유층은 화성과 목성의 위성에 새로운 식민지를 건설했습니다.

### 사회 구조
- **지구 돔 시티**: 노동계급과 하층민이 거주, 자원 부족으로 인한 갈등
- **화성 엘리트 구역**: 부유층과 기업 총수들의 거주지
- **프론티어 지역**: 법의 손길이 닿지 않는 소행성대 무법지대

### 기술 수준
- 초광속 통신은 가능하지만 이동은 아직 미개발
- 의식 업로드 기술의 초기 단계
- 유전자 조작 인간 "제네틱"의 등장

### 핵심 갈등
자연 인간과 제네틱 사이의 권리 투쟁, 그리고 이를 이용하려는 기업들의 암투...

---
*이 세계관은 AI가 확장한 것입니다. 자유롭게 수정하세요.*`;

      setExpandedWorldview(mockExpanded);
      setIsExpandingWorldview(false);
    }, 2000);
  };

  // Job 상태 타입 정의
  type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

  const [pollingStatus, setPollingStatus] = useState<string>("");

  const handleGenerate = async () => {
    if (!story.trim()) {
      alert("스토리를 먼저 입력해주세요!");
      return;
    }

    setIsGenerating(true);
    setWorkflowError(null);
    setWorkflowResults(null);
    setPollingStatus("작업 요청 중...");

    try {
      // 1. 작업 생성 요청 (POST /api/jobs)
      const response = await fetch("http://localhost:8000/api/jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ story }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "작업 생성 중 오류가 발생했습니다.");
      }

      const { job_id } = await response.json();
      setPollingStatus("작업 대기 중...");

      // 2. 폴링 시작
      const pollJobStatus = async () => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/api/jobs/${job_id}`);
          if (!statusResponse.ok) {
            throw new Error("작업 상태 확인 실패");
          }

          const jobData = await statusResponse.json();
          const { status, result, message } = jobData;

          if (status === 'completed') {
            setWorkflowResults(result);
            setPollingStatus("");
            setIsGenerating(false);
            alert("✅ GPT 워크플로우가 성공적으로 완료되었습니다!");
          } else if (status === 'failed') {
            throw new Error(message || "작업 처리 중 오류가 발생했습니다.");
          } else {
            // 계속 폴링 (pending or processing)
            setPollingStatus(status === 'processing' ? "작업 처리 중..." : "작업 대기 중...");
            setTimeout(pollJobStatus, 2000); // 2초 후 재시도
          }
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
          setWorkflowError(errorMessage);
          setPollingStatus("");
          setIsGenerating(false);
          alert(`❌ 오류: ${errorMessage}`);
        }
      };

      // 폴링 시작
      pollJobStatus();

    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
      setWorkflowError(errorMessage);
      setPollingStatus("");
      setIsGenerating(false);
      alert(`❌ 오류: ${errorMessage}\n\n백엔드 서버가 실행 중인지 확인해주세요.`);
    }
  };

  const handleLoadSettings = () => {
    alert("설정 불러오기 (UI Demo)");
  };

  const handleSaveSettings = () => {
    alert("설정 저장하기 (UI Demo)");
  };

  const addCharacter = () => {
    setCharacters([
      ...characters,
      { id: Date.now().toString(), name: "", appearance: "", personality: "" },
    ]);
  };

  const removeCharacter = (id: string) => {
    setCharacters(characters.filter((c) => c.id !== id));
  };

  const updateCharacter = (id: string, field: keyof Character, value: string) => {
    setCharacters(
      characters.map((c) => (c.id === id ? { ...c, [field]: value } : c))
    );
  };



  // AI 설정 핸들러
  const handleAIConfigChange = (category: string, config: AIModelConfig) => {
    setAiConfigs(prev => ({ ...prev, [category]: config }));
  };

  const handleTestConnection = async (category: string): Promise<boolean> => {
    // Mock 테스트
    await new Promise(resolve => setTimeout(resolve, 1000));
    return Math.random() > 0.3;
  };

  // 워크플로우 핸들러
  const handleWorkflowStart = () => {
    setIsWorkflowRunning(true);
    handleGenerate();
  };

  const handleWorkflowPause = () => {
    setIsWorkflowRunning(false);
  };

  const handleWorkflowReset = () => {
    setIsWorkflowRunning(false);
    setCurrentNodeIndex(0);
    setShowSceneConfirm(false);
    setWorkflowNodes(
      DEFAULT_WORKFLOW_NODES.map((node, index) => ({
        ...node,
        id: `node-${index}`,
      }))
    );
  };

  // 씬 컨펌 핸들러
  const handleSceneApprove = (sceneIds: string[]) => {
    setMockScenes(prev => prev.map(s =>
      sceneIds.includes(s.id) ? { ...s, status: 'approved' as const } : s
    ));
  };

  const handleSceneRegenerate = (sceneIds: string[]) => {
    setMockScenes(prev => prev.map(s =>
      sceneIds.includes(s.id) ? { ...s, status: 'pending' as const, needsRegeneration: true } : s
    ));
    alert(`${sceneIds.length}개 씬 재생성 요청 (UI Demo)`);
  };

  const handleApproveAll = () => {
    setMockScenes(prev => prev.map(s => ({ ...s, status: 'approved' as const })));
    setShowSceneConfirm(false);
    setCurrentNodeIndex(4); // 다음 단계로
    setWorkflowNodes(prev => prev.map((node, idx) =>
      idx === 3 ? { ...node, status: 'completed' } :
        idx === 4 ? { ...node, status: 'processing' } : node
    ));
    alert("전체 승인! 다음 단계(영상 생성)로 진행합니다. (UI Demo)");
  };

  const openTrendDetail = (trend: typeof MOCK_TRENDING[0]) => {
    setSelectedTrend(trend);
    setDetailDrawerOpen(true);
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case "youtube": return <IconBrandYoutube size={16} />;
      case "tiktok": return <IconBrandTiktok size={16} />;
      case "instagram": return <IconBrandInstagram size={16} />;
      default: return <IconBrandX size={16} />;
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case "youtube": return "red";
      case "tiktok": return "dark";
      case "instagram": return "grape";
      default: return "blue";
    }
  };

  return (
    <AppShell
      navbar={{
        width: 80,
        breakpoint: 'sm',
      }}
      padding={viewMode === 'workflow' ? 0 : 'md'}
    >
      {/* 메인 네비게이션 레일 */}
      <AppShell.Navbar p="md" style={{ background: 'var(--mantine-color-dark-8)', borderRight: '1px solid var(--mantine-color-dark-4)' }}>
        <Stack align="center" gap="lg">
          <ThemeIcon size={40} radius="md" variant="gradient" gradient={{ from: 'violet', to: 'cyan' }}>
            <IconVideo size={24} />
          </ThemeIcon>

          <Tooltip label="대시보드" position="right">
            <ActionIcon
              variant={viewMode === 'dashboard' ? 'filled' : 'subtle'}
              color={viewMode === 'dashboard' ? 'violet' : 'gray'}
              size="xl"
              onClick={() => setViewMode('dashboard')}
            >
              <IconLayoutSidebar size={24} />
            </ActionIcon>
          </Tooltip>

          <Tooltip label="워크플로우 (n8n 스타일)" position="right">
            <ActionIcon
              variant={viewMode === 'workflow' ? 'filled' : 'subtle'}
              color={viewMode === 'workflow' ? 'violet' : 'gray'}
              size="xl"
              onClick={() => setViewMode('workflow')}
            >
              <IconBrain size={24} />
            </ActionIcon>
          </Tooltip>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        {viewMode === 'workflow' ? (
          <WorkflowEditor initialNodes={workflowNodes} />
        ) : (
          <>
            {/* 대시보드 뷰 */}

            <Container size="lg" py="xl">
              <Stack gap="xl">
                {/* 헤더 */}
                <div className="text-center space-y-2">
                  <Group justify="center" mb="xs">
                    <ThemeIcon
                      size={60}
                      radius="md"
                      variant="gradient"
                      gradient={{ from: "violet", to: "cyan" }}
                    >
                      <IconVideo style={{ width: rem(32), height: rem(32) }} />
                    </ThemeIcon>
                  </Group>
                  <Title order={1} className="font-extrabold tracking-tight">
                    AI 쇼츠 팩토리
                  </Title>
                  <Text c="dimmed" size="lg">
                    아이디어를 시네마틱 영상으로 변환하세요
                  </Text>
                </div>

                {/* 메인 탭 */}
                <Tabs
                  value={activeTab}
                  onChange={(value) => setActiveTab(value as TabType)}
                  variant="pills"
                  radius="xl"
                >
                  <Tabs.List grow mb="lg">
                    <Tabs.Tab
                      value="create"
                      leftSection={<IconMovie size={20} />}
                      className="tab-premium"
                    >
                      영상 제작
                    </Tabs.Tab>

                    <Tabs.Tab
                      value="trending"
                      leftSection={<IconFlame size={20} />}
                      className="tab-premium"
                    >
                      트렌드 분석
                    </Tabs.Tab>
                    <Tabs.Tab
                      value="settings"
                      leftSection={<IconSettings size={20} />}
                      className="tab-premium"
                    >
                      AI 설정
                    </Tabs.Tab>
                  </Tabs.List>

                  {/* ==================== 영상 제작 탭 ==================== */}
                  <Tabs.Panel value="create">
                    <Stack gap="lg">
                      {/* 씬 컨펌 패널 (생성 후 표시) */}
                      {showSceneConfirm && (
                        <SceneConfirmPanel
                          scenes={mockScenes}
                          nodeType="image_gen"
                          onApprove={handleSceneApprove}
                          onRegenerate={handleSceneRegenerate}
                          onApproveAll={handleApproveAll}
                        />
                      )}

                      {/* 모드 선택 & 설정 버튼 */}
                      <Paper p="md" radius="md" className="glass-card">
                        <Group justify="space-between">
                          <SegmentedControl
                            value={mode}
                            onChange={(value) => setMode(value as ModeType)}
                            data={[
                              { label: "단편 영상", value: "short" },
                              { label: "시리즈", value: "series" },
                            ]}
                            size="md"
                            radius="xl"
                          />
                          <Group gap="xs">
                            <Tooltip label="설정 불러오기">
                              <ActionIcon
                                variant="light"
                                size="lg"
                                radius="xl"
                                onClick={handleLoadSettings}
                              >
                                <IconUpload size={18} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="설정 저장하기">
                              <ActionIcon
                                variant="light"
                                size="lg"
                                radius="xl"
                                onClick={handleSaveSettings}
                              >
                                <IconDeviceFloppy size={18} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Group>
                      </Paper>

                      {/* 영상 테마 선택 */}
                      <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Stack gap="md">
                          <Group gap="xs">
                            <IconPalette size={20} className="text-violet-500" />
                            <Text fw={600} size="lg">영상 테마 선택</Text>
                          </Group>
                          <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm">
                            {VIDEO_THEMES.map((theme) => (
                              <UnstyledButton
                                key={theme.id}
                                onClick={() => setSelectedTheme(theme.id)}
                                className="theme-button"
                              >
                                <Paper
                                  p="md"
                                  radius="md"
                                  withBorder
                                  className={`theme-card ${selectedTheme === theme.id ? "theme-selected" : ""}`}
                                  style={{
                                    borderColor: selectedTheme === theme.id ? `var(--mantine-color-${theme.color}-5)` : undefined,
                                    background: selectedTheme === theme.id ? `var(--mantine-color-${theme.color}-light)` : undefined,
                                  }}
                                >
                                  <Stack align="center" gap="xs">
                                    <Text size="xl">{theme.emoji}</Text>
                                    <Text size="sm" fw={500}>{theme.label}</Text>
                                  </Stack>
                                </Paper>
                              </UnstyledButton>
                            ))}
                          </SimpleGrid>
                        </Stack>
                      </Card>

                      {/* 스토리 입력 (단편) */}
                      {mode === "short" && (
                        <>
                          <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Stack gap="md">
                              <Group gap="xs">
                                <IconSparkles size={20} className="text-cyan-500" />
                                <Text fw={600} size="lg">스토리 입력</Text>
                              </Group>
                              <Textarea
                                placeholder="예: 네온 비 속에서 명상하는 사이버네틱 사무라이, 도시의 불빛이 반사되는 가운데 내면의 평화를 찾는다..."
                                minRows={4}
                                autosize
                                value={story}
                                onChange={(e) => setStory(e.currentTarget.value)}
                              />
                            </Stack>
                          </Card>

                          {/* GPT 워크플로우 결과 표시 */}
                          {workflowResults && (
                            <Card shadow="md" padding="lg" radius="md" withBorder style={{ borderColor: "var(--mantine-color-green-5)" }}>
                              <Stack gap="lg">
                                <Group gap="xs">
                                  <IconBrain size={24} className="text-green-500" />
                                  <Text fw={700} size="xl" c="green">✅ GPT 워크플로우 완료!</Text>
                                </Group>

                                {/* 1. 확장된 이야기 */}
                                <div>
                                  <Group gap="xs" mb="sm">
                                    <Badge color="violet" variant="filled">1단계</Badge>
                                    <Text fw={600} size="md">📖 확장된 이야기 (Fable Forge)</Text>
                                  </Group>
                                  <Paper p="md" radius="md" withBorder style={{ background: "var(--mantine-color-dark-6)" }}>
                                    <ScrollArea h={200}>
                                      <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                                        {workflowResults.expanded_story}
                                      </Text>
                                    </ScrollArea>
                                  </Paper>
                                </div>

                                <Divider />

                                {/* 2. 스토리보드 */}
                                <div>
                                  <Group gap="xs" mb="sm">
                                    <Badge color="blue" variant="filled">2단계</Badge>
                                    <Text fw={600} size="md">🎬 스토리보드 (Storyboard GPT)</Text>
                                  </Group>
                                  <Paper p="md" radius="md" withBorder style={{ background: "var(--mantine-color-dark-6)" }}>
                                    <ScrollArea h={200}>
                                      <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                                        {workflowResults.storyboard}
                                      </Text>
                                    </ScrollArea>
                                  </Paper>
                                </div>

                                <Divider />

                                {/* 3. 프롬프트 */}
                                <div>
                                  <Group gap="xs" mb="sm">
                                    <Badge color="cyan" variant="filled">3단계</Badge>
                                    <Text fw={600} size="md">✨ 생성 프롬프트 (Storyboard Maker)</Text>
                                  </Group>
                                  <Paper p="md" radius="md" withBorder style={{ background: "var(--mantine-color-dark-6)" }}>
                                    <ScrollArea h={200}>
                                      <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                                        {workflowResults.prompts}
                                      </Text>
                                    </ScrollArea>
                                  </Paper>
                                </div>
                              </Stack>
                            </Card>
                          )}

                          {/* 에러 표시 */}
                          {workflowError && (
                            <Alert variant="light" color="red" title="오류 발생" icon={<IconBrain size={18} />}>
                              {workflowError}
                            </Alert>
                          )}
                        </>
                      )}

                      {/* 시리즈 컨셉 입력 (개선된 UI) */}
                      {mode === "series" && (
                        <>
                          {/* 기본 정보 */}
                          <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Stack gap="md">
                              <Group gap="xs">
                                <IconSparkles size={20} className="text-cyan-500" />
                                <Text fw={600} size="lg">시리즈 기본 정보</Text>
                              </Group>
                              <Group grow>
                                <TextInput
                                  label="시리즈 제목"
                                  placeholder="예: 우주 탐험가의 일기"
                                  value={seriesTitle}
                                  onChange={(e) => setSeriesTitle(e.currentTarget.value)}
                                />
                                <NumberInput
                                  label="에피소드 수"
                                  placeholder="1-10"
                                  min={1}
                                  max={10}
                                  value={episodeCount}
                                  onChange={(value) => setEpisodeCount(typeof value === "number" ? value : "")}
                                />
                              </Group>
                            </Stack>
                          </Card>

                          {/* 자유로운 세계관 입력 (개선됨!) */}
                          <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Stack gap="md">
                              <Group gap="xs">
                                <IconWorld size={20} className="text-violet-500" />
                                <Text fw={600} size="lg">🌍 세계관 만들기</Text>
                                <Badge variant="light" color="violet">AI 확장 지원</Badge>
                              </Group>

                              <Alert
                                variant="light"
                                color="violet"
                                icon={<IconBrain size={18} />}
                              >
                                간단한 아이디어만 적어주세요. AI가 풍부한 세계관으로 확장해드립니다!
                              </Alert>

                              <Textarea
                                label="세계관 아이디어"
                                placeholder="예: 마법과 기술이 공존하는 미래 도시, 마법사와 해커가 함께 살아가는 세상..."
                                minRows={3}
                                value={worldviewInput}
                                onChange={(e) => setWorldviewInput(e.currentTarget.value)}
                              />

                              <Button
                                variant="gradient"
                                gradient={{ from: "violet", to: "grape" }}
                                leftSection={isExpandingWorldview ? <Loader size="xs" color="white" /> : <IconWand size={18} />}
                                onClick={handleExpandWorldview}
                                loading={isExpandingWorldview}
                                disabled={!worldviewInput.trim()}
                              >
                                ✨ AI로 세계관 확장하기
                              </Button>

                              {expandedWorldview && (
                                <>
                                  <Divider label="확장된 세계관" labelPosition="center" />
                                  <Textarea
                                    value={expandedWorldview}
                                    onChange={(e) => setExpandedWorldview(e.currentTarget.value)}
                                    minRows={12}
                                    autosize
                                    styles={{
                                      input: {
                                        fontFamily: 'monospace',
                                        fontSize: '14px',
                                        lineHeight: 1.6,
                                      },
                                    }}
                                  />
                                  <Text size="xs" c="dimmed">
                                    💡 AI가 확장한 세계관입니다. 자유롭게 수정하세요!
                                  </Text>
                                </>
                              )}
                            </Stack>
                          </Card>

                          {/* 캐릭터 시트 */}
                          <Accordion variant="separated" radius="md">
                            <Accordion.Item value="characters">
                              <Accordion.Control icon={<IconUsers size={20} />}>
                                <Text fw={600}>캐릭터 시트</Text>
                              </Accordion.Control>
                              <Accordion.Panel>
                                <Stack gap="md">
                                  {characters.length === 0 ? (
                                    <Text c="dimmed" ta="center" py="md">
                                      캐릭터를 추가하여 시리즈에 등장하는 인물들을 정의하세요
                                    </Text>
                                  ) : (
                                    characters.map((char, index) => (
                                      <Card key={char.id} withBorder padding="md" radius="md">
                                        <Group justify="space-between" mb="sm">
                                          <Badge variant="light">캐릭터 {index + 1}</Badge>
                                          <ActionIcon
                                            variant="subtle"
                                            color="red"
                                            size="sm"
                                            onClick={() => removeCharacter(char.id)}
                                          >
                                            <IconTrash size={14} />
                                          </ActionIcon>
                                        </Group>
                                        <Stack gap="xs">
                                          <TextInput
                                            placeholder="캐릭터 이름"
                                            size="sm"
                                            value={char.name}
                                            onChange={(e) => updateCharacter(char.id, "name", e.currentTarget.value)}
                                          />
                                          <TextInput
                                            placeholder="외형 묘사 (예: 은발의 장신, 사이버네틱 눈)"
                                            size="sm"
                                            value={char.appearance}
                                            onChange={(e) => updateCharacter(char.id, "appearance", e.currentTarget.value)}
                                          />
                                          <TextInput
                                            placeholder="성격 및 특징"
                                            size="sm"
                                            value={char.personality}
                                            onChange={(e) => updateCharacter(char.id, "personality", e.currentTarget.value)}
                                          />
                                        </Stack>
                                      </Card>
                                    ))
                                  )}
                                  <Button
                                    variant="light"
                                    leftSection={<IconPlus size={16} />}
                                    onClick={addCharacter}
                                  >
                                    캐릭터 추가
                                  </Button>
                                </Stack>
                              </Accordion.Panel>
                            </Accordion.Item>

                            {/* 고급 설정 */}
                            <Accordion.Item value="advanced">
                              <Accordion.Control icon={<IconSettings size={20} />}>
                                <Text fw={600}>고급 설정</Text>
                              </Accordion.Control>
                              <Accordion.Panel>
                                <Stack gap="md">
                                  <Group grow>
                                    <Select
                                      label="영상 스타일"
                                      placeholder="선택하세요"
                                      data={[
                                        { value: "realistic", label: "실사풍" },
                                        { value: "anime", label: "애니메이션" },
                                        { value: "3d", label: "3D 렌더링" },
                                        { value: "illustration", label: "일러스트" },
                                        { value: "watercolor", label: "수채화" },
                                      ]}
                                    />
                                    <Select
                                      label="화면 비율"
                                      placeholder="선택하세요"
                                      data={[
                                        { value: "9:16", label: "9:16 (세로 - 쇼츠)" },
                                        { value: "16:9", label: "16:9 (가로 - 유튜브)" },
                                        { value: "1:1", label: "1:1 (정사각형)" },
                                      ]}
                                      defaultValue="9:16"
                                    />
                                  </Group>
                                  <Group grow>
                                    <NumberInput
                                      label="영상 길이 (초)"
                                      placeholder="4-60"
                                      min={4}
                                      max={60}
                                      defaultValue={15}
                                    />
                                    <Select
                                      label="품질"
                                      placeholder="선택하세요"
                                      data={[
                                        { value: "draft", label: "초안 (빠름)" },
                                        { value: "standard", label: "표준" },
                                        { value: "high", label: "고품질 (느림)" },
                                      ]}
                                      defaultValue="standard"
                                    />
                                  </Group>
                                </Stack>
                              </Accordion.Panel>
                            </Accordion.Item>
                          </Accordion>
                        </>
                      )}

                      {/* 단편 전용: 고급 설정 */}
                      {mode === "short" && (
                        <Accordion variant="separated" radius="md">
                          <Accordion.Item value="advanced">
                            <Accordion.Control icon={<IconSettings size={20} />}>
                              <Text fw={600}>고급 설정</Text>
                            </Accordion.Control>
                            <Accordion.Panel>
                              <Stack gap="md">
                                <Group grow>
                                  <Select
                                    label="영상 스타일"
                                    placeholder="선택하세요"
                                    data={[
                                      { value: "realistic", label: "실사풍" },
                                      { value: "anime", label: "애니메이션" },
                                      { value: "3d", label: "3D 렌더링" },
                                      { value: "illustration", label: "일러스트" },
                                      { value: "watercolor", label: "수채화" },
                                    ]}
                                  />
                                  <Select
                                    label="화면 비율"
                                    placeholder="선택하세요"
                                    data={[
                                      { value: "9:16", label: "9:16 (세로 - 쇼츠)" },
                                      { value: "16:9", label: "16:9 (가로 - 유튜브)" },
                                      { value: "1:1", label: "1:1 (정사각형)" },
                                    ]}
                                    defaultValue="9:16"
                                  />
                                </Group>
                              </Stack>
                            </Accordion.Panel>
                          </Accordion.Item>
                        </Accordion>
                      )}

                      {/* 생성 버튼 */}
                      <Button
                        size="lg"
                        radius="xl"
                        rightSection={!isGenerating && <IconSparkles size={20} />}
                        onClick={handleGenerate}
                        loading={isGenerating}
                        variant="gradient"
                        gradient={mode === "short" ? { from: "violet", to: "cyan" } : { from: "grape", to: "violet" }}
                        fullWidth
                      >
                        {isGenerating && pollingStatus ? pollingStatus : (mode === "short" ? "단편 영상 생성" : "시리즈 생성")}
                      </Button>
                    </Stack>
                  </Tabs.Panel>



                  {/* ==================== 트렌드 분석 탭 ==================== */}
                  <Tabs.Panel value="trending">
                    <Stack gap="lg">
                      {/* 플랫폼 & 기간 선택 */}
                      <Paper p="md" radius="md" className="glass-card">
                        <Stack gap="md">
                          <Group justify="space-between" wrap="wrap">
                            <Group gap="xs">
                              <Text fw={500} size="sm">플랫폼:</Text>
                              <Chip.Group multiple value={selectedPlatforms} onChange={setSelectedPlatforms}>
                                <Group gap="xs">
                                  <Chip value="youtube" color="red" variant="filled" size="sm">
                                    <Group gap={4}><IconBrandYoutube size={14} /> YouTube</Group>
                                  </Chip>
                                  <Chip value="tiktok" color="dark" variant="filled" size="sm">
                                    <Group gap={4}><IconBrandTiktok size={14} /> TikTok</Group>
                                  </Chip>
                                  <Chip value="instagram" color="grape" variant="filled" size="sm">
                                    <Group gap={4}><IconBrandInstagram size={14} /> Instagram</Group>
                                  </Chip>
                                  <Chip value="x" color="blue" variant="filled" size="sm">
                                    <Group gap={4}><IconBrandX size={14} /> X</Group>
                                  </Chip>
                                </Group>
                              </Chip.Group>
                            </Group>
                            <SegmentedControl
                              value={timePeriod}
                              onChange={setTimePeriod}
                              data={[
                                { label: "오늘", value: "today" },
                                { label: "이번 주", value: "week" },
                                { label: "이번 달", value: "month" },
                              ]}
                              size="xs"
                            />
                          </Group>
                        </Stack>
                      </Paper>

                      {/* 필터 & 검색 */}
                      <Card shadow="sm" padding="md" radius="md" withBorder>
                        <Stack gap="md">
                          <Group gap="xs">
                            <IconFilter size={18} />
                            <Text fw={600}>필터</Text>
                          </Group>
                          <Group grow>
                            <Chip.Group multiple value={selectedCategories} onChange={setSelectedCategories}>
                              <ScrollArea>
                                <Group gap="xs" wrap="nowrap" pb="xs">
                                  {TREND_CATEGORIES.map((cat) => (
                                    <Chip key={cat.value} value={cat.value} size="xs" variant="outline">
                                      {cat.label}
                                    </Chip>
                                  ))}
                                </Group>
                              </ScrollArea>
                            </Chip.Group>
                          </Group>
                          <Group grow>
                            <TextInput
                              placeholder="키워드 검색..."
                              leftSection={<IconSearch size={16} />}
                              value={trendKeyword}
                              onChange={(e) => setTrendKeyword(e.currentTarget.value)}
                            />
                            <Select
                              placeholder="지역 선택"
                              leftSection={<IconMapPin size={16} />}
                              data={[
                                { value: "kr", label: "🇰🇷 한국" },
                                { value: "us", label: "🇺🇸 미국" },
                                { value: "jp", label: "🇯🇵 일본" },
                                { value: "global", label: "🌍 글로벌" },
                              ]}
                              defaultValue="kr"
                            />
                          </Group>
                        </Stack>
                      </Card>

                      {/* 급상승 콘텐츠 */}
                      <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Stack gap="md">
                          <Group justify="space-between">
                            <Group gap="xs">
                              <IconTrendingUp size={20} className="text-orange-500" />
                              <Text fw={600} size="lg">🔥 급상승 콘텐츠</Text>
                            </Group>
                            <Badge variant="light" color="orange">실시간</Badge>
                          </Group>
                          <Grid>
                            {MOCK_TRENDING.map((trend) => (
                              <Grid.Col key={trend.id} span={{ base: 12, sm: 6, md: 4 }}>
                                <Card
                                  padding="md"
                                  radius="md"
                                  withBorder
                                  className="trend-card"
                                  onClick={() => openTrendDetail(trend)}
                                  style={{ cursor: "pointer" }}
                                >
                                  <Card.Section>
                                    <Box
                                      className="trend-thumbnail"
                                      style={{
                                        height: 120,
                                        background: "linear-gradient(135deg, var(--mantine-color-dark-6), var(--mantine-color-dark-4))",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: 40,
                                        position: "relative",
                                      }}
                                    >
                                      {trend.thumbnail}
                                      <Badge
                                        color={getPlatformColor(trend.platform)}
                                        variant="filled"
                                        size="xs"
                                        style={{ position: "absolute", top: 8, left: 8 }}
                                        leftSection={getPlatformIcon(trend.platform)}
                                      >
                                        {trend.platform}
                                      </Badge>
                                      <Badge
                                        color="red"
                                        variant="filled"
                                        size="xs"
                                        style={{ position: "absolute", top: 8, right: 8 }}
                                      >
                                        +{trend.rise}%
                                      </Badge>
                                    </Box>
                                  </Card.Section>
                                  <Stack gap="xs" mt="sm">
                                    <Text fw={500} size="sm" lineClamp={2}>{trend.title}</Text>
                                    <Group gap="md">
                                      <Group gap={4}>
                                        <IconEye size={12} />
                                        <Text size="xs" c="dimmed">{trend.views}</Text>
                                      </Group>
                                      <Group gap={4}>
                                        <IconHeart size={12} />
                                        <Text size="xs" c="dimmed">{trend.likes}</Text>
                                      </Group>
                                    </Group>
                                  </Stack>
                                </Card>
                              </Grid.Col>
                            ))}
                          </Grid>
                        </Stack>
                      </Card>

                      {/* 트렌드 분석 차트 */}
                      <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Stack gap="md">
                          <Group gap="xs">
                            <IconChartLine size={20} className="text-blue-500" />
                            <Text fw={600} size="lg">📊 트렌드 분석</Text>
                          </Group>
                          <Grid>
                            <Grid.Col span={{ base: 12, md: 8 }}>
                              <Paper p="md" radius="md" withBorder h={200} className="chart-placeholder">
                                <Text c="dimmed" ta="center" pt={80}>
                                  📈 시간별 인기도 추이 그래프
                                </Text>
                              </Paper>
                            </Grid.Col>
                            <Grid.Col span={{ base: 12, md: 4 }}>
                              <Paper p="md" radius="md" withBorder h={200}>
                                <Stack gap="xs">
                                  <Text fw={500} size="sm">📌 인기 키워드</Text>
                                  {["#AI영상", "#쇼츠", "#밈", "#챌린지", "#브이로그"].map((tag, i) => (
                                    <Group key={tag} justify="space-between">
                                      <Group gap="xs">
                                        <Text size="xs" c="dimmed">{i + 1}</Text>
                                        <Text size="sm">{tag}</Text>
                                      </Group>
                                      <Progress value={100 - i * 15} size="xs" w={60} color="violet" />
                                    </Group>
                                  ))}
                                </Stack>
                              </Paper>
                            </Grid.Col>
                          </Grid>
                        </Stack>
                      </Card>

                      {/* 밈 탐색기 */}
                      <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Stack gap="md">
                          <Group justify="space-between">
                            <Group gap="xs">
                              <IconMoodSmile size={20} className="text-pink-500" />
                              <Text fw={600} size="lg">😂 밈 탐색기</Text>
                            </Group>
                            <Button variant="subtle" size="xs" rightSection={<IconChevronRight size={14} />}>
                              더보기
                            </Button>
                          </Group>
                          <SimpleGrid cols={{ base: 2, sm: 4 }}>
                            {MOCK_MEMES.map((meme) => (
                              <Paper
                                key={meme.id}
                                p="md"
                                radius="md"
                                withBorder
                                className="meme-card"
                                style={{ cursor: "pointer" }}
                                onClick={() => alert(`밈 "${meme.title}" 선택 (UI Demo)`)}
                              >
                                <Stack align="center" gap="xs">
                                  <RingProgress
                                    size={60}
                                    thickness={4}
                                    sections={[{ value: meme.popularity, color: "pink" }]}
                                    label={
                                      <Text ta="center" size="xs" fw={700}>{meme.popularity}%</Text>
                                    }
                                  />
                                  <Text size="sm" fw={500} ta="center">{meme.title}</Text>
                                  <Badge size="xs" variant="light" color="gray">{meme.category}</Badge>
                                </Stack>
                              </Paper>
                            ))}
                          </SimpleGrid>
                        </Stack>
                      </Card>
                    </Stack>
                  </Tabs.Panel>

                  {/* ==================== AI 설정 탭 ==================== */}
                  <Tabs.Panel value="settings">
                    <AIModelSettings
                      configs={aiConfigs}
                      onConfigChange={handleAIConfigChange}
                      onTestConnection={handleTestConnection}
                    />
                  </Tabs.Panel>
                </Tabs>
              </Stack>
            </Container>

            {/* 트렌드 상세 Drawer */}
            <Drawer
              opened={detailDrawerOpen}
              onClose={() => setDetailDrawerOpen(false)}
              title={
                <Group gap="xs">
                  <IconTrendingUp size={20} />
                  <Text fw={600}>트렌드 상세 분석</Text>
                </Group>
              }
              position="right"
              size="md"
            >
              {selectedTrend && (
                <Stack gap="lg">
                  <Paper p="lg" radius="md" withBorder>
                    <Stack gap="md">
                      <Box
                        style={{
                          height: 150,
                          background: "linear-gradient(135deg, var(--mantine-color-dark-6), var(--mantine-color-dark-4))",
                          borderRadius: "var(--mantine-radius-md)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 60,
                        }}
                      >
                        {selectedTrend.thumbnail}
                      </Box>
                      <Text fw={600} size="lg">{selectedTrend.title}</Text>
                      <Group>
                        <Badge color={getPlatformColor(selectedTrend.platform)} leftSection={getPlatformIcon(selectedTrend.platform)}>
                          {selectedTrend.platform}
                        </Badge>
                        <Badge color="red">🔥 +{selectedTrend.rise}%</Badge>
                      </Group>
                    </Stack>
                  </Paper>

                  <Paper p="md" radius="md" withBorder>
                    <Stack gap="sm">
                      <Text fw={500}>📊 통계</Text>
                      <Group grow>
                        <Stack align="center" gap={4}>
                          <IconEye size={24} />
                          <Text size="lg" fw={700}>{selectedTrend.views}</Text>
                          <Text size="xs" c="dimmed">조회수</Text>
                        </Stack>
                        <Stack align="center" gap={4}>
                          <IconHeart size={24} />
                          <Text size="lg" fw={700}>{selectedTrend.likes}</Text>
                          <Text size="xs" c="dimmed">좋아요</Text>
                        </Stack>
                        <Stack align="center" gap={4}>
                          <IconShare size={24} />
                          <Text size="lg" fw={700}>12K</Text>
                          <Text size="xs" c="dimmed">공유</Text>
                        </Stack>
                      </Group>
                    </Stack>
                  </Paper>

                  <Paper p="md" radius="md" withBorder>
                    <Stack gap="sm">
                      <Text fw={500}>🏷️ 관련 해시태그</Text>
                      <Group>
                        {["#트렌드", "#viral", "#쇼츠", "#shorts", "#인기"].map((tag) => (
                          <Badge key={tag} variant="light" color="gray">{tag}</Badge>
                        ))}
                      </Group>
                    </Stack>
                  </Paper>

                  <Button
                    fullWidth
                    variant="gradient"
                    gradient={{ from: "orange", to: "red" }}
                    leftSection={<IconSparkles size={18} />}
                    onClick={() => {
                      setDetailDrawerOpen(false);
                      setActiveTab("create");
                      setStory(`"${selectedTrend.title}" 트렌드를 참고한 영상 컨셉...`);
                      alert("트렌드를 영상 제작에 적용했습니다! (UI Demo)");
                    }}
                  >
                    이 트렌드로 영상 만들기
                  </Button>
                </Stack>
              )}
            </Drawer>
          </>
        )}
      </AppShell.Main>
    </AppShell >
  );
}
