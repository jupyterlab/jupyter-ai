import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Collapse,
  IconButton,
  CircularProgress
} from '@mui/material';
import ExpandMore from '@mui/icons-material/ExpandMore';
import CheckCircle from '@mui/icons-material/CheckCircle';

type JaiToolCallProps = {
  id: string;
  type: string;
  function: {
    name: string;
    arguments: Record<string, any>;
  };
  index: number;
  output?: {
    tool_call_id: string;
    role: string;
    name: string;
    content: string | null;
  };
};

export function JaiToolCall(props: JaiToolCallProps): JSX.Element | null {
  const [expanded, setExpanded] = useState(false);
  console.log({
    output: props.output
  });
  const toolComplete = !!(props.output && Object.keys(props.output).length > 0);
  const hasOutput = !!(toolComplete && props.output?.content?.length);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const statusIcon: JSX.Element = toolComplete ? (
    <CheckCircle sx={{ color: 'green', fontSize: 16 }} />
  ) : (
    <CircularProgress size={16} />
  );

  const statusText: JSX.Element = (
    <Typography variant="caption">
      {toolComplete ? 'Ran' : 'Running'}{' '}
      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
        {props.function.name}
      </Typography>{' '}
      tool
      {toolComplete ? '.' : '...'}
    </Typography>
  );

  const toolArgsJson = useMemo(
    () => JSON.stringify(props.function.arguments, null, 2),
    [props.function.arguments]
  );

  const toolArgsSection: JSX.Element | null =
    toolArgsJson === '{}' ? null : (
      <Box>
        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
          Tool arguments
        </Typography>
        <pre style={{ marginBottom: toolComplete ? 8 : 'unset' }}>
          {toolArgsJson}
        </pre>
      </Box>
    );

  const toolOutputSection: JSX.Element | null = hasOutput ? (
    <Box>
      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
        Tool output
      </Typography>
      <pre>{props.output?.content}</pre>
    </Box>
  ) : null;

  if (!props.id || !props.type || !props.function) {
    return null;
  }

  return (
    <Box
      sx={{
        border: '1px solid #e0e0e0',
        borderRadius: 1,
        p: 1,
        mb: 1
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {statusIcon}
        {statusText}

        <IconButton
          onClick={handleExpandClick}
          size="small"
          sx={{
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s',
            borderRadius: 'unset'
          }}
        >
          <ExpandMore />
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #f0f0f0' }}>
          {toolArgsSection}
          {toolOutputSection}
        </Box>
      </Collapse>
    </Box>
  );
}
