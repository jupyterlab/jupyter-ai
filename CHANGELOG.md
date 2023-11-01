# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 2.4.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@2.3.0...92dab10608ea090b6bd87ca5ffe9ccff7a15b449))

Hey Jupyternauts! We're excited to announce the 2.4.0 release of Jupyter AI, which includes better support for Bedrock Anthropic models. Thanks to [@krassowski](https://github.com/krassowski) for providing a new feature in Jupyter AI that let's admins specify allowlists and blocklists to filter the list of providers available in the chat settings panel.

### Enhancements made

- Allow to define block and allow lists for providers [#415](https://github.com/jupyterlab/jupyter-ai/pull/415) ([@krassowski](https://github.com/krassowski))

### Bugs fixed

- Refactor generate for better stability with all providers/models [#407](https://github.com/jupyterlab/jupyter-ai/pull/407) ([@3coins](https://github.com/3coins))

### Maintenance and upkeep improvements

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-10-09&to=2023-10-24&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-10-09..2023-10-24&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Akrassowski+updated%3A2023-10-09..2023-10-24&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Apre-commit-ci+updated%3A2023-10-09..2023-10-24&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 2.3.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@2.2.0...7f854007263f1a9393e41611028d7cc57313c577))

Hey Jupyternauts! We're excited to announce the 2.3.0 release of Jupyter AI, which includes better support for Anthropic models and integration with Amazon Bedrock.

