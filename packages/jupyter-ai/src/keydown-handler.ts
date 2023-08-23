import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
import { keymap } from '@codemirror/view';
import { EditorView } from '@codemirror/view';
import { Prec } from '@codemirror/state';
import { StateEffect } from '@codemirror/state';
import { Notebook } from '@jupyterlab/notebook';
import { NotebookPanel } from '@jupyterlab/notebook';
import { Extension } from '@codemirror/state';
import { getContent } from "./utils/instance"


// 创建一个软引用集合存放 editor
const mountedEditors = new WeakSet<CodeMirrorEditor>();

// 挂载"键盘按下 extension"到 editor 实例中
const mountExtension = (
  editor: CodeMirrorEditor,
  extension: Extension
): void => {
  // 如果 editor 已经被处理过
  if (mountedEditors.has(editor)) {
    return;
  }

  const view = editor.editor as EditorView;
  const tr = view.state.update({
    effects: StateEffect.appendConfig.of(extension)
  });

  view.dispatch(tr);
  mountedEditors.add(editor);
};


const generateKeyDownExtension = (app: JupyterFrontEnd): Extension => {
  return Prec.highest(
    keymap.of([
      {
        key: 'Ctrl-Space',
        run: () => {
          // 当你按下 Ctrl 和 Space，console 会打印如下字符串
          console.log("Ctrl and Space keys are pressed");
          /*
          * 我们使用了 highest，如果return true，则不会触发除此事件外任何事件，否则反之，会继续触发其他事件。
          * 例如：如果此事件为 Enter 事件，return true 之后，在单元格中不会新起一行
          */
          return true
        }
      }
    ])
  );
};

const init = (app: JupyterFrontEnd) => {
  if (!(app.shell instanceof LabShell)) {
    throw 'Shell is not an instance of LabShell. Jupyter AI does not currently support custom shells.';
  }

  const extension = generateKeyDownExtension(app);

  // 监听当前的 weiget 发生变化时
  app.shell.currentChanged.connect(async (sender, args) => {
    const currentWidget = args.newValue;
    if (!currentWidget || !(currentWidget instanceof NotebookPanel)) {
      return;
    }

    await currentWidget.context.ready;
    const content = getContent(currentWidget);

    if (content instanceof Notebook) {
      // 优先挂载加载 notebook 时默认选中的 Cell。在"content.activeCellChanged.connect"中，默认选中的 Cell 的 editor 为空
      const firstCell = content.activeCell;
      if (firstCell) {
        const firstCellEditor = firstCell.editor as CodeMirrorEditor;
        mountExtension(firstCellEditor, extension);
      }

      // 监听选中的 cell 发生变化时
      content.activeCellChanged.connect(async (sender, cell) => {
        if (!cell) {
          return;
        }

        // 在新增单元格时，editor 可能没有被实例化，所以我们需将挂载事件放在异步队列最低端，以用来保证 editor 实例化完成
        const waitCellInitTimer = setTimeout(() => {
          const editor = cell.editor as CodeMirrorEditor;
          mountExtension(editor, extension);
          clearTimeout(waitCellInitTimer);
        }, 0);
      });
    }
  });
};

export const keyDownHandle = async (app: JupyterFrontEnd): Promise<void> => {
  // 等待 notebook 完成初始化
  await app.start();
  init(app);
  console.log('keyDownHandle is start');
};