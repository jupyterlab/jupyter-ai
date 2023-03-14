import React, { useEffect, useState } from 'react';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { Widget } from '@lumino/widgets';

import { ThemeProvider } from '@mui/material/styles';
import {
  Box,
  InputLabel,
  MenuItem,
  FormControl,
  Select,
  SelectChangeEvent,
  Stack,
  Button
} from '@mui/material';
import { ExpandableTextField } from './expandable-text-field';

import { insertOutput } from '../inserter';
import { AiService } from '../handler';
import { getJupyterLabTheme } from '../theme-provider';

/**
 * Map of human-readable descriptions per insertion mode.
 */
const TASK_DESCS: Record<string, string> = {
  above: 'AI output will be inserted above the selected text',
  replace: 'AI output will replace the selected text',
  below: 'AI output will be inserted below the selected text',
  'above-in-cells': 'AI output will be inserted above in new notebook cells',
  'below-in-cells': 'AI output will be inserted below in new notebook cells'
};

export interface IOpenTaskDialogProps {
  selectedText: string;
  app: JupyterFrontEnd;
  editorWidget: Widget;
  closeDialog: () => unknown;
}

export function OpenTaskDialog(props: IOpenTaskDialogProps): JSX.Element {
  // response from ListTasks endpoint
  const [taskList, setTaskList] = useState<AiService.ListTasksEntry[]>([]);
  // ID of the selected task, set on selection
  const [taskId, setTaskId] = useState<string>('');
  // response from DescribeTask endpoint, called after selection
  const [taskDesc, setTaskDesc] = useState<AiService.DescribeTaskResponse>();
  // currently selected model engine
  const [engineId, setEngineId] = useState<string>('');
  // whether the UI is currently awaiting a ListTasks call
  const [loading, setLoading] = useState<boolean>(false);

  const onSubmitClick = async () => {
    setLoading(true);

    try {
      const request: AiService.IPromptRequest = {
        task_id: taskId,
        engine_id: engineId,
        prompt_variables: {
          body: props.selectedText
        }
      };
      const response = await AiService.sendPrompt(request);
      insertOutput(props.app, {
        widget: props.editorWidget,
        request,
        response
      });
      props.closeDialog();
      return true;
    } catch (e: unknown) {
      alert('**Failed** with error:\n```\n' + (e as Error).message + '\n```');
      setLoading(false);
      return false;
    }
  };

  /**
   * Effect: call ListTasks endpoint on initial render.
   */
  useEffect(() => {
    async function listTasks() {
      const listTasksResponse = await AiService.listTasks();
      setTaskList(listTasksResponse.tasks);
      if (!listTasksResponse.tasks.length) {
        console.error('No tasks returned via the backend');
        return;
      }
      const taskId = listTasksResponse.tasks[0].id;
      setTaskId(taskId);
      const describeTaskResponse = await AiService.describeTask(taskId);
      setTaskDesc(describeTaskResponse);
    }
    listTasks();
  }, []);

  /**
   * Effect: when a task is selected, default to selecting the first available
   * model engine.
   */
  useEffect(() => {
    if (taskDesc?.engines?.length) {
      setEngineId(taskDesc.engines[0].id);
    }
  }, [taskDesc]);

  const handleTaskChange = async (event: SelectChangeEvent) => {
    setTaskId(event.target.value);
    const describeTaskResponse = await AiService.describeTask(
      event.target.value
    );
    setTaskDesc(describeTaskResponse);
  };

  const handleEngineChange = async (event: SelectChangeEvent) => {
    setEngineId(event.target.value);
  };

  const taskDescription =
    taskDesc?.insertion_mode && taskDesc.insertion_mode in TASK_DESCS
      ? TASK_DESCS[taskDesc.insertion_mode]
      : '';

  return (
    <ThemeProvider theme={getJupyterLabTheme()}>
      <Box padding={1} width={'40em'}>
        <Stack spacing={4}>
          <FormControl fullWidth>
            <InputLabel id="task-select-label">Task</InputLabel>
            <Select
              value={taskId}
              onChange={handleTaskChange}
              label="Task"
              labelId="task-select-label"
              MenuProps={{
                style: { zIndex: 20000 }
              }}
              autoFocus
            >
              {taskList.map(task => (
                <MenuItem key={task.id} value={task.id}>
                  {task.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Box pt={4} width={'40em'}>
            <Stack spacing={4}>
              <FormControl fullWidth>
                <InputLabel id="engine-select-label">Model engine</InputLabel>
                <Select
                  value={engineId}
                  onChange={handleEngineChange}
                  label="Model engine"
                  labelId="engine-select-label"
                  MenuProps={{
                    style: { zIndex: 20000 }
                  }}
                  autoFocus
                >
                  {taskDesc?.engines.map(engine => (
                    <MenuItem key={engine.id} value={engine.id}>
                      {engine.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <ExpandableTextField
                label="Prompt template"
                text={taskDesc?.prompt_template}
              />
              {taskDescription && (
                <ExpandableTextField
                  label="Task description"
                  text={taskDescription}
                />
              )}
            </Stack>
          </Box>
          <Stack direction="row" justifyContent="flex-end" spacing={1}>
            <Button variant="outlined" onClick={props.closeDialog}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={onSubmitClick}
              disabled={!!loading || taskId === ''}
            >
              {loading ? 'Submitting…' : 'Submit'}
            </Button>
          </Stack>
        </Stack>
      </Box>
    </ThemeProvider>
  );
}
