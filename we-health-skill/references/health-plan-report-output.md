# 健康管理方案 HTML 报告输出

> 本文件由 SKILL.md 主流程按需引用，不可独立执行。
>
> **适用场景**：仅「健康管理方案」场景（意图识别第 8 条），且接口已返回**完整方案**（含控制目标、饮食方案、运动方案三部分正文）时，才进入 HTML 报告输出流程。
>
> **定位**：HTML 报告是「展示层」的格式优化，不改内容。`query.py` 只输出 `data.markdown_content`，由 AI 在展示时决定是否整理为 HTML 报告。Markdown→HTML 属核心规则 14「可对格式排版做适当优化润色」范畴。

---

## 触发条件

| 情形 | 是否生成 HTML 报告 |
|------|:----------------:|
| 接口返回完整方案（含控制目标/饮食方案/运动方案） | ✅ 生成 |
| 接口返回追问（继续收集信息） | ❌ 不生成，按多轮流程继续追问 |
| 特殊生理状态/急性症状等触发阻断，返回就医引导 | ❌ 不生成，按原文文字回复 |
| 用户明确表示只要文字、不要报告 | ❌ 不生成，原样输出 Markdown |

---

## 核心规则

| 规则 | 说明 |
|------|------|
| 内容只来自接口 | 控制目标（血糖/血压/血脂/BMI/腰围/心率）、饮食方案、运动方案三部分正文只能来自接口返回，严禁补写、扩写或改写 |
| 完整转换不删减 | `markdown_content` 必须完整映射为 HTML，不得删减、精简、截断或改写正文 |
| 免责声明逐字保留 | 接口自带免责声明必须完整展示、逐字保留；仅在确无免责声明时，按核心规则 11 追加固定免责声明 |
| 仅做格式优化 | Markdown→HTML 只做结构映射与排版，不改变语义与结构，不新增接口未给出的结论、风险等级或总结陈词 |
| 自然章节标题 | 章节用「控制目标 / 饮食方案 / 运动方案 / 免责声明」等自然标题，禁止「模块A/B/C」等内部标签 |
| 结构元素映射 | 标题、表格、列表、加粗、链接等 Markdown 结构一一映射为对应 HTML 元素，链接 URL 保留完整 |
| **默认样式可覆盖** | 下文「默认样式与布局」为保证多份报告视觉统一的基础外观；若用户希望自定义配色/字号/布局，允许整体替换样式块或调整变量，**不拦截、不强求一致**，改样式不视为改内容 |

---

## 默认样式与布局

### 整体布局顺序

按以下顺序组织报告，顺序固定、不得调换：

1. **报告头**：报告标题（如「个人健康管理方案」）+ 生成日期
2. **用户信息（方案生成依据）**：汇总本会话已收集的年龄、性别、身高、体重等字段，**未提供的字段不写、不猜**
3. **控制目标**：接口返回的控制目标正文（血糖/血压/血脂/BMI/腰围/心率等）
4. **饮食方案**：接口返回的饮食方案正文（含结构、手掌法则等原样保留）
5. **运动方案**：接口返回的运动方案正文（含安全分级、目标心率等原样保留）
6. **免责声明**：接口自带免责声明逐字展示；确无时追加核心规则 11 的固定免责声明

### 默认 HTML/CSS 模板

