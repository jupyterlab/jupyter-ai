import React, { useRef, useEffect } from 'react';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Widget } from '@lumino/widgets';
import { LuminoComponent } from './lumino-component';

type MarkdownWidgetProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
};

type MarkdownComponentProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
};

class MarkdownWidget extends Widget {
  private rmRegistry: IRenderMimeRegistry;
  private markdownStr: string;

  constructor(props: MarkdownWidgetProps) {
    super();
    this.rmRegistry = props.rmRegistry;
    this.markdownStr = props.markdownStr;
    this.initializeMarkdownRendering();
  }

  async initializeMarkdownRendering(): Promise<void> {
    const mimeType = 'text/markdown';
    const model = this.rmRegistry.createModel({
      data: { [mimeType]: this.markdownStr }
    });
    const renderer = this.rmRegistry.createRenderer(mimeType);
    await renderer.renderModel(model);
    this.node.appendChild(renderer.node);
  }
}

export function MarkdownComponent(
  props: MarkdownComponentProps
): React.ReactElement | null {
  const widgetRef = useRef<MarkdownWidget | null>(null);

  useEffect(() => {
    if (!widgetRef.current) {
      widgetRef.current = new MarkdownWidget({
        markdownStr: props.markdownStr,
        rmRegistry: props.rmRegistry
      });
    }

    return () => {
      widgetRef.current?.dispose();
    };
  }, []);

  return widgetRef.current ? (
    <LuminoComponent widget={widgetRef.current} />
  ) : null;
}
