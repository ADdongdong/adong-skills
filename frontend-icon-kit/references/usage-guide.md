# 图标集成规范（HTML / 交互原型）

面向"交付完整前端交互代码"的场景。**核心原则：一套界面只用 Tabler 一套图标，尺寸和颜色全部走设计 token。**

---

## 一、两种交付模式

| 模式 | 写法 | 什么时候用 | 代价 |
|---|---|---|---|
| **CDN** | `<iconify-icon icon="tabler:x">` | 原型阶段、要改要迭代、代码要短好读 | 打开页面需联网 |
| **内联 SVG** | 直接写 `<svg>` | 最终交付单文件、要离线跑、要精确控色控尺寸 | 代码变长 |

原型期用 CDN，交付期切内联。切换只需重跑一次取图脚本，业务代码不用动。

---

## 二、CDN 模式标准写法

在页面末尾引入一次：

```html
<script src="https://code.iconify.design/iconify-icon/2.1.0/iconify-icon.min.js"></script>
```

用图标：

```html
<!-- 纯装饰，屏幕阅读器跳过 -->
<iconify-icon icon="tabler:building-bank" width="24" height="24" aria-hidden="true"></iconify-icon>

<!-- 有语义，需要被读到 -->
<iconify-icon icon="tabler:circle-check" width="16" height="16" role="img" aria-label="审核通过"></iconify-icon>
```

**注意**：`iconify-icon` 是自定义元素，尺寸必须写 `width`/`height` 属性，CSS 里的 `font-size` 对它无效。

---

## 三、内联 SVG 模式标准写法

```html
<svg class="ti" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     width="24" height="24" aria-hidden="true">
  <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
        stroke-width="2" d="..."/>
</svg>
```

关键点：
- Tabler 的 path 自带 `stroke="currentColor"`，所以**图标颜色跟着父元素 `color` 走**，不需要给 SVG 单独设色。
- 想用 CSS 控制尺寸时，加 `--no-size-attrs` 生成不带 `width/height` 属性的版本，然后用 CSS 给 `.ti` 设尺寸。

---

## 四、尺寸 token（后台系统推荐值）

| 场景 | 尺寸 | 说明 |
|---|---|---|
| 内联在正文里的图标 | 14–16px | 与文字基线对齐，`vertical-align: -0.125em` |
| 按钮、输入框、表格行操作 | 16px | 后台系统最高频尺寸 |
| 侧边导航、Tab 标签 | 20px | |
| 卡片标题、模块入口 | 24px | |
| 空状态、引导页主图标 | 48–64px | 配灰阶配色，别用饱和色 |

**小尺寸要降描边**：Tabler 默认 `stroke-width: 2`，在 16px 以下会显糊。小于 16px 时用 CSS 覆盖：

```css
.ti-sm path { stroke-width: 1.5; }
```

---

## 五、颜色规范

图标默认继承 `color`。建议在根节点定义语义色，图标只引用变量：

```css
:root {
  --icon-default: #475569;   /* 常规 */
  --icon-muted:   #94a3b8;   /* 次要、禁用 */
  --icon-primary: #2563eb;   /* 主色、可点击 */
  --icon-success: #16a34a;   /* 通过、已完成 */
  --icon-warning: #d97706;   /* 待处理、风险提示 */
  --icon-danger:  #dc2626;   /* 驳回、逾期、错误 */
}
```

用法：`<span style="color: var(--icon-danger)"><iconify-icon .../></span>`

> **金融/投行场景提醒**：涨跌颜色遵循国内习惯——**涨用红、跌用绿**，与欧美相反。图标配色不要在这里搞反。

---

## 六、交互态

图标本身不处理交互，用父元素承接：

```html
<button class="btn">
  <iconify-icon icon="tabler:file-export" width="16" height="16" aria-hidden="true"></iconify-icon>
  <span>导出</span>
</button>
```

```css
.btn { display: inline-flex; align-items: center; gap: 6px; color: var(--icon-default); }
.btn:hover  { color: var(--icon-primary); }
.btn:active { transform: translateY(1px); }
.btn:disabled { color: var(--icon-muted); cursor: not-allowed; }
```

- **对齐**：一律用 `display: inline-flex; align-items: center; gap: 6px`，不要靠 `vertical-align` 猜。
- **可点击区域**：纯图标按钮的实际点击区不小于 32×32，图标 16–20px 外面补 padding。

---

## 七、无障碍（交付给开发必写）

| 情况 | 写法 |
|---|---|
| 图标旁已有文字 | `aria-hidden="true"`，避免重复朗读 |
| 纯图标按钮 | 图标 `aria-label="导出"`，或给 `<button>` 加 `aria-label` |
| 表意状态图标（如"已逾期"） | 用 `role="img"` + `aria-label="已逾期"` |

---

## 八、常见陷阱

1. **别混搭图标集**。Tabler 的描边是圆头 `stroke-linecap="round"`，掺入方头图标会立刻显得廉价。
2. **别用图标当唯一信息载体**。风险状态光靠一个红色三角不够，必须配文字。
3. **别硬编码颜色**。内联 SVG 里把 `currentColor` 改成固定色，后续换肤就废了。
4. **别在 HTML 里重复贴同一个图标**。内联模式下如果同一图标用超过 5 次，抽成 `<symbol>` + `<use>`。
5. **别用 emoji 替代图标**。emoji 跨平台字形不一致，在正式系统界面里会失控。

---

## 九、图标名必须先校验

图标名是**硬事实**，不能凭感觉写。像 `tabler:risk`、`tabler:audit`、`tabler:workflow`、`tabler:approve` 这些看起来非常合理的名字，在 Tabler 里**都不存在**。

所有写入代码的图标名，必须过一遍校验脚本：

```bash
python scripts/icon_check.py tabler:building-bank tabler:circle-check
```

输出 ❌ 的一律重选，不许"先写上再说"。
