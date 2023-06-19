import React from 'react';
import { FormControl, InputLabel, Select as MuiSelect } from '@mui/material';
import type {
  SelectChangeEvent,
  SelectProps as MuiSelectProps
} from '@mui/material';

export type SelectProps = Omit<MuiSelectProps<string>, 'value' | 'onChange'> & {
  value: string | null;
  onChange: (
    event: SelectChangeEvent<string | null>,
    child: React.ReactNode
  ) => void;
};

/**
 * A helpful wrapper around MUI's native `Select` component that provides the
 * following services:
 *
 * - automatically wraps base `Select` component in `FormControl` context and
 * prepends an input label derived from `props.label`.
 *
 * - limits max height of menu
 *
 * - handles `null` values by coercing them to the string `'null'`. The
 * corresponding `MenuItem` should have the value `'null'`.
 */
export function Select(props: SelectProps): JSX.Element {
  return (
    <FormControl fullWidth>
      <InputLabel>{props.label}</InputLabel>
      <MuiSelect
        {...props}
        value={props.value === null ? 'null' : props.value}
        label={props.label}
        onChange={(e, child) => {
          if (e.target.value === 'null') {
            e.target.value = null as any;
          }
          props.onChange?.(e, child);
        }}
        MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
      >
        {props.children}
      </MuiSelect>
    </FormControl>
  );
}
