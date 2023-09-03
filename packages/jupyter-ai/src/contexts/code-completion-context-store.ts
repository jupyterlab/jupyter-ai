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

  /**
   * Maximum prompt tokens when requested
   */
  @observable maxPromptToken = 400;

  /**
   * Maximum response tokens when requested
   */
  @observable maxResponseToken = 20;

  constructor() {
    makeObservable(this);

    const dataPersistenceStr = localStorage.getItem(
      '@jupyterlab-ai/CodeCompletionState'
    );

    if (dataPersistenceStr) {
      const dataPersistence: IGlobalStore = JSON.parse(dataPersistenceStr);
      this.enableCodeCompletion = dataPersistence.enableCodeCompletion;
      this.bigcodeUrl = dataPersistence.bigcodeUrl;
      this.shortcutStr = dataPersistence.shortcutStr;
      this.maxPromptToken = dataPersistence.maxPromptToken;
      this.maxResponseToken = dataPersistence.maxResponseToken;
    }
  }

  saveDataToLoaclStorage() {
    // Do not store sensitive information
    localStorage.setItem(
      '@jupyterlab-ai/CodeCompletionState',
      JSON.stringify({
        enableCodeCompletion: this.enableCodeCompletion,
        bigcodeUrl: this.bigcodeUrl,
        shortcutStr: this.shortcutStr,
        maxPromptToken: this.maxPromptToken,
        maxResponseToken: this.maxResponseToken
      })
    );
  }

  @action
  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  @action
  setBigcodeUrl(url: string): void {
    this.bigcodeUrl = url;
    this.saveDataToLoaclStorage();
  }

  @action
  toggleCodeCompletion(): void {
    this.enableCodeCompletion = !this.enableCodeCompletion;
    this.saveDataToLoaclStorage();
  }

  @action
  setCodeOnRequest(code: string): void {
    this.codeOnRequest = code;
  }

  @action
  setShortcutStr(shortcutStr: string): void {
    this.shortcutStr = shortcutStr;
    this.saveDataToLoaclStorage();
  }

  @action
  setMaxPromptTokens(newValue: number): void {
    this.maxPromptToken = newValue;
    this.saveDataToLoaclStorage();
  }

  @action
  setMaxResponseTokens(newValue: number): void {
    this.maxResponseToken = newValue;
    this.saveDataToLoaclStorage();
  }
}

export default new CodeCompletionContextstore();
export type IGlobalStore = CodeCompletionContextstore;
