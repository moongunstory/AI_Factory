"use client";

import React, { useState } from 'react';
import { Paper, Stack, Group, Button, Text, Badge, Loader, Modal, Textarea, Box, Divider } from '@mantine/core';
import { IconSparkles, IconPlayerPlay, IconRefresh } from '@tabler/icons-react';

// 3단계 노드 타입
type StepType = 'expand' | 'storyboard' | 'prompt';
type StepStatus = 'pending' | 'processing' | 'completed' | 'error';

interface StepNode {
  id: StepType;
  label: string;
  icon: string;
  status: StepStatus;
  result?: string;
  error?: string;
}

interface SimplifiedWorkflowProps {
  initialStory: string;
  onComplete?: (results: { expanded_story: string; storyboard: string; prompts: string }) => void;
}

export function SimplifiedWorkflow({ initialStory, onComplete }: SimplifiedWorkflowProps) {
  // 3개 노드 상태
  const [nodes, setNodes] = useState<StepNode[]>([
    { id: 'expand', label: '이야기 확장', icon: '📖', status: 'pending' },
    { id: 'storyboard', label: '스토리보드 작성', icon: '🎬', status: 'pending' },
    { id: 'prompt', label: '프롬프트 작성', icon: '✨', status: 'pending' },
  ]);

  // 워크플로우 실행 상태
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState<StepType | null>(null);

  // 재시도 모달 상태
  const [revisionModalOpen, setRevisionModalOpen] = useState(false);
  const [revisionStep, setRevisionStep] = useState<StepType | null>(null);
  const [revisionText, setRevisionText] = useState('');

  // 노드 업데이트 헬퍼
  const updateNode = (id: StepType, updates: Partial<StepNode>) => {
    setNodes(prev => prev.map(n => n.id === id ? { ...n, ...updates } : n));
  };

  // 원클릭 제작 핸들러
  const handleOneClickGeneration = async () => {
    setIsRunning(true);

    try {
      // Step 1: 이야기 확장
      await executeStep('expand', initialStory);

      // Step 2: 스토리보드 작성
      const expandedStory = nodes.find(n => n.id === 'expand')?.result || '';
      await executeStep('storyboard', expandedStory);

      // Step 3: 프롬프트 작성
      const storyboard = nodes.find(n => n.id === 'storyboard')?.result || '';
      await executeStep('prompt', storyboard);

      // 완료 콜백
      if (onComplete) {
        const results = {
          expanded_story: nodes.find(n => n.id === 'expand')?.result || '',
          storyboard: nodes.find(n => n.id === 'storyboard')?.result || '',
          prompts: nodes.find(n => n.id === 'prompt')?.result || '',
        };
        onComplete(results);
      }

    } catch (error) {
      console.error('워크플로우 실행 중 오류:', error);
    } finally {
      setIsRunning(false);
      setCurrentStep(null);
    }
  };

  // 개별 단계 실행
  const executeStep = async (step: StepType, input: string) => {
    setCurrentStep(step);
    updateNode(step, { status: 'processing' });

    try {
      // API 호출 (실제 구현 필요)
      const result = await callGPTWorkflowStep(step, input);
      updateNode(step, { status: 'completed', result });
    } catch (error: any) {
      updateNode(step, { status: 'error', error: error.message });
      throw error;
    }
  };

  // GPT API 호출 (Mock)
  const callGPTWorkflowStep = async (step: StepType, input: string): Promise<string> => {
    // Mock 딜레이
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 실제로는 백엔드 API 호출
    // const response = await fetch(`/api/gpt/${step}`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ input })
    // });
    // return await response.json();

    return `${step} 결과: ${input.substring(0, 50)}...`;
  };

  // 재시도 핸들러
  const handleRevisionClick = (step: StepType) => {
    setRevisionStep(step);
    setRevisionModalOpen(true);
    setRevisionText('');
  };

  const handleRevisionSubmit = async () => {
    if (!revisionStep || !revisionText.trim()) return;

    setRevisionModalOpen(false);
    updateNode(revisionStep, { status: 'processing' });

    try {
      // 재시도 API 호출 (실제 구현 필요)
      const result = await callGPTRevision(revisionStep, revisionText);
      updateNode(revisionStep, { status: 'completed', result });
    } catch (error: any) {
      updateNode(revisionStep, { status: 'error', error: error.message });
    }
  };

  const callGPTRevision = async (step: StepType, revisionText: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return `${step} 재생성 결과: ${revisionText}`;
  };

  return (
    <Box p="xl">
      {/* 그룹 컨테이너 */}
      <Paper
        p="xl"
        radius="lg"
        withBorder
        style={{
          borderColor: 'var(--mantine-color-violet-5)',
          borderWidth: 2,
          background: 'var(--mantine-color-dark-7)',
        }}
      >
        <Stack gap="xl">
          {/* 그룹 헤더 + 원클릭 제작 버튼 */}
          <Group justify="space-between" align="center">
            <Text size="xl" fw={700} c="bright">
              🎬 비디오 생성 워크플로우
            </Text>
            <Button
              size="lg"
              variant="gradient"
              gradient={{ from: 'violet', to: 'cyan' }}
              leftSection={isRunning ? <Loader size="xs" color="white" /> : <IconPlayerPlay size={20} />}
              onClick={handleOneClickGeneration}
              disabled={isRunning || !initialStory}
            >
              원클릭 제작
            </Button>
          </Group>

          <Divider />

          {/* 3개 노드 플로우차트 스타일 */}
          <Group justify="center" align="flex-start" gap="xl" wrap="nowrap">
            {nodes.map((node, index) => (
              <React.Fragment key={node.id}>
                {/* 노드 카드 */}
                <Stack align="center" gap="sm" style={{ flex: 1, maxWidth: 300 }}>
                  <Paper
                    shadow="md"
                    p="lg"
                    radius="md"
                    withBorder
                    style={{
                      width: '100%',
                      minHeight: 150,
                      borderColor: node.status === 'processing' || node.status === 'completed'
                        ? 'var(--mantine-color-green-5)'
                        : node.status === 'error'
                          ? 'var(--mantine-color-red-5)'
                          : 'var(--mantine-color-dark-4)',
                      borderWidth: node.status === 'processing' ? 3 : 1,
                      animation: node.status === 'processing' ? 'pulse-green 1.5s ease-in-out infinite' : 'none',
                      background: 'var(--mantine-color-dark-6)',
                    }}
                  >
                    <Stack gap="md" align="center">
                      {/* 아이콘 + 라벨 */}
                      <Group gap="xs">
                        <Text size="2rem">{node.icon}</Text>
                        <Stack gap={0}>
                          <Text fw={700} size="lg">{node.label}</Text>
                          <Badge
                            color={
                              node.status === 'completed' ? 'green' :
                                node.status === 'processing' ? 'green' :
                                  node.status === 'error' ? 'red' : 'gray'
                            }
                            variant="light"
                            size="sm"
                          >
                            {node.status === 'pending' ? '대기 중' :
                              node.status === 'processing' ? '진행 중...' :
                                node.status === 'completed' ? '완료' : '오류'}
                          </Badge>
                        </Stack>
                      </Group>

                      {/* 결과 미리보기 */}
                      {node.result && (
                        <Paper p="xs" radius="sm" withBorder w="100%" style={{ background: 'var(--mantine-color-dark-8)' }}>
                          <Text size="xs" c="dimmed" lineClamp={3}>
                            {node.result}
                          </Text>
                        </Paper>
                      )}

                      {/* 에러 메시지 */}
                      {node.error && (
                        <Text size="xs" c="red">
                          {node.error}
                        </Text>
                      )}

                      {/* 버튼들 */}
                      <Group gap="xs" mt="auto">
                        <Button
                          size="xs"
                          variant="light"
                          color="violet"
                          leftSection={<IconPlayerPlay size={14} />}
                          onClick={() => executeStep(node.id, initialStory)}
                          disabled={isRunning}
                        >
                          진행
                        </Button>
                        <Button
                          size="xs"
                          variant="light"
                          color="gray"
                          leftSection={<IconRefresh size={14} />}
                          onClick={() => handleRevisionClick(node.id)}
                          disabled={!node.result}
                        >
                          재시도
                        </Button>
                      </Group>
                    </Stack>
                  </Paper>
                </Stack>

                {/* 연결선 화살표 */}
                {index < nodes.length - 1 && (
                  <Box style={{ paddingTop: 60 }}>
                    <Text size="3rem" c="violet">→</Text>
                  </Box>
                )}
              </React.Fragment>
            ))}
          </Group>
        </Stack>
      </Paper>

      {/* 재시도 모달 */}
      <Modal
        opened={revisionModalOpen}
        onClose={() => setRevisionModalOpen(false)}
        title={
          <Group gap="xs">
            <IconRefresh size={20} />
            <Text fw={600}>재시도 요청</Text>
          </Group>
        }
        centered
      >
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            수정하고 싶은 부분을 구체적으로 설명해주세요.
          </Text>
          <Textarea
            placeholder="예: 더 극적인 전개로 바꿔주세요. 클라이맥스 부분이 약한 것 같아요."
            minRows={4}
            autosize
            value={revisionText}
            onChange={(e) => setRevisionText(e.currentTarget.value)}
          />
          <Group justify="flex-end" gap="xs">
            <Button variant="subtle" onClick={() => setRevisionModalOpen(false)}>
              취소
            </Button>
            <Button
              variant="gradient"
              gradient={{ from: 'violet', to: 'cyan' }}
              onClick={handleRevisionSubmit}
              disabled={!revisionText.trim()}
            >
              재생성 요청
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes pulse-green {
          0%, 100% {
            border-color: var(--mantine-color-green-5);
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
          }
          50% {
            border-color: var(--mantine-color-green-4);
            box-shadow: 0 0 0 10px rgba(34, 197, 94, 0);
          }
        }
      `}</style>
    </Box>
  );
}
