# 每日推文选题池（跨领域 · 费曼科普）

目标：每天一篇，用费曼对话体把「难懂的概念」讲通俗。选题不限于 AI——
**AI 技术、金融投资、通用商业/产品** 都行，跨领域混合推进，避免单调。

## 选题机制
- 每次运行，从下方池子里**推荐 3–5 个**（跨领域混合、优先选未用的），用选择卡让用户挑。
- 用户也可以直接手动输入自己的选题（如「给我写讲久期的」），跳过推荐。
- 跑完一篇，在末尾「已用记录」里打勾 + 日期，下次优先推未用的。

---

## 领域 A · AI / Agent（技术向）
- A0 LLM 演化史：从「聊天」到「办事」，为什么 Agent 必然出现（打字机→秘书→实习生）✅ 2026-07-31
- A1 什么是 AI Agent（从「问答」到「办事」）✅ 2026-07-30
- A2 ReAct 循环：思考 → 行动 → 观察 ✅ 2026-08-03
- A-mcp MCP 协议：从 Function Calling 到统一接口（万能插头）✅ 2026-07-31
- A3 记忆（Memory）让 Agent 记住上下文 ✅ 2026-08-04
- A4 工具调用（Tool Use）让 Agent 动手干活
- A5 规划（Planning）把大目标拆成步骤
- A6 怎么看懂模型升级（benchmark 三维度 + 四步法）✅ 2026-08-03
- B1 什么是 RAG（检索增强生成）
- B2 Embedding 与向量库（文字怎么变成可搜索的向量）
- B3 提示词工程（怎么把话说清楚）
- B4 上下文窗口（模型能「看到」多少）
- B4a 缓存命中/未命中（Prompt Caching：省的是「读题」不是答案）✅ 2026-07-30（用户自选）
- B5 多智能体：为什么需要多个 Agent 分工 ✅ 2026-08-06
- B6 微调 vs 提示（什么时候才要训练）
- B7 推理优化：蒸馏 / 量化 / 投机解码
- B8 AI 编程（Copilot / Agent 写代码）
- B9 评测与安全（怎么知道 Agent 真靠谱）

## 领域 C · 金融 / 投资（结合用户投行产品背景）
- C1 除权除息：分红为什么不是「白捡钱」
- C2 ROE：为什么高 ROE 的公司更值钱
- C3 基金分红：红利基金那笔钱到底哪来的
- C4 ETF：一篮子股票怎么像一只股票买卖
- C5 可转债：债主怎样变成股东的
- C6 债券久期：利率一动，价格动多少
- C7 PE / PB 估值：一只股票便宜还是贵怎么看
- C8 现金流折现（DCF）：一家公司的未来值多少钱
- C9 资产配置：别把所有鸡蛋放一个篮子
- C10 动量因子：涨的还会接着涨吗
- C11 雪球结构：高收益背后的风险开关
- C12 ABS 储架发行（结合用户业务）
- C13 债券付息兑付：钱是怎么准时到账的
- C14 函证业务：审计怎么确认账面数字没造假
- C15 IPO 上市流程：承揽·承做·承销，谁在干活谁在赚钱 ✅ 2026-07-31

## 领域 D · 通用商业 / 产品（轻量、接地气）
- D1 什么是 MVP（最小可行产品）
- D2 用户画像 Persona：你的产品到底服务谁
- D3 A/B 测试：两个版本到底哪个更好
- D4 需求优先级：RICE / Kano 怎么排
- D5 复利：为什么时间比收益率更可怕

---

