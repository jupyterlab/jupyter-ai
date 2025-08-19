import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Alert,
  IconButton,
  Autocomplete
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import Save from '@mui/icons-material/Save';
import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';

type ModelParameter = {
  id: string;
  name: string;
  type: string;
  value: string;
  isStatic?: boolean;
};

export type ModelParametersInputProps = {
  modelId?: string | null;
};

export function ModelParametersInput(
  props: ModelParametersInputProps
): JSX.Element {
  const [availableParameters, setAvailableParameters] = useState<any>(null);
  const [parameters, setParameters] = useState<ModelParameter[]>([]);
  const [validationError, setValidationError] = useState<string>('');
  const alert = useStackingAlert();

  useEffect(() => {
    async function fetchAvailableParameters() {
      if (!props.modelId) {
        setAvailableParameters(null);
        return;
      }

      try {
        const response = await AiService.getModelParameters(props.modelId);
        setAvailableParameters(response);
      } catch (error) {
        console.error('Failed to fetch available parameters:', error);
        setAvailableParameters(null);
      }
    }

    fetchAvailableParameters();
  }, [props.modelId]);

  const handleAddParameter = () => {
    const newParameter: ModelParameter = {
      id: Date.now().toString(),
      name: '',
      type: '',
      value: '',
      isStatic: false
    };
    setParameters([...parameters, newParameter]);
    setValidationError('');
  };

  const handleParameterChange = (
    id: string,
    field: keyof ModelParameter,
    value: string
  ) => {
    setParameters(prev =>
      prev.map(param =>
        param.id === id ? { ...param, [field]: value } : param
      )
    );
    setValidationError('');
  };

  // Handle parameter name selection from dropdown
  const handleParameterNameSelect = (id: string, paramName: string | null) => {
    if (!paramName) {
      return;
    }
    const paramSchema = availableParameters?.parameters?.[paramName];

    setParameters(prev =>
      prev.map(param =>
        param.id === id
          ? {
              ...param,
              name: paramName,
              type: paramSchema?.type || param.type
            }
          : param
      )
    );
    setValidationError('');
  };

  const handleDeleteParameter = (id: string) => {
    setParameters(prev => prev.filter(param => param.id !== id));
    setValidationError('');
  };

  const handleSaveParameters = async () => {
    // Validation: Check if any parameter has a value but missing name or type (only for custom parameters)
    const invalidParams = parameters.filter(
      param =>
        param.value.trim() !== '' &&
        !param.isStatic &&
        (param.name.trim() === '' || param.type.trim() === '')
    );

    if (invalidParams.length > 0) {
      setValidationError(
        'Parameter value specified but name or type is missing'
      );
      return;
    }

    if (!props.modelId) {
      setValidationError('No model selected');
      return;
    }

    // Check for empty parameter values
    const emptyParams = parameters.filter(param => param.value.trim() === '');
    if (emptyParams.length > 0) {
      alert.show('error', 'All parameters must have argument values. Use the delete button to remove unwanted parameters.');
      return;
    }

    // Validation: Check boolean values
    const hasBooleanError = parameters.some(param => {
      if (param.type.toLowerCase() === 'boolean') {
        const value = param.value.toLowerCase().trim();
        return value !== 'true' && value !== 'false';
      }
      return false;
    });

    if (hasBooleanError) {
      setValidationError(
        'Boolean parameters must have value "true" or "false"'
      );
      return;
    }

    // Creates JSON object of parameters ONLY if all 3 fields are given valid inputs
    const paramsObject = parameters.reduce((acc, param) => {
      acc[param.name] = param.value;
      return acc;
    }, {} as Record<string, string>);

    try {
      await AiService.saveModelParameters(props.modelId, paramsObject);
      setValidationError('');

      // Show success alert
      console.log('About to show alert with:', alert);
      alert.show(
        'success',
        `Successfully saved parameters for model '${props.modelId}'.`
      );
      console.log('Alert.show called successfully');
    } catch (error) {
      console.error('Failed to save model parameters:', error);
      const msg =
        error instanceof Error ? error.message : 'An unknown error occurred';

      // Show error alert
      alert.show('error', `Failed to save model parameters: ${msg}`);
      setValidationError('Failed to save parameters. Please try again.');
    }
  };

  const showSaveButton = parameters.length > 0;

  const getParameterOptions = (excludeParamId?: string) => {
    const apiParamNames = availableParameters?.parameters
      ? Object.keys(availableParameters.parameters)
      : [];

    // Filters out parameters that are already selected by other rows
    const usedParamNames = parameters
      .filter(param => param.id !== excludeParamId && param.name.trim() !== '')
      .map(param => param.name);

    return apiParamNames.filter(name => !usedParamNames.includes(name));
  };

  return (
    <Box>
      {parameters.map(param => (
        <Box
          key={param.id}
          sx={{
            display: 'flex',
            gap: 2,
            mb: 2,
            alignItems: 'center'
          }}
        >
          {param.isStatic ? (
            <TextField
              label="Parameter name"
              value={param.name}
              size="small"
              sx={{ flex: 1 }}
              disabled={true}
              InputProps={{
                readOnly: true
              }}
            />
          ) : (
            <Autocomplete
              options={getParameterOptions(param.id)}
              value={param.name || null}
              onChange={(_, newValue) => {
                handleParameterNameSelect(param.id, newValue);
              }}
              freeSolo
              size="small"
              sx={{ flex: 1 }}
              renderInput={params => (
                <TextField
                  {...params}
                  label="Parameter name"
                  placeholder="Select or type parameter name"
                />
              )}
              getOptionLabel={option => {
                if (typeof option === 'string') {
                  return option;
                }
                return '';
              }}
              renderOption={(props, option) => {
                const schema = availableParameters?.parameters?.[option];
                return (
                  <Box component="li" {...props} title={schema?.description}>
                    <Box>
                      <Box sx={{ fontWeight: 'medium' }}>{option}</Box>
                      {schema && (
                        <Box
                          sx={{ fontSize: '0.75rem', color: 'text.secondary' }}
                        >
                          {schema.type}{' '}
                          {schema.description &&
                            `- ${schema.description.slice(0, 50)}${
                              schema.description.length > 50 ? '...' : ''
                            }`}
                        </Box>
                      )}
                    </Box>
                  </Box>
                );
              }}
            />
          )}
          <TextField
            label="Parameter type"
            placeholder="e.g. float, string"
            value={param.type}
            onChange={e =>
              handleParameterChange(param.id, 'type', e.target.value)
            }
            size="small"
            sx={{ flex: 1 }}
            disabled={param.isStatic}
            InputProps={{
              readOnly: param.isStatic
            }}
          />
          <TextField
            label="Argument value"
            placeholder="e.g. 0.7, https://localhost:8989"
            value={param.value}
            onChange={e =>
              handleParameterChange(param.id, 'value', e.target.value)
            }
            size="small"
            sx={{ flex: 1 }}
          />
          <IconButton
            onClick={() => handleDeleteParameter(param.id)}
            color="error"
            size="small"
            sx={{ ml: 1 }}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ))}

      {validationError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {validationError}
        </Alert>
      )}

      <Button variant="outlined" onClick={handleAddParameter} sx={{ m: 3 }}>
        Add a custom model parameter
      </Button>

      {showSaveButton && (
        <Button
          variant="contained"
          onClick={handleSaveParameters}
          sx={{ alignSelf: 'center' }}
          startIcon={<Save />}
        >
          Update Model Parameters
        </Button>
      )}
      {alert.jsx}
    </Box>
  );
}
