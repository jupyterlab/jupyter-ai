import React, { useState, useCallback } from 'react';

import { Box, Button } from '@mui/material';

// const CC_BTN_CLASS = 'jp-ai-copy-button';
// const CC_BTN_CONTAINER_CLASS = 'jp-ai-copy-button-container';

enum CopyStatus {
  None,
  Copying,
  Copied
}

const COPYBTN_TEXT_BY_STATUS: Record<CopyStatus, string> = {
  [CopyStatus.None]: 'Copy To Clipboard',
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
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <Button
        onClick={copy}
        disabled={copyStatus !== CopyStatus.None}
        aria-label="Copy To Clipboard"
        sx={{
          alignSelf: 'flex-end',
          textTransform: 'none'
        }}
      >
        {COPYBTN_TEXT_BY_STATUS[copyStatus]}
      </Button>
    </Box>
  );
}