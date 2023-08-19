import { useState, useEffect, useMemo } from 'react';
import { AiService } from '../../handler';

export type ServerInfo = {
  config: AiService.DescribeConfigResponse;
  lmProviders: AiService.ListProvidersResponse;
  emProviders: AiService.ListProvidersResponse;
  lmProvider: AiService.ListProvidersEntry | null;
  emProvider: AiService.ListProvidersEntry | null;
  lmLocalId: string;
};

export enum ServerInfoState {
  /**
   * Server info is being fetched.
   */
  Loading,
  /**
   * Unable to retrieve server info.
   */
  Error,
  /**
   * Server info was loaded successfully.
   */
  Ready
}

type ServerInfoLoading = { state: ServerInfoState.Loading };
type ServerInfoError = {
  state: ServerInfoState.Error;
  error?: string;
};
type ServerInfoReady = { state: ServerInfoState.Ready } & ServerInfo;

type UseServerInfoReturn =
  | ServerInfoLoading
  | ServerInfoError
  | ServerInfoReady;

/**
 * A hook that fetches the current configuration and provider lists from the
 * server. The status of the network request is expressed in `serverInfo.state`.
 */
export function useServerInfo(): UseServerInfoReturn {
  const [state, setState] = useState<ServerInfoState>(ServerInfoState.Loading);
  const [serverInfo, setServerInfo] = useState<ServerInfo>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    async function getConfig() {
      try {
        const [config, lmProviders, emProviders] = await Promise.all([
          AiService.getConfig(),
          AiService.listLmProviders(),
          AiService.listEmProviders()
        ]);
        const lmGid = config.model_provider_id;
        const emGid = config.embeddings_provider_id;
        const lmProvider =
          lmGid === null ? null : getProvider(lmGid, lmProviders);
        const emProvider =
          emGid === null ? null : getProvider(emGid, emProviders);
        const lmLocalId = lmGid === null ? '' : getLocalId(lmGid);
        setServerInfo({
          config,
          lmProviders,
          emProviders,
          lmProvider,
          emProvider,
          lmLocalId
        });

        setState(ServerInfoState.Ready);
      } catch (e) {
        console.error(e);
        if (e instanceof Error) {
          setError(e.message);
        }
        setState(ServerInfoState.Error);
      }
    }
    getConfig();
  }, []);

  return useMemo<UseServerInfoReturn>(() => {
    if (state === ServerInfoState.Loading) {
      return { state };
    }

    if (state === ServerInfoState.Error || !serverInfo) {
      return { state: ServerInfoState.Error, error };
    }

    return {
      state,
      ...serverInfo
    };
  }, [state, serverInfo, error]);
}

function getProvider(
  gid: string,
  providers: AiService.ListProvidersResponse
): AiService.ListProvidersEntry | null {
  const providerId = getProviderId(gid);
  const provider = providers.providers.find(p => p.id === providerId);
  return provider ?? null;
}

function getProviderId(gid: string) {
  if (!gid) {
    return null;
  }

  const components = gid.split(':');
  if (components.length < 2) {
    return null;
  }

  return components[0];
}

function getLocalId(gid: string) {
  const components = gid.split(':');
  if (components.length < 2) {
    return '';
  }

  return components[1];
}
