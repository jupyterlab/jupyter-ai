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

export class MarkdownWidget extends Widget {
  private rendermime: IRenderMimeRegistry;
  private markdownString: string;

  constructor(props: MarkdownWidgetProps) {
    super();
    this.rendermime = props.rendermime;
    this.markdownString = props.markdownString;
    this.onAfterAttach = this.onAfterAttach.bind(this);
  }

  onAfterAttach(): void {
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

  async updateMarkdown(markdownString: string): Promise<void> {
    this.markdownString = markdownString;
    // Clear the existing content
    while (this.node.firstChild) {
      this.node.removeChild(this.node.firstChild);
    }
    // Reinitialize rendering with the new markdown string
    await this.initializeMarkdownRendering();
  }
}

export function MarkdownComponent({
  markdownString,
  rendermime
}: MarkdownComponentProps): React.ReactElement | null {
  const widgetRef = useRef<MarkdownWidget | null>(null);

  useEffect(() => {
    if (!widgetRef.current) {
      widgetRef.current = new MarkdownWidget({ rendermime, markdownString });
    } else {
      widgetRef.current.updateMarkdown(markdownString);
    }

    return () => {
      widgetRef.current?.dispose();
    };
  }, [markdownString, rendermime]);

  return widgetRef.current ? (
    <LuminoComponent widget={widgetRef.current} />
  ) : null;
}
