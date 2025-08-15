import React, { useState, useEffect } from 'react';
import {
  TextField,
  Button,
  Box,
  Typography,
  Autocomplete
} from '@mui/material';
import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';
import Save from '@mui/icons-material/Save';

/**
 * Highlights matched substrings in a given text by wrapping them in bold tags.
 */
const highlightMatches = (text: string, inputValue: string) => {
  const trimmedInput = inputValue.trim();
  if (!trimmedInput) {
    return text;
  } // If input is empty, return original text

  const parts = text.split(new RegExp(`(${trimmedInput})`, 'gi'));
  return (
    <Typography component="span">
      {parts.map((part, index) =>
        part.toLowerCase() === trimmedInput.toLowerCase() ? (
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
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const alert = useStackingAlert();

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

      // run parent callback
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
      <Autocomplete
        freeSolo
        autoComplete
        options={models}
        value={input}
        onChange={(_, newValue) => {
          setInput(newValue || '');
          // Close dropdown after selection
          if (newValue && models.includes(newValue)) {
            setIsOpen(false);
          }
        }}
        onInputChange={(_, newValue, reason) => {
          setInput(newValue);
          // Show dropdown when typing, hide on selection
          setIsOpen(reason === 'input' && Boolean(newValue?.trim()));
        }}
        filterOptions={(options, { inputValue }) => {
          const searchTerm = inputValue.trim().toLowerCase();
          if (!searchTerm || searchTerm.length < 2) return []; // Don't filter if input is empty or too short
          return options.filter(option =>
            option.toLowerCase().includes(searchTerm)
          );
        }}
        open={
          isOpen &&
          input.trim().length >= 2 && // Only show dropdown if input is at least 2 characters, reduces fuzziness of search
          Boolean(
            models.filter(model =>
              model.toLowerCase().includes(input.trim().toLowerCase())
            ).length > 0
          )
        }
        renderInput={params => (
          <TextField
            {...params}
            label={props.label || 'Model ID'}
            placeholder={props.placeholder}
            fullWidth={props.fullWidth ?? true}
          />
        )}
        renderOption={(props, option) => (
          <li {...props}>{highlightMatches(option, input)}</li>
        )}
      />
      <Button
        variant="contained"
        onClick={handleUpdateChatModel}
        disabled={loading || updating}
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
