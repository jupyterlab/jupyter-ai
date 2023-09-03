import { makeObservable, observable, action } from 'mobx';

class CodeCompletionContextstore {
  /**
   * Whether to enable code completion function.
   */
  @observable enableCodeCompletion = false;

  /**
   * Observable huggingface token for authentication purposes.
   */
  @observable accessToken = '';

  /**
   * Observable URL for the BigCode service.
   */
  @observable bigcodeUrl = '';

  /**
   * Observable state for the code being requested for completion.
   */
  @observable codeOnRequest = '';

  /**
   * Observable string representing the shortcut key combination for triggering code completion.
   * Default is set to 'Ctrl + Space'.
   */
  @observable shortcutStr = 'Ctrl + Space';

  constructor() {
    makeObservable(this);

    const storedShortcutStr = localStorage.getItem(
      '@jupyterlab-ai/CodeCompletionState:ShortcutStr'
    );
    if (storedShortcutStr) {
      this.shortcutStr = storedShortcutStr;
    }

    const enableCodeCompletion = localStorage.getItem(
      '@jupyterlab-ai/CodeCompletionState:EnableCodeCompletion'
    );
    if (enableCodeCompletion) {
      this.enableCodeCompletion = Boolean(Number(enableCodeCompletion));
    }
  }

  @action
  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  @action
  setBigcodeUrl(url: string): void {
    this.bigcodeUrl = url;
  }

  @action
  toggleCodeCompletion(): void {
    this.enableCodeCompletion = !this.enableCodeCompletion;
    localStorage.setItem(
      '@jupyterlab-ai/CodeCompletionState:EnableCodeCompletion',
      `${+this.enableCodeCompletion}`
    );
  }

  @action
  setCodeOnRequest(code: string): void {
    this.codeOnRequest = code;
  }

  @action
  setShortcutStr(shortcutStr: string): void {
    localStorage.setItem(
      '@jupyterlab-ai/CodeCompletionState:ShortcutStr',
      shortcutStr
    );
    this.shortcutStr = shortcutStr;
  }
}

export default new CodeCompletionContextstore();
export type IGlobalStore = CodeCompletionContextstore;
