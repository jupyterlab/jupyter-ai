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
import { useSelectionContext } from '../contexts/selection-context';
import { useNotebookTrackerContext } from '../contexts/notebook-tracker-context';
import { formatCodeForCell, getCompletion, processVariables } from '../utils';

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
  /**
   * Whether the backend is streaming a reply to any message sent by the current
   * user.
   */
  streamingReplyHere: boolean;
};

/**
 * List of icons per slash command, shown in the autocomplete popup.
 *
 * This list of icons should eventually be made configurable. However, it is
 * unclear whether custom icons should be defined within a Lumino plugin (in the
 * frontend) or served from a static server route (in the backend).
 */
const DEFAULT_COMMAND_ICONS: Record<string, JSX.Element> = {
  '/ask': <FindInPage />,
  '/clear': <HideSource />,
  '/export': <Download />,
  '/fix': <AutoFixNormal />,
  '/generate': <MenuBook />,
  '/help': <Help />,
  '/learn': <School />,
  // TODO: Reenable it when we are more confident here
  //   '@file': <FindInPage />,
  unknown: <MoreHoriz />
};

/**
 * Renders an option shown in the slash command autocomplete.
 */
function renderAutocompleteOption(
  optionProps: React.HTMLAttributes<HTMLLIElement>,
  option: AiService.AutocompleteOption
): JSX.Element {
  const icon =
    option.id in DEFAULT_COMMAND_ICONS
      ? DEFAULT_COMMAND_ICONS[option.id]
      : DEFAULT_COMMAND_ICONS.unknown;

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
        {option.description.length > 0 && <Typography
          component="span"
          sx={{ opacity: 0.618, fontSize: 'var(--jp-ui-font-size0)' }}
        >
          {' — ' + option.description}
        </Typography>}
      </Box>
    </li>
  );
}

