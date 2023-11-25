import React, { useEffect, useCallback, useRef, useState } from 'react';
import {
  Box,
  IconButton,
  Typography,
  TextField,
  InputAdornment
} from '@mui/material';
import {
  Edit,
  DeleteOutline,
  Cancel,
  Check,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import { AsyncIconButton } from '../mui-extras/async-icon-button';

import { AiService } from '../../handler';
import { StackingAlert } from '../mui-extras/stacking-alert';

export type ExistingApiKeysProps = {
  alert: StackingAlert;
  apiKeys: string[];
  onSuccess: () => unknown;
};

/**
 * Component that renders a list of existing API keys. Each API key is rendered
 * by a unique `ExistingApiKey` component.
 */
export function ExistingApiKeys(props: ExistingApiKeysProps): JSX.Element {
  // current editable API key name, if any.
  const [editableApiKey, setEditableApiKey] = useState<string | null>(null);

  return (
    <Box
      sx={{
        '& > .MuiBox-root:not(:first-child)': {
          marginTop: -2
        }
      }}
    >
      {props.apiKeys.map(apiKey => (
        <ExistingApiKey
          key={apiKey}
          alert={props.alert}
          apiKey={apiKey}
          editable={editableApiKey === apiKey}
          setEditable={setEditableApiKey}
          onSuccess={props.onSuccess}
        />
      ))}
      {props.alert.jsx}
    </Box>
  );
}

type ExistingApiKeyProps = {
  alert: StackingAlert;
  apiKey: string;
  editable: boolean;
  setEditable: React.Dispatch<React.SetStateAction<string | null>>;
  onSuccess: () => unknown;
};

/**
 * Component that renders a single existing API key specified by `props.apiKey`.
 * Includes actions for editing and deleting the API key.
 */
function ExistingApiKey(props: ExistingApiKeyProps) {
  const [input, setInput] = useState('');
  const [inputVisible, setInputVisible] = useState(false);
  const [error, setError] = useState(false);
  const inputRef = useRef<HTMLInputElement>();

  /**
   * Effect: Select the input after `editable` is set to `true`. This needs to
   * be done in an effect because the TextField needs to be rendered with
   * `disabled=false` first. When `editable` is set to `false`, reset any
   * input-related state.
   */
  useEffect(() => {
    if (props.editable) {
      inputRef.current?.focus();
    } else {
      setInput('');
      setInputVisible(false);
      setError(false);
    }
  }, [props.editable]);

  const onEditIntent = useCallback(() => {
    props.setEditable(props.apiKey);
  }, []);

  const onDelete = useCallback(() => {
    return AiService.deleteApiKey(props.apiKey);
  }, []);

  const toggleInputVisibility = useCallback(() => {
    setInputVisible(visible => !visible);
  }, []);

  const onEditCancel = useCallback(() => {
    props.setEditable(null);
  }, []);

  const onEditSubmit = useCallback(() => {
    return AiService.updateConfig({
      api_keys: { [props.apiKey]: input }
    });
  }, [input]);

  const onError = useCallback(
    (emsg: string) => {
      props.alert.show('error', emsg);
    },
    [props.alert]
  );

  const validateInput = useCallback(() => {
    if (!props.editable) {
      return;
    }

    setError(!input);
  }, [props.editable, input]);

  const onEditSuccess = useCallback(() => {
    props.setEditable(null);
    props.alert.show('success', 'API key updated successfully.');
    props.onSuccess();
  }, [props.alert, props.onSuccess]);

  const onDeleteSuccess = useCallback(() => {
    props.alert.show('success', 'API key deleted successfully.');
    props.onSuccess();
  }, [props.alert, props.onSuccess]);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-start'
      }}
    >
      <TextField
        // core props
        value={input}
        onChange={e => setInput(e.target.value)}
        disabled={!props.editable}
        inputRef={inputRef}
        // validation props
        onBlur={validateInput}
        error={error}
        helperText={'API key value must not be empty'}
        FormHelperTextProps={{
          sx: {
            visibility: error ? 'unset' : 'hidden',
            margin: 0,
            whiteSpace: 'nowrap'
          }
        }}
        // style props
        size="small"
        variant="standard"
        type={inputVisible ? 'text' : 'password'}
        label={
          <Typography>
            <pre style={{ margin: 0 }}>{props.apiKey}</pre>
          </Typography>
        }
        InputProps={{
          endAdornment: props.editable && (
            <InputAdornment position="end">
              <IconButton
                onClick={toggleInputVisibility}
                edge="end"
                onMouseDown={e => e.preventDefault()}
              >
                {inputVisible ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          )
        }}
        sx={{
          flexGrow: 1,
          margin: 0,
          '& .MuiInputBase-input': {
            padding: 0,
            paddingBottom: 1
          }
        }}
      />
      <Box sx={{ marginTop: '11px', marginLeft: 2, whiteSpace: 'nowrap' }}>
        {props.editable ? (
          // 16px margin top - 5px padding
          <>
            <IconButton
              onClick={onEditCancel}
              onMouseDown={e => e.preventDefault()}
            >
              <Cancel />
            </IconButton>
            <AsyncIconButton
              onClick={onEditSubmit}
              onError={onError}
              onSuccess={onEditSuccess}
              onMouseDown={e => e.preventDefault()}
              confirm={true}
            >
              <Check color="success" />
            </AsyncIconButton>
          </>
        ) : (
          <>
            <IconButton onClick={onEditIntent}>
              <Edit />
            </IconButton>
            <AsyncIconButton
              onClick={onDelete}
              onError={onError}
              onSuccess={onDeleteSuccess}
              confirm={true}
            >
              <DeleteOutline color="error" />
            </AsyncIconButton>
          </>
        )}
      </Box>
    </Box>
  );
}
