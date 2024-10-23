import {
  AutocompleteCommand,
  IAutocompletionCommandsProps
} from '@jupyter/chat';
import {
  Download,
  FindInPage,
  Help,
  MoreHoriz,
  MenuBook,
  School,
  HideSource,
  AutoFixNormal
} from '@mui/icons-material';
import { Box, Typography } from '@mui/material';
import React from 'react';
import { AiService } from './handler';

type SlashCommandOption = AutocompleteCommand & {
  id: string;
  description: string;
};

/**
 * List of icons per slash command, shown in the autocomplete popup.
 *
 * This list of icons should eventually be made configurable. However, it is
 * unclear whether custom icons should be defined within a Lumino plugin (in the
 * frontend) or served from a static server route (in the backend).
 */
const DEFAULT_SLASH_COMMAND_ICONS: Record<string, JSX.Element> = {
  ask: <FindInPage />,
  clear: <HideSource />,
  export: <Download />,
  fix: <AutoFixNormal />,
  generate: <MenuBook />,
  help: <Help />,
  learn: <School />,
  unknown: <MoreHoriz />
};

/**
 * Renders an option shown in the slash command autocomplete.
 */
function renderSlashCommandOption(
  optionProps: React.HTMLAttributes<HTMLLIElement>,
  option: SlashCommandOption
): JSX.Element {
  const icon =
    option.id in DEFAULT_SLASH_COMMAND_ICONS
      ? DEFAULT_SLASH_COMMAND_ICONS[option.id]
      : DEFAULT_SLASH_COMMAND_ICONS.unknown;

  return (
    <li {...optionProps}>
      <Box sx={{ lineHeight: 0, marginRight: 4, opacity: 0.618 }}>{icon}</Box>
      <Box sx={{ flexGrow: 1 }}>
        <Typography
          component="span"
          sx={{
            fontSize: 'var(--jp-ui-font-size1)'
          }}
        >
          {option.label}
        </Typography>
        <Typography
          component="span"
          sx={{ opacity: 0.618, fontSize: 'var(--jp-ui-font-size0)' }}
        >
          {' — ' + option.description}
        </Typography>
      </Box>
    </li>
  );
}

/**
 * The autocompletion command properties to add to the registry.
 */
export const autocompletion: IAutocompletionCommandsProps = {
  opener: '/',
  commands: async () => {
    const slashCommands = (await AiService.listSlashCommands()).slash_commands;
    return slashCommands.map<SlashCommandOption>(slashCommand => ({
      id: slashCommand.slash_id,
      label: '/' + slashCommand.slash_id + ' ',
      description: slashCommand.description
    }));
  },
  props: {
    renderOption: renderSlashCommandOption
  }
};
