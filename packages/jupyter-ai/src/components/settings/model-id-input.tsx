import React, { useState, useEffect, useMemo } from 'react';
import { Button, Box } from '@mui/material';
import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';
import Save from '@mui/icons-material/Save';
import { SimpleAutocomplete } from '../mui-extras/simple-autocomplete';

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

  const fetchModelParameters = async (modelId: string) => {
    try {
      await AiService.getModelParameters(modelId);
      // Just validate model has parameters, don't store them
    } catch (error) {
      console.error('Failed to fetch model parameters:', error);
    }
  };

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

  const modelsAsOptions = useMemo(() => {
    return models.map(m => ({ label: m, value: m }));
  }, [models]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <SimpleAutocomplete
        options={modelsAsOptions}
        value={input}
        onChange={v => setInput(v)}
        placeholder={props.placeholder}
        boldMatches
        showClearButton
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
