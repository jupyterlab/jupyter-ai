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
import { TelemetryEvent } from '../../tokens';
import { useUtilsContext } from '../../contexts/utils-context';

export type CodeToolbarProps = {
  /**
   * The content of the Markdown code block this component is attached to.
   */
  code: string;
  /**
   * Parent message which contains the code referenced by `content`.
   */
  parentMessage?: AiService.ChatMessage;
};

export function CodeToolbar(props: CodeToolbarProps): JSX.Element {
  const activeCell = useActiveCellContext();
  const sharedToolbarButtonProps: ToolbarButtonProps = {
    code: props.code,
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
        padding: '2px 2px',
        marginBottom: '1em',
        border: '1px solid var(--jp-cell-editor-border-color)',
        borderTop: 'none'
      }}
    >
      <CopyButton {...sharedToolbarButtonProps} />
      <ReplaceButton {...sharedToolbarButtonProps} />
      <InsertAboveButton {...sharedToolbarButtonProps} />
      <InsertBelowButton {...sharedToolbarButtonProps} />
    </Box>
  );
}

const useCellAction = (callback: () => void, command: string, props: ToolbarButtonProps) => {
    const { goBackToNotebook } = useUtilsContext();
    const telemetryHandler = useTelemetry();

    return () => {
        callback();
        if (goBackToNotebook) goBackToNotebook();

        try {
            telemetryHandler.onEvent(buildTelemetryEvent(command, props));
          } catch (e) {
            console.error(e);
            return;
          }
    }
}

type ToolbarButtonProps = {
  code: string;
  activeCellExists: boolean;
  activeCellManager: ActiveCellManager;
  parentMessage?: AiService.ChatMessage;
  // TODO: parentMessage should always be defined, but this can be undefined
  // when the code toolbar appears in Markdown help messages in the Settings
  // UI. The Settings UI should use a different component to render Markdown,
  // and should never render code toolbars within it.
};

function buildTelemetryEvent(
  type: string,
  props: ToolbarButtonProps
): TelemetryEvent {
  const charCount = props.code.length;
  // number of lines = number of newlines + 1
  const lineCount = (props.code.match(/\n/g) ?? []).length + 1;

  return {
    type,
    message: {
      id: props.parentMessage?.id ?? '',
      type: props.parentMessage?.type ?? 'human',
      time: props.parentMessage?.time ?? 0,
      metadata:
        props.parentMessage && 'metadata' in props.parentMessage
          ? props.parentMessage.metadata
          : {}
    },
    code: {
      charCount,
      lineCount
    }
  };
}

function InsertAboveButton(props: ToolbarButtonProps) {
  const tooltip = props.activeCellExists
    ? 'Insert above active cell'
    : 'Insert above active cell (no active cell)';
  const cb = useCellAction(() => props.activeCellManager.insertAbove(props.code), 'insert-above', props);

  return (
    <TooltippedIconButton
      tooltip={tooltip}
      onClick={cb}
      disabled={!props.activeCellExists}
    >
      <addAboveIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

function InsertBelowButton(props: ToolbarButtonProps) {
  const tooltip = props.activeCellExists
    ? 'Insert below active cell'
    : 'Insert below active cell (no active cell)';
  const cb = useCellAction(() => props.activeCellManager.insertBelow(props.code), 'insert-below', props);

  return (
    <TooltippedIconButton
      tooltip={tooltip}
      disabled={!props.activeCellExists}
      onClick={cb}
    >
      <addBelowIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

function ReplaceButton(props: ToolbarButtonProps) {
  const { replace, replaceDisabled, replaceLabel } = useReplace();
  const cb = useCellAction(() => replace(props.code), 'replace', props);

  return (
    <TooltippedIconButton
      tooltip={replaceLabel}
      disabled={replaceDisabled}
      onClick={cb}
    >
      <replaceCellIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

export function CopyButton(props: ToolbarButtonProps): JSX.Element {
  const { copy, copyLabel } = useCopy();

  const cb = useCellAction(() => copy(props.code), 'copy', props);

  return (
    <TooltippedIconButton
      tooltip={copyLabel}
      placement="top"
      onClick={cb}
      aria-label="Copy to clipboard"
    >
      <copyIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}
