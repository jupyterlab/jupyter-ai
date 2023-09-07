import React, { useState } from 'react';
import { AiService } from '../../handler';
import { TextField } from '@mui/material';

export type ModelFieldProps = {
  field: AiService.Field;
  values: Record<string, any>;
  onChange: (newValues: Record<string, any>) => unknown;
};

export function ModelField(props: ModelFieldProps): JSX.Element {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const value = props.values?.[props.field.key];

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    if (!('format' in props.field)) {
      return;
    }

    // Perform validation based on the field format
    switch (props.field.format) {
      case 'json':
        try {
          // JSON.parse does not allow single quotes or trailing commas
          JSON.parse(e.target.value);
          setErrorMessage(null);
        } catch (exc) {
          setErrorMessage('You must specify a value in JSON format.');
        }
        break;
      case 'jsonpath':
        // TODO: Do JSONPath validation
        break;
      default:
        // No validation performed
        break;
    }

    props.onChange({
      ...props.values,
      [props.field.key]: e.target.value
    });
  }

  if (props.field.type === 'integer') {
    return (
      <TextField
        label={props.field.label}
        value={value}
        onChange={handleChange}
        inputProps={{ inputMode: 'numeric', pattern: '[0-9]*' }}
        fullWidth
      />
    );
  }

  if (props.field.type === 'text') {
    return (
      <TextField
        label={props.field.label}
        value={value ?? ''}
        onChange={handleChange}
        error={!!errorMessage}
        helperText={errorMessage ?? undefined}
        fullWidth
      />
    );
  }

  if (props.field.type === 'text-multiline') {
    return (
      <TextField
        label={props.field.label}
        value={value ?? ''}
        onChange={handleChange}
        fullWidth
        multiline
        error={!!errorMessage}
        helperText={errorMessage ?? undefined}
        minRows={2}
      />
    );
  }

  return <></>;
}

export type ModelFieldsProps = Omit<ModelFieldProps, 'field'> & {
  fields?: AiService.Field[];
  values: Record<string, any>;
  onChange: (newValues: Record<string, any>) => unknown;
};

export function ModelFields(props: ModelFieldsProps): JSX.Element | null {
  if (!props.fields?.length) {
    return null;
  }

  return (
    <>
      {props.fields.map((field, idx) => (
        <ModelField
          {...props}
          field={field}
          key={idx}
          values={props.values}
          onChange={props.onChange}
        />
      ))}
    </>
  );
}
