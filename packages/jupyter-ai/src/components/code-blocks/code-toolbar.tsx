import React from 'react';
import { Box } from '@mui/material';
import { addAboveIcon, addBelowIcon } from '@jupyterlab/ui-components';

import { CopyButton } from './copy-button';
import { replaceCellIcon } from '../../icons';

import {
  ActiveCellManager,
  useActiveCellContext
} from '../../contexts/active-cell-context';
import { TooltippedIconButton } from '../mui-extras/tooltipped-icon-button';
import { useReplace } from '../../hooks/use-replace';

export type CodeToolbarProps = {
  /**
   * The content of the Markdown code block this component is attached to.
   */
  content: string;
};

export function CodeToolbar(props: CodeToolbarProps): JSX.Element {
  const activeCell = useActiveCellContext();
  const sharedToolbarButtonProps = {
    content: props.content,
    activeCellManager: activeCell.manager,
    activeCellExists: activeCell.exists
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
      <ReplaceButton value={props.content} />
      <CopyButton value={props.content} />
    </Box>
  );
}

type ToolbarButtonProps = {
  content: string;
  activeCellExists: boolean;
  activeCellManager: ActiveCellManager;
};

function InsertAboveButton(props: ToolbarButtonProps) {
  const tooltip = props.activeCellExists
    ? 'Insert above active cell'
    : 'Insert above active cell (no active cell)';

  return (
    <TooltippedIconButton
      tooltip={tooltip}
      onClick={() => props.activeCellManager.insertAbove(props.content)}
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

  return (
    <TooltippedIconButton
      tooltip={tooltip}
      disabled={!props.activeCellExists}
      onClick={() => props.activeCellManager.insertBelow(props.content)}
    >
      <addBelowIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}

function ReplaceButton(props: { value: string }) {
  const { replace, replaceDisabled, replaceLabel } = useReplace();

  return (
    <TooltippedIconButton
      tooltip={replaceLabel}
      disabled={replaceDisabled}
      onClick={() => replace(props.value)}
    >
      <replaceCellIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}
