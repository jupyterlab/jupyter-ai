import React, { useState, useEffect } from 'react';
import {
  TextField,
  Button,
  Box,
  Typography,
  Menu,
  MenuItem
} from '@mui/material';
import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';
import Save from '@mui/icons-material/Save';

/**
 * Highlights matched substrings in a given text by wrapping them in bold tags.
 */
const highlightMatches = (text: string, inputValue: string) => {
  if (!inputValue) return text;

  const parts = text.split(new RegExp(`(${inputValue})`, 'gi'));
  return (
    <Typography component="span">
      {parts.map((part, index) =>
        part.toLowerCase() === inputValue.toLowerCase() ? (
          <Typography component="span" key={index} sx={{ fontWeight: 'bold' }}>
            {part}
          </Typography>
        ) : (
          part
        )
      )}
    </Typography>
  );
};

export type ModelIdInputProps = {
  /**
   * The label of the model ID input field.
   */
  label: string;

  /**
   * The "type" of the model being configured. This prop should control the API
   * endpoints used to get the current model, set the current model, and
   * retrieve model ID suggestions.
   */
  modality: 'chat' | 'completion';

  /**
   * (optional) The placeholder text shown within the model ID input field.
   */
  placeholder?: string;

  /**
   * (optional) Whether to render in full width. Defaults to `true`.
   */
  fullWidth?: boolean;

  /**
   * (optional) Callback that is run when the component retrieves the current
   * model ID _or_ successfully updates the model ID. Details:
   *
   * - This callback is run once when the current model ID is retrieved from the
   * backend, with `initial=true`. Any model ID updates made through this
   * component run this callback with `initial=false`.
   *
   * - This callback will not run if an exception was raised while updating the
   * model ID.
   */
  onModelIdFetch?: (modelId: string | null, initial: boolean) => unknown;
};

/**
 * A model ID input.
 */
export function ModelIdInput(props: ModelIdInputProps): JSX.Element {
  const [models, setModels] = useState<string[]>([]);
  const [prevModel, setPrevModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const [input, setInput] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const alert = useStackingAlert();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleMenuItemClick = (value: string) => {
    setInput(value);
    handleMenuClose();
  };

  const filteredModels = models.filter(model =>
    model.toLowerCase().includes(input.toLowerCase())
  );

  /**
   * Effect: Fetch list of models and current model on initial render, based on
   * the modality.
   */
  useEffect(() => {
    async function loadData() {
      try {
        let modelsResponse: string[];
        let currModelResponse: string | null;

        if (props.modality === 'chat') {
          [modelsResponse, currModelResponse] = await Promise.all([
            AiService.listChatModels(),
            AiService.getChatModel()
          ]);
        } else if (props.modality === 'completion') {
          [modelsResponse, currModelResponse] = await Promise.all([
            AiService.listChatModels(),
            AiService.getCompletionModel()
          ]);
        } else {
          throw new Error(`Unrecognized model modality '${props.modality}'.`);
        }

        setModels(modelsResponse);
        setPrevModel(currModelResponse);
        setInput(currModelResponse ?? '');
      } catch (error) {
        console.error('Failed to load chat models:', error);
        setModels([]);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleUpdateChatModel = async () => {
    setUpdating(true);
    try {
      // perform correct REST API call based on model modality
      const newModelId = input.trim() || null;
      if (props.modality === 'chat') {
        await AiService.updateChatModel(newModelId);
      } else if (props.modality === 'completion') {
        await AiService.updateCompletionModel(newModelId);
      } else {
        throw new Error(`Unrecognized model modality '${props.modality}'.`);
      }

      // update local state and run parent callback
      setPrevModel(newModelId);
      props.onModelIdFetch?.(newModelId, true);

      // show success alert
      // TODO: maybe just use the JL Notifications API
      alert.show(
        'success',
        newModelId
          ? `Successfully updated ${props.modality} model to '${input.trim()}'.`
          : `Successfully cleared ${props.modality} model.`
      );
    } catch (error) {
      console.error(`Failed to update ${props.modality} model:`, error);
      const msg =
        error instanceof Error ? error.message : 'An unknown error occurred';
      alert.show('error', `Failed to update ${props.modality} model: ${msg}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        label={props.label || 'Model ID'}
        placeholder={props.placeholder}
        fullWidth={props.fullWidth ?? true}
        value={input}
        onChange={e => {
          const newValue = e.target.value;
          if (!newValue.includes(' ')) {
            setInput(newValue);
          }
        }}
        InputProps={{
          endAdornment:
            // input && filteredModels.length > 0 ? (
            input ? (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  height: '100%',
                  justifyContent: 'left',
                  width: '100%'
                }}
              >
                <Box
                  sx={{
                    cursor: 'pointer',
                    ml: 1,
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  onClick={handleMenuOpen}
                  tabIndex={0}
                  role="button"
                >
                  <svg width="20" height="20" fill="none" viewBox="0 0 24 24">
                    <path
                      d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99a1 1 0 0 0 1.41-1.41l-4.99-5zm-6 0C8.01 14 6 11.99 6 9.5S8.01 5 10.5 5 15 7.01 15 9.5 12.99 14 10.5 14z"
                      fill="currentColor"
                    />
                  </svg>
                  {filteredModels.length > 0 ? (
                    <Typography
                      variant="body2"
                      sx={{
                        ml: 1,
                        userSelect: 'none',
                        color: 'text.secondary'
                      }}
                    >
                      Click to see {filteredModels.length} match
                      {filteredModels.length !== 1 ? 'es' : ''}
                    </Typography>
                  ) : (
                    <Typography
                      variant="body2"
                      sx={{
                        ml: 1,
                        userSelect: 'none',
                        color: 'text.secondary'
                      }}
                    >
                      No matches
                    </Typography>
                  )}
                </Box>
              </Box>
            ) : null
        }}
      />
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left'
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left'
        }}
      >
        {filteredModels.map((model, index) => (
          <MenuItem key={index} onClick={() => handleMenuItemClick(model)}>
            {highlightMatches(model, input)}
          </MenuItem>
        ))}
      </Menu>
      <Button
        variant="contained"
        onClick={handleUpdateChatModel}
        disabled={loading || prevModel === (input || null) || updating}
        sx={{ alignSelf: 'center' }}
        startIcon={<Save />}
      >
        {updating
          ? `Updating ${props.modality} model...`
          : `Update ${props.modality} model`}
      </Button>
      {alert.jsx}
    </Box>
  );
}
