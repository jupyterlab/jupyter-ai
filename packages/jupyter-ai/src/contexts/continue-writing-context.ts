import { makeObservable, observable, action } from 'mobx';

class GlobalStore {
  @observable accessToken = '';
  @observable bigcodeUrl = '';
  @observable codeOnRequest = '';
  @observable shortcutStr = 'Ctrl + Space';

  constructor() {
    makeObservable(this);
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
  setShortcutStr(keyDownStr: string): void {
    this.shortcutStr = keyDownStr;
  }
}

export default new GlobalStore();
export type IGlobalStore = GlobalStore;
