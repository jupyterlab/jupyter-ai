import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  TextField,
  Alert,
  IconButton,
  Autocomplete,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import Save from '@mui/icons-material/Save';
import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';

type ModelParameter = {
  name: string;
  type: string;
  value: string;
  isStatic?: boolean;
};

const PARAMETER_TYPES = [
  'string',
  'integer',
  'number',
  'boolean',
  'array',
  'object'
] as const;

export type ModelParametersInputProps = {
  modelId?: string | null;
};

export function ModelParametersInput(
  props: ModelParametersInputProps
): JSX.Element {
  const [availableParameters, setAvailableParameters] =
    useState<AiService.GetModelParametersResponse | null>(null);
  const [parameters, setParameters] = useState<ModelParameter[]>([]);
  const [validationError, setValidationError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const alert = useStackingAlert();
  const argumentValueRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const inferParameterType = (value: any): string => {
    if (typeof value === 'boolean') {
      return 'boolean';
    }
    if (typeof value === 'number') {
      return Number.isInteger(value) ? 'integer' : 'number';
    }
    if (Array.isArray(value)) {
      return 'array';
    }
    if (typeof value === 'object' && value !== null) {
      return 'object';
    }
    return 'string';
  };

  const convertConfigToParameters = (
    savedParams: Record<string, any>,
    parameterSchemas?: Record<string, AiService.ParameterSchema>
  ): ModelParameter[] => {
    return Object.entries(savedParams).map(([name, value]) => {
      const schema = parameterSchemas?.[name];
      const inferredType = schema?.type || inferParameterType(value);

      return {
        name,
        type: inferredType,
        value: String(value),
        isStatic: true
      };
    });
  };

  useEffect(() => {
    async function fetchParametersAndConfig() {
      if (!props.modelId) {
        setAvailableParameters(null);
        setParameters([]);
        return;
      }

      setIsLoading(true);
      try {
        // Fetch both parameter schemas and existing config in parallel
        const [paramResponse, configResponse] = await Promise.all([
          AiService.getModelParameters(props.modelId),
          AiService.getConfig()
        ]);

        setAvailableParameters(paramResponse);
        const savedParams = configResponse.fields[props.modelId] || {};
        const existingParams = convertConfigToParameters(
          savedParams,
          paramResponse.parameters
        );

        setParameters(existingParams);
      } catch (error) {
        console.error('Failed to fetch parameters:', error);
        setAvailableParameters(null);
        alert.show(
          'error',
          `Failed to fetch parameters for model '${props.modelId}'. You can still add custom parameters manually.`
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchParametersAndConfig();
  }, [props.modelId]);

  const handleAddParameter = () => {
    const newParameter: ModelParameter = {
      name: '',
      type: '',
      value: '',
      isStatic: false
    };
    setParameters([...parameters, newParameter]);
    setValidationError('');
  };

  const handleParameterChange = (
    name: string,
    field: keyof ModelParameter,
    value: string
  ) => {
    setParameters(prev =>
      prev.map(param =>
        param.name === name
          ? { ...param, [field]: value, isStatic: false }
          : param
      )
    );
    setValidationError('');

    // Auto-focus on the argument value input when type is selected
    if (field === 'type' && value) {
      setTimeout(() => {
        argumentValueRefs.current[name]?.focus();
      }, 0);
    }
  };

  // Handle parameter name selection from dropdown
  const handleParameterNameSelect = (
    currentName: string,
    paramName: string | null
  ) => {
    if (!paramName) {
      return;
    }
    const paramSchema = availableParameters?.parameters?.[paramName];

    setParameters(prev =>
      prev.map(param =>
        param.name === currentName
          ? {
              ...param,
              name: paramName,
              type: paramSchema?.type || param.type,
              isStatic: false
            }
          : param
      )
    );
    setValidationError('');
  };

  const handleDeleteParameter = (name: string) => {
    setParameters(prev => prev.filter(param => param.name !== name));
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
      alert.show(
        'error',

        'All parameters must have argument values. Use the delete button to remove unwanted parameters.'
      );
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

    // Creates JSON object of parameters with type and value structure
    const paramsObject = parameters.reduce((acc, param) => {
      acc[param.name] = {
        value: param.value,
        type: param.type
      };
      return acc;
    }, {} as Record<string, { value: string; type: string }>);

    try {
      await AiService.saveModelParameters(props.modelId, paramsObject);
      setValidationError('');

      // Show success alert
      alert.show(
        'success',
        `Successfully saved parameters for model '${props.modelId}'.`
      );
    } catch (error) {
      const msg =
        error instanceof Error ? error.message : 'An unknown error occurred';

      // Show error alert
      alert.show('error', `Failed to save model parameters: ${msg}`);
      setValidationError('Failed to save parameters. Please try again.');
    }
  };

  const showSaveButton = parameters.length > 0;

  const getParameterOptions = (excludeParamName?: string) => {
    const apiParamNames = availableParameters?.parameters
      ? Object.keys(availableParameters.parameters)
      : [];

    // Filters out parameters that are already selected by other rows
    const usedParamNames = parameters
      .filter(
        param => param.name !== excludeParamName && param.name.trim() !== ''
      )
      .map(param => param.name);

    return apiParamNames.filter(name => !usedParamNames.includes(name));
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        Loading parameters...
      </Box>
    );
  }

  return (
    <Box>
      {parameters.map((param, index) => (
        <Box
          key={index}
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
              options={getParameterOptions(param.name)}
              value={param.name || null}
              onChange={(_, newValue) => {
                handleParameterNameSelect(param.name, newValue);
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
          <FormControl size="small" sx={{ flex: 1 }} disabled={param.isStatic}>
            <InputLabel>Parameter type</InputLabel>
            <Select
              value={param.type}
              label="Parameter type"
              onChange={e =>
                handleParameterChange(param.name, 'type', e.target.value)
              }
              disabled={param.isStatic}
            >
              {PARAMETER_TYPES.map(type => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Argument value"
            placeholder="e.g. 0.7, https://localhost:8989"
            value={param.value}
            onChange={e =>
              handleParameterChange(param.name, 'value', e.target.value)
            }
            size="small"
            sx={{ flex: 1 }}
            inputRef={el => {
              argumentValueRefs.current[param.name] = el;
            }}
          />
          <IconButton
            onClick={() => handleDeleteParameter(param.name)}
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
          Save Model Parameters
        </Button>
      )}
      {alert.jsx}
    </Box>
  );
}
