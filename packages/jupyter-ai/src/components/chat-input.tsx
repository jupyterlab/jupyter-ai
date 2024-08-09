import React, { useEffect, useRef, useState } from 'react';

import {
  Autocomplete,
  Box,
  SxProps,
  TextField,
  Theme,
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
import { ISignal } from '@lumino/signaling';

import { AiService } from '../handler';
import { SendButton, SendButtonProps } from './chat-input/send-button';
import { useActiveCellContext } from '../contexts/active-cell-context';
import { ChatHandler } from '../chat_handler';

type ChatInputProps = {
  chatHandler: ChatHandler;
  focusInputSignal: ISignal<unknown, void>;
  sendWithShiftEnter: boolean;
  sx?: SxProps<Theme>;
  /**
   * Name of the persona, set by the selected chat model. This defaults to
   * `'Jupyternaut'`, but can differ for custom providers.
   */
  personaName: string;
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
  const [input, setInput] = useState('');
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

  // store reference to the input element to enable focusing it easily
  const inputRef = useRef<HTMLInputElement>();

  /**
   * Effect: connect the signal emitted on input focus request.
   */
  useEffect(() => {
    const focusInputElement = () => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    };
    props.focusInputSignal.connect(focusInputElement);
    return () => {
      props.focusInputSignal.disconnect(focusInputElement);
    };
  }, []);

  /**
   * Effect: Open the autocomplete when the user types a slash into an empty
   * chat input. Close the autocomplete when the user clears the chat input.
   */
  useEffect(() => {
    if (input === '/') {
      setOpen(true);
      return;
    }

    if (input === '') {
      setOpen(false);
      return;
    }
  }, [input]);

  /**
   * Effect: Set current slash command
   */
  useEffect(() => {
    const matchedSlashCommand = input.match(/^\s*\/\w+/);
    setCurrSlashCommand(matchedSlashCommand && matchedSlashCommand[0]);
  }, [input]);

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

  function onSend(selection?: AiService.Selection) {
    const prompt = input;
    setInput('');

    // if the current slash command is `/fix`, we always include a code cell
    // with error output in the selection.
    if (currSlashCommand === '/fix') {
      const cellWithError = activeCell.manager.getContent(true);
      if (!cellWithError) {
        return;
      }

      props.chatHandler.sendMessage({
        prompt,
        selection: { ...cellWithError, type: 'cell-with-error' }
      });
      return;
    }

    // otherwise, send a ChatRequest with the prompt and selection
    props.chatHandler.sendMessage({ prompt, selection });
  }

  const inputExists = !!input.trim();
  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'Enter') {
      return;
    }

    // do not send the message if the user was just trying to select a suggested
    // slash command from the Autocomplete component.
    if (highlighted) {
      return;
    }

    if (!inputExists) {
      event.stopPropagation();
      event.preventDefault();
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
        inputValue={input}
        onInputChange={(_, newValue: string) => {
          setInput(newValue);
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
            maxRows={20}
            multiline
            placeholder={`Ask ${props.personaName}`}
            onKeyDown={handleKeyDown}
            inputRef={inputRef}
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <InputAdornment
                  position="end"
                  sx={{ height: 'unset', alignSelf: 'flex-end' }}
                >
                  <SendButton {...sendButtonProps} />
                </InputAdornment>
              )
            }}
            FormHelperTextProps={{
              sx: { marginLeft: 'auto', marginRight: 0 }
            }}
            helperText={input.length > 2 ? helperText : ' '}
          />
        )}
      />
    </Box>
  );
}
