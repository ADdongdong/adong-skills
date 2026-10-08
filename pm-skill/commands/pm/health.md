---
name: pm-health
description: ".planning/ 目录完整性检查。验证项目结构、必需文件、配置有效性。--repair 自动修复缺失文件。"
argument-hint: "[--repair]"
---

# /pm-health — 项目健康检查

触发 `pm-skill`，验证 `.planning/` 目录完整性。

## 工作流

1. **结构验证**：
   - `.planning/` 目录存在？
   - `phases/` 目录存在？
   - 所有必需文件存在？（PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json）

2. **内容验证**：
   - config.json 是否有效的 JSON？
   - PROJECT.md 是否有必需的章节？
   - ROADMAP.md 阶段数与 `phases/` 目录一致？
   - STATE.md < 100 行？

3. **阶段验证**：
   - 每个 ROADMAP 中的阶段是否有对应目录？
   - 完成的阶段是否有 SUMMARY.md 和 VERIFICATION.md？
   - 文件命名是否符合约定？（NN-name/NN-MM-PLAN.md）

4. **报告生成**：
   ```
   ## .planning/ 健康报告
   
   ### 结构
   ✅ .planning/ 存在
   ✅ phases/ 存在
   ❌ REQUIREMENTS.md 缺失
   
   ### 阶段
   Phase 1: ✅ Plans(1) ✅ Summary ✅ Verified
   Phase 2: ⚠️ Plans(1) ❌ Summary ❌ Verified
   
   总体评分: {score}/10
   ```

5. **自动修复**（`--repair` 标志）：
   - 缺失文件从模板重新创建
   - 无效 config.json → 使用默认值
   - 缺失目录 → 创建

## 关键规则

- 不自动修复（除非 `--repair`）
- 中文输出
