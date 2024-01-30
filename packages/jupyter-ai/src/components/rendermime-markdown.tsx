import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

import { CopyButton } from './copy-button';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

const BASE_MIME_TYPE = 'text/markdown';
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
      const mimeType =
        props.rmRegistry.preferredMimeType({
          BASE_MIME_TYPE: props.markdownStr
        }) || BASE_MIME_TYPE;

      const model = props.rmRegistry.createModel({
        data: { [mimeType]: props.markdownStr }
      });
      const renderer = props.rmRegistry.createRenderer(mimeType);
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
