import React, { useRef, useEffect } from 'react';
import { Widget } from '@lumino/widgets';

type LuminoComponentProps = {
  widget: Widget;
};

export function LuminoComponent(
  props: LuminoComponentProps
): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      Widget.attach(props.widget, ref.current);
    }

    return () => {
      // Detach the widget when the component unmounts
      Widget.detach(props.widget);
    };
  }, [props.widget]);

  return <div ref={ref} />;
}
