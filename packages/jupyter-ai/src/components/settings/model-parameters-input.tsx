import React, { useState } from 'react';
import { Button, TextField, Box, Alert, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

interface ModelParameter {
  id: string;
  name: string;
  type: string;
  value: string;
  isStatic?: boolean;
}

interface StaticParameterDef {
  name: string;
  type: string;
  label: string;
}

// Add some common fields as static parameters here
const STATIC_PARAMETERS: StaticParameterDef[] = [
  { name: 'temperature', type: 'float', label: 'Temperature' },
  { name: 'api_url', type: 'string', label: 'API URL' },
  { name: 'max_tokens', type: 'integer', label: 'Max Tokens' },
];

export function ModelParametersInput(): JSX.Element {
  const [parameters, setParameters] = useState<ModelParameter[]>([]);
  const [validationError, setValidationError] = useState<string>('');

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

  const handleAddStaticParameter = (staticParam: StaticParameterDef) => {
    // Check if static parameter already exists
    const exists = parameters.some(param => param.name === staticParam.name && param.isStatic);
    if (exists) {
      setValidationError(`Parameter "${staticParam.label}" is already added`);
      return;
    }
    const newParameter: ModelParameter = {
      id: Date.now().toString(),
      name: staticParam.name,
      type: staticParam.type,
      value: '',
      isStatic: true
    };
    setParameters([...parameters, newParameter]);
    setValidationError('');
  };
  // For when user changes their parameter
  const handleParameterChange = (id: string, field: keyof ModelParameter, value: string) => {
    setParameters(prev => 
      prev.map(param => 
        param.id === id ? { ...param, [field]: value } : param
      )
    );
    setValidationError('');
  };

  // For when user deletes parameter
  const handleDeleteParameter = (id: string) => {
    setParameters(prev => prev.filter(param => param.id !== id));
    setValidationError('');
  };

  const handleSaveParameters = () => {
    
    // Validation: Check if any parameter has a value but missing name or type (only for custom parameters)
    const invalidParams = parameters.filter(param => 
      param.value.trim() !== '' && 
      !param.isStatic && 
      (param.name.trim() === '' || param.type.trim() === '')
    );

    if (invalidParams.length > 0) {
      setValidationError('Parameter value specified but name or type is missing');
      return;
    }

    // Filter out parameters with empty values
    const validParams = parameters.filter(param => param.value.trim() !== '');

    // Creates JSON object of valid parameters ONLY if all 3 fields are given valid inputs
    const paramsObject = validParams.reduce((acc, param) => {
      acc[param.name] = param.value;
      return acc;
    }, {} as Record<string, string>);

    // Logs the JSON object of its input state to the browser console
    console.log('Model Parameters:', paramsObject);
  };

  const showSaveButton = parameters.length > 0;
  const availableStaticParams = STATIC_PARAMETERS.filter(staticParam => 
    !parameters.some(param => param.name === staticParam.name && param.isStatic)
  );

  return (
    <Box>
      <Button 
        variant="outlined" 
        onClick={handleAddParameter}
        sx={{ mb: 2 }}
      >
        Add a custom model parameter
      </Button>
      {/* Static parameter buttons */}
      {availableStaticParams.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Box sx={{ mb: 1, fontWeight: 'medium', fontSize: '0.875rem' }}>
            Common parameters:
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {availableStaticParams.map(staticParam => (
              <Button
                key={staticParam.name}
                variant="outlined"
                size="small"
                onClick={() => handleAddStaticParameter(staticParam)}
              >
                {staticParam.label}
              </Button>
            ))}
          </Box>
        </Box>
      )}

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
          <TextField
            label="Parameter name"
            placeholder="e.g. temperature, api_url"
            value={param.name}
            onChange={(e) => handleParameterChange(param.id, 'name', e.target.value)}
            size="small"
            sx={{ flex: 1 }}
            disabled={param.isStatic}
            InputProps={{
              readOnly: param.isStatic
            }}
          />
          <TextField
            label="Parameter type"
            placeholder="e.g. float, string"
            value={param.type}
            onChange={(e) => handleParameterChange(param.id, 'type', e.target.value)}
            size="small"
            sx={{ flex: 1 }}
            disabled={param.isStatic}
            InputProps={{
              readOnly: param.isStatic
            }}
          />
          <TextField
            label="Parameter value"
            placeholder="e.g. 0.7, https://localhost:8989"
            value={param.value}
            onChange={(e) => handleParameterChange(param.id, 'value', e.target.value)}
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

      {showSaveButton && (
        <Button 
          variant="contained" 
          onClick={handleSaveParameters}
          sx={{ mt: 1 }}
        >
          Save Model Parameters
        </Button>
      )}
    </Box>
  );
}