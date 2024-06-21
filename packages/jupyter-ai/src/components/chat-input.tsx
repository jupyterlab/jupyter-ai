import React, { useEffect, useState } from 'react';

import {
  Autocomplete,
  Box,
  SxProps,
  TextField,
  Theme,
  FormGroup,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  Typography
} from '@mui/material';
import {
  Download,
  FindInPage,
  Help,
  MoreHoriz,
  MenuBook,
  School,
  HideSource,
  AutoFixNormal
} from '@mui/icons-material';

import { AiService } from '../handler';
import { SendButton, SendButtonProps } from './chat-input/send-button';
import { useActiveCellContext } from '../contexts/active-cell-context';

type ChatInputProps = {
  value: string;
  onChange: (newValue: string) => unknown;
  onSend: (selection?: AiService.Selection) => unknown;
  hasSelection: boolean;
  includeSelection: boolean;
  toggleIncludeSelection: () => unknown;
  replaceSelection: boolean;
  toggleReplaceSelection: () => unknown;
  sendWithShiftEnter: boolean;
  sx?: SxProps<Theme>;
};

type SlashCommandOption = {
  id: string;
  label: string;
  description: string;
};

/**
 * List of icons per slash command, shown in the autocomplete popup.
 *
 * This list of icons should eventually be made configurable. However, it is
 * unclear whether custom icons should be defined within a Lumino plugin (in the
 * frontend) or served from a static server route (in the backend).
 */
const DEFAULT_SLASH_COMMAND_ICONS: Record<string, JSX.Element> = {
  ask: <FindInPage />,
  clear: <HideSource />,
  export: <Download />,
  fix: <AutoFixNormal />,
  generate: <MenuBook />,
  help: <Help />,
  learn: <School />,
  unknown: <MoreHoriz />
};

/**
 * Renders an option shown in the slash command autocomplete.
 */
function renderSlashCommandOption(
  optionProps: React.HTMLAttributes<HTMLLIElement>,
  option: SlashCommandOption
): JSX.Element {
  const icon =
    option.id in DEFAULT_SLASH_COMMAND_ICONS
      ? DEFAULT_SLASH_COMMAND_ICONS[option.id]
      : DEFAULT_SLASH_COMMAND_ICONS.unknown;

  return (
    <li {...optionProps}>
      <Box sx={{ lineHeight: 0, marginRight: 4, opacity: 0.618 }}>{icon}</Box>
      <Box sx={{ flexGrow: 1 }}>
        <Typography
          component="span"
          sx={{
            fontSize: 'var(--jp-ui-font-size1)'
          }}
        >
          {option.label}
        </Typography>
        <Typography
          component="span"
          sx={{ opacity: 0.618, fontSize: 'var(--jp-ui-font-size0)' }}
        >
          {' — ' + option.description}
        </Typography>
      </Box>
    </li>
  );
}

