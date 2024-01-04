import React, { useRef, useEffect } from 'react';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Widget } from '@lumino/widgets';
import { LuminoComponent } from './lumino-component';

type MarkdownWidgetProps = {
  markdownString: string;
  rmRegistry: IRenderMimeRegistry;
};

type MarkdownComponentProps = {
  markdownString: string;
  rmRegistry: IRenderMimeRegistry;
};

class MarkdownWidget extends Widget {
  private rmRegistry: IRenderMimeRegistry;
  private markdownString: string;

  constructor(props: MarkdownWidgetProps) {
    super();
    this.rmRegistry = props.rmRegistry;
    this.markdownString = props.markdownString;
    this.initializeMarkdownRendering();
  }

  async initializeMarkdownRendering(): Promise<void> {
    const mimeType = 'text/markdown';
    const model = this.rmRegistry.createModel({
      data: { [mimeType]: this.markdownString }
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
        markdownString: props.markdownString,
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
