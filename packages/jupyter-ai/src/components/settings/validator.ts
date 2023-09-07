import { AiService } from '../../handler';

export class SettingsValidator {
  constructor(
    protected lmProviders: AiService.ListProvidersResponse,
    protected emProviders: AiService.ListProvidersResponse
  ) {}
}
