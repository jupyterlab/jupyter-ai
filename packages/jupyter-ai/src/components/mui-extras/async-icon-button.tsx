import React, { useMemo, useState } from 'react';
import { Box, CircularProgress, IconButton } from '@mui/material';

type AsyncIconButtonProps = {
  onClick: () => Promise<unknown>;
  onError: (emsg: string) => unknown;
  onSuccess: () => unknown;
  children: JSX.Element;
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
      <IconButton disabled={loading} onClick={handleClick}>
        {props.children}
      </IconButton>
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
