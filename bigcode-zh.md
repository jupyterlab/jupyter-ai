# 整合bigcode续写逻辑说明


## 逻辑梳理
我们目前的做法是基于现有的 jupyter-ai 代码做的扩展（属于 jupyter-ai 的一部分）

### 前端

#### 键盘处理事件

1. 创建 mirrorcode 的 extension（键盘事件）
2. 当 notebook 发生变化时，将 notebbok 默认选中的 cell 添加此 extension
3. 在 notebook 中挂载 cell 变化事件，如果 cell 发生变化，则将 extension 添加至 
4. cell 的 codemirror实例中
5. 在app加载此处理程序


代码参考[keydown-handler.ts](./packages/jupyter-ai/src/keydown-handler.ts)

#### 侧边栏(暂无代码实现)
1. 定义Widget构造器方法 export function buildBigcodeSidebar(): ReactWidget {}
2. 在构造器中构造Widget const BigCodeWidget = ReactWidget.create( dom结构... );
3. 配置如id，图标，标题等基本信息 BigCodeWidget.xxx = xxx
4. labextension 前端入口点添加这个侧边栏（Widget）到jupyterlab中 app.shell.add5.(bigcodeWidget, 'left', { rank: 2401 })


#### 续写（ctrl+space）



### 后端

在 jupyter-ai 中，用户填写的信息后，会进行请求到后端[handlers](./packages/jupyter-ai/jupyter_ai/handlers.py)，由后端保存到"~/.loacl"目录中。

我们延伸此架构，使原先的接口可以新增 bigcode 的配置