export function ChatInput(props: ChatInputProps): JSX.Element {
  const [input, setInput] = useState('');
  const [autocompleteOptions, setAutocompleteOptions] = useState<
    AiService.AutocompleteOption[]
  >([]);
  const [autocompleteCommandOptions, setAutocompleteCommandOptions] = useState<
    AiService.AutocompleteOption[]
  >([]);
  const [autocompleteArgOptions, setAutocompleteArgOptions] = useState<
    AiService.AutocompleteOption[]
  >([]);
  const [currSlashCommand, setCurrSlashCommand] = useState<string | null>(null);
  const activeCell = useActiveCellContext();
  const [textSelection] = useSelectionContext();
  const notebookTracker = useNotebookTrackerContext();

  /**
   * Effect: fetch the list of available slash commands from the backend on
   * initial mount to populate the slash command autocomplete.
   */
  useEffect(() => {
    async function getAutocompleteCommandOptions() {
      const response = await AiService.listAutocompleteOptions();
      setAutocompleteCommandOptions(response.options);
    }
    getAutocompleteCommandOptions();
  }, []);

  useEffect(() => {
    async function getAutocompleteArgOptions() {
      let options: AiService.AutocompleteOption[] = [];
      const lastWord = getLastWord(input);
      if (lastWord.includes(':')) {
        const id = lastWord.split(':', 1)[0];
        // get option that matches the command
        const option = autocompleteCommandOptions.find(
          option => option.id === id
        );
        if (option) {
          const response = await AiService.listAutocompleteArgOptions(lastWord);
          options = response.options;
        }
      }
      setAutocompleteArgOptions(options);
    }
    getAutocompleteArgOptions();
  }, [autocompleteCommandOptions, input]);

  // Combine the fixed options with the argument options
  useEffect(() => {
    if (autocompleteArgOptions.length > 0) {
      setAutocompleteOptions(autocompleteArgOptions);
    } else {
      setAutocompleteOptions(autocompleteCommandOptions);
    }
  }, [autocompleteCommandOptions, autocompleteArgOptions]);

  // whether any option is highlighted in the autocomplete
  const [highlighted, setHighlighted] = useState<boolean>(false);

  // controls whether the autocomplete is open
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
    if (filterAutocompleteOptions(autocompleteOptions, input).length > 0) {
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


  const _getNotebookCells = () => {
    const cells = notebookTracker?.currentWidget?.model?.sharedModel.cells;
    const notebookCode: AiService.NotebookCell[] | undefined = cells?.map((cell, index) =>  ({
        content: formatCodeForCell(cell, index),
        type: cell.cell_type
    }));


    const activeCellId = activeCell.manager.getActiveCellId()
    const activeCellIdx = cells?.findIndex(cell => cell.id === activeCellId);

    return {
        notebookCode,
        activeCellId: activeCellIdx !== -1 ? activeCellIdx : undefined
    }
  }

  async function onSend() {
    const {varValues, processedInput} = await processVariables(input, notebookTracker);
    const prompt = processedInput;
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

    const selection: AiService.Selection | null = textSelection?.text ? {
        type: "text",
        source: textSelection.text
    } : activeCell.manager.getContent(false) ? {
        type: "cell",
        source: activeCell.manager.getContent(false)?.source || ""
    } : null;

    const { notebookCode, activeCellId } = _getNotebookCells();
    const notebook: AiService.ChatNotebookContent | null = {
        notebook_code: notebookCode,
        active_cell_id: activeCellId,
        variable_context: varValues
    }

    // otherwise, send a ChatRequest with the prompt and selection
    props.chatHandler.sendMessage({ prompt, selection, notebook });
  }

  useEffect(() => {
    const _getcompletionUtil = async (prefix: string) => {
        const completions = await getCompletion(prefix, notebookTracker);

        setAutocompleteOptions(completions.map(option => ({
            id: option,
            // Add an explict space for better user experience
            // as one generally wants to select and type directly
            label: `${option} `,
            description: "",
            only_start: false
        })))
        setOpen(true);
        return;
    }

    // This represents a slash command run directly
    // However, when a /command has a certain prompt associated
    // with it we do not want to return just yet to still support
    // @ based autocompletions
    // For eg. /ask What is @x?
    if (input.startsWith("/") && !input.includes(" ")) return;

    const splitInput = input.split(" ");
    if (!splitInput.length) {
        setOpen(false);
        return;
    }

    const prefix = splitInput[splitInput.length - 1];
    if (prefix[0] !== "@") {
        setOpen(false);
        return;
    }

    _getcompletionUtil(prefix.slice(1));
  }, [input])


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
  const helperText = (
    <span>
        Open with <b>Ctrl</b>+<b>Shift</b>+<b>Space</b>
    </span>
  )

  ;

  const sendButtonProps: SendButtonProps = {
    onSend,
    onStop: () => {
      props.chatHandler.sendMessage({
        type: 'stop'
      });
    },
    streamingReplyHere: props.streamingReplyHere,
    sendWithShiftEnter: props.sendWithShiftEnter,
    inputExists,
    activeCellHasError: activeCell.hasError,
    currSlashCommand
  };

  function filterAutocompleteOptions(
    options: AiService.AutocompleteOption[],
    inputValue: string
  ): AiService.AutocompleteOption[] {
    const lastWord = getLastWord(inputValue);
    if (lastWord === '') {
        return [];
      }

    // When we trigger @ based autocompletions, we want to filter out
    // slash commands
    if (lastWord.startsWith("@")) {
        return options.filter(option => !option.label.startsWith("/"))
    }

    const isStart = lastWord === inputValue;
    return options.filter(
      option =>
        option.label.startsWith(lastWord) && (!option.only_start || isStart)
    );
  }


  return (
    <Box sx={props.sx}>
      <Autocomplete
        autoHighlight
        freeSolo
        inputValue={input}
        filterOptions={(options, { inputValue }) => {
          return filterAutocompleteOptions(options, inputValue);
        }}
        onChange={(_, option) => {
          const value = typeof option === 'string' ? option : option.label;
          let matchLength = 0;
          for (let i = 1; i <= value.length; i++) {
            if (input.endsWith(value.slice(0, i))) {
              matchLength = i;
            }
          }
          setInput(input + value.slice(matchLength));
        }}
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
        onClose={(_, reason) => {
          if (reason !== 'selectOption' || input.endsWith(' ')) {
            setOpen(false);
          }
        }}
        // set this to an empty string to prevent the last selected slash
        // command from being shown in blue
        value=""
        open={open}
        options={autocompleteOptions}
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
        renderOption={renderAutocompleteOption}
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
            placeholder={`Ask me anything about your notebook, current selection or any generic python query`}
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
                sx: {
                    marginLeft: "auto",
                    marginRight: 0
                }
            }}
            helperText={helperText}
          />
        )}
      />
    </Box>
  );
}

function getLastWord(input: string): string {
  return input.split(/(?<!\\)\s+/).pop() || '';
}
