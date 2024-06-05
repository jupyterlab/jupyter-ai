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
  IconButton,
  InputAdornment,
  Typography
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import {
  Download,
  FindInPage,
  Help,
  MoreHoriz,
  MenuBook,
  School,
  HideSource
} from '@mui/icons-material';

import { AiService } from '../handler';

type ChatInputProps = {
  value: string;
  onChange: (newValue: string) => unknown;
  onSend: () => unknown;
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
   * chat input. Close the autocomplete and reset the last selected value when
   * the user clears the chat input.
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
      props.onSend();
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
           *
           * This isn't called when an option is selected for some reason, so we
           * need to call `setHighlighted(false)` in `onClose()`.
           */
          (_, highlightedOption) => {
            setHighlighted(!!highlightedOption);
          }
        }
        onClose={
          /**
           * On close: set `highlighted` to `false` and close the popup by
           * setting `open` to `false`.
           */
          () => {
            setHighlighted(false);
            setOpen(false);
          }
        }
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
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={props.onSend}
                    disabled={!props.value.trim().length}
                    title={
                      props.sendWithShiftEnter
                        ? 'Send message (SHIFT+ENTER)'
                        : 'Send message (ENTER)'
                    }
                  >
                    <SendIcon />
                  </IconButton>
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