## 已用记录
- A1 · 2026-07-30 · 端到端验证通过，已推送草稿（标题：Agent 到底是什么？用「点外卖」给你讲明白）
- B4a · 2026-07-30 · 用户自选题「缓存命中/未命中」，已推送草稿（标题：大模型的「缓存命中」到底省了什么？用看小说的书签给你讲明白）
- A0 · 2026-07-31 · 用户指定为主线引子（解释为什么 Agent 必然出现），已推送草稿（标题：大模型是怎么从「聊天」进化到「办事」的？用打字机给你讲明白）
- A-mcp · 2026-07-31 · 用户指定 MCP 协议（Function Calling→统一接口），已推送草稿（标题：MCP 到底是什么？用「万能插头」给你讲明白）
- C15 · 2026-07-31 · 用户指定 IPO 金融科普（以长鑫存储上市为例，承揽/承做/承销），已推送草稿（标题：长鑫上市，券商到底赚了多少钱？一文讲清 IPO 里的"承揽、承做、承销"）
- A2 · 2026-08-03 · Agent 主线正经下一站，承接 LLM 演化史引子：ReAct=想→做→看循环（修水管类比），含 Yao et al. 2022 论文数据(ALFWorld 71% vs 37%)，已推送草稿
- A6 · 2026-08-03 · 用户指定"普通人怎么看懂大模型厂商每次模型升级的提升"，以 DeepSeek V4-Flash 7/31 正式版为案例（Agent benchmark 大涨、原生 Responses API、仅 Flash API 升级），已推送草稿
- A3 · 2026-08-04 · 用户四问（无状态/多用户隔离/Agent关系/省token）收成一个主题"大模型没有记忆，记忆是应用层喂回去的上下文"，已推送草稿（标题：大模型其实没有记忆：一次讲清对话、多用户隔离、Agent 和省 token 的底层逻辑）
- B4+B1 · 2026-08-06 · 深化上下文窗口管理：截断/滑窗、摘要压缩、RAG 外挂具体干什么 + RAG 优劣势 + WorkBuddy/Codex 主流 Agent 实战组合拳，承接 08（A3），已生成待推送
- B5 · 2026-08-06 · 用户指定"多专家模式底层实现逻辑"，参考 Hermes 3-7 多专家/多上下文隔离文档：N+1独立循环+预算per-instance+实例级隔离+两层并发（协程内部/线程进程间），投行项目组类比，已推送草稿
- 11·GPT-5.6 Sol · 2026-08-07 · 用户给 OpenAI 官方文链接(improving-gpt-5-6-sol)，费曼对话体第11篇：GPT-5.6 Sol 更聚焦(先答真问题)/更可靠(硬事实错误↓68%,金融医疗法律)/滑动条控思考深度(Instant=Thinking同一模型,体验连续)/免费Luna无限聊；呼应前几篇省token·多专家隔离·上下文管理原理。封面改用 /guizang-social-card-skill(Swiss IKB Blue,21:9 S08 Image Hero+cand2 照片+1:1 短标题"GPT-5.6 Sol 改了啥"+pair-preview)。**已推送草稿成功(media_id rpOZCEvfKNcn7bvXZgohPyNXg9E6r0pgAmnBL71IApt6UqEnZIU5_BtGS3T_2jXc)**। IP白名单改用整段 219.144.248.0/24 后一次通过
- 12·RAG技术 · 2026-08-07 · 用户点名"详细说RAG：为什么ChatGPT问答那么智能"，费曼对话体第12篇（承接08记忆/09上下文窗口）：幻觉=闭卷硬编→RAG=开卷(检索增强生成,R/A/G拆解)；双链路(离线:切块→Embedding→向量库 / 在线:问题向量化→Top-K相似检索→拼接上下文→LLM带引用作答)；向量=语义坐标(神似非形似,水果→苹果例子)；ChatGPT过人之处=联网检索+引用溯源[1][2]+私有知识库(呼应11篇事实错误↓68%机制)；RAG vs 微调(换参考书vs换脑子,微调定调性+RAG给事实)；三坑(检索不准GIGO/窗口装不下/不会跨文档推理)+进化(混合检索BM25/Agentic RAG=ReAct/GraphRAG)。**插图三轨制（用户定案，此后系列通用）**：比喻图→baoyu+ImageGen(AI手绘,images/ai_openbook.png)｜知识框架→architecture-diagram浅色大字三层分组(images/rag_framework.png)｜分支图→Mermaid。**已推送草稿成功(media_id rpOZCEvfKNcn7bvXZgohPzn-xtPgrYExYf-pFMSiRMdgcMgIObZ2gMMIsLHHMwH4)**；IP白名单整段219.144.248.0/24一次通过。三轨制详见项目MEMORY.md
- 下次推荐优先：C1（除权除息）/ C7（PE/PB）/ A5（规划 Planning）/ A4（工具调用 Tool Use）/ D1（MVP）
- 13·ReAct对话循环 · 2026-08-08 · 用户点名（参考 Hermes 3-1 对话循环四阶段 + 3-3 IterationBudget）：AI 答一个问题背后反复调 LLM。四阶段循环 Build→Call→Parse→Execute（餐厅服务生类比：开台/问主厨/回话/取料）；**对话结束**=Parse 看 finish_reason（stop=说完/tool_calls=继续/length=截断续写）；**调用上限**=默认 90 次迭代（非 token），每调 API 扣 1；**上限判断**=三层防线（硬计数 api_call_count / 可退还 iteration_budget+execute_code refund / 逃生舱 grace_call），空转可拦冻结不可拦。三轨制配图：框架图 architecture-diagram 浅色（react-loop.html 四阶段+循环+90+三层防线）/ Mermaid 循环流程图 / baoyu AI 餐厅四格插画（兼做封面）。**IP 白名单跨段坑**：出口 219.144.248.x → 36.163.168.24 换段，白名单需多 /24 共存。**已推送成功(media_id rpOZCEvfKNcn7bvXZgohP9YxGWUf5I7OxnCg4vqyepB6Zab10gDrHhR6B3S82hk0)**
- 14·通用Agent vs 自建Agent · 2026-08-10 · 用户自拟主题+五轮反问式讨论定稿（独立单篇，脱离系列）：通用 Agent+Codex/WorkBuddy/豆包/扣子 这么强为什么还自建？论据链：MCP 解决管道不解决确定性 → 把规则写进 prompt 不可靠（LLM 概率模型,10000 笔 99%=100 笔错）→ 概念澄清 workflow(代码写死)/agent(LLM 自主决策)/通用 agent → 开源框架拿来改→"改改"才是真工作量(上下文工程/工具工程/Guardrail 工程) → 从"造引擎"到"调引擎"。**章节标题用【】括号格式**（**加粗在微信渲染 API 里和正文无区别，读者找不到分界）。三轨制配图：框架图 architecture-diagram 浅色（680 画布/19px 标题/箭头 x=340 中线）/ Mermaid 决策路径图 / Unsplash 修表匠封面。**已推送成功(media_id rpOZCEvfKNcn7bvXZgohP08CfJpzpOP33pBkbGIUw5hieHx7U4SmTZO5jIuLAFA_)**；资料库已同步「推文集合」下
- 16·DeepSeek Harness · 2026-08-18 · 用户点名（从 08-17 费曼 L5 输出验证对话直接整理为推文）：Agent=Model+Harness 骨架公式（马具类比→升级为一台机 vs 组装机）；LLM 碰不到文件、工具调用链路 6 步闭环；Harness 六部件（工具/循环/上下文/权限/技能/UI），skill 本质是提示词；一体机（WorkBuddy/Claude Code 部件焊死）vs 组装机（dsh 一切皆插件，连模型接入适配器都换）；优缺点对比（开箱即用 vs 自由定制）；WorkBuddy 不凉的判断（非科班门槛+日常办公够用+积分 vs 买 token）。三轨制配图：知识框架图 architecture-diagram 浅色大字（大脑+身体+六部件+被调用资源+总结条, agent-framework.html）/ Mermaid 工具调用链路（tool_chain.png）/ 手写 SVG 对比图（compare.png 左右并排一体机焊死链 vs 组装机积木星型）。封面：Unsplash 真实照片（cand1=蓝色电路板特写，jXd2FSvcRr8），与清新蓝主题融合。**已推送草稿成功(media_id rpOZCEvfKNcn7bvXZgohPxrEY1JjHsRlL2Whpr5ce2tDpe3eM-LqD20veMEFzql8)**
- 17·大模型定价（DeepSeek V4.1 Flash）· 2026-09-11 · 用户四轮深挖对话直接收成一篇（承接 A6 看懂模型升级）：**以 V4.1 Flash 9/10 发布为索引**串起三层——① 定价=按烧算力收费不是按字数（打字社 vs 智库）；② **输入/输出价差的物理原因**（prefill 可并行=100 人分页读，decode 只能串行=第 2 个字取决于第 1 个，瓶颈是显存带宽不是算力，故输出贵 2~8 倍）；③ **Agent 场景该盯输入价**（每轮重发全部历史：10 轮累计输入 10 万 / 输出 3 千，输入占账单 89%；你打的那句话只占 0.5%）→ 缓存命中价（0.02 元 vs 1 元，50 倍）→ **CED 架构**（40 层拆 20 层编码器 + 20 层解码器，prompt 不进解码器、读只激活 8B vs 写 16B；CSA2 的 Full/Reindex/Reuse 层间"抄作业"；FP4 存 KV；SWA 只重放最后 128 token → 890 字节/token = 上一代 1/4、V1 的 1/437）；MoE 类比"1000 人医院只看 3 个科室"（1 共享 + 384 路由，每 token 激活 6 个）。**三张图**：知识框架图 architecture-diagram 浅色大字 8 卡三层（framework.html，放文章开头）/ Mermaid 读并行 vs 写串行（**踩坑：外层 TB + 两个孤立 subgraph 会被并排渲染成超宽图 → 字号被压糊；加一条真实语义跨边 `读完了才开始写` 才转成竖排**）/ Mermaid CED 读写分离。**封面改走 Pexels**（Unsplash 搜索页已被 Anubis 反爬挡住，WebFetch 只回挑战页）→ cand1=904618 手写笔记本；写进 cover.html 时**必须直接替换 `{{配图绝对路径}}`**（render_cover.cjs 的 art.* 分支是死代码）。章节标题用【】格式。**已推送草稿成功(media_id rpOZCEvfKNcn7bvXZgohPwNQ-wgxavTGrn7eneg2fgDakYpV_phSmtz6r71fRarv)**；净化移除 14 处背景色、3 张正文图自动上传替换
