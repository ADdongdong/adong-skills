# PRD & 交付物验证模式

> 改编自 spec-skill 的 verification-patterns.md，适配 PM 产物验证。
> 核心原则：**存在 ≠ 实质化**。必须用 grep 检测占位符。

---

## 通用桩检测模式

### 占位符残留检测
```bash
# 检测未填充的占位符
grep -n '\[待补充\]\|\[placeholder\]\|\[描述\]\|\[内容\]\|\[产品名称\]\|\[日期\]\|\[姓名\]' {file}

# 检测 TODO/TBD 标记（表示未完成）
grep -n 'TODO\|TBD\|FIXME\|XXX' {file}

# 检测空表格行（模板残留）
grep -n '| {.*} |' {file}
```

### 内容实质性检测
```bash
# 文件行数检查（< 模板预期 80% = 不完整）
wc -l {file}

# 空白段落检测
grep -n '^$' {file} | wc -l

# 模板原文未替换（检测模板中的固定文本）
grep -n '\[市场机会、用户痛点' {file}
```

---

## PM 产物特定验证

### PRD 验证
```bash
# 所有章节标题存在
grep -c '^## ' prd.md  # 应 ≥ 模板定义的章节数

# 用户故事的验收标准非空
grep 'AC-' prd.md | grep -v '\[待补充\]' | wc -l

# P0 功能有对应的用户故事（交叉引用检查）
grep 'P0' prd.md | wc -l  # P0 功能数
grep 'US-' prd.md | grep 'P0' | wc -l  # 有用户故事的 P0 数
# 两个数字应该一致
```

### 研究报告验证
```bash
# 数据来源引用（所有数据应有来源）
grep '来源\|source\|from' research.md | wc -l

# 竞品数验证
grep -c '### 竞品\|## 竞品' research.md  # 应 ≥ 配置的竞品数

# 结论存在性
grep -c '建议\|推荐\|action' research.md  # 应有可执行的建议
```

### 策略画布验证
```bash
# 9 个区块全部填充
grep -c '^## [0-9]\.' strategy.md  # 应 = 9

# 价值主张非空
grep '作为 \*\*.*\*\*' strategy.md  # JTBD 格式存在
```

---

## 交叉引用验证

### PRD ↔ 研究报告
```bash
# PRD 是否引用了研究结论
grep -i 'research\|研究报告\|用户画像\|竞品分析' prd.md
# 应至少找到 1 处引用
```

### 策略 ↔ 研究
```bash
# 策略是否基于研究
grep -i 'research\|研究报告\|TAM\|SAM\|竞品' strategy.md
# 应至少找到 1 处引用
```

### 路线图 ↔ 阶段产出
```bash
# 验证 ROADMAP 中的阶段数与 phases/ 目录一致
ls -d .planning/phases/*/ | wc -l
grep -c '| [0-9]\+ |' ROADMAP.md
# 两个数字应一致（排除表头）
```

---

## 质量维度评分

每次验证时对以下维度评分（0.0-1.0）：

1. **完整性**: 所有必填章节是否存在且实质化？
2. **一致性**: 产物间引用是否建立？（PRD → Research, Strategy → Research）
3. **可执行性**: 验收标准是否具体？（grep 5 秒内可验证）
4. **数据溯源**: 数据是否有来源标注？（URL / wiki / 文件引用）

总分 = 平均分。≥ 0.8 视为通过。

---

## 更新指南

- 新增产物类型 → 添加对应的验证模式
- 发现新的占位符模式 → 更新通用检测正则
- 中文输出
