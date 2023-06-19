import React, { useState, useMemo } from 'react';

import type { CodeProps } from 'react-markdown/lib/ast-to-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { duotoneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Box, Button } from '@mui/material';
import cx from 'clsx';

type ChatCodeViewProps = CodeProps;

type ChatCodeInlineProps = ChatCodeViewProps;

type ChatCodeBlockProps = ChatCodeViewProps & {
  language?: string;
};

const JPAI_CODE_CLASS = 'jp-ai-code';

function ChatCodeInline({
  className,
  children,
  ...props
}: ChatCodeInlineProps) {
  return (
    <code {...props} className={cx(JPAI_CODE_CLASS, className)}>
      {children}
    </code>
  );
}

enum CopyStatus {
  None,
  Copying,
  Copied
}

const COPYBTN_TEXT_BY_STATUS: Record<CopyStatus, string> = {
  [CopyStatus.None]: 'Copy to clipboard',
  [CopyStatus.Copying]: 'Copying...',
  [CopyStatus.Copied]: 'Copied!'
};

function ChatCodeBlock({ language, children, ...props }: ChatCodeBlockProps) {
  const value = useMemo(() => String(children).replace(/\n$/, ''), [children]);
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(CopyStatus.None);

  const copy = async () => {
    setCopyStatus(CopyStatus.Copying);
    try {
      await navigator.clipboard.writeText(value);
    } catch (e) {
      console.error(e);
      setCopyStatus(CopyStatus.None);
      return;
    }

    setCopyStatus(CopyStatus.Copied);
    setTimeout(() => setCopyStatus(CopyStatus.None), 1000);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <SyntaxHighlighter
        {...props}
        className={cx(props.className, JPAI_CODE_CLASS)}
        children={value}
        style={duotoneLight}
        language={language}
        PreTag="div"
      />
      <Button
        onClick={copy}
        disabled={copyStatus !== CopyStatus.None}
        sx={{ alignSelf: 'flex-end' }}
      >
        {COPYBTN_TEXT_BY_STATUS[copyStatus]}
      </Button>
    </Box>
  );
}

export function ChatCodeView({
  inline,
  className,
  ...props
}: ChatCodeViewProps): JSX.Element {
  const match = /language-(\w+)/.exec(className || '');
  return inline ? (
    <ChatCodeInline {...props} />
  ) : (
    <ChatCodeBlock {...props} language={match ? match[1] : undefined} />
  );
}
