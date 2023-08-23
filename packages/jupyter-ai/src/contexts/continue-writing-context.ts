import { makeObservable, observable, action } from 'mobx';

class GlobalStore {
  @observable accessToken: string = "";
  @observable bigcodeUrl: string = "";
  @observable codeOnRequest: string = "";
  @observable isRequest: boolean = false;

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
  changeIsRequest(): void {
    this.isRequest = !this.isRequest;
  }

}

export default new GlobalStore();
export type IGlobalStore = GlobalStore;