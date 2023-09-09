import React, { useState, useMemo, useCallback } from 'react';
import { Alert, AlertColor, Collapse } from '@mui/material';

export type StackingAlert = {
  /**
   * A function that triggers an alert. Successive alerts are indicated in the
   * JSX element.
   * @param alertType Type of alert.
   * @param msg Message contained within the alert.
   * @returns
   */
  show: (alertType: AlertColor, msg: string | Error) => void;
  /**
   * The Alert JSX element that should be rendered by the consumer.
   * This will be `null` if no alerts were triggered.
   */
  jsx: JSX.Element | null;
  /**
   * An async function that closes the alert, and returns a Promise that
   * resolves when the onClose animation is completed.
   */
  clear: () => void | Promise<void>;
};

/**
 * Hook that returns a function to trigger an alert, and a corresponding alert
 * JSX element for the consumer to render. The number of successive identical
 * alerts `X` is indicated in the element via the suffix "(X)".
 */
export function useStackingAlert(): StackingAlert {
  const [type, setType] = useState<AlertColor | null>(null);
  const [msg, setMsg] = useState<string>('');
  const [repeatCount, setRepeatCount] = useState(0);
  const [expand, setExpand] = useState(false);
  const [exitPromise, setExitPromise] = useState<Promise<void>>();
  const [exitPromiseResolver, setExitPromiseResolver] = useState<() => void>();

  const showAlert = useCallback(
    (nextType: AlertColor, _nextMsg: string | Error) => {
      // if the alert is identical to the previous alert, increment the
      // `repeatCount` indicator.
      const nextMsg = _nextMsg.toString();
      if (nextType === type && nextMsg === msg) {
        setRepeatCount(currCount => currCount + 1);
        return;
      }

      if (type === null) {
        // if this alert is being shown for the first time, initialize the
        // exitPromise so we can await it on `clear()`.
        setExitPromise(
          new Promise(res => {
            setExitPromiseResolver(() => res);
          })
        );
      }

      setType(nextType);
      setMsg(nextMsg);
      setRepeatCount(0);
      setExpand(true);
    },
    [msg, type]
  );

  const alertJsx = useMemo(
    () => (
      <Collapse
        in={expand}
        onExited={() => {
          exitPromiseResolver?.();
          // only clear the alert after the Collapse exits, otherwise the alert
          // disappears without any animation.
          setType(null);
          setMsg('');
          setRepeatCount(0);
        }}
        timeout={200}
      >
        {type !== null && (
          <Alert severity={type}>
            {msg + (repeatCount ? ` (${repeatCount})` : '')}
          </Alert>
        )}
      </Collapse>
    ),
    [msg, repeatCount, type, expand, exitPromiseResolver]
  );

  const clearAlert = useCallback(() => {
    setExpand(false);
    return exitPromise;
  }, [expand, exitPromise]);

  return {
    show: showAlert,
    jsx: alertJsx,
    clear: clearAlert
  };
}
