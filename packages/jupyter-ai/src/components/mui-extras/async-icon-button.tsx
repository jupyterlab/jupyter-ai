import React, { useMemo, useState } from 'react';
import { Box, CircularProgress, IconButton } from '@mui/material';
import { ContrastingTooltip } from './contrasting-tooltip';

type AsyncIconButtonProps = {
  onClick: () => Promise<unknown>;
  onError: (emsg: string) => unknown;
  onSuccess: () => unknown;
  children: JSX.Element;
  onMouseDown?: React.MouseEventHandler<HTMLButtonElement>;
  /**
   * Whether this component should require confirmation from the user before
   * calling `props.onClick()`. This is only read on initial render.
   */
  confirm?: boolean;
};

/**
 * A MUI IconButton that indicates whether the click handler is resolving via a
 * circular spinner around the IconButton. Requests user confirmation when
 * `confirm` is set to `true`.
 */
export function AsyncIconButton(props: AsyncIconButtonProps): JSX.Element {
  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const shouldConfirm = useMemo(() => !!props.confirm, []);

  async function handleClick() {
    if (shouldConfirm && !showConfirm) {
      setShowConfirm(true);
      return;
    }

    setLoading(true);
    let thrown = false;
    try {
      await props.onClick();
    } catch (e: unknown) {
      thrown = true;
      if (e instanceof Error) {
        props.onError(e.toString());
      } else {
        // this should never happen.
        // if this happens, it means the thrown value was not of type `Error`.
        props.onError('Unknown error occurred.');
      }
    }
    setLoading(false);
    if (!thrown) {
      props.onSuccess();
    }
  }

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-block',
        boxSizing: 'content-box'
      }}
    >
      <ContrastingTooltip
        title="Click again to confirm"
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        arrow
        placement="top"
      >
        <IconButton
          disabled={loading}
          onClick={handleClick}
          onMouseDown={props.onMouseDown}
        >
          {props.children}
        </IconButton>
      </ContrastingTooltip>
      {loading && (
        <CircularProgress
          size="100%"
          sx={{
            position: 'absolute',
            top: 0,
            left: 0
          }}
        />
      )}
    </Box>
  );
}
