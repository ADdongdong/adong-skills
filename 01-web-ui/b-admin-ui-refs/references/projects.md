# B 端后台 UI 参考库 · 项目清单

> stars 与最近提交取自 GitHub API，**快照时间 2026-09-21**；数值会变动，需要最新数据时重新查 `https://api.github.com/repos/{owner}/{repo}`。
> 演示入口优先给官网；若某链接失效，**以仓库 README 里的 Demo 链接为准**（各项目改版时会换域名）。

## 1. 现代 SaaS 产品级（抄质感与交互细节）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `twentyhq/twenty` | 57.2k | TS + React | https://twenty.com | **记录型数据的界面范式**：表格/看板双视图、一行一记录、右侧属性面板、就地编辑、空状态、设置页分区 |
| `makeplane/plane` | 59.7k | TS + React | https://app.plane.so | 列表 + 详情主从布局、常驻右侧属性栏、工作流状态、批量操作、键盘快捷键 |
| `calcom/cal.diy`（原 `calcom/cal.com`） | 48.6k | TS + Next.js | https://cal.com | 多步表单、时间/可用性选择、确认与取消流、通知邮件模板 |
| `dubinc/dub` | 24.8k | TS + Next.js | https://dub.co | 极简到极致、数据表 + 图表、空状态、`Cmd+K` 命令面板 |
| `midday-ai/midday` | 15.0k | TS + Next.js | https://midday.ai | **财务/交易/对账**：票据识别界面、收件箱式审核、报表 ·（2026-06 后更新放缓） |
| `medusajs/medusa` | 36.4k | TS + React | https://demo.medusajs.com | 订单详情 + 时间线、状态流转、（`Medusa UI` 组件与 Tailwind 预设） |
| `chatwoot/chatwoot` | 37.0k | Ruby + Vue | https://app.chatwoot.com | 三栏会话布局、筛选器、标签体系、SLA 提示 |

## 2. 数据密集 / 记录型后台（抄表格与表单排版）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `payloadcms/payload` | 44.9k | TS + React | https://demo.payloadcms.com | **字段编辑排版最值得抄**：字段分组 / 行列节奏 / 条件显示 / 侧栏元数据 / 版本与草稿 |
| `directus/directus` | 37.9k | TS + Vue | https://demo.directus.io | 自动 CRUD 后台、字段配置、**权限矩阵**、数据模型可视化 |
| `nocodb/nocodb` | 65.0k | TS + Vue | https://nocodb.com | 列类型、**筛选器构建器**、分组/排序、表单视图、批量编辑 |
| `refinedev/refine` | 35.7k | TS + React | https://refine.dev | Headless 后台框架：CRUD、权限、路由的**模式**参考（无 UI 包袱） |
| `marmelab/react-admin` | 26.9k | TS + React | https://marmelab.com/react-admin | 老牌 React 后台框架：列表/编辑/过滤/引用的实现范式 |

## 3. 文档 / 财务 / 审核流（业务形态最接近「函证」）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `documenso/documenso` | 15.1k | TS + Next.js | https://documenso.com | **最值得看**：文档签署 + 签名位标注 + 状态流 + **审计留痕**「谁在何时确认了什么」+ 收件人字段 |
| `invoiceninja/invoiceninja` | 10.1k | PHP + Vue | https://www.invoiceninja.com | 单据状态机、发票列表、客户/项目关联 |
| `akaunting/akaunting` | 10.1k | PHP | https://akaunting.com | 会计：科目、凭证、报表、多公司 |
| `frappe/erpnext` | 39.4k | Python + Vue | https://erpnext.com | 大型 ERP 的**表单密度与审批流**（UI 偏传统，看结构与字段组织） |
| `odoo/odoo` | 54.5k | Python | https://www.odoo.com | 业务对象建模与视图定义（同上，看结构） |
| `formbricks/formbricks` | 13.0k | TS + Next.js | https://formbricks.com | 表单构建器：问题类型、逻辑跳转、预览与发布 |

