import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

import { CodeToolbar, CodeToolbarProps } from './code-blocks/code-toolbar';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

const MD_MIME_TYPE = 'text/markdown';
const RENDERMIME_MD_CLASS = 'jp-ai-rendermime-markdown';

type RendermimeMarkdownProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
  /**
   * Whether the message is complete. This is generally `true` except in the
   * case where `markdownStr` contains the incomplete contents of a
   * `AgentStreamMessage`, in which case this should be set to `false`.
   */
  complete: boolean;
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
  // create a single renderer object at component mount
  const [renderer] = useState(() => {
    return props.rmRegistry.createRenderer(MD_MIME_TYPE);
  });

  // ref that tracks the content container to store the rendermime node in
  const renderingContainer = useRef<HTMLDivElement | null>(null);
  // ref that tracks whether the rendermime node has already been inserted
  const renderingInserted = useRef<boolean>(false);

  // each element is a two-tuple with the structure [codeToolbarRoot, codeToolbarProps].
  const [codeToolbarDefns, setCodeToolbarDefns] = useState<
    Array<[HTMLDivElement, CodeToolbarProps]>
  >([]);

  /**
   * Effect: use Rendermime to render `props.markdownStr` into an HTML element,
   * and insert it into `renderingContainer` if not yet inserted. When the
   * message is completed, add code toolbars.
   */
  useEffect(() => {
    const renderContent = async () => {
      const mdStr = escapeLatexDelimiters(props.markdownStr);
      const model = props.rmRegistry.createModel({
        data: { [MD_MIME_TYPE]: mdStr }
      });

      await renderer.renderModel(model);
      props.rmRegistry.latexTypesetter?.typeset(renderer.node);
      if (!renderer.node) {
        throw new Error(
          'Rendermime was unable to render Markdown content within a chat message. Please report this upstream to Jupyter AI on GitHub.'
        );
      }

      // insert the rendering into renderingContainer if not yet inserted
      if (renderingContainer.current !== null && !renderingInserted.current) {
        renderingContainer.current.appendChild(renderer.node);
        renderingInserted.current = true;
      }

      // if complete, render code toolbars
      if (!props.complete) {
        return;
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
    };

    renderContent();
  }, [props.markdownStr, props.complete, props.rmRegistry]);

  return (
    <div className={RENDERMIME_MD_CLASS}>
      <div ref={renderingContainer} />
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
