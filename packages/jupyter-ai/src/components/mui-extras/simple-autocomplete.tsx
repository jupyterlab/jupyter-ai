import React, {
  useState,
  useRef,
  useEffect,
  useMemo,
  useCallback
} from 'react';
import {
  TextField,
  MenuItem,
  Paper,
  Popper,
  ClickAwayListener,
  TextFieldProps,
  IconButton,
  InputAdornment
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ClearIcon from '@mui/icons-material/Clear';

const StyledPopper = styled(Popper)(({ theme }) => ({
  zIndex: theme.zIndex.modal,
  '& .MuiPaper-root': {
    maxHeight: '200px',
    overflow: 'auto',
    border: `1px solid ${theme.palette.divider}`,
    boxShadow: theme.shadows[8]
  }
}));

export type AutocompleteOption = {
  label: string;
  value: string;
};

export type SimpleAutocompleteProps = {
  /**
   * List of options to show. Each option value should be unique.
   */
  options: AutocompleteOption[];
  /**
   * (optional) Controls the value of the `Autocomplete` component.
   */
  value?: string;
  /**
   * (optional) Callback fired when the input changes.
   */
  onChange?: (value: string) => void;
  /**
   * (optional) Placeholder string shown in the text input while it is empty.
   * This can be used to provide a short example blurb.
   */
  placeholder?: string;
  /**
   * (optional) Function that filters the list of options based on the input
   * value. By default, options whose labels do not contain the input value as a
   * substring are filtered and hidden. The default filter only filters the list
   * of options if the input contains >1 non-whitespace character.
   */
  optionsFilter?: (
    options: AutocompleteOption[],
    inputValue: string
  ) => AutocompleteOption[];
  /**
   * (optional) Additional props passed directly to the `TextField` child
   * component.
   */
  textFieldProps?: Omit<TextFieldProps, 'value' | 'onChange'>;
  /**
   * (optional) Controls the number of options shown in the autocomplete menu.
   * Defaults to unlimited.
   */
  maxOptions?: number;
  /**
   * (optional) If true, the component will treat options as case-sensitive when
   * the default options filter is used (i.e. `props.optionsFilter` is unset).
   */
  caseSensitive?: boolean;
  /**
   * (optional) If true, the component will bold the substrings matching the
   * current input on each option. The input must contain >1 non-whitespace
   * character for this prop to take effect.
   */
  boldMatches?: boolean;

  /**
   * (optional) If true, shows a clear button when the input has a value.
   */
  showClearButton?: boolean;
};

function defaultOptionsFilter(
  options: AutocompleteOption[],
  inputValue: string,
  caseSensitive = false
): AutocompleteOption[] {
  // Do nothing if the input contains <=1 non-whitespace character
  if (inputValue.trim().length <= 1) {
    return options;
  }

  const searchValue = caseSensitive ? inputValue : inputValue.toLowerCase();

  return options.filter(option => {
    const optionLabel = caseSensitive
      ? option.label
      : option.label.toLowerCase();
    return optionLabel.includes(searchValue);
  });
}

function highlightMatches(
  text: string,
  searchValue: string,
  caseSensitive = false
): React.ReactNode {
  // Do nothing if the input contains <=1 non-whitespace character
  if (searchValue.trim().length <= 1) {
    return text;
  }

  const searchText = caseSensitive ? searchValue : searchValue.toLowerCase();
  const targetText = caseSensitive ? text : text.toLowerCase();

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let matchIndex = targetText.indexOf(searchText);

  while (matchIndex !== -1) {
    if (matchIndex > lastIndex) {
      parts.push(text.slice(lastIndex, matchIndex));
    }

    parts.push(
      <strong key={`${matchIndex}-${searchText}`}>
        {text.slice(matchIndex, matchIndex + searchText.length)}
      </strong>
    );

    lastIndex = matchIndex + searchText.length;
    matchIndex = targetText.indexOf(searchText, lastIndex);
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? <>{parts}</> : text;
}

/**
 * A simple `Autocomplete` component with an emphasis on being bug-free and
 * performant. Notes:
 *
 * - By default, options are filtered using case-insensitive substring matching.
 *
 * - Clicking an option sets the value of this component and fires
 * `props.onChange()` if passed. It is treated identically to a user typing the
 * option literally.
 *
 * - Matched substrings will be shown in bold on each option when the
 * `boldMatches` prop is set.
 */
export function SimpleAutocomplete(
  props: SimpleAutocompleteProps
): React.ReactElement {
  const [inputValue, setInputValue] = useState(props.value || '');
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const textFieldRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter and limit options
  const filteredOptions = useMemo(() => {
    const filterFn = props.optionsFilter || defaultOptionsFilter;
    const filtered = filterFn(props.options, inputValue, props.caseSensitive);
    return filtered.slice(0, props.maxOptions ?? props.options.length);
  }, [
    props.options,
    inputValue,
    props.optionsFilter,
    props.maxOptions,
    props.caseSensitive
  ]);

  // Sync external value changes
  useEffect(() => {
    setInputValue(props.value || '');
  }, [props.value]);

  // Determine if menu should be open
  const shouldShowMenu = isOpen && filteredOptions.length > 0;

  const handleInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>): void => {
      const newValue = event.target.value;
      setInputValue(newValue);
      setFocusedIndex(-1);

      if (!isOpen && newValue.trim() !== '') {
        setIsOpen(true);
      }

      if (props.onChange) {
        props.onChange(newValue);
      }
    },
    [isOpen, props.onChange]
  );

  const handleInputFocus = useCallback((): void => {
    setIsOpen(true);
  }, []);

  const handleOptionClick = useCallback(
    (option: AutocompleteOption): void => {
      setInputValue(option.value);
      setIsOpen(false);
      setFocusedIndex(-1);

      if (props.onChange) {
        props.onChange(option.value);
      }

      if (inputRef.current) {
        inputRef.current.blur();
      }
    },
    [props.onChange]
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent): void => {
      if (!shouldShowMenu) {
        return;
      }

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setFocusedIndex(prev => {
            return prev < filteredOptions.length - 1 ? prev + 1 : 0;
          });
          break;

        case 'ArrowUp':
          event.preventDefault();
          setFocusedIndex(prev => {
            return prev > 0 ? prev - 1 : filteredOptions.length - 1;
          });
          break;

        case 'Enter':
          event.preventDefault();
          if (focusedIndex >= 0 && focusedIndex < filteredOptions.length) {
            handleOptionClick(filteredOptions[focusedIndex]);
          }
          break;

        case 'Escape':
          setIsOpen(false);
          setFocusedIndex(-1);
          break;
      }
    },
    [shouldShowMenu, filteredOptions, focusedIndex, handleOptionClick]
  );

  const handleClickAway = useCallback((): void => {
    setIsOpen(false);
    setFocusedIndex(-1);
  }, []);

  return (
    <ClickAwayListener onClickAway={handleClickAway}>
      <div style={{ position: 'relative', width: '100%' }}>
        <TextField
          {...props.textFieldProps}
          ref={textFieldRef}
          inputRef={inputRef}
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onKeyDown={handleKeyDown}
          placeholder={props.placeholder}
          fullWidth
          InputProps={{
            ...props.textFieldProps?.InputProps,
            endAdornment:
              props.showClearButton && inputValue ? (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="clear input"
                    onClick={() => {
                      setInputValue('');
                      if (props.onChange) {
                        props.onChange('');
                      }
                      if (inputRef.current) {
                        inputRef.current.focus();
                      }
                    }}
                    edge="end"
                    size="small"
                  >
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              ) : (
                props.textFieldProps?.InputProps?.endAdornment
              )
          }}
        />

        <StyledPopper
          open={shouldShowMenu}
          anchorEl={textFieldRef.current}
          placement="bottom-start"
          style={{ width: textFieldRef.current?.offsetWidth }}
        >
          <Paper>
            {filteredOptions.map((option, index) => {
              const displayLabel = props.boldMatches
                ? highlightMatches(
                    option.label,
                    inputValue,
                    props.caseSensitive
                  )
                : option.label;

              return (
                <MenuItem
                  key={`${option.value}-${index}`}
                  selected={index === focusedIndex}
                  onClick={() => {
                    handleOptionClick(option);
                  }}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'action.hover'
                    },
                    '&.Mui-selected:hover': {
                      backgroundColor: 'action.selected'
                    }
                  }}
                >
                  {displayLabel}
                </MenuItem>
              );
            })}
          </Paper>
        </StyledPopper>
      </div>
    </ClickAwayListener>
  );
}
