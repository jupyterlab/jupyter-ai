import React, { useEffect, useCallback, useRef, useState } from 'react';
import {
  Box,
  IconButton,
  Typography,
  TextField,
  InputAdornment,
  Button
} from '@mui/material';
import Edit from '@mui/icons-material/Edit';
import DeleteOutline from '@mui/icons-material/DeleteOutline';
import Cancel from '@mui/icons-material/Cancel';
import Check from '@mui/icons-material/Check';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import Add from '@mui/icons-material/Add';
import { AsyncIconButton } from '../mui-extras/async-icon-button';

import { AiService } from '../../handler';
import { StackingAlert, useStackingAlert } from '../mui-extras/stacking-alert';

export type SecretsInputProps = {
  editableSecrets: string[];
  reloadSecrets: () => unknown;
};

/**
 * Component that renders a list of editable secrets. Each secret is
 * rendered by a unique `EditableSecret` component.
 */
export function SecretsInput(props: SecretsInputProps): JSX.Element | null {
  const alert = useStackingAlert();
  const [isAddingSecret, setIsAddingSecret] = useState(false);

  if (!props.editableSecrets) {
    return null;
  }

  const onAddSecretClick = useCallback(() => {
    setIsAddingSecret(true);
  }, []);

  const onAddSecretCancel = useCallback(() => {
    setIsAddingSecret(false);
  }, []);

  const onAddSecretSuccess = useCallback(() => {
    setIsAddingSecret(false);
    alert.show('success', 'Secret added successfully.');
    props.reloadSecrets();
  }, [alert, props.reloadSecrets]);

  const onAddSecretError = useCallback(
    (emsg: string) => {
      alert.show('error', emsg);
    },
    [alert]
  );

  return (
    <Box>
      {/* SUBSECTION: Editable secrets */}
      {props.editableSecrets.length > 0 ? (
        <Box
          sx={{
            '& > .MuiBox-root:not(:first-child)': {
              marginTop: -2
            }
          }}
        >
          {props.editableSecrets.map(secret => (
            <EditableSecret
              key={secret}
              alert={alert}
              secret={secret}
              reloadSecrets={props.reloadSecrets}
            />
          ))}
        </Box>
      ) : (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 4,
            textAlign: 'center',
            color: 'text.secondary',
            backgroundColor: 'action.hover',
            borderRadius: 1,
            marginBottom: 2
          }}
        >
          <Typography variant="h6" sx={{ marginBottom: 1, fontWeight: 500 }}>
            No secrets configured
          </Typography>
          <Typography variant="body2" sx={{ maxWidth: 400, opacity: 0.8 }}>
            Add your first API key or secret to start using Jupyter AI with your
            preferred model provider.
          </Typography>
        </Box>
      )}

      {/* Add secret button */}
      {isAddingSecret ? (
        <NewSecretInput
          alert={alert}
          onCancel={onAddSecretCancel}
          onSuccess={onAddSecretSuccess}
          onError={onAddSecretError}
        />
      ) : (
        <Button
          startIcon={<Add />}
          onClick={onAddSecretClick}
          sx={{
            color: 'primary.main',
            backgroundColor: 'transparent',
            border: 'none',
            padding: 0,
            fontSize: 'inherit',
            textTransform: 'none',
            '&:hover': {
              backgroundColor: 'transparent',
              textDecoration: 'underline'
            }
          }}
        >
          Add secret
        </Button>
      )}

      {/* Info shown to the user after adding/updating a secret */}
      {alert.jsx}
    </Box>
  );
}

export type EditableSecretProps = {
  alert: StackingAlert;
  secret: string;
  reloadSecrets: () => unknown;
};

/**
 * Component that renders a single editable secret specified by `props.apiKey`.
 * Includes actions for editing and deleting the secret.
 */
