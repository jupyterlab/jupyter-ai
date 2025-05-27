import {
  IChatModel,
  MessageFooterSectionProps,
  TooltippedButton
} from '@jupyter/chat';
import StopIcon from '@mui/icons-material/Stop';
import React, { useEffect, useState } from 'react';
import { requestAPI } from '../../handler';

/**
 * The stop button.
 */
export function StopButton(props: MessageFooterSectionProps): JSX.Element {
  const { message, model } = props;
  const [visible, setVisible] = useState<boolean>(false);
  const tooltip = 'Stop streaming';

  useEffect(() => {
    const writerChanged = (_: IChatModel, writers: IChatModel.IWriter[]) => {
      const w = writers.filter(w => w.messageID === message.id);
      if (w.length > 0) {
        setVisible(true);
      } else {
        setVisible(false);
      }
    };

    // Listen only the messages that are from a bot.
    if (
      message.sender.username !== model.user?.username &&
      message.sender.bot
    ) {
      model.writersChanged?.connect(writerChanged);

      // Check if the message is currently being edited.
      writerChanged(model, model.writers);
    }

    return () => {
      model.writersChanged?.disconnect(writerChanged);
    };
  }, [model]);

  const onClick = () => {
    // Post request to the stop streaming handler.
    requestAPI('chats/stop_streaming', {
      method: 'POST',
      body: JSON.stringify({
        message_id: message.id
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    });
  };

  return visible ? (
    <TooltippedButton
      onClick={onClick}
      tooltip={tooltip}
      buttonProps={{
        size: 'small',
        variant: 'contained',
        title: tooltip
      }}
      sx={{ display: visible ? 'inline-flex' : 'none' }}
    >
      <StopIcon />
    </TooltippedButton>
  ) : (
    <></>
  );
}
