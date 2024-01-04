import React, { useRef, useEffect } from 'react';
import { MessageLoop } from '@lumino/messaging';
import { Widget } from '@lumino/widgets';

type LuminoComponentProps = {
  widget: Widget;
};

export function LuminoComponent({
  widget
}: LuminoComponentProps): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) {
      return;
    }

    try {
      MessageLoop.sendMessage(widget, Widget.Msg.BeforeAttach);
      ref.current.appendChild(widget.node);
      MessageLoop.sendMessage(widget, Widget.Msg.AfterAttach);
    } catch (e) {
      console.warn('Exception while attaching Lumino widget:', e);
    }

    return () => {
      try {
        if (widget.isAttached || widget.node.isConnected) {
          Widget.detach(widget);
        }
      } catch (e) {
        console.warn('Exception while detaching Lumino widget:', e);
      }
    };
  }, [widget]);

  return <div ref={ref} />;
}
