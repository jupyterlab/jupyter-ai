import React, { useMemo, useRef, useState } from 'react';

import { IconButton, Menu, MenuItem, SxProps } from '@mui/material';
import { MoreVert } from '@mui/icons-material';
import {
  addAboveIcon,
  addBelowIcon,
  copyIcon,
  deleteIcon
} from '@jupyterlab/ui-components';

import { AiService } from '../../handler';
import { CopyStatus, useCopy } from '../../hooks/use-copy';
import { useReplace } from '../../hooks/use-replace';
import { useActiveCellContext } from '../../contexts/active-cell-context';
import { replaceCellIcon } from '../../icons';
import { ChatHandler } from '../../chat_handler';

type ChatMessageMenuBaseProps = {
  menuItems: {
    onClick: () => void;
    children?: React.ReactNode;
  }[];
};

export function ChatMessageMenuBase(props: ChatMessageMenuBaseProps): JSX.Element {
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const openMenu = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setMenuOpen(true);
  };

  const menuItemSx: SxProps = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    lineHeight: 0
  };

  const onClickHandler = (callback: () => void) => {
    return () => {
        callback();
        setMenuOpen(false);
    }
  }

  return (
    <>
      <IconButton onClick={openMenu} ref={menuButtonRef} sx={{ marginRight: -2 }}>
        <MoreVert />
      </IconButton>
      <Menu
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        anchorEl={anchorEl}
      >
        {
            props.menuItems.map(menuItemProps => (
                <MenuItem onClick={onClickHandler(menuItemProps.onClick)} sx={menuItemSx}>
                    {menuItemProps.children}
                </MenuItem>
            ))
        }
      </Menu>
    </>
  );
}


interface ChatMessageMenuProps {
    message: AiService.ChatMessage;
    chatHandler: ChatHandler;
}

export const AIMessageMenu = (props: ChatMessageMenuProps) => {
    const { copy, copyLabel } = useCopy({
        labelOverrides: { [CopyStatus.None]: 'Copy response' }
      });
      const { replace, replaceLabel } = useReplace();
      const activeCell = useActiveCellContext();

  const menuItems: ChatMessageMenuBaseProps["menuItems"] = useMemo(() => {
    const res = [{
        onClick: () => copy(props.message.body),
        children: (
            <>
                <copyIcon.react />
                {copyLabel}
            </>
        )
    }, {
        onClick: () => replace(props.message.body),
        children: (
            <>
                <replaceCellIcon.react />
                {replaceLabel}
            </>
        )
    }];

    if (activeCell.exists) {
        res.push({
            onClick: () => activeCell.manager.insertAbove(props.message.body),
            children: (
                <>
                    <addAboveIcon.react />
                    Insert response above active cell
                </>
            )
        })

        res.push({
            onClick: () => activeCell.manager.insertBelow(props.message.body),
            children: (
                <>
                    <addBelowIcon.react />
                    Insert response below active cell
                </>
            )
        })
    }

    return res;
  }, [activeCell]);

  return (
    <ChatMessageMenuBase
        menuItems={menuItems}
    />
  )
}

export const HumanMessageMenu = (props: ChatMessageMenuProps) => {
    const { copy, copyLabel } = useCopy();

    // We replace back all the content of the form `var` to @var
    const messageToCopy = props.message.body.replace(/`([^`]*)`/g, '@$1');

  const menuItems: ChatMessageMenuBaseProps["menuItems"] = useMemo(() => {
    const res = [{
        onClick: () => copy(messageToCopy),
        children: (
            <>
                <copyIcon.react />
                {copyLabel}
            </>
        )
    }, {
        onClick: () => props.chatHandler.sendMessage({
            type: 'clear',
            target: props.message.id
        }),
        children: (
            <>
                <deleteIcon.react />
                Delete This Exchange
            </>
        )
    }];


    return res;
  }, []);

  return (
    <ChatMessageMenuBase
        menuItems={menuItems}
    />
  )
}

export const ChatMessageMenu = (props: ChatMessageMenuProps) => {
    switch (props.message.type) {
        case "human":
            return <HumanMessageMenu {...props} />
        case "agent":
        case "agent-stream":
            return <AIMessageMenu {...props} />
    }
}