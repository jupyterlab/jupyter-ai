import React from 'react';
import { Box } from '@mui/material';
import {
  addAboveIcon,
  addBelowIcon,
  copyIcon
} from '@jupyterlab/ui-components';
import { replaceCellIcon } from '../../icons';

import {
  ActiveCellManager,
  useActiveCellContext
} from '../../contexts/active-cell-context';
import { TooltippedIconButton } from '../mui-extras/tooltipped-icon-button';
import { useReplace } from '../../hooks/use-replace';
import { useCopy } from '../../hooks/use-copy';
import { AiService } from '../../handler';
import { useTelemetry } from '../../contexts/telemetry-context';

export type CodeToolbarProps = {
  /**
   * The content of the Markdown code block this component is attached to.
   */
  content: string;
  /**
   * Parent message which contains the code referenced by `content`.
   */
  parentMessage?: AiService.ChatMessage;
};

export function CodeToolbar(props: CodeToolbarProps): JSX.Element {
  const activeCell = useActiveCellContext();
  const sharedToolbarButtonProps: ToolbarButtonProps = {
    content: props.content,
    activeCellManager: activeCell.manager,
    activeCellExists: activeCell.exists,
    parentMessage: props.parentMessage
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        padding: '6px 2px',
        marginBottom: '1em',
        border: '1px solid var(--jp-cell-editor-border-color)',
        borderTop: 'none'
      }}
    >
      <InsertAboveButton {...sharedToolbarButtonProps} />
      <InsertBelowButton {...sharedToolbarButtonProps} />
      <ReplaceButton {...sharedToolbarButtonProps} />
      <CopyButton {...sharedToolbarButtonProps} />
    </Box>
  );
}

type ToolbarButtonProps = {
  content: string;
  activeCellExists: boolean;
  activeCellManager: ActiveCellManager;
  parentMessage?: AiService.ChatMessage;
};

function InsertAboveButton(props: ToolbarButtonProps) {
  const telemetryHandler = useTelemetry();
  const tooltip = props.activeCellExists
    ? 'Insert above active cell'
    : 'Insert above active cell (no active cell)';

  return (
    <TooltippedIconButton
      tooltip={tooltip}
      onClick={() => {
        props.activeCellManager.insertAbove(props.content);

        try {
          telemetryHandler.onEvent({
            type: 'insert-above',
            parentMessage: props.parentMessage,
            code: props.content
          });
        } catch (e) {
          console.error(e);
          return;
        }
      }}
      disabled={!props.activeCellExists}
    >
      <addAboveIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

function InsertBelowButton(props: ToolbarButtonProps) {
  const telemetryHandler = useTelemetry();
  const tooltip = props.activeCellExists
    ? 'Insert below active cell'
    : 'Insert below active cell (no active cell)';

  return (
    <TooltippedIconButton
      tooltip={tooltip}
      disabled={!props.activeCellExists}
      onClick={() => {
        props.activeCellManager.insertBelow(props.content);

        try {
          telemetryHandler.onEvent({
            type: 'insert-below',
            parentMessage: props.parentMessage,
            code: props.content
          });
        } catch (e) {
          console.error(e);
          return;
        }
      }}
    >
      <addBelowIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

function ReplaceButton(props: ToolbarButtonProps) {
  const telemetryHandler = useTelemetry();
  const { replace, replaceDisabled, replaceLabel } = useReplace();

  return (
    <TooltippedIconButton
      tooltip={replaceLabel}
      disabled={replaceDisabled}
      onClick={() => {
        replace(props.content);

        try {
          telemetryHandler.onEvent({
            type: 'replace',
            parentMessage: props.parentMessage,
            code: props.content
          });
        } catch (e) {
          console.error(e);
          return;
        }
      }}
    >
      <replaceCellIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

export function CopyButton(props: ToolbarButtonProps): JSX.Element {
  const telemetryHandler = useTelemetry();
  const { copy, copyLabel } = useCopy();

  return (
    <TooltippedIconButton
      tooltip={copyLabel}
      placement="top"
      onClick={() => {
        copy(props.content);

        try {
          telemetryHandler.onEvent({
            type: 'copy',
            parentMessage: props.parentMessage,
            code: props.content
          });
        } catch (e) {
          console.error(e);
          return;
        }
      }}
      aria-label="Copy to clipboard"
    >
      <copyIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}
