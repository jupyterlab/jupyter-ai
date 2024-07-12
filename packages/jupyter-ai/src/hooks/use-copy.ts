import { useState, useRef, useCallback } from 'react';

export enum CopyStatus {
  None,
  Copying,
  Copied
}

export type UseCopyProps = {
  /**
   * List of labels by copy status. Used to override the default labels provided
   * by this hook.
   */
  labelOverrides?: Partial<Record<CopyStatus, string>>;
};

export type UseCopyReturn = {
  /**
   * The status of the copy operation. This is set to CopyStatus.None when no
   * copy operation was performed, set to CopyStatus.Copying while the copy
   * operation is executing, and set to CopyStatus.Copied for 1000ms after the
   * copy operation completes.
   *
   */
  copyStatus: CopyStatus;
  /**
   * Label that should be shown by the copy button based on the copy status.
   * This can be selectively overridden via the `labelOverrides` prop passed to
   * the `useCopy()` hook.
   */
  copyLabel: string;
  /**
   * Function that takes a string and copies it to the clipboard.
   */
  copy: (value: string) => unknown;
};

const DEFAULT_LABELS_BY_COPY_STATUS: Record<CopyStatus, string> = {
  [CopyStatus.None]: 'Copy to clipboard',
  [CopyStatus.Copying]: 'Copying…',
  [CopyStatus.Copied]: 'Copied!'
};

/**
 * Hook that provides a function to copy a string to a clipboard and manages
 * related UI state. Should be used by any button that intends to copy text.
 */
export function useCopy(props?: UseCopyProps): UseCopyReturn {
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(CopyStatus.None);
  const timeoutId = useRef<number | null>(null);

  const copy = useCallback(
    async (value: string) => {
      // ignore if we are already copying
      if (copyStatus === CopyStatus.Copying) {
        return;
      }

      try {
        await navigator.clipboard.writeText(value);
      } catch (err) {
        console.error('Failed to copy text: ', err);
        setCopyStatus(CopyStatus.None);
        return;
      }

      setCopyStatus(CopyStatus.Copied);
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
      timeoutId.current = setTimeout(
        () => setCopyStatus(CopyStatus.None),
        1000
      );
    },
    [copyStatus]
  );

  const copyLabel = {
    ...DEFAULT_LABELS_BY_COPY_STATUS,
    ...props?.labelOverrides
  }[copyStatus];

  return {
    copyStatus,
    copyLabel,
    copy
  };
}
