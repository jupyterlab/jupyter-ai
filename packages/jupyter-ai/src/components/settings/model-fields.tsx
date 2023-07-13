import React, { useState } from 'react';
import { AiService } from '../../handler';
import { TextField } from '@mui/material';

export type ModelFieldProps = {
  /**
   * The global model ID to which these fields belong.
   */
  gmid: string;
  field: AiService.Field;
  config: AiService.Config;
  setConfig: (newConfig: AiService.Config) => unknown;
};

export function ModelField(props: ModelFieldProps): JSX.Element {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
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

    props.setConfig({
      ...props.config,
      fields: {
        ...props.config.fields,
        [props.gmid]: {
          ...props.config.fields[props.gmid],
          [props.field.key]: e.target.value
        }
      }
    });
  }

  if (props.field.type === 'text') {
    return (
      <TextField
        label={props.field.label}
        value={props.config.fields[props.gmid]?.[props.field.key]}
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
        value={props.config.fields[props.gmid]?.[props.field.key]}
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
};

export function ModelFields(props: ModelFieldsProps): JSX.Element | null {
  if (!props.fields?.length) {
    return null;
  }

  return (
    <>
      {props.fields.map((field, idx) => (
        <ModelField {...props} field={field} key={idx} />
      ))}
    </>
  );
}
