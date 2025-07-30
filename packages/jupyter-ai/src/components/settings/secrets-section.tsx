import React, { useEffect, useState } from 'react';
import { Alert, Box, CircularProgress, Link } from '@mui/material';

import { AiService } from '../../handler';
import { useStackingAlert } from '../mui-extras/stacking-alert';
import { SecretsInput } from './secrets-input';
import { SecretsList } from './secrets-list';

/**
 * Renders the "Secrets" section in the Jupyter AI settings.
 *
 * - Editable secrets (stored in `.env` by default) are rendered by the
 * `<SecretsInput />` component.
 *
 * - Static secrets are rendered by the `<SecretsList />` component.
 */
export function SecretsSection(): JSX.Element {
  const [editableSecrets, setEditableSecrets] = useState<string[]>([]);
  const [staticSecrets, setStaticSecrets] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const errorAlert = useStackingAlert();

  const loadSecrets = async () => {
    try {
      setLoading(true);
      const secrets = await AiService.listSecrets();
      setEditableSecrets(secrets.editable_secrets);
      setStaticSecrets(secrets.static_secrets);
      setError(false);
    } catch (error) {
      setError(true);
      errorAlert.show('error', error as unknown as any);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Effect: Fetch the secrets via the Secrets REST API on initial render.
   */
  useEffect(() => {
    loadSecrets();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', padding: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return <Box>{errorAlert.jsx}</Box>;
  }

  return (
    <Box>
      {/* Editable secrets subsection */}
      <p>
        This section shows the secrets set in the <code>.env</code> file at the
        workspace root. For most chat models, an API key secret in{' '}
        <code>.env</code> is required for Jupyternaut to reply in the chat. See
        the{' '}
        <Link
          href="https://docs.litellm.ai/docs/providers"
          target="_blank"
          rel="noopener noreferrer"
        >
          documentation
        </Link>{' '}
        for information on which API key is required for your model provider.
      </p>
      <p>
        Click "Add secret" to add a secret to the <code>.env</code> file.
        Secrets can also be updated by editing the <code>.env</code> file
        directly in JupyterLab.
      </p>
      <SecretsInput
        editableSecrets={editableSecrets}
        reloadSecrets={loadSecrets}
      />

      {/* Static secrets subsection */}
      {staticSecrets && (
        <Alert severity="info">
          <p style={{ marginTop: 0 }}>
            The secrets below are set by the environment variables and the
            traitlets configuration passed to the server process. These secrets
            can only be changed either upon restarting the server or by
            contacting your server administrator.
          </p>
          <SecretsList secrets={staticSecrets} />
        </Alert>
      )}
    </Box>
  );
}
