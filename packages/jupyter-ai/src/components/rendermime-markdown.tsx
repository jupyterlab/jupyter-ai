import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';

import { CodeToolbar, CodeToolbarProps } from './code-blocks/code-toolbar';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

const MD_MIME_TYPE = 'text/markdown';
const RENDERMIME_MD_CLASS = 'jp-ai-rendermime-markdown';

type RendermimeMarkdownProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
};

/**
 * Takes \( and returns \\(. Escapes LaTeX delimeters by adding extra backslashes where needed for proper rendering by @jupyterlab/rendermime.
 */
function escapeLatexDelimiters(text: string) {
  return text
    .replace(/\\\(/g, '\\\\(')
    .replace(/\\\)/g, '\\\\)')
    .replace(/\\\[/g, '\\\\[')
    .replace(/\\\]/g, '\\\\]');
}

function RendermimeMarkdownBase(props: RendermimeMarkdownProps): JSX.Element {
  const [renderedContent, setRenderedContent] = useState<HTMLElement | null>(
    null
  );

  // each element is a two-tuple with the structure [codeToolbarRoot, codeToolbarProps].
  const [codeToolbarDefns, setCodeToolbarDefns] = useState<
    Array<[HTMLDivElement, CodeToolbarProps]>
  >([]);

  useEffect(() => {
    const renderContent = async () => {
      const mdStr = escapeLatexDelimiters(props.markdownStr);
      const model = props.rmRegistry.createModel({
        data: { [MD_MIME_TYPE]: mdStr }
      });

      const renderer = props.rmRegistry.createRenderer(MD_MIME_TYPE);
      await renderer.renderModel(model);
      props.rmRegistry.latexTypesetter?.typeset(renderer.node);
      if (!renderer.node) {
        throw new Error(
          'Rendermime was unable to render Markdown content within a chat message. Please report this upstream to Jupyter AI on GitHub.'
        );
      }

      const newCodeToolbarDefns: [HTMLDivElement, CodeToolbarProps][] = [];

      // Attach CodeToolbar root element to each <pre> block
      const preBlocks = renderer.node.querySelectorAll('pre');
      preBlocks.forEach(preBlock => {
        const codeToolbarRoot = document.createElement('div');
        preBlock.parentNode?.insertBefore(
          codeToolbarRoot,
          preBlock.nextSibling
        );
        newCodeToolbarDefns.push([
          codeToolbarRoot,
          { content: preBlock.textContent || '' }
        ]);
      });

      setCodeToolbarDefns(newCodeToolbarDefns);
      setRenderedContent(renderer.node);
    };

    renderContent();
  }, [props.markdownStr, props.rmRegistry]);

  return (
    <div className={RENDERMIME_MD_CLASS}>
      {renderedContent && (
        <div ref={node => node && node.appendChild(renderedContent)} />
      )}
      {
        // Render a `CodeToolbar` element underneath each code block.
        // We use ReactDOM.createPortal() so each `CodeToolbar` element is able
        // to use the context in the main React tree.
        codeToolbarDefns.map(codeToolbarDefn => {
          const [codeToolbarRoot, codeToolbarProps] = codeToolbarDefn;
          return createPortal(
            <CodeToolbar {...codeToolbarProps} />,
            codeToolbarRoot
          );
        })
      }
    </div>
  );
}

export const RendermimeMarkdown = React.memo(RendermimeMarkdownBase);
