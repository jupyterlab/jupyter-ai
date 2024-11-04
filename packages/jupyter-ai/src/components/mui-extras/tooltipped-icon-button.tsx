import React from 'react';
import {
  IconButton,
  IconButtonProps,
  SxProps,
  TooltipProps
} from '@mui/material';

import { ContrastingTooltip } from './contrasting-tooltip';

export type TooltippedIconButtonProps = {
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  tooltip: string;
  children: JSX.Element;
  disabled?: boolean;
  placement?: TooltipProps['placement'];
  /**
   * The offset of the tooltip popup.
   *
   * The expected syntax is defined by the Popper library:
   * https://popper.js.org/docs/v2/modifiers/offset/
   */
  offset?: [number, number];
  'aria-label'?: string;
  /**
   * Props passed directly to the MUI `IconButton` component.
   */
  iconButtonProps?: IconButtonProps;
  /**
   * Styles applied to the MUI `IconButton` component.
   */
  sx?: SxProps;
};

/**
 * A component that renders an MUI `IconButton` with a high-contrast tooltip
 * provided by `ContrastingTooltip`. This component differs from the MUI
 * defaults in the following ways:
 *
 * - Shows the tooltip on hover even if disabled.
 * - Renders the tooltip above the button by default.
 * - Renders the tooltip closer to the button by default.
 * - Lowers the opacity of the IconButton when disabled.
 * - Renders the IconButton with `line-height: 0` to avoid showing extra
 * vertical space in SVG icons.
 *
 * NOTE TO DEVS: Please keep this component's features synchronized with
 * features available to `TooltippedButton`.
 */
export function TooltippedIconButton(
  props: TooltippedIconButtonProps
): JSX.Element {
  return (
    <ContrastingTooltip
      title={props.tooltip}
      placement={props.placement ?? 'top'}
      slotProps={{
        popper: {
          modifiers: [
            {
              name: 'offset',
              options: {
                offset: [0, -8]
              }
            }
          ]
        }
      }}
    >
      {/*
        By default, tooltips never appear when the IconButton is disabled. The
        official way to support this feature in MUI is to wrap the child Button
        element in a `span` element.

        See: https://mui.com/material-ui/react-tooltip/#disabled-elements
      */}
      <span style={{ cursor: 'default' }}>
        <IconButton
          {...props.iconButtonProps}
          onClick={props.onClick}
          disabled={props.disabled}
          sx={{
            ml: '8px',
            lineHeight: 0,
            ...(props.disabled && { opacity: 0.5 }),
            ...props.sx
          }}
          aria-label={props['aria-label']}
        >
          {props.children}
        </IconButton>
      </span>
    </ContrastingTooltip>
  );
}
