import React, { useState, useCallback } from 'react';

import { Box, Button } from '@mui/material';

enum CopyStatus {
  None,
  Copied
}

const COPYBTN_TEXT_BY_STATUS: Record<CopyStatus, string> = {
  [CopyStatus.None]: 'Copy to Clipboard',
  [CopyStatus.Copied]: 'Copied!'
};

type CopyButtonProps = {
  value: string;
};

export function CopyButton(props: CopyButtonProps): JSX.Element {
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(CopyStatus.None);

  const copy = useCallback(async () => {
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
