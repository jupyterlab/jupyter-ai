import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography
} from '@mui/material';
import LockIcon from '@mui/icons-material/Lock';

export type SecretsListProps = {
  secrets: string[];
};

/**
 * Component that renders a list of secrets. This should be used to render the
 * "static secrets" set by the traitlets configuration / environment variables
 * passed directly to the `jupyter-lab` process.
 *
 * Editable secrets should be rendered using the `<SecretsInput />` component.
 */
export function SecretsList(props: SecretsListProps): JSX.Element | null {
  if (!props.secrets || props.secrets.length === 0) {
    return null;
  }

  return (
    <List sx={{ padding: 0 }}>
      {props.secrets.map((secret, index) => (
        <ListItem
          key={secret}
          sx={{
            borderBottom:
              index < props.secrets.length - 1 ? '1px solid' : 'none',
            borderBottomColor: 'divider',
            paddingY: 1.5,
            paddingX: 2,
            '&:hover': {
              backgroundColor: 'action.hover'
            }
          }}
        >
          <ListItemIcon sx={{ minWidth: 36 }}>
            <LockIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography
                  variant="body1"
                  component="code"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    opacity: 0.618
                  }}
                >
                  {secret}
                </Typography>
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  );
}