There is also a significant change to how Jupyter AI settings are handled (see #353). The most significant changes are:

1. **API key values can no longer be read from the client.** This was taken as a security measure to prevent accidental leakage of keys. You can still update existing API keys if you do decide to change your key in the future.
1. **The settings can not be updated if they were updated by somebody else after you opened the settings panel.** This prevents different users connecting to the same server from clobbering updates from each other.
1. **There is now a much better UI for updating and deleting API keys.** We hope you enjoy it.

Updating to 2.3.0 shouldn't require any changes on your end. However, if you notice an error, please submit a bug report with the server logs emitted in the terminal from the `jupyter lab` process. Renaming the config file `$JUPYTER_DATA_DIR/jupyter_ai/config.json` to some other name and then restarting `jupyter lab` may fix the issue if it is a result of the new config changes.

### Enhancements made

- Adds chat anthropic provider, new models [#391](https://github.com/jupyterlab/jupyter-ai/pull/391) ([@3coins](https://github.com/3coins))
- Adds help text for registry model providers in chat UI settings [#373](https://github.com/jupyterlab/jupyter-ai/pull/373) ([@JasonWeill](https://github.com/JasonWeill))
- jupyter_ai and jupyter_ai_magics version match [#367](https://github.com/jupyterlab/jupyter-ai/pull/367) ([@JasonWeill](https://github.com/JasonWeill))
- Config V2 [#353](https://github.com/jupyterlab/jupyter-ai/pull/353) ([@dlqqq](https://github.com/dlqqq))
- Add E2E tests [#350](https://github.com/jupyterlab/jupyter-ai/pull/350) ([@andrii-i](https://github.com/andrii-i))

### Bugs fixed

- Upgraded LangChain, fixed prompts for Bedrock [#401](https://github.com/jupyterlab/jupyter-ai/pull/401) ([@3coins](https://github.com/3coins))
- Adds chat anthropic provider, new models [#391](https://github.com/jupyterlab/jupyter-ai/pull/391) ([@3coins](https://github.com/3coins))

### Maintenance and upkeep improvements

- Upgraded LangChain, fixed prompts for Bedrock [#401](https://github.com/jupyterlab/jupyter-ai/pull/401) ([@3coins](https://github.com/3coins))
- Add E2E tests [#350](https://github.com/jupyterlab/jupyter-ai/pull/350) ([@andrii-i](https://github.com/andrii-i))

### Documentation improvements

- jupyter_ai and jupyter_ai_magics version match [#367](https://github.com/jupyterlab/jupyter-ai/pull/367) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-09-05&to=2023-10-09&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-09-05..2023-10-09&type=Issues) | [@andrii-i](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aandrii-i+updated%3A2023-09-05..2023-10-09&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-09-05..2023-10-09&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-09-05..2023-10-09&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Akrassowski+updated%3A2023-09-05..2023-10-09&type=Issues)

## 2.2.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@2.1.0...56c1f518afd09d0d09a43221f0767aa961e9430f))

### Enhancements made

- Loads vector store index lazily [#374](https://github.com/jupyterlab/jupyter-ai/pull/374) ([@3coins](https://github.com/3coins))
- Added alias for bedrock titan model [#368](https://github.com/jupyterlab/jupyter-ai/pull/368) ([@3coins](https://github.com/3coins))
- Update README, docs [#347](https://github.com/jupyterlab/jupyter-ai/pull/347) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- fix newline typo in improve_code [#364](https://github.com/jupyterlab/jupyter-ai/pull/364) ([@michaelchia](https://github.com/michaelchia))

### Maintenance and upkeep improvements

- Upgrades LangChain to 0.0.277 [#375](https://github.com/jupyterlab/jupyter-ai/pull/375) ([@3coins](https://github.com/3coins))
- relax pinning on importlib_metadata, typing_extensions [#363](https://github.com/jupyterlab/jupyter-ai/pull/363) ([@minrk](https://github.com/minrk))

### Documentation improvements

- Remove front end unit tests from code and README.md [#371](https://github.com/jupyterlab/jupyter-ai/pull/371) ([@andrii-i](https://github.com/andrii-i))
- Update README, docs [#347](https://github.com/jupyterlab/jupyter-ai/pull/347) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-08-15&to=2023-09-05&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-08-15..2023-09-05&type=Issues) | [@andrii-i](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aandrii-i+updated%3A2023-08-15..2023-09-05&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-08-15..2023-09-05&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Akrassowski+updated%3A2023-08-15..2023-09-05&type=Issues) | [@michaelchia](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Amichaelchia+updated%3A2023-08-15..2023-09-05&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aminrk+updated%3A2023-08-15..2023-09-05&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-08-15..2023-09-05&type=Issues)

## 2.1.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@2.0.1...c689c6c0cce5212238943ec2ff1559f6ad2f63d5))

### Enhancements made

- Add new 0613 GPT-3.5 and GPT-4 models [#337](https://github.com/jupyterlab/jupyter-ai/pull/337) ([@bjornjorgensen](https://github.com/bjornjorgensen))
- howto add key [#330](https://github.com/jupyterlab/jupyter-ai/pull/330) ([@bjornjorgensen](https://github.com/bjornjorgensen))
- Azure OpenAI and OpenAI proxy support [#322](https://github.com/jupyterlab/jupyter-ai/pull/322) ([@dlqqq](https://github.com/dlqqq))
- Add GPT4All local provider [#209](https://github.com/jupyterlab/jupyter-ai/pull/209) ([@krassowski](https://github.com/krassowski))

### Documentation improvements

- Update README.md [#338](https://github.com/jupyterlab/jupyter-ai/pull/338) ([@3coins](https://github.com/3coins))
- howto add key [#330](https://github.com/jupyterlab/jupyter-ai/pull/330) ([@bjornjorgensen](https://github.com/bjornjorgensen))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-08-08&to=2023-08-15&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-08-08..2023-08-15&type=Issues) | [@anammari](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aanammari+updated%3A2023-08-08..2023-08-15&type=Issues) | [@bjornjorgensen](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Abjornjorgensen+updated%3A2023-08-08..2023-08-15&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-08-08..2023-08-15&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-08-08..2023-08-15&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Akrassowski+updated%3A2023-08-08..2023-08-15&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-08-08..2023-08-15&type=Issues)

## 2.0.1

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@2.0.0...f38d7f4a5b38ae1583c97bc8a0bb58ab09cdabdd))

### Enhancements made

- add claude 2 to anthropic models [#314](https://github.com/jupyterlab/jupyter-ai/pull/314) ([@jmkuebler](https://github.com/jmkuebler))
- Prompt template override in BaseProvider [#309](https://github.com/jupyterlab/jupyter-ai/pull/309) ([@JasonWeill](https://github.com/JasonWeill))
- Updates docs to refer to JupyterLab versions [#300](https://github.com/jupyterlab/jupyter-ai/pull/300) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- handle IDPs that don't return initials [#316](https://github.com/jupyterlab/jupyter-ai/pull/316) ([@dlqqq](https://github.com/dlqqq))
- Handles /clear command with selection [#307](https://github.com/jupyterlab/jupyter-ai/pull/307) ([@JasonWeill](https://github.com/JasonWeill))

### Maintenance and upkeep improvements

### Documentation improvements

- Updates docs to refer to JupyterLab versions [#300](https://github.com/jupyterlab/jupyter-ai/pull/300) ([@JasonWeill](https://github.com/JasonWeill))

### Other merged PRs

- Update magics.ipynb [#320](https://github.com/jupyterlab/jupyter-ai/pull/320) ([@eltociear](https://github.com/eltociear))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-07-27&to=2023-08-08&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-07-27..2023-08-08&type=Issues) | [@eltociear](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aeltociear+updated%3A2023-07-27..2023-08-08&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-07-27..2023-08-08&type=Issues) | [@jmkuebler](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Ajmkuebler+updated%3A2023-07-27..2023-08-08&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Apre-commit-ci+updated%3A2023-07-27..2023-08-08&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-07-27..2023-08-08&type=Issues)

This is currently the latest major version, and supports exclusively JupyterLab 4.

Existing users who are unable to migrate to JupyterLab 3 immediately should use v1.x. However, feature releases and bug fixes will only be backported to v1.x as we deem necessary, so we highly encourage existing Jupyter AI users to migrate to JupyterLab 4 and Jupyter AI v2 as soon as possible to enjoy all of the latest features we are currently developing.

Thank you all for your support of Jupyter AI! 🎉

## 2.0.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@1.0.0...4ad7fa695b89abc0df4d510f20e9036b6907fd51))

### Enhancements made

- Upgrade to JupyterLab 4 [#296](https://github.com/jupyterlab/jupyter-ai/pull/296) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-07-27&to=2023-07-27&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-07-27..2023-07-27&type=Issues)

## 1.0.0

This release serves exclusively to dedicate a major version to the 1.x branch providing JupyterLab 3 support.

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.10.1...0afca1c387e19a9da1f31080a69d8a16e71a310b))

### Enhancements made

- Chat help message on load [#277](https://github.com/jupyterlab/jupyter-ai/pull/277) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-07-21&to=2023-07-27&type=c))

[@andrii-i](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aandrii-i+updated%3A2023-07-21..2023-07-27&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-07-21..2023-07-27&type=Issues)

## 0.10.1

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.10.0...4049084fc1c62bc00bdd2eeddd1b4630094a5a57))

### Bugs fixed

- fix /learn TypeError [#286](https://github.com/jupyterlab/jupyter-ai/pull/286) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-07-18&to=2023-07-21&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-07-18..2023-07-21&type=Issues)

## 0.10.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.9.0...70725c0ff9b5eb313294bdab6e3ff183a6aad88b))

### Enhancements made

- Allows specifying chunk size and overlap with /learn [#267](https://github.com/jupyterlab/jupyter-ai/pull/267) ([@3coins](https://github.com/3coins))
- Added Bedrock provider [#263](https://github.com/jupyterlab/jupyter-ai/pull/263) ([@3coins](https://github.com/3coins))
- Validate JSON for request schema [#261](https://github.com/jupyterlab/jupyter-ai/pull/261) ([@JasonWeill](https://github.com/JasonWeill))
- Updates docs with reset, model lists [#254](https://github.com/jupyterlab/jupyter-ai/pull/254) ([@JasonWeill](https://github.com/JasonWeill))
- Migrate to Dask [#244](https://github.com/jupyterlab/jupyter-ai/pull/244) ([@dlqqq](https://github.com/dlqqq))

### Bugs fixed

- Sets font color for intro text [#265](https://github.com/jupyterlab/jupyter-ai/pull/265) ([@JasonWeill](https://github.com/JasonWeill))
- Added Bedrock provider [#263](https://github.com/jupyterlab/jupyter-ai/pull/263) ([@3coins](https://github.com/3coins))

### Maintenance and upkeep improvements

### Documentation improvements

- Updates docs with reset, model lists [#254](https://github.com/jupyterlab/jupyter-ai/pull/254) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-07-05&to=2023-07-18&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-07-05..2023-07-18&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-07-05..2023-07-18&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-07-05..2023-07-18&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Apre-commit-ci+updated%3A2023-07-05..2023-07-18&type=Issues)

## 0.9.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.8.0...b62c8160f8e078fe8f7145be4d12c7982d9eafdb))

### Bugs fixed

- Fixes "replace selection" behavior when nothing is selected [#251](https://github.com/jupyterlab/jupyter-ai/pull/251) ([@JasonWeill](https://github.com/JasonWeill))
- Adds __str__ method for TextWithMetadata [#250](https://github.com/jupyterlab/jupyter-ai/pull/250) ([@JasonWeill](https://github.com/JasonWeill))
- Fix settings update and vertical scroll [#249](https://github.com/jupyterlab/jupyter-ai/pull/249) ([@3coins](https://github.com/3coins))
- Truncate chat history to last 2 conversations [#240](https://github.com/jupyterlab/jupyter-ai/pull/240) ([@3coins](https://github.com/3coins))

### Maintenance and upkeep improvements

- Use pre-commit [#237](https://github.com/jupyterlab/jupyter-ai/pull/237) ([@dlqqq](https://github.com/dlqqq))
- Removes unused dialog code [#234](https://github.com/jupyterlab/jupyter-ai/pull/234) ([@JasonWeill](https://github.com/JasonWeill))
- Change sagemaker example to make more sense [#231](https://github.com/jupyterlab/jupyter-ai/pull/231) ([@JasonWeill](https://github.com/JasonWeill))
- add JS lint workflow [#230](https://github.com/jupyterlab/jupyter-ai/pull/230) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-06-16&to=2023-07-05&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-06-16..2023-07-05&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-06-16..2023-07-05&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-06-16..2023-07-05&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Apre-commit-ci+updated%3A2023-06-16..2023-07-05&type=Issues)

## 0.8.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.7.3...4169ebf0274b177573dce43197d2c2e5169fc71b))

### Enhancements made

- Support SageMaker Endpoints in chat [#197](https://github.com/jupyterlab/jupyter-ai/pull/197) ([@dlqqq](https://github.com/dlqqq))
- Migrate to click [#188](https://github.com/jupyterlab/jupyter-ai/pull/188) ([@dlqqq](https://github.com/dlqqq))
- Adds %ai error magic command to explain the most recent error [#170](https://github.com/jupyterlab/jupyter-ai/pull/170) ([@JasonWeill](https://github.com/JasonWeill))
- Register, update, and delete aliases [#136](https://github.com/jupyterlab/jupyter-ai/pull/136) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- Only attempt re-connect on abnormal closure [#222](https://github.com/jupyterlab/jupyter-ai/pull/222) ([@3coins](https://github.com/3coins))
- Update system prompt [#221](https://github.com/jupyterlab/jupyter-ai/pull/221) ([@JasonWeill](https://github.com/JasonWeill))
- Fixes double call to cell help command [#220](https://github.com/jupyterlab/jupyter-ai/pull/220) ([@JasonWeill](https://github.com/JasonWeill))
- Creates a new websocket connection in case of disconnect [#219](https://github.com/jupyterlab/jupyter-ai/pull/219) ([@3coins](https://github.com/3coins))
- SageMaker endpoint magic command support [#215](https://github.com/jupyterlab/jupyter-ai/pull/215) ([@JasonWeill](https://github.com/JasonWeill))
- Removes comment from magic command [#213](https://github.com/jupyterlab/jupyter-ai/pull/213) ([@JasonWeill](https://github.com/JasonWeill))

### Maintenance and upkeep improvements

- Added python version to release action [#223](https://github.com/jupyterlab/jupyter-ai/pull/223) ([@3coins](https://github.com/3coins))
- Pinning python version to 3.10.x [#212](https://github.com/jupyterlab/jupyter-ai/pull/212) ([@3coins](https://github.com/3coins))

### Documentation improvements

- Add documentation for running magics in remote kernels [#196](https://github.com/jupyterlab/jupyter-ai/pull/196) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-05-26&to=2023-06-16&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-05-26..2023-06-16&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-05-26..2023-06-16&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-05-26..2023-06-16&type=Issues)

## 0.7.3

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.7.2...241f58adf8d52d68c8c57fed6a04cbcd558f17bc))

### Enhancements made

- Additional docs fix for 3.8 support [#185](https://github.com/jupyterlab/jupyter-ai/pull/185) ([@JasonWeill](https://github.com/JasonWeill))
- Drops support for Python 3.7, mandates 3.8 or later [#184](https://github.com/jupyterlab/jupyter-ai/pull/184) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- SageMaker Studio support [#192](https://github.com/jupyterlab/jupyter-ai/pull/192) ([@3coins](https://github.com/3coins))
- fix: Correct recursion error on load in JupyterHub [#178](https://github.com/jupyterlab/jupyter-ai/pull/178) ([@mschroering](https://github.com/mschroering))

### Documentation improvements

- Additional docs fix for 3.8 support [#185](https://github.com/jupyterlab/jupyter-ai/pull/185) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-05-19&to=2023-05-26&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-05-19..2023-05-26&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-05-19..2023-05-26&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-05-19..2023-05-26&type=Issues) | [@mschroering](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Amschroering+updated%3A2023-05-19..2023-05-26&type=Issues)

## 0.7.2

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.7.1...3b6b1a083a045b4587c84314fa1851092fdad675))

### Enhancements made

- Adds config option to use ENTER to send message [#164](https://github.com/jupyterlab/jupyter-ai/pull/164) ([@JasonWeill](https://github.com/JasonWeill))
- Changes chat messages to use absolute timestamps [#159](https://github.com/jupyterlab/jupyter-ai/pull/159) ([@JasonWeill](https://github.com/JasonWeill))
- Chat UI quality of life improvements [#154](https://github.com/jupyterlab/jupyter-ai/pull/154) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- Fix `yarn install` in CI [#174](https://github.com/jupyterlab/jupyter-ai/pull/174) ([@dlqqq](https://github.com/dlqqq))
- Avoids using str.removeprefix and str.removesuffix [#169](https://github.com/jupyterlab/jupyter-ai/pull/169) ([@JasonWeill](https://github.com/JasonWeill))
- Remove reference to now-nonexistent file [#165](https://github.com/jupyterlab/jupyter-ai/pull/165) ([@JasonWeill](https://github.com/JasonWeill))
- Uses React 17, not 18, for @jupyter-ai/core dependency [#157](https://github.com/jupyterlab/jupyter-ai/pull/157) ([@JasonWeill](https://github.com/JasonWeill))

### Documentation improvements

- Remove reference to now-nonexistent file [#165](https://github.com/jupyterlab/jupyter-ai/pull/165) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-05-11&to=2023-05-19&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-05-11..2023-05-19&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-05-11..2023-05-19&type=Issues)

## 0.7.1

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.7.0...7f9581c3ed735032f6e22cdde047fd6cabb43755))

### Enhancements made

- Documents server 2 as a requirement [#158](https://github.com/jupyterlab/jupyter-ai/pull/158) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- Fixes error for config, when new installation is done [#161](https://github.com/jupyterlab/jupyter-ai/pull/161) ([@3coins](https://github.com/3coins))

### Documentation improvements

- Documents server 2 as a requirement [#158](https://github.com/jupyterlab/jupyter-ai/pull/158) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-05-11&to=2023-05-11&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-05-11..2023-05-11&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-05-11..2023-05-11&type=Issues)

## 0.7.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.6.0...76039cffc6c6031f61726c8bc090e0384b82548e))

### Enhancements made

- Updates docs to refer to new setup process [#149](https://github.com/jupyterlab/jupyter-ai/pull/149) ([@JasonWeill](https://github.com/JasonWeill))
- Tweak font styles for code blocks in chat [#148](https://github.com/jupyterlab/jupyter-ai/pull/148) ([@dlqqq](https://github.com/dlqqq))
- Introduce Jupyternaut [#147](https://github.com/jupyterlab/jupyter-ai/pull/147) ([@dlqqq](https://github.com/dlqqq))
- Runtime model configurability [#146](https://github.com/jupyterlab/jupyter-ai/pull/146) ([@dlqqq](https://github.com/dlqqq))
- Update providers.py [#145](https://github.com/jupyterlab/jupyter-ai/pull/145) ([@thorhojhus](https://github.com/thorhojhus))
- Adds helper text to chat input field [#139](https://github.com/jupyterlab/jupyter-ai/pull/139) ([@3coins](https://github.com/3coins))
- Additional README copy edits [#132](https://github.com/jupyterlab/jupyter-ai/pull/132) ([@JasonWeill](https://github.com/JasonWeill))
- Copy edits in README [#131](https://github.com/jupyterlab/jupyter-ai/pull/131) ([@JasonWeill](https://github.com/JasonWeill))
- Revise screen shots in docs [#125](https://github.com/jupyterlab/jupyter-ai/pull/125) ([@JasonWeill](https://github.com/JasonWeill))
- Docs: Moves chat icon to left tab bar [#120](https://github.com/jupyterlab/jupyter-ai/pull/120) ([@JasonWeill](https://github.com/JasonWeill))
- Update chat interface privacy and cost notice [#116](https://github.com/jupyterlab/jupyter-ai/pull/116) ([@JasonWeill](https://github.com/JasonWeill))
- Implement better non-collaborative identity [#114](https://github.com/jupyterlab/jupyter-ai/pull/114) ([@dlqqq](https://github.com/dlqqq))
- Adds initial docs for chat UI [#112](https://github.com/jupyterlab/jupyter-ai/pull/112) ([@JasonWeill](https://github.com/JasonWeill))
- Updates contributor docs with more info about prerequisites [#109](https://github.com/jupyterlab/jupyter-ai/pull/109) ([@JasonWeill](https://github.com/JasonWeill))
- Adds %ai list, %ai help magic commands [#100](https://github.com/jupyterlab/jupyter-ai/pull/100) ([@JasonWeill](https://github.com/JasonWeill))
- Removes version from docs config [#99](https://github.com/jupyterlab/jupyter-ai/pull/99) ([@JasonWeill](https://github.com/JasonWeill))
- Format image provider [#66](https://github.com/jupyterlab/jupyter-ai/pull/66) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- Adds missing newline before closing code block [#155](https://github.com/jupyterlab/jupyter-ai/pull/155) ([@JasonWeill](https://github.com/JasonWeill))
- Runtime model configurability [#146](https://github.com/jupyterlab/jupyter-ai/pull/146) ([@dlqqq](https://github.com/dlqqq))
- Pin LangChain version [#134](https://github.com/jupyterlab/jupyter-ai/pull/134) ([@3coins](https://github.com/3coins))
- Upgraded ray version, installation instructions that work with python 3.9 and 3.10 [#127](https://github.com/jupyterlab/jupyter-ai/pull/127) ([@3coins](https://github.com/3coins))
- Strips language indicator from start of code output [#126](https://github.com/jupyterlab/jupyter-ai/pull/126) ([@JasonWeill](https://github.com/JasonWeill))

### Documentation improvements

- Updates docs to refer to new setup process [#149](https://github.com/jupyterlab/jupyter-ai/pull/149) ([@JasonWeill](https://github.com/JasonWeill))
- Additional README copy edits [#132](https://github.com/jupyterlab/jupyter-ai/pull/132) ([@JasonWeill](https://github.com/JasonWeill))
- Copy edits in README [#131](https://github.com/jupyterlab/jupyter-ai/pull/131) ([@JasonWeill](https://github.com/JasonWeill))
- Revise screen shots in docs [#125](https://github.com/jupyterlab/jupyter-ai/pull/125) ([@JasonWeill](https://github.com/JasonWeill))
- Docs: Moves chat icon to left tab bar [#120](https://github.com/jupyterlab/jupyter-ai/pull/120) ([@JasonWeill](https://github.com/JasonWeill))
- Update chat interface privacy and cost notice [#116](https://github.com/jupyterlab/jupyter-ai/pull/116) ([@JasonWeill](https://github.com/JasonWeill))
- Adds initial docs for chat UI [#112](https://github.com/jupyterlab/jupyter-ai/pull/112) ([@JasonWeill](https://github.com/JasonWeill))
- Updates contributor docs with more info about prerequisites [#109](https://github.com/jupyterlab/jupyter-ai/pull/109) ([@JasonWeill](https://github.com/JasonWeill))
- Removes version from docs config [#99](https://github.com/jupyterlab/jupyter-ai/pull/99) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-04-20&to=2023-05-10&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-04-20..2023-05-10&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-04-20..2023-05-10&type=Issues) | [@ellisonbg](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aellisonbg+updated%3A2023-04-20..2023-05-10&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-04-20..2023-05-10&type=Issues) | [@thorhojhus](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Athorhojhus+updated%3A2023-04-20..2023-05-10&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-04-20..2023-05-10&type=Issues)

## 0.6.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/chatgpt@0.5.0...629909aa1b3a956015b0a2b8a0501cd5ec1f0b52))

### Enhancements made

- Ray based document parsing of more file types [#94](https://github.com/jupyterlab/jupyter-ai/pull/94) ([@ellisonbg](https://github.com/ellisonbg))
- Create /autonotebook command for AI generated notebooks [#90](https://github.com/jupyterlab/jupyter-ai/pull/90) ([@ellisonbg](https://github.com/ellisonbg))
- Added support to index py, ipynb, md, and R files [#89](https://github.com/jupyterlab/jupyter-ai/pull/89) ([@3coins](https://github.com/3coins))
- This creates a memory actor for sharing memory across actors [#82](https://github.com/jupyterlab/jupyter-ai/pull/82) ([@ellisonbg](https://github.com/ellisonbg))
- Add a /clear command to clear the chat history [#78](https://github.com/jupyterlab/jupyter-ai/pull/78) ([@ellisonbg](https://github.com/ellisonbg))
- Removes chatgpt, dalle modules [#71](https://github.com/jupyterlab/jupyter-ai/pull/71) ([@JasonWeill](https://github.com/JasonWeill))
- General UI/UX improvements [#70](https://github.com/jupyterlab/jupyter-ai/pull/70) ([@ellisonbg](https://github.com/ellisonbg))
- Added doc indexing, moved processing to ray actors [#67](https://github.com/jupyterlab/jupyter-ai/pull/67) ([@3coins](https://github.com/3coins))
- implement better chat history UI [#65](https://github.com/jupyterlab/jupyter-ai/pull/65) ([@dlqqq](https://github.com/dlqqq))
- Basic collaborative chat [#58](https://github.com/jupyterlab/jupyter-ai/pull/58) ([@dlqqq](https://github.com/dlqqq))
- Adds code format option [#57](https://github.com/jupyterlab/jupyter-ai/pull/57) ([@JasonWeill](https://github.com/JasonWeill))
- make selections more robust [#54](https://github.com/jupyterlab/jupyter-ai/pull/54) ([@dlqqq](https://github.com/dlqqq))
- Adds prompt templates [#53](https://github.com/jupyterlab/jupyter-ai/pull/53) ([@JasonWeill](https://github.com/JasonWeill))
- Make provider call async [#51](https://github.com/jupyterlab/jupyter-ai/pull/51) ([@3coins](https://github.com/3coins))
- Adds Err array with exceptions captured [#34](https://github.com/jupyterlab/jupyter-ai/pull/34) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- Error handling and messaging when the chat service doesn't work [#88](https://github.com/jupyterlab/jupyter-ai/pull/88) ([@3coins](https://github.com/3coins))
- Removed sleep that was slowing replies down [#79](https://github.com/jupyterlab/jupyter-ai/pull/79) ([@ellisonbg](https://github.com/ellisonbg))
- Documents requirements to use Python 3.10, JupyterLab [#74](https://github.com/jupyterlab/jupyter-ai/pull/74) ([@JasonWeill](https://github.com/JasonWeill))
- Documents special error list, updates example file [#63](https://github.com/jupyterlab/jupyter-ai/pull/63) ([@JasonWeill](https://github.com/JasonWeill))
- Strips prefix and suffix [#60](https://github.com/jupyterlab/jupyter-ai/pull/60) ([@JasonWeill](https://github.com/JasonWeill))
- Updates README, adds screen shots [#56](https://github.com/jupyterlab/jupyter-ai/pull/56) ([@JasonWeill](https://github.com/JasonWeill))

### Maintenance and upkeep improvements

- Moved actors to separate modules. [#80](https://github.com/jupyterlab/jupyter-ai/pull/80) ([@3coins](https://github.com/3coins))
- Remove old UI [#77](https://github.com/jupyterlab/jupyter-ai/pull/77) ([@ellisonbg](https://github.com/ellisonbg))
- Removes chatgpt, dalle modules [#71](https://github.com/jupyterlab/jupyter-ai/pull/71) ([@JasonWeill](https://github.com/JasonWeill))

### Documentation improvements

- Documents requirements to use Python 3.10, JupyterLab [#74](https://github.com/jupyterlab/jupyter-ai/pull/74) ([@JasonWeill](https://github.com/JasonWeill))
- Misc work on README, docs, and magic [#69](https://github.com/jupyterlab/jupyter-ai/pull/69) ([@ellisonbg](https://github.com/ellisonbg))
- Documents special error list, updates example file [#63](https://github.com/jupyterlab/jupyter-ai/pull/63) ([@JasonWeill](https://github.com/JasonWeill))
- Updates README, adds screen shots [#56](https://github.com/jupyterlab/jupyter-ai/pull/56) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-04-11&to=2023-04-20&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-04-11..2023-04-20&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-04-11..2023-04-20&type=Issues) | [@ellisonbg](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aellisonbg+updated%3A2023-04-11..2023-04-20&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-04-11..2023-04-20&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-04-11..2023-04-20&type=Issues)

## 0.5.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/chatgpt@0.4.0...9ff812b8231d7d41f3431a1a82acb56e2babca49))

### Enhancements made

- use --force-publish option for lerna version [#49](https://github.com/jupyterlab/jupyter-ai/pull/49) ([@dlqqq](https://github.com/dlqqq))
- Move magics to `jupyter-ai-magics` package [#48](https://github.com/jupyterlab/jupyter-ai/pull/48) ([@dlqqq](https://github.com/dlqqq))
- Chat backend [#40](https://github.com/jupyterlab/jupyter-ai/pull/40) ([@3coins](https://github.com/3coins))
- Documents changes while server is running [#33](https://github.com/jupyterlab/jupyter-ai/pull/33) ([@JasonWeill](https://github.com/JasonWeill))
- Implement chat UI [#25](https://github.com/jupyterlab/jupyter-ai/pull/25) ([@dlqqq](https://github.com/dlqqq))

### Bugs fixed

- use --force-publish option for lerna version [#49](https://github.com/jupyterlab/jupyter-ai/pull/49) ([@dlqqq](https://github.com/dlqqq))

### Documentation improvements

- Documents changes while server is running [#33](https://github.com/jupyterlab/jupyter-ai/pull/33) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-04-06&to=2023-04-11&type=c))

[@3coins](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3A3coins+updated%3A2023-04-06..2023-04-11&type=Issues) | [@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-04-06..2023-04-11&type=Issues) | [@ellisonbg](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Aellisonbg+updated%3A2023-04-06..2023-04-11&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-04-06..2023-04-11&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-04-06..2023-04-11&type=Issues)

## 0.4.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/chatgpt@0.3.0...cf5abf866fe1fdb71f9a646077746a41e7ab1b91))

### Enhancements made

- Various magic enhancements and fixes [#32](https://github.com/jupyterlab/jupyter-ai/pull/32) ([@dlqqq](https://github.com/dlqqq))
- Magic tweaks [#31](https://github.com/jupyterlab/jupyter-ai/pull/31) ([@dlqqq](https://github.com/dlqqq))
- Add magics example notebook [#30](https://github.com/jupyterlab/jupyter-ai/pull/30) ([@dlqqq](https://github.com/dlqqq))
- Removes docs about dialog, replaces with magics [#29](https://github.com/jupyterlab/jupyter-ai/pull/29) ([@JasonWeill](https://github.com/JasonWeill))
- Update README.md [#24](https://github.com/jupyterlab/jupyter-ai/pull/24) ([@JasonWeill](https://github.com/JasonWeill))
- Use new provider interface in magics [#23](https://github.com/jupyterlab/jupyter-ai/pull/23) ([@dlqqq](https://github.com/dlqqq))
- Initial docs [#22](https://github.com/jupyterlab/jupyter-ai/pull/22) ([@JasonWeill](https://github.com/JasonWeill))

### Bugs fixed

- Various magic enhancements and fixes [#32](https://github.com/jupyterlab/jupyter-ai/pull/32) ([@dlqqq](https://github.com/dlqqq))
- Update config.example.py [#26](https://github.com/jupyterlab/jupyter-ai/pull/26) ([@JasonWeill](https://github.com/JasonWeill))

### Documentation improvements

- Add magics example notebook [#30](https://github.com/jupyterlab/jupyter-ai/pull/30) ([@dlqqq](https://github.com/dlqqq))
- Removes docs about dialog, replaces with magics [#29](https://github.com/jupyterlab/jupyter-ai/pull/29) ([@JasonWeill](https://github.com/JasonWeill))
- Update README.md [#24](https://github.com/jupyterlab/jupyter-ai/pull/24) ([@JasonWeill](https://github.com/JasonWeill))
- Initial docs [#22](https://github.com/jupyterlab/jupyter-ai/pull/22) ([@JasonWeill](https://github.com/JasonWeill))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-03-21&to=2023-04-06&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-03-21..2023-04-06&type=Issues) | [@JasonWeill](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3AJasonWeill+updated%3A2023-03-21..2023-04-06&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-03-21..2023-04-06&type=Issues)

## 0.3.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/chatgpt@0.2.0...10c0e3257c9abfc67a89860f7b70d63020d0e361))

### Enhancements made

- implement IPython magics [#18](https://github.com/jupyterlab/jupyter-ai/pull/18) ([@dlqqq](https://github.com/dlqqq))
- add tasks for AI modules [#16](https://github.com/jupyterlab/jupyter-ai/pull/16) ([@dlqqq](https://github.com/dlqqq))
- Decouple tasks from model engines and introduce modalities [#15](https://github.com/jupyterlab/jupyter-ai/pull/15) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-03-07&to=2023-03-21&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-03-07..2023-03-21&type=Issues)

## 0.2.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.1.1...d3be35480f4ca8370cd6bd8b5231af53493cb139))

### Enhancements made

- import ChatGPT AI module [#14](https://github.com/jupyterlab/jupyter-ai/pull/14) ([@dlqqq](https://github.com/dlqqq))
- import AI module cookiecutter [#13](https://github.com/jupyterlab/jupyter-ai/pull/13) ([@dlqqq](https://github.com/dlqqq))

### Bugs fixed

- include root package in version bump script [#12](https://github.com/jupyterlab/jupyter-ai/pull/12) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-03-05&to=2023-03-07&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-03-05..2023-03-07&type=Issues)

## 0.1.1

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/@jupyter-ai/core@0.1.0...e4824ad3f5bfd0fec7701f8c7917cd3305c23269))

### Bugs fixed

- bump all project versions in bump-version [#10](https://github.com/jupyterlab/jupyter-ai/pull/10) ([@dlqqq](https://github.com/dlqqq))
- fix insert-below-in-image insertion mode [#9](https://github.com/jupyterlab/jupyter-ai/pull/9) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-03-04&to=2023-03-05&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-03-04..2023-03-05&type=Issues)

## 0.1.0

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/0d4009ab7cb344f9e7c86b0d77e9f84ccde22382...285682d615bd0dfc5d2598490da3b5943a3c67d7))

### Enhancements made

- rename NPM packages to be under @jupyter-ai org [#7](https://github.com/jupyterlab/jupyter-ai/pull/7) ([@dlqqq](https://github.com/dlqqq))
- disable check-release for PRs [#6](https://github.com/jupyterlab/jupyter-ai/pull/6) ([@dlqqq](https://github.com/dlqqq))
- Set up releaser configuration [#3](https://github.com/jupyterlab/jupyter-ai/pull/3) ([@dlqqq](https://github.com/dlqqq))
- Improve development setup [#1](https://github.com/jupyterlab/jupyter-ai/pull/1) ([@dlqqq](https://github.com/dlqqq))

### Bugs fixed

- Add root package as Nx project [#8](https://github.com/jupyterlab/jupyter-ai/pull/8) ([@dlqqq](https://github.com/dlqqq))
- Fix check-release workflow [#5](https://github.com/jupyterlab/jupyter-ai/pull/5) ([@dlqqq](https://github.com/dlqqq))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlab/jupyter-ai/graphs/contributors?from=2023-02-10&to=2023-03-04&type=c))

[@dlqqq](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Adlqqq+updated%3A2023-02-10..2023-03-04&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterlab%2Fjupyter-ai+involves%3Awelcome+updated%3A2023-02-10..2023-03-04&type=Issues)
