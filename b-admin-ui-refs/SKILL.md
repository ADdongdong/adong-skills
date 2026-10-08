---
name: b-admin-ui-refs
description: 企业级后台（B 端）UI 参考库。索引 20+ 个界面质量高的开源项目（Tabler / Twenty / Plane / Payload / shadcn/ui / Vue Vben Admin / Ant Design Pro / Documenso / NocoDB 等），按「表格、表单、详情、审核留痕、工作流、图表、布局、主题」等需求类型路由到最合适的项目，并提供在仓库里定位具体组件文件的可行方法。当用户需要为后台 / 管理后台 / 管理系统 / 工作台寻找组件、交互或布局的参考实现，或提到「B 端」「后台该怎么设计」「找个组件参考」「别家是怎么做的」「抄一下 XX 的 UI」时使用。
---

# B 端后台 UI 参考库

把「某个后台组件/交互/布局该怎么做才到位」拆成三步：**归类 → 定位 → 提炼**。

> 一句话定位：这是一个**找参考**的 skill，不是套模板的 skill。它的价值在第二步「定位」——能真的把某个项目里实现某个交互的那个文件找出来看。

## 一、归类：这个需求属于哪一类

先读用户需求，按下表选定 1 个首选 + 1~2 个备选，**不要一上来把 20 个项目全列给用户**。

| 需求类型 | 首选 | 备选 |
|---|---|---|
| **表格**：列配置 / 筛选器 / 行展开 / 批量操作 / 列宽拖拽 / 虚拟滚动 | `tabler/tabler` | `nocodb/nocodb`、`twentyhq/twenty`、`teableio/teable` |
| **表单与字段排版**：分组、行列节奏、必填与校验、错误态 | `payloadcms/payload` | `twentyhq/twenty`、`formbricks/formbricks`、`ant-design/ant-design-pro` |
| **记录详情页**：主从布局、右侧属性面板、就地编辑 | `twentyhq/twenty` | `makeplane/plane`、`directus/directus` |
| **审核 / 确认 / 留痕 / 签署**：状态流、谁在何时确认、"已核验"表达 | `documenso/documenso` | `calcom/cal.diy`、`invoiceninja/invoiceninja` |
| **工作流 / 状态机 / 任务队列**：进度、重试、失败态、并行推进 | `makeplane/plane` | `documenso/documenso`、`n8n-io/n8n` |
| **文件预览与标注**：画布 + 叠加层 + 图例 + 缩放工具条 | `documenso/documenso` | — |
| **图表 / 数据可视化** | `tremorlabs/tremor` | `dubinc/dub`、`nocodb/nocodb` |
| **布局 / 导航 / 侧栏 / 密度切换** | `tabler/tabler` | `vbenjs/vue-vben-admin`、`soybeanjs/soybean-admin` |
| **主题令牌 / 深色模式 / 设计系统** | `shadcn-ui/ui` | `vbenjs/vue-vben-admin`、`soybeanjs/soybean-admin` |
| **空状态 / 引导 / 首屏** | `twentyhq/twenty` | `calcom/cal.diy`、`dubinc/dub` |
| **权限 / 角色 / 字段级配置** | `directus/directus` | `appwrite/appwrite`、`frappe/erpnext` |
| **数据表格型产品**（多维表格、视图、分组） | `teableio/teable` | `apitable/apitable`、`baserow/baserow`、`gristlabs/grist-core` |
| **AI 类界面**（对话、流式、草稿建议） | `langgenius/dify` | `twentyhq/twenty` |
| **低代码 / 表单搭建** | `appsmithorg/appsmith` | `ToolJet/ToolJet` |

完整项目清单（stars / 技术栈 / demo 链接 / 逐项借鉴点）→ **`references/projects.md`**

## 二、定位：把那个文件真正找出来

**不要靠肉眼翻仓库、也不要靠 `git clone`**（本机到 `github.com:443` 时通时不通）。

用本 skill 的脚本（Node 18+，本机 v24 可直接跑）：

```bash
# 1) 按关键词列出匹配的文件路径（走 api.github.com 的 git/trees，匿名可用）
node "C:\Users\10355\.codebuddy\skills\b-admin-ui-refs\scripts\ghfind.mjs" twentyhq/twenty "record-table" --ext tsx

# 2) 打印某个文件的内容（走 jsDelivr，失败自动回退 raw.githubusercontent.com）
node "...\scripts\ghfind.mjs" tabler/tabler --get src/pages/xxx.html

# 3) 想要总览时：列出全部路径（大仓库会被 GitHub 截断，配合 --ext 缩小）
node "...\scripts\ghfind.mjs" nocodb/nocodb --tree --ext vue
```

其它可用通道（脚本内部已封装备选）：
- 取文件：`https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{path}` → 回退 `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}`
- 整包（需要全量本地看时）：`https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}`
- **不要用** GitHub MCP（本机 PAT 已失效，报 `Bad credentials`）、不要依赖 `git clone`

看视觉而不是看代码时：优先让用户去各项目的官网 / demo（链接见 `references/projects.md`），比读源码快得多。

## 三、提炼：参考 ≠ 覆盖（硬约束）

1. **项目的既有设计体系优先。** 目标项目若已有锁定令牌/设计约定（如本工作区 `.codebuddy/memory/界面与视觉约定.md`），**先读它**；引入任何第三方做法前，**先提示冲突并等确认**，不要直接改。
2. **只提取可迁移的「做法」**，不要照搬代码：结构、间距节奏、状态表达方式、交互反馈时机。栈通常不同（Tailwind / Vue / Bootstrap vs antd），代码级复制会带来不一致。
3. **警惕与本项目相反的取向**：目标项目若明确禁止渐变、大圆角、装饰动效、新色相，则不要把参考项目里这些元素带进来。
4. 给出的建议要落到**具体文件路径 + 具体做法**，而不是"XX 做得不错，可以学学"。
5. 若参考项目的许可证不允许，只作设计参考、不复制代码，并在结论里说明。

## 使用流程（照这个顺序做）

1. 读用户需求 → 用第一节的表选出 1 个首选 + 1~2 个备选；
2. 若用户是"看 UI"，先给 demo 链接；若是"要做法"，走第二步脚本定位文件；
3. 读目标文件 → 提炼 3~5 条可迁移做法 → 与本项目设计约定对照，标出冲突项；
4. 输出：候选项目 → 定位到的文件 → 可迁移做法 → 冲突提示（若有）→ 建议动作。

## 与其它 skill 的分工

- `ui-designer`（像素君）/ `frontend-dev` / `impeccable` / `polish` —— 负责**产出与打磨**；本 skill 只负责**找参考**，找到后把结论交给它们落地。
- `awesome-design-md` —— 提供**74 个品牌的 DESIGN.md 设计语言**（成套令牌）；本 skill 提供**可运行的完整产品/后台**（含真实交互代码）。两者互补，不要混用结论。
- `improve-ui` —— 只读审计目标项目自身；本 skill 提供**外部对照样本**。
