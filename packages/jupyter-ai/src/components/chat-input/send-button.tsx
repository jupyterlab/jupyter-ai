import React, { useCallback, useState } from 'react';
import { Box, Menu, MenuItem, Typography } from '@mui/material';
import KeyboardArrowDown from '@mui/icons-material/KeyboardArrowDown';
import SendIcon from '@mui/icons-material/Send';
import StopIcon from '@mui/icons-material/Stop';

import { TooltippedButton } from '../mui-extras/tooltipped-button';
import { includeSelectionIcon } from '../../icons';
import { useActiveCellContext } from '../../contexts/active-cell-context';
import { useSelectionContext } from '../../contexts/selection-context';
import { AiService } from '../../handler';

const FIX_TOOLTIP = '/fix requires an active code cell with an error';

export type SendButtonProps = {
  onSend: (selection?: AiService.Selection) => unknown;
  onStop: () => unknown;
  sendWithShiftEnter: boolean;
  currSlashCommand: string | null;
  inputExists: boolean;
  activeCellHasError: boolean;
  /**
   * Whether the backend is streaming a reply to any message sent by the current
   * user.
   */
  streamingReplyHere: boolean;
};

export function SendButton(props: SendButtonProps): JSX.Element {
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [textSelection] = useSelectionContext();
  const activeCell = useActiveCellContext();

  const openMenu = useCallback((el: HTMLElement | null) => {
    setMenuAnchorEl(el);
    setMenuOpen(true);
  }, []);

  const closeMenu = useCallback(() => {
    setMenuOpen(false);
  }, []);

  let action: 'send' | 'stop' | 'fix' = props.inputExists
    ? 'send'
    : props.streamingReplyHere
    ? 'stop'
    : 'send';
  if (props.currSlashCommand === '/fix') {
    action = 'fix';
  }

  let disabled = false;
  if (action === 'send' && !props.inputExists) {
    disabled = true;
  }
  if (action === 'fix' && !props.activeCellHasError) {
    disabled = true;
  }

  const includeSelectionDisabled = !(activeCell.exists || textSelection);

  const includeSelectionTooltip =
    action === 'fix'
      ? FIX_TOOLTIP
      : textSelection
      ? `${textSelection.text.split('\n').length} lines selected`
      : activeCell.exists
      ? 'Code from 1 active cell'
      : 'No selection or active cell';

  const defaultTooltip = props.sendWithShiftEnter
    ? 'Send message (SHIFT+ENTER)'
    : 'Send message (ENTER)';

  const tooltip =
    action === 'fix' && !props.activeCellHasError
      ? FIX_TOOLTIP
      : action === 'stop'
      ? 'Stop streaming'
      : !props.inputExists
      ? 'Message must not be empty'
      : defaultTooltip;

  function sendWithSelection() {
    // if the current slash command is `/fix`, `props.onSend()` should always
    // include the code cell with error output, so the `selection` argument does
    // not need to be defined.
    if (action === 'fix') {
      props.onSend();
      closeMenu();
      return;
    }

    // otherwise, parse the text selection or active cell, with the text
    // selection taking precedence.
    if (textSelection?.text) {
      props.onSend({
        type: 'text',
        source: textSelection.text
      });
      closeMenu();
      return;
    }

    if (activeCell.exists) {
      props.onSend({
        type: 'cell',
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        source: activeCell.manager.getContent(false)!.source
      });
      closeMenu();
      return;
    }
  }

  return (
    <Box sx={{ display: 'flex', flexWrap: 'nowrap' }}>
      <TooltippedButton
        onClick={() => (action === 'stop' ? props.onStop() : props.onSend())}
        disabled={disabled}
        tooltip={tooltip}
        buttonProps={{
          size: 'small',
          title: defaultTooltip,
          variant: 'contained'
        }}
        sx={{
          minWidth: 'unset',
          borderRadius: '2px 0px 0px 2px'
        }}
      >
        {action === 'stop' ? <StopIcon /> : <SendIcon />}
      </TooltippedButton>
      <TooltippedButton
        onClick={e => {
          openMenu(e.currentTarget);
        }}
        disabled={disabled}
        tooltip=""
        buttonProps={{
          variant: 'contained',
          onKeyDown: e => {
            if (e.key !== 'Enter' && e.key !== ' ') {
              return;
            }
            openMenu(e.currentTarget);
            // stopping propagation of this event prevents the prompt from being
            // sent when the dropdown button is selected and clicked via 'Enter'.
            e.stopPropagation();
          }
        }}
        sx={{
          minWidth: 'unset',
          padding: '4px 0px',
          borderRadius: '0px 2px 2px 0px',
          borderLeft: '1px solid white'
        }}
      >
        <KeyboardArrowDown />
      </TooltippedButton>
      <Menu
        open={menuOpen}
        onClose={closeMenu}
        anchorEl={menuAnchorEl}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right'
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'right'
        }}
        sx={{
          '& .MuiMenuItem-root': {
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          },
          '& svg': {
            lineHeight: 0
          }
        }}
      >
        <MenuItem
          onClick={e => {
            sendWithSelection();
            // prevent sending second message with no selection
            e.stopPropagation();
          }}
          disabled={includeSelectionDisabled}
        >
          <includeSelectionIcon.react />
          <Box>
            <Typography display="block">Send message with selection</Typography>
            <Typography display="block" sx={{ opacity: 0.618 }}>
              {includeSelectionTooltip}
            </Typography>
          </Box>
        </MenuItem>
      </Menu>
    </Box>
  );
}
