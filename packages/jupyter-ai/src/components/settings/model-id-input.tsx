import React, { useState, useEffect } from 'react';
import { Autocomplete, TextField, Button, Box } from '@mui/material';
import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';

export type ModelIdInputProps = {
  /**
   * The label of the model ID input field.
   */
  label?: string;

  /**
   * The placeholder text shown within the model ID input field.
   */
  placeholder?: string;

  /**
   * Whether to render in full width. Defaults to `true`.
   */
  fullWidth?: boolean;
};

/**
 * A model ID input.
 */
export function ModelIdInput(props: ModelIdInputProps): JSX.Element {
  const [chatModels, setChatModels] = useState<string[]>([]);
  const [prevModel, setPrevModel] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const [input, setInput] = useState('');
  const alert = useStackingAlert();

  /**
   * Effect: Fetch list of chat models and current chat model on initial render.
   */
  useEffect(() => {
    async function loadData() {
      try {
        const [models, currentModel] = await Promise.all([
          AiService.listChatModels(),
          AiService.getChatModel()
        ]);
        setChatModels(models);
        setPrevModel(currentModel ?? '');
        setInput(currentModel ?? '');
      } catch (error) {
        console.error('Failed to load chat models:', error);
        setChatModels([]);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleUpdateChatModel = async () => {
    if (!input.trim()) {
      return;
    }

    setUpdating(true);
    try {
      await AiService.setChatModel(input.trim());
      setPrevModel(input.trim());
      alert.show(
        'success',
        `Successfully updated chat model to: ${input.trim()}`
      );
    } catch (error) {
      console.error('Failed to update chat model:', error);
      const msg =
        error instanceof Error ? error.message : 'An unknown error occurred';
      alert.show('error', `Failed to update chat model: ${msg}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Autocomplete
        options={chatModels}
        value={input}
        onChange={(_, newValue) => {
          // This condition prevents whitespace from being inserted in the model
          // ID by accident.
          if (newValue !== null && !newValue.includes(' ')) {
            setInput(newValue);
          }
        }}
        freeSolo
        autoSelect
        loading={loading}
        fullWidth={props.fullWidth}
        renderInput={params => (
          <TextField
            {...params}
            label={props.label || 'Model ID'}
            placeholder={props.placeholder}
            fullWidth={props.fullWidth ?? true}
          />
        )}
      />
      <Button
        variant="contained"
        onClick={handleUpdateChatModel}
        disabled={prevModel === input || updating}
        sx={{ alignSelf: 'center' }}
      >
        {updating ? 'Updating...' : 'Update chat model'}
      </Button>
      {alert.jsx}
    </Box>
  );
}