export function ChatInput(props: ChatInputProps): JSX.Element {
  const [slashCommandOptions, setSlashCommandOptions] = useState<
    SlashCommandOption[]
  >([]);
  const [currSlashCommand, setCurrSlashCommand] = useState<string | null>(null);
  const activeCell = useActiveCellContext();

  /**
   * Effect: fetch the list of available slash commands from the backend on
   * initial mount to populate the slash command autocomplete.
   */
  useEffect(() => {
    async function getSlashCommands() {
      const slashCommands = (await AiService.listSlashCommands())
        .slash_commands;
      setSlashCommandOptions(
        slashCommands.map<SlashCommandOption>(slashCommand => ({
          id: slashCommand.slash_id,
          label: '/' + slashCommand.slash_id + ' ',
          description: slashCommand.description
        }))
      );
    }
    getSlashCommands();
  }, []);

  // whether any option is highlighted in the slash command autocomplete
  const [highlighted, setHighlighted] = useState<boolean>(false);

  // controls whether the slash command autocomplete is open
  const [open, setOpen] = useState<boolean>(false);

  /**
   * Effect: Open the autocomplete when the user types a slash into an empty
   * chat input. Close the autocomplete when the user clears the chat input.
   */
  useEffect(() => {
    if (props.value === '/') {
      setOpen(true);
      return;
    }

    if (props.value === '') {
      setOpen(false);
      return;
    }
  }, [props.value]);

  /**
   * Effect: Set current slash command
   */
  useEffect(() => {
    const matchedSlashCommand = props.value.match(/^\s*\/\w+/);
    setCurrSlashCommand(matchedSlashCommand && matchedSlashCommand[0]);
  }, [props.value]);

  /**
   * Effect: ensure that the `highlighted` is never `true` when `open` is
   * `false`.
   *
   * For context: https://github.com/jupyterlab/jupyter-ai/issues/849
   */
  useEffect(() => {
    if (!open && highlighted) {
      setHighlighted(false);
    }
  }, [open, highlighted]);

  // TODO: unify the `onSend` implementation in `chat.tsx` and here once text
  // selection is refactored.
  function onSend() {
    // case: /fix
    if (currSlashCommand === '/fix') {
      const cellWithError = activeCell.manager.getContent(true);
      if (!cellWithError) {
        return;
      }

      props.onSend({
        ...cellWithError,
        type: 'cell-with-error'
      });
      return;
    }

    // default case
    props.onSend();
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'Enter') {
      return;
    }

    // do not send the message if the user was just trying to select a suggested
    // slash command from the Autocomplete component.
    if (highlighted) {
      return;
    }

    if (
      event.key === 'Enter' &&
      ((props.sendWithShiftEnter && event.shiftKey) ||
        (!props.sendWithShiftEnter && !event.shiftKey))
    ) {
      onSend();
      event.stopPropagation();
      event.preventDefault();
    }
  }

  // Set the helper text based on whether Shift+Enter is used for sending.
  const helperText = props.sendWithShiftEnter ? (
    <span>
      Press <b>Shift</b>+<b>Enter</b> to send message
    </span>
  ) : (
    <span>
      Press <b>Shift</b>+<b>Enter</b> to add a new line
    </span>
  );

  const inputExists = !!props.value.trim();
  const sendButtonProps: SendButtonProps = {
    onSend,
    sendWithShiftEnter: props.sendWithShiftEnter,
    inputExists,
    activeCellHasError: activeCell.hasError,
    currSlashCommand
  };

  return (
    <Box sx={props.sx}>
      <Autocomplete
        autoHighlight
        freeSolo
        inputValue={props.value}
        onInputChange={(_, newValue: string) => {
          props.onChange(newValue);
        }}
        onHighlightChange={
          /**
           * On highlight change: set `highlighted` to whether an option is
           * highlighted by the user.
           */
          (_, highlightedOption) => {
            setHighlighted(!!highlightedOption);
          }
        }
        onClose={() => setOpen(false)}
        // set this to an empty string to prevent the last selected slash
        // command from being shown in blue
        value=""
        open={open}
        options={slashCommandOptions}
        // hide default extra right padding in the text field
        disableClearable
        // ensure the autocomplete popup always renders on top
        componentsProps={{
          popper: {
            placement: 'top'
          },
          paper: {
            sx: {
              border: '1px solid lightgray'
            }
          }
        }}
        renderOption={renderSlashCommandOption}
        ListboxProps={{
          sx: {
            '& .MuiAutocomplete-option': {
              padding: 2
            }
          }
        }}
        renderInput={params => (
          <TextField
            {...params}
            fullWidth
            variant="outlined"
            multiline
            placeholder="Ask Jupyternaut"
            onKeyDown={handleKeyDown}
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <InputAdornment position="end">
                  <SendButton {...sendButtonProps} />
                </InputAdornment>
              )
            }}
            FormHelperTextProps={{
              sx: { marginLeft: 'auto', marginRight: 0 }
            }}
            helperText={props.value.length > 2 ? helperText : ' '}
          />
        )}
      />
      {props.hasSelection && (
        <FormGroup sx={{ display: 'flex', flexDirection: 'row' }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={props.includeSelection}
                onChange={props.toggleIncludeSelection}
              />
            }
            label="Include selection"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={props.replaceSelection}
                onChange={props.toggleReplaceSelection}
              />
            }
            label="Replace selection"
          />
        </FormGroup>
      )}
    </Box>
  );
}
