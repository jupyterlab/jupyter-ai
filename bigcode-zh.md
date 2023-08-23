# 整合bigcode续写逻辑说明

## 依赖项
- "mobx" and "mobx-react": react的一个全局变量管理库
- typescript: ~4.1.3 -> 5.1.6，之前的ts版本会打包失败，原因为ts语法检查依赖项中的代码不通过

## 逻辑梳理
我们目前的做法是基于现有的 jupyter-ai 代码做的扩展（属于 jupyter-ai 的一部分）

### 前端

#### 侧边栏
1. 定义Widget构造器方法
2. 配置如id，图标，标题等基本信息（暂时没有图标，使用的是jupyter-ai的）
3. labextension 前端入口点添加这个侧边栏（Widget）到jupyterlab中，参考[labextension 前端入口点](./packages/jupyter-ai/src/index.ts)

代码参考[bigcode-sidebar](./packages/jupyter-ai/src/widgets/bigcode-sidebar.tsx)

#### 键盘处理事件

1. 创建 codemirror 的 extension（键盘事件）,此 extension 在下述流程中被绑定到 codemirror 的实例
2. 当 notebook 发生变化时，将 notebbok 默认选中的 cell 添加此 extension
3. 在 notebook 中挂载 cell 变化事件，如果 cell 发生变化，则将 extension 添加至 cell 的 codemirror 实例中
4. 在app加载此处理程序

代码参考[keydown-handler.ts](./packages/jupyter-ai/src/keydown-handler.ts)

### 后端（最后做）

在 jupyter-ai 中，用户填写的信息后，会进行请求到后端[handlers](./packages/jupyter-ai/jupyter_ai/handlers.py)，由后端保存到"~/.loacl"目录中。

我们延伸此架构，使原先的接口可以新增 bigcode 的配置。并且在请求 bigcode 时，由后端做请求转发

