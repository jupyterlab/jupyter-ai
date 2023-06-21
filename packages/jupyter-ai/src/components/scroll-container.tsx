import React, { useEffect, useMemo } from 'react';
import { Box, SxProps, Theme } from '@mui/material';

type ScrollContainerProps = {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
};

/**
 * Component that handles intelligent scrolling.
 *
 * - If viewport is at the bottom of the overflow container, appending new
 * children keeps the viewport on the bottom of the overflow container.
 *
 * - If viewport is in the middle of the overflow container, appending new
 * children leaves the viewport unaffected.
 *
 * Currently only works for Chrome and Firefox due to reliance on
 * `overflow-anchor`.
 *
 * **References**
 * - https://css-tricks.com/books/greatest-css-tricks/pin-scrolling-to-bottom/
 */
export function ScrollContainer(props: ScrollContainerProps): JSX.Element {
  const id = useMemo(
    () => 'jupyter-ai-scroll-container-' + Date.now().toString(),
    []
  );

  /**
   * Effect: Scroll the container to the bottom as soon as it is visible.
   */
  useEffect(() => {
    const el = document.querySelector<HTMLElement>(`#${id}`);
    if (!el) {
      return;
    }

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            el.scroll({ top: 999999999 });
          }
        });
      },
      { threshold: 1.0 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Box
      id={id}
      sx={{
        overflowY: 'scroll',
        '& *': {
          overflowAnchor: 'none'
        },
        ...props.sx
      }}
    >
      <Box sx={{ minHeight: '100.01%' }}>{props.children}</Box>
      <Box sx={{ overflowAnchor: 'auto', height: '1px' }} />
    </Box>
  );
}
