// import React, { useEffect } from 'react';
import React, { useEffect } from 'react';
import { Box, TextField } from '@mui/material';
import GlobalStore from "../contexts/continue-writing-context"
import { observer } from 'mobx-react-lite';

type BigcodeSettingProps = {

};


export const BigCodeSetting = observer(({ }: BigcodeSettingProps) => {
  const { bigcodeUrl } = GlobalStore
  const { accessToken } = GlobalStore

  const setBigcodeUrlWrapper = (value: string) => {
    GlobalStore.setBigcodeUrl(value)
  }
  
  const setAccessTokenWrapper = (value: string) => {
    GlobalStore.setAccessToken(value)
  }

  useEffect(()=>{
    GlobalStore.setBigcodeUrl("https://api-inference.huggingface.co/models/bigcode/starcoderbase/")
  }, [])

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

    </Box>
  );
})