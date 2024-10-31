import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

import { CodeToolbar, CodeToolbarProps } from './code-blocks/code-toolbar';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { AiService } from '../handler';

const MD_MIME_TYPE = 'text/markdown';
const RENDERMIME_MD_CLASS = 'jp-ai-rendermime-markdown';

type RendermimeMarkdownProps = {
  markdownStr: string;
  rmRegistry: IRenderMimeRegistry;
  /**
   * Reference to the parent message object in the Jupyter AI chat.
   */
  parentMessage?: AiService.ChatMessage;
  /**
   * Whether the message is complete. This is generally `true` except in the
   * case where `markdownStr` contains the incomplete contents of a
   * `AgentStreamMessage`, in which case this should be set to `false`.
   */
  complete: boolean;
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

/**
 * Type predicate function that determines whether a given DOM Node is a Text
 * node.
 */
function isTextNode(node: Node | null): node is Text {
  return node?.nodeType === Node.TEXT_NODE;
}

/**
 * Escapes all `$` symbols present in an HTML element except those within the
 * following elements: `pre`, `code`, `samp`, `kbd`.
 *
 * This prevents `$` symbols from being used as inline math delimiters, allowing
 * `$` symbols to be used literally to denote quantities of USD. This does not
 * escape literal `$` within elements that display their contents literally,
 * like code elements. This overrides JupyterLab's default rendering of MarkDown
 * w/ LaTeX.
 *
 * The Jupyter AI system prompt should explicitly request that the LLM not use
 * `$` as an inline math delimiter. This is the default behavior.
 */
function escapeDollarSymbols(el: HTMLElement) {
  // Get all text nodes that are not within pre, code, samp, or kbd elements
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode: node => {
      const isInSkippedElements = node.parentElement?.closest(
        'pre, code, samp, kbd'
      );
      return isInSkippedElements
        ? NodeFilter.FILTER_SKIP
        : NodeFilter.FILTER_ACCEPT;
    }
  });

  // Collect all valid text nodes in an array.
  const textNodes: Text[] = [];
  let currentNode: Node | null;
  while ((currentNode = walker.nextNode())) {
    if (isTextNode(currentNode)) {
      textNodes.push(currentNode);
    }
  }

  // Replace each `$` symbol with `\$` for each text node, unless there is
  // another `$` symbol adjacent. Examples:
  // - `$10 - $5` => `\$10 - \$5` (escaped)
  // - `$$ \infty $$` => `$$ \infty $$` (unchanged)
  textNodes.forEach(node => {
    if (node.textContent) {
      node.textContent = node.textContent.replace(/(?<!\$)\$(?!\$)/g, '\\$');
    }
  });
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
      // initialize mime model
      const mdStr = escapeLatexDelimiters(props.markdownStr);
      const model = props.rmRegistry.createModel({
        data: { [MD_MIME_TYPE]: mdStr }
      });

      // step 1: render markdown
      await renderer.renderModel(model);
      if (!renderer.node) {
        throw new Error(
          'Rendermime was unable to render Markdown content within a chat message. Please report this upstream to Jupyter AI on GitHub.'
        );
      }

      // step 2: render LaTeX via MathJax, while escaping single dollar symbols.
      escapeDollarSymbols(renderer.node);
      props.rmRegistry.latexTypesetter?.typeset(renderer.node);

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
          {
            code: preBlock.textContent || '',
            parentMessage: props.parentMessage
          }
        ]);
      });

      setCodeToolbarDefns(newCodeToolbarDefns);
    };

    renderContent();
  }, [
    props.markdownStr,
    props.complete,
    props.rmRegistry,
    props.parentMessage
  ]);

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
