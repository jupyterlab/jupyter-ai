import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

import { CopyButton } from './copy-button';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { MathJaxTypesetter } from '@jupyterlab/mathjax-extension';

const RENDERMIME_MD_CLASS = 'jp-ai-rendermime-markdown';

type RendermimeMarkdownProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
};

function RendermimeMarkdownBase(props: RendermimeMarkdownProps): JSX.Element {
  const [renderedContent, setRenderedContent] = useState<HTMLElement | null>(
    null
  );
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderContent = async () => {
      const rmRegistry = props.rmRegistry.clone({
        latexTypesetter: new MathJaxTypesetter()
      });

      const mimeType = 'text/markdown';

      const model = rmRegistry.createModel({
        data: { [mimeType]: props.markdownStr }
      });
      const renderer = rmRegistry.createRenderer(mimeType);
      await renderer.renderModel(model);
      setRenderedContent(renderer.node);

      // Attach CopyButton to each <pre> block
      if (containerRef.current && renderer.node) {
        const preBlocks = renderer.node.querySelectorAll('pre');
        preBlocks.forEach(preBlock => {
          const copyButtonContainer = document.createElement('div');
          preBlock.parentNode?.insertBefore(
            copyButtonContainer,
            preBlock.nextSibling
          );
          ReactDOM.render(
            <CopyButton value={preBlock.textContent || ''} />,
            copyButtonContainer
          );
        });
      }
    };

    renderContent();
  }, [props.markdownStr, props.rmRegistry]);

  return (
    <div ref={containerRef} className={RENDERMIME_MD_CLASS}>
      {renderedContent && (
        <div ref={node => node && node.appendChild(renderedContent)} />
      )}
    </div>
  );
}

export const RendermimeMarkdown = React.memo(RendermimeMarkdownBase);
