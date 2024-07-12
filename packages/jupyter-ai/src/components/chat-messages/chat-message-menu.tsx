import React, { useRef, useState } from 'react';

import { IconButton, Menu, MenuItem, SxProps } from '@mui/material';
import { MoreVert } from '@mui/icons-material';
import {
  addAboveIcon,
  addBelowIcon,
  copyIcon
} from '@jupyterlab/ui-components';

import { AiService } from '../../handler';
import { CopyStatus, useCopy } from '../../hooks/use-copy';
import { useReplace } from '../../hooks/use-replace';
import { useActiveCellContext } from '../../contexts/active-cell-context';
import { replaceCellIcon } from '../../icons';

type ChatMessageMenuProps = {
  message: AiService.ChatMessage;

  /**
   * Styles applied to the menu icon button.
   */
  sx?: SxProps;
};

export function ChatMessageMenu(props: ChatMessageMenuProps): JSX.Element {
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const { copy, copyLabel } = useCopy({
    labelOverrides: { [CopyStatus.None]: 'Copy response' }
  });
  const { replace, replaceLabel } = useReplace();
  const activeCell = useActiveCellContext();

  const [menuOpen, setMenuOpen] = useState(false);

  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const openMenu = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setMenuOpen(true);
  };

  const insertAboveLabel = activeCell.exists
    ? 'Insert response above active cell'
    : 'Insert response above active cell (no active cell)';

  const insertBelowLabel = activeCell.exists
    ? 'Insert response below active cell'
    : 'Insert response below active cell (no active cell)';

  const menuItemSx: SxProps = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    lineHeight: 0
  };

  return (
    <>
      <IconButton onClick={openMenu} ref={menuButtonRef} sx={props.sx}>
        <MoreVert />
      </IconButton>
      <Menu
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        anchorEl={anchorEl}
      >
        <MenuItem onClick={() => copy(props.message.body)} sx={menuItemSx}>
          <copyIcon.react />
          {copyLabel}
        </MenuItem>
        <MenuItem onClick={() => replace(props.message.body)} sx={menuItemSx}>
          <replaceCellIcon.react />
          {replaceLabel}
        </MenuItem>
        <MenuItem
          onClick={() => activeCell.manager.insertAbove(props.message.body)}
          disabled={!activeCell.exists}
          sx={menuItemSx}
        >
          <addAboveIcon.react />
          {insertAboveLabel}
        </MenuItem>
        <MenuItem
          onClick={() => activeCell.manager.insertBelow(props.message.body)}
          disabled={!activeCell.exists}
          sx={menuItemSx}
        >
          <addBelowIcon.react />
          {insertBelowLabel}
        </MenuItem>
      </Menu>
    </>
  );
}
