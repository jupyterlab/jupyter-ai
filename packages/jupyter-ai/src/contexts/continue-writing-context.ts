import { makeObservable, observable, action } from 'mobx';

class GlobalStore {
  @observable accessToken: string = "";
  @observable bigcodeUrl: string = "";

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

}

export default new GlobalStore();
export type IGlobalStore = GlobalStore;