# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

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

<!-- <END NEW CHANGELOG ENTRY> -->

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
