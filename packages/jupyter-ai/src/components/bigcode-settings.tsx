// import React, { useEffect } from 'react';
import React, { useEffect } from 'react';
import { Box, TextField } from '@mui/material';
import CodeCompletionContextstore from '../contexts/code-completion-context-store';
import { observer } from 'mobx-react-lite';
import { parseKeyboardEventToShortcut } from '../utils/keyboard';
import Switch from '@mui/material/Switch';
import Slider from '@mui/material/Slider';

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

  const toggleCodeCompletionWrapper = () => {
    CodeCompletionContextstore.toggleCodeCompletion();
  };

  useEffect(() => {
    CodeCompletionContextstore.setBigcodeUrl(
      'https://api-inference.huggingface.co/models/bigcode/starcoderbase/'
    );
  }, []);

  const changeMaxPromptTokens = (
    event: Event,
    newValue: number | number[],
    activeThumb: number
  ) => {
    // For the current scene, it can only be number
    if (typeof newValue === 'number') {
      CodeCompletionContextstore.setMaxPromptTokens(newValue);
    }
  };

  const changeMaxResponseokens = (
    event: Event,
    newValue: number | number[],
    activeThumb: number
  ) => {
    // For the current scene, it can only be number
    if (typeof newValue === 'number') {
      CodeCompletionContextstore.setMaxResponseTokens(newValue);
    }
  };

  return (
    <Box
      sx={{
        padding: 4,
        boxSizing: 'border-box',
        '& > .MuiAlert-root': { marginBottom: 2 },
        overflowY: 'auto'
      }}
    >
      <h1 className="jp-ai-ChatSettings-header bigcode-setting-level-1-title">
        Enable code completion
        <Switch
          checked={CodeCompletionContextstore.enableCodeCompletion}
          onChange={toggleCodeCompletionWrapper}
        />
      </h1>
      <div
        className={
          CodeCompletionContextstore.enableCodeCompletion
            ? 'code-completion-setting-entered'
            : 'code-completion-setting-exiting'
        }
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
        <h2 className="jp-ai-ChatSettings-header">Short cut for completion</h2>
        <TextField
          label="Please press the short cut you need"
          value={CodeCompletionContextstore.shortcutStr}
          fullWidth
          type="text"
          onKeyDown={setHotKeyWrapper}
        />
        <h1 className="jp-ai-ChatSettings-header bigcode-setting-level-1-title">
          Advanced Settings
        </h1>
        <div className="bigcode-setting-configuration">
          <h2 className="jp-ai-ChatSettings-header">Max prompt tokens</h2>
          <div className="bigcode-settings-token">
            <Slider
              className="token-slider"
              value={CodeCompletionContextstore.maxPromptToken}
              onChange={changeMaxPromptTokens}
              aria-label="Default"
              valueLabelDisplay="auto"
              min={100}
              max={1000}
            />
          </div>
          <h2 className="jp-ai-ChatSettings-header">Max response tokens</h2>
          <div className="bigcode-settings-token">
            <Slider
              className="token-slider"
              value={CodeCompletionContextstore.maxResponseToken}
              onChange={changeMaxResponseokens}
              aria-label="Default"
              valueLabelDisplay="auto"
              min={10}
              max={200}
            />
          </div>
        </div>
      </div>
    </Box>
  );
});
