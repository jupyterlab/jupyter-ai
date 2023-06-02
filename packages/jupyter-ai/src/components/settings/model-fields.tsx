import React from 'react';
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
  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
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
        minRows={2}
      />
    );
  }

  return <></>;
}

export type ModelFieldsProps = Omit<ModelFieldProps, 'field'> & {
  fields?: AiService.Field[];
};

export function ModelFields(props: ModelFieldsProps) {
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
