import React from 'react';

import { copyIcon } from '@jupyterlab/ui-components';

import { TooltippedIconButton } from '../mui-extras/tooltipped-icon-button';
import { useCopy } from '../../hooks/use-copy';

type CopyButtonProps = {
  value: string;
};

export function CopyButton(props: CopyButtonProps): JSX.Element {
  const { copy, copyLabel } = useCopy();

  return (
    <TooltippedIconButton
      tooltip={copyLabel}
      placement="top"
      onClick={() => copy(props.value)}
      aria-label="Copy to clipboard"
    >
      <copyIcon.react height="16px" width="16px" />
    </TooltippedIconButton>
  );
}
