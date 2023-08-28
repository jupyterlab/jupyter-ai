// import React, { useEffect } from 'react';
import React, { useEffect } from 'react';
import { Box, TextField } from '@mui/material';
import CodeCompletionContextstore from '../contexts/code-completion-context-store';
import { observer } from 'mobx-react-lite';
import { parseKeyboardEventToShortcut } from '../utils/keyboard';

export const BigCodeSetting = observer(() => {
  const { bigcodeUrl } = CodeCompletionContextstore;
  const { accessToken } = CodeCompletionContextstore;

  const setBigcodeUrlWrapper = (value: string) => {
    CodeCompletionContextstore.setBigcodeUrl(value);
  };

  const setAccessTokenWrapper = (value: string) => {
    CodeCompletionContextstore.setAccessToken(value);
    console.debug('setAccessToken()');
  };

  const setHotKeyWrapper = (event: React.KeyboardEvent<HTMLInputElement>) => {
    event.preventDefault();
    const shortcutStr = parseKeyboardEventToShortcut(event);
    CodeCompletionContextstore.setShortcutStr(shortcutStr);
    console.debug('setHotKey() => The current hotkey is ', shortcutStr);
  };

  useEffect(() => {
    CodeCompletionContextstore.setBigcodeUrl(
      'https://api-inference.huggingface.co/models/bigcode/starcoderbase/'
    );
  }, []);

  return (
    <Box
      sx={{
        padding: 4,
        boxSizing: 'border-box',
        '& > .MuiAlert-root': { marginBottom: 2 },
        overflowY: 'auto'
      }}
    >
      <h2 className="jp-ai-ChatSettings-header">Bigcode service url</h2>
      <TextField
        label="Bigcode service url"
        value={bigcodeUrl}
        fullWidth
        type="text"
        onChange={e => setBigcodeUrlWrapper(e.target.value)}
      />

      <h2 className="jp-ai-ChatSettings-header">Huggingface Access Token</h2>
      <TextField
        label="Huggingface Access Token"
        value={accessToken}
        fullWidth
        type="password"
        onChange={e => setAccessTokenWrapper(e.target.value)}
      />

      <h2 className="jp-ai-ChatSettings-header">Hotkey for continue writing</h2>
      <TextField
        label="Please press the hotkey you need"
        value={CodeCompletionContextstore.shortcutStr}
        fullWidth
        type="text"
        onKeyDown={setHotKeyWrapper}
      />
    </Box>
  );
});
