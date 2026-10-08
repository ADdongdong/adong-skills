---
name: pm-verify
description: "验证阶段 N 的完成度。检查 must_haves（truths/artifacts/key_links），生成验证报告，识别缺口。"
argument-hint: "<phase-number>"
---

# /pm-verify — 验证阶段

触发 `pm-skill`，验证阶段 N 的交付物是否满足计划要求。

## 工作流

1. **加载验证上下文** — 参考 `workflows/verify-work.md`：
   - 读取阶段所有 PLAN.md，收集 must_haves
   - 读取所有 SUMMARY.md，了解已完成的交付物
   - 加载 `references/verification-patterns.md`

2. **自动化检查** — 如适用：
   - 文件存在性：所有 artifact 文件是否存在
   - 内容实质性：文件是否有实质内容（非仅占位符）
   - 模板符合性：是否遵循模板结构
   - 交叉引用：ROADMAP ↔ 阶段产出物是否一致

3. **Must-haves 验证** — 逐项检查：
   - **truths**：系统是否表现出预期行为（从 PM 视角验证）
   - **artifacts**：所有产物文件是否存在且实质化
     - 检测占位符：`[待补充]`、`TODO`、`TBD`、空白段落
     - 检测模板原文未替换、章节缺失等质量问题
   - **key_links**：产物之间的关键关联是否建立
     - PRD 是否引用了研究结论
     - 策略是否引用了竞品分析

4. **缺口处理**：
   - 关键缺口 → 创建修复计划 → 建议重新执行
   - 非关键缺口 → 记录为已知问题 → 可过渡到下一阶段

5. **生成报告**：
   - 创建 `NN-VERIFICATION.md`（遵循 `templates/VERIFICATION.md`）
   - 展示结果 → STOP → 等待用户确认

## 产出物

- `.planning/phases/NN-name/NN-VERIFICATION.md` — 验证报告

## 关键规则

- 存在 ≠ 实质化。grep 检测占位符和桩内容。
- 关键缺口必须修复后才能 transition
- 非关键缺口记录即可，不阻塞
- 中文输出
