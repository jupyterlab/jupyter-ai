import React from 'react';
import { Button, ButtonProps, SxProps, TooltipProps } from '@mui/material';

import { ContrastingTooltip } from './contrasting-tooltip';

export type TooltippedButtonProps = {
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
   * Props passed directly to the MUI `Button` component.
   */
  buttonProps?: ButtonProps;
  /**
   * Styles applied to the MUI `Button` component.
   */
  sx?: SxProps;
};

/**
 * A component that renders an MUI `Button` with a high-contrast tooltip
 * provided by `ContrastingTooltip`. This component differs from the MUI
 * defaults in the following ways:
 *
 * - Shows the tooltip on hover even if disabled.
 * - Renders the tooltip above the button by default.
 * - Renders the tooltip closer to the button by default.
 * - Lowers the opacity of the Button when disabled.
 * - Renders the Button with `line-height: 0` to avoid showing extra
 * vertical space in SVG icons.
 *
 * NOTE TO DEVS: Please keep this component's features synchronized with
 * features available to `TooltippedIconButton`.
 */
export function TooltippedButton(props: TooltippedButtonProps): JSX.Element {
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
        By default, tooltips never appear when the Button is disabled. The
        official way to support this feature in MUI is to wrap the child Button
        element in a `span` element.

        See: https://mui.com/material-ui/react-tooltip/#disabled-elements
      */}
      <span style={{ cursor: 'default' }}>
        <Button
          {...props.buttonProps}
          onClick={props.onClick}
          disabled={props.disabled}
          sx={{
            lineHeight: 0,
            ...(props.disabled && { opacity: 0.5 }),
            ...props.sx
          }}
          aria-label={props['aria-label']}
        >
          {props.children}
        </Button>
      </span>
    </ContrastingTooltip>
  );
}
