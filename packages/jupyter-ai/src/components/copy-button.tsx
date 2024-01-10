import React, { useState, useCallback } from 'react';

import Button from '@mui/material/Button';

const CC_BTN_CONTAINER_CLASS = 'jp-ai-copy-button-container';
const CC_BTN_CLASS = 'jp-ai-copy-button';

enum CopyStatus {
  None,
  Copying,
  Copied
}

const COPYBTN_TEXT_BY_STATUS: Record<CopyStatus, string> = {
  [CopyStatus.None]: 'Copy',
  [CopyStatus.Copying]: 'Copying...',
  [CopyStatus.Copied]: 'Copied!'
};

type CopyButtonProps = {
  value: string;
};

export function CopyButton(props: CopyButtonProps): JSX.Element {
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(CopyStatus.None);

  const copy = useCallback(async () => {
    setCopyStatus(CopyStatus.Copying);
    try {
      await navigator.clipboard.writeText(props.value);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      setCopyStatus(CopyStatus.None);
      return;
    }

    setCopyStatus(CopyStatus.Copied);
    setTimeout(() => setCopyStatus(CopyStatus.None), 1000);
  }, [props.value]);

  return (
    <div className={CC_BTN_CONTAINER_CLASS}>
      <Button
        onClick={copy}
        className={CC_BTN_CLASS}
        variant="outlined"
        aria-label="Copy to clipboard"
        title="Copy to clipboard"
      >
        {COPYBTN_TEXT_BY_STATUS[copyStatus]}
      </Button>
    </div>
  );
}
