import { useState, useEffect, useMemo, useCallback } from 'react';
import { AiService } from '../../handler';

type ServerInfoProperties = {
  config: AiService.DescribeConfigResponse;
  lmProviders: AiService.ListProvidersResponse;
  emProviders: AiService.ListProvidersResponse;
  lmProvider: AiService.ListProvidersEntry | null;
  emProvider: AiService.ListProvidersEntry | null;
  lmLocalId: string;
};

type ServerInfoMethods = {
  refetchAll: () => Promise<void>;
  refetchApiKeys: () => Promise<void>;
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
  error: string;
};
type ServerInfoReady = { state: ServerInfoState.Ready } & ServerInfoProperties &
  ServerInfoMethods;

type ServerInfo = ServerInfoLoading | ServerInfoError | ServerInfoReady;

/**
 * A hook that fetches the current configuration and provider lists from the
 * server. Returns a `ServerInfo` object that includes methods.
 */
export function useServerInfo(): ServerInfo {
  const [state, setState] = useState<ServerInfoState>(ServerInfoState.Loading);
  const [serverInfoProps, setServerInfoProps] =
    useState<ServerInfoProperties>();
  const [error, setError] = useState<string>('');

  const fetchServerInfo = useCallback(async () => {
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
      setServerInfoProps({
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
        setError(e.toString());
      } else {
        setError('An unknown error occurred.');
      }
      setState(ServerInfoState.Error);
    }
  }, []);

  const refetchApiKeys = useCallback(async () => {
    if (!serverInfoProps) {
      // this should never happen.
      return;
    }

    const config = await AiService.getConfig();
    setServerInfoProps({
      ...serverInfoProps,
      config: {
        ...serverInfoProps.config,
        api_keys: config.api_keys,
        last_read: config.last_read
      }
    });
  }, [serverInfoProps]);

  /**
   * Effect: fetch server info on initial render
   */
  useEffect(() => {
    fetchServerInfo();
  }, []);

  return useMemo<ServerInfo>(() => {
    if (state === ServerInfoState.Loading) {
      return { state };
    }

    if (state === ServerInfoState.Error || !serverInfoProps) {
      return { state: ServerInfoState.Error, error };
    }

    return {
      state,
      ...serverInfoProps,
      refetchAll: fetchServerInfo,
      refetchApiKeys
    };
  }, [state, serverInfoProps, error, refetchApiKeys]);
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
