import { Token } from '@lumino/coreutils';
import { ISignal } from '@lumino/signaling';
import type { IRankedMenu } from '@jupyterlab/ui-components';

export interface IJaiStatusItem {
  addItem(item: IRankedMenu.IItemOptions): void;
}

/**
 * The Jupyternaut status token.
 */
export const IJaiStatusItem = new Token<IJaiStatusItem>(
  'jupyter_ai:IJupyternautStatus',
  'Status indicator displayed in the statusbar'
);

export interface IJaiCompletionProvider {
  isEnabled(): boolean;
  settingsChanged: ISignal<IJaiCompletionProvider, void>;
}

/**
 * The inline completion provider token.
 */
export const IJaiCompletionProvider = new Token<IJaiCompletionProvider>(
  'jupyter_ai:IJaiCompletionProvider',
  'The jupyter-ai inline completion provider API'
);

/**
 * An object that describes an interaction event from the user.
 *
 * Jupyter AI natively emits 4 event types: "copy", "replace", "insert-above",
 * or "insert-below". These are all emitted by the code toolbar rendered
 * underneath code blocks in the chat sidebar.
 */
export type TelemetryEvent = {
  /**
   * Type of the interaction.
   *
   * Frontend extensions may add other event types in custom components. Custom
   * events can be emitted via the `useTelemetry()` hook.
   */
  type: 'copy' | 'replace' | 'insert-above' | 'insert-below' | string;
  /**
   * Anonymized details about the message that was interacted with.
   */
  message: {
    /**
     * ID of the message assigned by Jupyter AI.
     */
    id: string;
    /**
     * Type of the message.
     */
    type: 'human' | 'agent';
    /**
     * UNIX timestamp of the message.
     */
    time: number;
    /**
     * Metadata associated with the message, yielded by the underlying language
     * model provider.
     */
    metadata?: Record<string, unknown>;
  };
  /**
   * Anonymized details about the code block that was interacted with, if any.
   * This is left optional for custom events like message upvote/downvote that
   * do not involve interaction with a specific code block.
   */
  code?: {
    charCount: number;
    lineCount: number;
  };
};

export interface IJaiTelemetryHandler {
  onEvent: (e: TelemetryEvent) => unknown;
}

/**
 * An optional plugin that handles telemetry events emitted via user
 * interactions, when provided by a separate labextension. Not provided by
 * default.
 */
export const IJaiTelemetryHandler = new Token<IJaiTelemetryHandler>(
  'jupyter_ai:telemetry',
  'An optional plugin that handles telemetry events emitted via interactions on agent messages, when provided by a separate labextension. Not provided by default.'
);