## 4. 数据表格型产品（多维表格）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `teableio/teable` | 21.8k | TS + React | https://teable.io | 中文团队、完成度高：视图切换 / 字段类型 / 单元格编辑 / 分组汇总 |
| `apitable/apitable` | 15.6k | TS | https://apitable.com | 维格表：表格 + 视图 + 自动化 |
| `baserow/baserow` | 6.0k | Python + Vue | https://baserow.io | 结构清晰、风格朴素，适合看"最小可用"的数据后台 |
| `gristlabs/grist-core` | 11.8k | TS | https://www.getgrist.com | 表格 + 公式列 + 页面布局混排 |

## 5. 中文生态高颜值模板（技术栈更近）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `ant-design/ant-design-pro` | 38.8k | TS + React + antd | https://preview.pro.ant.design | **与 antd 栈同源**：页面骨架、抽屉/弹窗层级、表格工具栏、权限路由 |
| `vbenjs/vue-vben-admin` | 33.5k | Vue3 + TS | https://www.vben.pro | 国内颜值标杆：主题令牌、密度切换、多标签页、权限体系 |
| `soybeanjs/soybean-admin` | 15.0k | Vue3 + TS | https://admin.soybeanjs.cn | 清新优雅、深浅色与留白处理讲究 |
| `Daymychen/art-design-pro` | 5.9k | Vue3 | 以仓库 README 为准 | 视觉最"当代"的新项目 |
| `tabler/tabler` | 41.7k | Astro + Bootstrap | https://preview.tabler.io | **气质最接近克制型工具**：无花哨、密度高、层级靠留白与字重 |

## 6. 平台 / 低代码 / AI（相关但偏框架）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `n8n-io/n8n` | 205.5k | TS + Vue | https://n8n.io | 画布式工作流编辑器：节点、连线、执行日志、失败重试 |
| `langgenius/dify` | 156.7k | TS + React | https://dify.ai | LLM 应用编排：对话界面、流式输出、调试面板、Prompt 编辑 |
| `supabase/supabase` | 110.5k | TS + React | https://supabase.com | Studio：数据表编辑、SQL 编辑器、认证与存储配置 |
| `appwrite/appwrite` | 57.4k | PHP + React | https://appwrite.io | 控制台 + 平台配置型后台 |
| `appsmithorg/appsmith` | 40.9k | TS + React | https://www.appsmith.com | 低代码搭建器：属性面板 + 画布 + 数据源绑定 |
| `ToolJet/ToolJet` | 40.9k | JS + React | https://www.tooljet.com | 同上，另一种属性面板实现 |
| `hcengineering/platform`（Huly） | 27.7k | TS + Svelte | https://huly.io | 一体化协作平台，**信息密度极高**，看"多面板共存"的处理 |
| `maybe-finance/maybe` | 54.3k | Ruby + TS | 以仓库 README 为准 | 个人财务，UI 很精致 ·（2025-07 后停更，仅作视觉参考） |

## 7. 组件与设计系统（组件级抄质感）

| 项目 | Stars | 栈 | 演示 / 官网 | 借鉴点 |
|---|---|---|---|---|
| `shadcn-ui/ui` | 124.3k | TS + Tailwind | https://ui.shadcn.com | 现代 Web 组件事实标准：**令牌结构、变体（variants）、可访问性细节** |
| `tremorlabs/tremor` | 3.6k | TS + React | https://tremor.so | 仪表盘图表组件（已停更，结构仍可参考） |

---

## 选型心法（避免踩坑）

1. **star 高 ≠ UI 好。** 一批 star 很高的国内后台模板（RuoYi 系等）功能全但设计平庸，不要因为 star 就往里钻。
2. **先看 demo 再看代码。** 判断值不值得借鉴，30 秒看官网截图足够；确定要抄某一处再进仓库。
3. **看活跃度。** API 的 `pushed_at` 若在半年以前（如 `maybe-finance/maybe`、`tremorlabs/tremor`），只作视觉参考，不要跟着抄工程做法。
4. **优先选有独立设计系统的项目**（自带 tokens / 组件库的，如 `shadcn-ui`、`vben`、`medusa`）——它们的做法更容易迁移，而不是堆在页面里的行内样式。
5. **同栈优先**：React + antd 的项目（`ant-design-pro`）能直接对照；Vue / Bootstrap 的看结构就好。
