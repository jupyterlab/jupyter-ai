import React, { useState, useEffect, useRef } from 'react';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

const MD_MIME_TYPE = 'text/markdown';
const RENDERMIME_MD_CLASS = 'jp-ai-rendermime-markdown';

type RendermimeMarkdownProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
};

/**
 * Escapes backslashes in LaTeX delimiters such that they appear in the DOM
 * after the initial MarkDown render. For example, this function takes '\(` and
 * returns `\\(`.
 *
 * Required for proper rendering of MarkDown + LaTeX markup in the chat by
 * `ILatexTypesetter`.
 */
function escapeLatexDelimiters(text: string) {
  return text
    .replace(/\\\(/g, '\\\\(')
    .replace(/\\\)/g, '\\\\)')
    .replace(/\\\[/g, '\\\\[')
    .replace(/\\\]/g, '\\\\]');
}

export function RendermimeMarkdown(
  props: RendermimeMarkdownProps
): JSX.Element {
  // create a single renderer object at component mount
  const [renderer] = useState(() => {
    return props.rmRegistry.createRenderer(MD_MIME_TYPE);
  });

  // ref that tracks the content container to store the rendermime node in
  const renderingContainer = useRef<HTMLDivElement | null>(null);
  // ref that tracks whether the rendermime node has already been inserted
  const renderingInserted = useRef<boolean>(false);

  /**
   * Effect: use Rendermime to render `props.markdownStr` into an HTML element,
   * and insert it into `renderingContainer` if not yet inserted.
   */
  useEffect(() => {
    const renderContent = async () => {
      // initialize mime model
      const mdStr = escapeLatexDelimiters(props.markdownStr);
      const model = props.rmRegistry.createModel({
        data: { [MD_MIME_TYPE]: mdStr }
      });

      // step 1: render markdown
      await renderer.renderModel(model);
      if (!renderer.node) {
        throw new Error(
          'Rendermime was unable to render Markdown content. Please report this upstream to Jupyter AI on GitHub.'
        );
      }

      // step 2: render LaTeX via MathJax
      props.rmRegistry.latexTypesetter?.typeset(renderer.node);

      // insert the rendering into renderingContainer if not yet inserted
      if (renderingContainer.current !== null && !renderingInserted.current) {
        renderingContainer.current.appendChild(renderer.node);
        renderingInserted.current = true;
      }
    };

    renderContent();
  }, [props.markdownStr]);

  return (
    <div className={RENDERMIME_MD_CLASS}>
      <div ref={renderingContainer} />
    </div>
  );
}
