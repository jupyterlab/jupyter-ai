import React, { useContext, useState } from 'react';
import { IJaiTelemetryHandler } from '../tokens';

const defaultTelemetryHandler: IJaiTelemetryHandler = {
  onEvent: e => {
    /* no-op */
  }
};

const TelemetryContext = React.createContext<IJaiTelemetryHandler>(
  defaultTelemetryHandler
);

/**
 * Retrieves a reference to the current telemetry handler for Jupyter AI events
 * returned by another plugin providing the `IJaiTelemetryHandler` token. If
 * none exists, then the default telemetry handler is returned, which does
 * nothing when `onEvent()` is called.
 */
export function useTelemetry(): IJaiTelemetryHandler {
  return useContext(TelemetryContext);
}

type TelemetryContextProviderProps = {
  telemetryHandler: IJaiTelemetryHandler | null;
  children: React.ReactNode;
};

export function TelemetryContextProvider(
  props: TelemetryContextProviderProps
): JSX.Element {
  const [telemetryHandler] = useState<IJaiTelemetryHandler>(
    props.telemetryHandler ?? defaultTelemetryHandler
  );

  return (
    <TelemetryContext.Provider value={telemetryHandler}>
      {props.children}
    </TelemetryContext.Provider>
  );
}