export function EditableSecret(props: EditableSecretProps) {
  const [input, setInput] = useState('');
  const [inputVisible, setInputVisible] = useState(false);
  const [error, setError] = useState(false);
  const [editable, setEditable] = useState(false);
  const inputRef = useRef<HTMLInputElement>();

  /**
   * Effect: Select the input after `editable` is set to `true` and clear the
   * input after `editable` is set to `false`.
   */
  useEffect(() => {
    if (editable) {
      inputRef.current?.focus();
    } else {
      setInput('');
      setInputVisible(false);
      setError(false);
    }
  }, [editable]);

  const onEditIntent = useCallback(() => {
    setEditable(true);
  }, []);

  const onDelete = useCallback(() => {
    return AiService.deleteSecret(props.secret);
  }, []);

  const toggleInputVisibility = useCallback(() => {
    setInputVisible(visible => !visible);
  }, []);

  const onEditCancel = useCallback(() => {
    setEditable(false);
  }, []);

  const onEditSubmit = useCallback(() => {
    // If input is empty, defocus the input to show a validation error and
    // return early.
    if (input.length === 0) {
      inputRef.current?.blur();
      return 'canceled';
    }

    // Otherwise dispatch the request to the backend.
    return AiService.updateSecrets({
      [props.secret]: input
    });
  }, [input]);

  const onEditError = useCallback(
    (emsg: string) => {
      props.alert.show('error', emsg);
    },
    [props.alert]
  );

  const validateInput = useCallback(() => {
    if (!editable) {
      return;
    }

    setError(!input);
  }, [editable, input]);

  const onEditSuccess = useCallback(() => {
    setEditable(false);
    props.alert.show('success', 'API key updated successfully.');
    props.reloadSecrets();
  }, [props.alert, props.reloadSecrets]);

  const onDeleteSuccess = useCallback(() => {
    props.alert.show('success', 'API key deleted successfully.');
    props.reloadSecrets();
  }, [props.alert, props.reloadSecrets]);

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
        disabled={!editable}
        inputRef={inputRef}
        // validation props
        onBlur={validateInput}
        error={error}
        helperText={'Secret value must not be empty'}
        placeholder="Secret value"
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
            <pre style={{ margin: 0 }}>{props.secret}</pre>
          </Typography>
        }
        InputProps={{
          endAdornment: editable && (
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
        {editable ? (
          // If this secret is being edited, show the "cancel edit" and "apply
          // edit" buttons.
          <>
            <IconButton
              onClick={onEditCancel}
              onMouseDown={e => e.preventDefault()}
            >
              <Cancel />
            </IconButton>
            <AsyncIconButton
              onClick={onEditSubmit}
              onError={onEditError}
              onSuccess={onEditSuccess}
              onMouseDown={e => e.preventDefault()}
              confirm={false}
            >
              <Check color="success" />
            </AsyncIconButton>
          </>
        ) : (
          // Otherwise, show the "edit secret" and "delete secret" buttons.
          <>
            <IconButton onClick={onEditIntent}>
              <Edit />
            </IconButton>
            <AsyncIconButton
              onClick={onDelete}
              onError={onEditError}
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

export type NewSecretInputProps = {
  alert: StackingAlert;
  onCancel: () => void;
  onSuccess: () => void;
  onError: (emsg: string) => void;
};

export function NewSecretInput(props: NewSecretInputProps) {
  const [secretName, setSecretName] = useState('');
  const [secretValue, setSecretValue] = useState('');
  const [secretValueVisible, setSecretValueVisible] = useState(false);
  const [nameError, setNameError] = useState(false);
  const [valueError, setValueError] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>();
  const valueInputRef = useRef<HTMLInputElement>();

  useEffect(() => {
    nameInputRef.current?.focus();
  }, []);

  const toggleSecretValueVisibility = useCallback(() => {
    setSecretValueVisible(visible => !visible);
  }, []);

  const validateInputs = useCallback(() => {
    const nameEmpty = !secretName.trim();
    const valueEmpty = !secretValue.trim();
    setNameError(nameEmpty);
    setValueError(valueEmpty);
    return !nameEmpty && !valueEmpty;
  }, [secretName, secretValue]);

  const onSubmit = useCallback(() => {
    if (!validateInputs()) {
      return 'canceled';
    }

    return AiService.updateSecrets({
      [secretName.trim()]: secretValue.trim()
    });
  }, [secretName, secretValue, validateInputs]);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 2,
        marginTop: 2
      }}
    >
      <TextField
        value={secretName}
        onChange={e => setSecretName(e.target.value)}
        inputRef={nameInputRef}
        error={nameError}
        helperText={'Secret name must not be empty'}
        placeholder="Secret name"
        FormHelperTextProps={{
          sx: {
            visibility: nameError ? 'unset' : 'hidden',
            margin: 0,
            whiteSpace: 'nowrap'
          }
        }}
        size="small"
        variant="standard"
        label="Secret name"
        onBlur={() => !secretName.trim() && setNameError(true)}
        sx={{
          flexGrow: 1,
          margin: 0,
          '& .MuiInputBase-input': {
            padding: 0,
            paddingBottom: 1
          }
        }}
      />
      <TextField
        value={secretValue}
        onChange={e => setSecretValue(e.target.value)}
        inputRef={valueInputRef}
        error={valueError}
        helperText={'Secret value must not be empty'}
        placeholder="Secret value"
        FormHelperTextProps={{
          sx: {
            visibility: valueError ? 'unset' : 'hidden',
            margin: 0,
            whiteSpace: 'nowrap'
          }
        }}
        size="small"
        variant="standard"
        type={secretValueVisible ? 'text' : 'password'}
        label="Secret value"
        onBlur={() => !secretValue.trim() && setValueError(true)}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                onClick={toggleSecretValueVisibility}
                edge="end"
                onMouseDown={e => e.preventDefault()}
              >
                {secretValueVisible ? <VisibilityOff /> : <Visibility />}
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
      <Box sx={{ marginTop: '11px', whiteSpace: 'nowrap' }}>
        <IconButton
          onClick={props.onCancel}
          onMouseDown={e => e.preventDefault()}
        >
          <Cancel />
        </IconButton>
        <AsyncIconButton
          onClick={onSubmit}
          onError={props.onError}
          onSuccess={props.onSuccess}
          onMouseDown={e => e.preventDefault()}
          confirm={false}
        >
          <Check color="success" />
        </AsyncIconButton>
      </Box>
    </Box>
  );
}
