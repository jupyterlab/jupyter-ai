# Builds

## How to use
There are two different packages, clean and enhanced.

1. *clean* - let user input a question to the model
2. *enhanced* - let user twick context and ask question

### Manual deployment

1. Open jupyter.syapse.com
2. drug folder *clean* or *enhanced* to the jupyter env.
3. In the jupyter open your folder
4. Open notebook file and run each cell.


### Create new deployemnt

1. Make changes in the `packages/jupyter-ai-magics/jupyter-ai-magics`
2. make you r code changes to the providesr.py or any other files there
3. Run `python -m build` to create a build
