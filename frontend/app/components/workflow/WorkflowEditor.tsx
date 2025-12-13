"use client";

import React, { useCallback } from 'react';
import {
    ReactFlow,
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    Edge,
    Node,
    BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Box, Paper, Text, Group, Button, Badge, ThemeIcon, Stack } from '@mantine/core';
import { IconPlayerPlay, IconSettings } from '@tabler/icons-react';
import { WorkflowNode } from './WorkflowTypes';
import { NodeControlPanel } from './NodeControlPanel';


// Custom Node Component (can be expanded later)
const CustomNode = ({ data }: { data: WorkflowNode }) => {
    return (
        <Paper
            shadow="sm"
            p="sm"
            radius="md"
            withBorder
            style={{
                minWidth: 200,
                borderColor: data.status === 'processing' ? 'var(--mantine-color-violet-5)' :
                    data.status === 'completed' ? 'var(--mantine-color-green-5)' :
                        undefined,
                background: 'var(--mantine-color-dark-7)',
            }}
        >
            <Group justify="space-between" mb="xs">
                <ThemeIcon
                    size="md"
                    radius="md"
                    variant={data.status === 'processing' ? 'filled' : 'light'}
                    color={data.status === 'completed' ? 'green' : 'violet'}
                >
                    <Text size="sm">{data.icon}</Text>
                </ThemeIcon>
                <Badge
                    size="xs"
                    variant="light"
                    color={
                        data.status === 'completed' ? 'green' :
                            data.status === 'processing' ? 'violet' :
                                data.status === 'error' ? 'red' : 'gray'
                    }
                >
                    {data.status}
                </Badge>
            </Group>
            <Text size="sm" fw={700} c="bright">{data.label}</Text>
            <Text size="xs" c="dimmed">{data.config.modelType === 'api' ? data.config.provider : 'Local Model'}</Text>
        </Paper>
    );
};

const nodeTypes = {
    custom: CustomNode,
};

interface WorkflowEditorProps {
    initialNodes: WorkflowNode[];
}

export function WorkflowEditor({ initialNodes }: WorkflowEditorProps) {
    // Convert our WorkflowNodes to ReactFlow Nodes
    const initialFlowNodes: Node[] = initialNodes.map((node) => ({
        id: node.id,
        type: 'custom',
        position: node.position,
        data: { ...node }, // Pass the whole object as data
    }));

    // Create simple edges (linear flow for now)
    const initialEdges: Edge[] = initialNodes.slice(0, -1).map((node, index) => ({
        id: `e-${node.id}-${initialNodes[index + 1].id}`,
        source: node.id,
        target: initialNodes[index + 1].id,
        animated: true,
        style: { stroke: 'var(--mantine-color-violet-5)' },
    }));

    const [nodes, setNodes, onNodesChange] = useNodesState(initialFlowNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    /* Node Selection & Panel Logic */
    const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);

    const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        setSelectedNodeId(node.id);
    }, []);

    const closePanel = () => setSelectedNodeId(null);

    // Find user data for selected node
    const selectedNodeData = initialNodes.find(n => n.id === selectedNodeId);

    const handleNodeUpdate = (updatedNode: WorkflowNode) => {
        // In a real app, you would update the 'nodes' state here and propagate changes.
        // For UI demo, we'll just log or update the specific node in the local state if needed.
        console.log("Update Node:", updatedNode);
        // TODO: Implement state update logic
    };

    const handleRegenerate = () => {
        alert(`Regenerating logic for node ${selectedNodeId} (Demo)`);
    };

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <Box w="100%" h="calc(100vh - 20px)" style={{ background: '#1A1B1E', display: 'flex' }}>
            <Box style={{ flex: 1, position: 'relative' }}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeClick={onNodeClick}
                    nodeTypes={nodeTypes}
                    fitView
                    colorMode="dark"
                >
                    <Controls />
                    <MiniMap
                        nodeStrokeColor={(n) => '#fff'}
                        nodeColor={(n) => '#fff'}
                        style={{ background: '#2C2E33' }}
                    />
                    <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
                </ReactFlow>

                {/* Main Controls Overlay */}
                <Paper
                    pos="absolute"
                    top={20}
                    right={20}
                    p="sm"
                    radius="md"
                    withBorder
                    style={{ zIndex: 5, background: 'rgba(26, 27, 30, 0.8)', backdropFilter: 'blur(5px)' }}
                >
                    <Stack gap="xs">
                        <Button leftSection={<IconPlayerPlay size={16} />} variant="gradient" gradient={{ from: 'violet', to: 'cyan' }}>
                            Run Workflow
                        </Button>
                        <Button leftSection={<IconSettings size={16} />} variant="light" color="gray">
                            Settings
                        </Button>
                    </Stack>
                </Paper>
            </Box>

            {/* Detail Panel */}
            {selectedNodeId && selectedNodeData && (
                <NodeControlPanel
                    node={selectedNodeData}
                    onClose={closePanel}
                    onUpdate={handleNodeUpdate}
                    onRegenerate={handleRegenerate}
                />
            )}
        </Box>
    );
}

