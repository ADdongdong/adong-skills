---
name: frontend-icon-kit
description: 给前端界面和交互原型智能配置矢量图标。当需要为网页、HTML 原型、管理后台、表单、表格、导航菜单、按钮、状态标签、空状态配图标，或用户提到图标、icon、矢量图标、界面图标、图标不统一时使用。内置中文业务场景词到 Tabler 图标的语义映射，覆盖投行/债券/函证/审批/报表/权限等 11 个业务域；提供校验脚本杜绝编造图标名，支持 CDN 组件与内联 SVG 两种交付形态，并附可直接打开的可视化图标选择器。
---

# frontend-icon-kit

给前端界面配一批**场景匹配、风格统一**的图标，产出可直接粘贴的代码。

图标源锁定 **Tabler Icons**（Iconify 的 `tabler` 集合，6286 个图标，24×24 画布，圆头描边，MIT 许可）。整套界面只用这一套，保证视觉一致。

---

## 三条铁律

### 1. 绝不凭记忆写图标名

图标名是硬事实。`risk`、`audit`、`workflow`、`approve`、`seal`、`bond`、`quota`、`ledger`、`payment`、`project` —— 这些看起来再合理不过的名字，**在 Tabler 里全都不存在**。

任何要写进代码的图标名，必须先过校验：

```bash
python scripts/icon_check.py tabler:building-bank tabler:circle-check
```

输出 ❌ 的重新选，不许"先写上再说"。取图脚本 `icon_fetch.py` 内置了这道闸门，无效名会直接拒绝生成。

### 2. 选图标先查语义表，不要自己猜关键词

中文业务词 → 图标名的映射写在 `references/semantic-map.json`，覆盖 11 个业务域、447 个精选图标。直接用它，比临时猜英文关键词准得多。

```bash
python scripts/icon_search.py "函证"
```

### 3. 尺寸和颜色走 token，不硬编码

图标色一律用 `currentColor` 继承父元素 `color`；尺寸按场景取 14/16/20/24/32/48。细则见 `references/usage-guide.md`。

---

## 标准工作流

**第 1 步 · 盘点图标位**

通读界面结构，列出所有需要图标的位置：侧边导航项、工具栏按钮、表格行操作、状态标签、模块标题、空状态、Tab、面包屑。

**第 2 步 · 按业务语义检索**

```bash
python scripts/icon_search.py "受托管理"          # 中文业务词
python scripts/icon_search.py "bank" --limit 30    # 英文走全量名字匹配
python scripts/icon_search.py "审批通过" --json     # 机器可读，便于批量处理
```

检索是三级兜底：语义表 → 本地 6286 个名字子串匹配（零网络）→ Iconify 在线搜索。

**第 3 步 · 校验**

批量把候选名过一次校验，剔除无效项：

```bash
python scripts/icon_check.py tabler:mail-forward tabler:mail-opened tabler:mail-x
```

**第 4 步 · 生成代码**

```bash
# 原型阶段：CDN 组件，代码短、好改
python scripts/icon_fetch.py tabler:mail-forward tabler:mail-opened --mode cdn

# 交付阶段：内联 SVG，离线单文件可跑
python scripts/icon_fetch.py --file icons.txt --mode inline --out icons.snippet.html
```

**第 5 步 · 套用集成规范**

尺寸、颜色、交互态、无障碍写法见 `references/usage-guide.md`。三个要点：
- 图标旁已有文字 → `aria-hidden="true"`；纯图标按钮 → `aria-label`
- 与文字对齐用 `display:inline-flex; align-items:center; gap:6px`，别靠 `vertical-align` 猜
- 小于 16px 时把描边从 `stroke-width:2` 降到 `1.5`，否则显糊

---

## 脚本速查

| 脚本 | 用途 | 典型命令 |
|---|---|---|
| `scripts/icon_search.py` | 按中文业务词/英文关键词搜图标 | `python scripts/icon_search.py "额度"` |
| `scripts/icon_check.py` | **校验图标名是否存在**（防编造闸门） | `python scripts/icon_check.py tabler:x tabler:y` |
| `scripts/icon_fetch.py` | 生成 CDN 组件或内联 SVG 代码 | `python scripts/icon_fetch.py tabler:x --mode inline` |
| `scripts/build_index.py` | 刷新本地全量图标索引 | `python scripts/build_index.py --force` |
| `scripts/build_picker.py` | 重新生成可视化选择器 | `python scripts/build_picker.py` |

Python 用任意 3.9+ 解释器，**全部只用标准库**，无需安装依赖。

Windows 下解释器路径示例：
`"C:/Users/10355/.workbuddy/binaries/python/versions/3.13.12/python.exe"`

---

## 可视化选择器

`assets/icon-picker.html` —— 双击直接用浏览器打开，无需服务器。

- 左侧按 11 个业务域分组（投行/债券业务、函证核查、文件单据、审批流程、数据报表、导航布局、用户权限、状态反馈、通用操作、时间日历、金融货币）
- 支持中文场景词搜索、尺寸切换、语义色切换
- **单击**复制当前格式，**Shift + 单击**复制另一种格式
- 「全量检索」可搜 Tabler 全部 6286 个图标

改完 `semantic-map.json` 或刷新了索引后，跑一次 `build_picker.py` 重新生成。

---

## 语义映射表

`references/semantic-map.json`，结构：

```json
{
  "groups": [
    {
      "id": "ib-business",
      "title": "投行 / 债券业务",
      "items": [
        { "zh": ["立项", "项目立项"], "en": ["clipboard"], "icons": ["clipboard-list", "briefcase", "file-plus"] }
      ]
    }
  ]
}
```

- `zh`：中文业务词，支持包含匹配（查"银行"能命中"银行账户""银行流水"）
- `en`：英文关键词，用于在线检索兜底
- `icons`：候选图标名，第一个是首选

**新增条目务必先校验**，把不存在的名字滤掉再写入。

---

## 配好的示例

`assets/demo-ib-console.html` —— 一个投行后台控制台的图标应用示例，演示侧边导航、工具栏、表格操作、状态标签、空状态五类图标位的规范用法。可对照它理解尺寸与配色如何落地。

---

## 已知环境坑

1. **Iconify API 不带 User-Agent 会返回 403**。脚本已内置 UA，勿去掉。
2. **本机 `.curlrc` 里若配了未启动的本地代理**（如 `127.0.0.1:7890`），curl 会被劫持到死端口并静默返回空。脚本在 Python 侧显式禁用代理直连；确需代理时设 `ICONKIT_PROXY=http://host:port`。
3. **本地 HTML 用 `file://` 打开时不能 `fetch` 同目录 JSON**（CORS 拦截）。选择器的数据已内联进 HTML，不要再改成外部 fetch。

---

## 换图标集（可选）

当前锁定 Tabler。若要换成 Lucide，改 `scripts/iconify_api.py` 里的 `DEFAULT_PREFIX`，重跑 `build_index.py` 和 `build_picker.py`，并把 `semantic-map.json` 里的图标名逐个替换（**必须重新校验**，不同图标集的命名规则不同）。
