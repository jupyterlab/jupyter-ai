import { makeObservable, observable, action } from 'mobx';

class CodeCompletionContextstore {
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

    const storedShortcutStr = localStorage.getItem('shortcutStr');
    if (storedShortcutStr) {
      this.shortcutStr = storedShortcutStr;
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
  setCodeOnRequest(code: string): void {
    this.codeOnRequest = code;
  }

  @action
  setShortcutStr(shortcutStr: string): void {
    localStorage.setItem('shortcutStr', shortcutStr);
    this.shortcutStr = shortcutStr;
  }
}

export default new CodeCompletionContextstore();
export type IGlobalStore = CodeCompletionContextstore;
