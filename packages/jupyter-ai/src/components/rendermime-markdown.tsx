import React, { useRef, useEffect } from 'react';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

type RendermimeMarkdownProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
};

export function RendermimeMarkdown(
  props: RendermimeMarkdownProps
): JSX.Element {
  const { markdownStr, rmRegistry } = props;
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderMarkdown = async () => {
      if (!ref.current) {
        return;
      }
      ref.current.innerHTML = '';

      const mimeType = 'text/markdown';
      const model = rmRegistry.createModel({
        data: { [mimeType]: markdownStr }
      });
      const renderer = rmRegistry.createRenderer(mimeType);
      await renderer.renderModel(model);
      ref.current.appendChild(renderer.node);
    };

    renderMarkdown();
  }, [markdownStr, rmRegistry]);

  return <div ref={ref} />;
}