> 以下为保证视觉统一的基础模板：颜色/字号/圆角集中在 `:root` 变量，改一处即全局生效；正文三部分（控制目标/饮食/运动）按 Markdown 结构映射填入对应位置，不补写内容。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>个人健康管理方案</title>
<style>
  :root {
    --primary: #0F766E;
    --primary-50: #F0FDFA;
    --ink: #1F2937;
    --ink-2: #4B5563;
    --line: #E5E7EB;
    --bg: #F6F8FA;
    --card: #FFFFFF;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--ink);
    line-height: 1.75; padding: 32px 16px;
  }
  .report { max-width: 860px; margin: 0 auto; background: var(--card);
    border-radius: 12px; box-shadow: 0 4px 24px rgba(16,24,40,.08); overflow: hidden; }
  .hero { background: linear-gradient(135deg, #134E4A, #0D9488); color: #fff; padding: 30px 36px; }
  .hero h1 { font-size: 22px; font-weight: 700; }
  .hero .meta { font-size: 13px; opacity: .9; margin-top: 6px; }
  .user-info { margin: 20px 36px 0; background: var(--primary-50);
    border-left: 4px solid var(--primary); border-radius: 8px; padding: 12px 16px; font-size: 14px; }
  .content { padding: 8px 36px 32px; }
  h2 { font-size: 18px; color: var(--ink); font-weight: 700;
    margin: 28px 0 14px; padding-left: 12px; border-left: 4px solid var(--primary); }
  h3 { font-size: 15px; color: var(--primary); font-weight: 600; margin: 18px 0 8px; }
  p { margin: 8px 0; }
  ul, ol { margin: 8px 0 8px 22px; }
  li { margin: 4px 0; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; margin: 10px 0 14px; }
  th, td { padding: 10px 12px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }
  th { background: var(--primary-50); color: var(--primary); font-weight: 600; }
  blockquote { background: var(--primary-50); border-left: 4px solid var(--primary);
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 14px 0; font-size: 13.5px; color: var(--ink-2); }
  .disclaimer { margin: 24px 0 8px; background: #FFF1F2; border-left: 4px solid #9F1239;
    border-radius: 0 8px 8px 0; padding: 14px 18px; font-size: 13px; color: #9F1239; }
  @media print { body { background: #fff; padding: 0; } .report { box-shadow: none; } }
</style>
</head>
<body>
<div class="report">
  <div class="hero">
    <h1>个人健康管理方案</h1>
    <div class="meta">生成日期：{{date}}</div>
  </div>
  <div class="user-info"><strong>用户基本信息：</strong>{{已收集信息摘要，未提供字段不写不猜}}</div>
  <div class="content">
    <h2>一、控制目标</h2>
    <!-- 接口返回的控制目标正文，按 Markdown 结构映射 -->
    <h2>二、饮食方案</h2>
    <!-- 接口返回的饮食方案正文，按 Markdown 结构映射 -->
    <h2>三、运动方案</h2>
    <!-- 接口返回的运动方案正文，按 Markdown 结构映射 -->
    <div class="disclaimer">
      <!-- 接口自带免责声明逐字保留；确无则核心规则 11 固定声明 -->
    </div>
  </div>
</div>
</body>
</html>
```

> 该模板只规定**基础外观与布局骨架**。食谱卡片、运动分阶段时间轴等增强排版为可选项，非默认必需；用户明确要更精致版式时可在此基础上扩展，但不得因此改动正文内容。

---

## 交付方式

- 将整理好的 HTML 写入本地 `.html` 文件并打开预览（present_files）
- 同时保留纯文本/Markdown 版正文供用户直接复制
- 报告内容不改变方案本身的任何信息

---

## 禁止行为清单

| # | 禁止行为 | 原因 |
|---|---------|------|
| 1 | 追问阶段就生成 HTML 报告 | 方案尚未完整，生成的是残缺报告 |
| 2 | 删减、精简、改写 `markdown_content` 正文 | 违反核心规则 14 |
| 3 | 补写接口未给出的内容（结论/风险等级/建议等） | 违反核心规则 16，自编方案内容 |
| 4 | 忽略、删减或改写接口自带免责声明 | 医疗合规红线 |
| 5 | 用「模块A/B/C」等内部标签做章节标题 | 违反评测 R8/D5，标签泄漏 |
| 6 | 修改或截断 Markdown 中的链接 URL | 违反核心规则 14，链接须保留完整 |
| 7 | 强制套用默认样式、拒绝用户的样式自定义请求 | 违反「默认样式可覆盖」规则，样式可改、内容不可改 |
