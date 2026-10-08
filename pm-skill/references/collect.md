# PRD Template Type Detection

Auto-detect the correct PRD template type from user requirements.
Use with `references/prompts/prd-research.md` for the full PRD workflow.

## Auto-Match Rule

**DO NOT ask "Which template type do you want?"** Infer from natural language.

### ToC (Consumer Product)
Keywords: APP, 用户, 消费者, 体验, 交互, 注册, 登录, 留存, 转化, 分享, 社交,
电商, 内容, 社区, 短视频, 直播, 游戏, C端, 移动端, iOS, Android, user experience, consumer, mobile app

Template: `references/templates/prd-toc.md`

### ToB (Business Product)
Keywords: SaaS, 企业, B端, 审批, 权限, 组织架构, ERP, CRM, 工单, 流程, 配置,
租户, 交付, 验收, 合同, 结算, 对账, enterprise, business, approval, workflow, tenant

Template: `references/templates/prd-tob.md`

### Backend (Admin System)
Keywords: 后台, 管理后台, CMS, 运营, 审核, 列表, 表单, 导入, 导出, 数据统计,
看板, 菜单, 操作日志, admin, dashboard, backend, operation, batch

Template: `references/templates/prd-tob.md` (adapted for admin context)

### Mini-Program
Keywords: 小程序, 微信, 支付宝, 扫码, 订阅消息, 授权, 分包, 主包, 分享, 裂变,
miniprogram, wechat, alipay

Template: `references/templates/prd-toc.md` (adapted with mini-program constraints)

## Decision Rules

1. **Clear match** (3+ keyword signals) → Auto-set. Confirm at Phase 2 GATE.
2. **Ambiguous** (signals for 2+ types) → Ask ONE clarifying question.
3. **NEVER** list all 4 types as multiple choice.
