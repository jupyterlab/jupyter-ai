import React, { useEffect, useState } from 'react';
import { Box, CircularProgress, Link } from '@mui/material';

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
        This section allows you to set secrets as environment variables. Most
        language models expect an API key to be set here. See the{' '}
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
        The secrets listed below are stored in the <code>.env</code> file at the
        workspace root. These can be freely modified here or directly in the{' '}
        <code>.env</code> file.
      </p>
      <SecretsInput editableSecrets={editableSecrets} reloadSecrets={loadSecrets} />

      {/* Static secrets subsection */}
      <h3 className="jp-ai-ChatSettings-h3">Static secrets</h3>
      <p>
        The secrets listed below are set by the environment variables and/or the
        traitlets configuration passed to the <code>jupyter-lab</code> server
        process, and can only be modified by restarting the server.
      </p>
      <p>
        Contact your server administrator if these secrets need to be updated.
      </p>
      <SecretsList secrets={staticSecrets} />
    </Box>
  );
}
