import React, { useRef, useEffect } from 'react';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Widget } from '@lumino/widgets';
import { LuminoComponent } from './lumino-component';

type MarkdownWidgetProps = {
  rendermime: IRenderMimeRegistry;
  markdownString: string;
};

type MarkdownComponentProps = {
  markdownString: string;
  rendermime: IRenderMimeRegistry;
};

class MarkdownWidget extends Widget {
  private rendermime: IRenderMimeRegistry;
  private markdownString: string;

  constructor(props: MarkdownWidgetProps) {
    super();
    this.rendermime = props.rendermime;
    this.markdownString = props.markdownString;
    this.initializeMarkdownRendering();
  }

  async initializeMarkdownRendering(): Promise<void> {
    const mimeType = 'text/markdown';
    const model = this.rendermime.createModel({
      data: { [mimeType]: this.markdownString }
    });
    const renderer = this.rendermime.createRenderer(mimeType);
    await renderer.renderModel(model);
    this.node.appendChild(renderer.node);
  }
}

export function MarkdownComponent(
  props: MarkdownComponentProps
): React.ReactElement | null {
  const { markdownString, rendermime } = props;
  const widgetRef = useRef<MarkdownWidget | null>(null);

  useEffect(() => {
    if (!widgetRef.current) {
      widgetRef.current = new MarkdownWidget({ rendermime, markdownString });
    }

    return () => {
      widgetRef.current?.dispose();
    };
  }, []); // Empty dependency array if props are not expected to change

  return widgetRef.current ? (
    <LuminoComponent widget={widgetRef.current} />
  ) : null;
}
