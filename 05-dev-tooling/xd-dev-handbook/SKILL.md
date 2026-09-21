---
name: xd-dev-handbook
disable-model-invocation: true
description: >-
  XD开发手册 — XD 系列项目统一开发规范（仅限用户手动调用 /xd-dev-handbook）。
  覆盖 Java 后端（Spring Boot 2.7 + Java 8 + Gradle 多模块、三层架构、统一响应/异常）
  与前端（UmiJS 3 + React 17 + Ant Design 4 + dva、路由集中、request 封装）的编码约定，
  保证新代码与现有框架风格完全一致。
---

# XD 开发手册

本手册沉淀 XD 系列项目（函证系统等）实际使用的**公共框架规范**，只包含通用、可复用的技术栈约定；任何私有/内部框架依赖不在本手册范围内。新写的 Java 代码与前端代码必须遵循本手册，与现有框架保持一致。

## 1. 技术栈总览

| 层 | 技术 | 版本 |
|---|---|---|
| 后端运行时 | Java | 1.8 |
| 后端框架 | Spring Boot | 2.7.18 |
| 构建工具 | Gradle（多模块） | 7.x 兼容 |
| ORM/数据访问 | Spring JdbcTemplate（手写 SQL + 预编译参数） | - |
| 数据库 | 达梦 DM8（SQL 兼容 Oracle 风格，大写字段名） | - |
| API 文档 | Swagger（springfox，@Api/@ApiOperation/@ApiModelProperty） | 2.x |
| 工具库 | Lombok 1.18、fastjson、commons-lang3 | - |
| 日志 | log4j2（异步 + disruptor），禁止混入 logback/log4j 1.x | 2.17.1 |
| 前端框架 | UmiJS 3.5 + React 17 + Ant Design 4 | - |
| 状态管理 | dva | - |
| HTTP 客户端 | axios（统一封装 request） | - |
| 国际化 | react-intl / umi locale | - |

## 2. 后端规范

详细代码样例见 [references/backend.md](references/backend.md)。

### 2.1 工程组织（Gradle 多模块）

- 根 `settings.gradle` 聚合所有子模块，根 `build.gradle` 统一声明版本（`ext` 常量）、仓库、编码 UTF-8、`-parameters` 编译参数、全局依赖排除。
- 模块划分建议：
  - `xxx.web` / `xxx.http.api`：全部 `@RestController`，只做参数接收与响应封装，不含业务逻辑
  - `xxx.core`：业务实现（Service 实现 + Dao）
  - `xxx.service.api`：Service 接口 + Entity/Vo/Dto 定义
  - `xxx.system` / `xxx.common`：系统级、公共组件
- 版本统一在根 build.gradle `ext` 中管理，子模块不自行指定版本。

### 2.2 分层与命名（强制）

```
Controller（web 模块）
  └─ IXxxService（service.api 模块，接口）
       └─ XxxServiceImpl（core 模块，@Service 实现）
            └─ XxxDao（core 模块，@Repository/@Component，手写 SQL）
```

| 类型 | 命名与注解 | 规则 |
|---|---|---|
| Controller | `XxxController`，`@Slf4j @Api(tags=...) @RestController @RequestMapping("/模块/资源")` | 方法返回 `ResponseData<T>`；每个接口加 `@ApiOperation`；通过 `HttpServletRequest` 参数获取会话用户 |
| Service 接口 | `IXxxService` | 定义业务方法签名，不放实现 |
| Service 实现 | `XxxServiceImpl`，`@Slf4j @Service implements IXxxService` | 用 `@Resource` 注入 Dao（不用 @Autowired on field 亦可，统一即可）；业务校验失败抛业务异常 |
| Dao | `XxxDao`，`@Repository` | 手写 SQL（字符串拼接 SQL + `?` 占位 + 参数数组），用 JdbcTemplate 执行；SQL 关键字小写、表名/字段名大写 |
| Entity | `XxxEntity`，`@Getter @Setter implements Serializable` | 字段驼峰，对应数据库大写下划线字段；含 `serialVersionUID`；Swagger 字段用 `@ApiModelProperty(value="中文")` |
| Vo/Dto | `XxxVo`（视图/请求）、`XxxDto`（传输） | 组合多个 Entity 字段或查询参数，不映射单表 |

### 2.3 统一响应与异常（强制）

- 所有接口返回 `ResponseData<T>`：字段 `code`（200 成功）、`message`（提示信息）、`data`（泛型数据）。
- 成功：`ResponseData.success(data)` / `new ResponseData<>("提示语")`；失败：`ResponseData.error(500, "错误信息")`。
- 业务异常统一抛 `BusinessException(msg)`（继承 RuntimeException），由全局异常处理器 `@RestControllerAdvice` 捕获并转成 `ResponseData.error`；Controller 内不吞异常、不打印堆栈后返回 error 的写法仅允许在确需兜底的场景。

### 2.4 数据访问

- 用 `JdbcTemplate` 手写 SQL：查询用 `query(sql, args, BeanPropertyRowMapper)`；分页在 Dao 层完成（`Page<T>` + `PageSort` 分页参数对象，含 page/pageSize/sortField/sortOrder）。
- 动态条件：`StringBuilder` 拼 SQL + `JSONArray`/`List<Object>` 按序追加 `?` 参数，禁止字符串拼接用户输入。
- 写操作：`insert`/`update`/`delete` 用 `update(sql, args...)`，主键用雪花 ID/序列，不做数据库自增假设。
- 每个表对应一个 `XxxEntity`，公共审计字段统一为：`ID`、`CREATE_USER`、`CREATE_TIME`、`UPDATE_USER`、`UPDATE_TIME`。

### 2.5 配置

- `application.yml` + 多环境 `application-{env}.yml`（如 hztest/hzpre），`spring.profiles.active` 切换。
- 关键配置：`server.servlet.context-path`（如 `/i5_hz_api`）、`spring.jackson.time-zone: GMT+8` + `date-format: yyyy-MM-dd HH:mm:ss`、`spring.redis`（session 共享 store-type: redis）、`spring.servlet.multipart` 大小限制。
- 日志用 log4j2：`spring-boot-starter-log4j2` + 全局排除 `spring-boot-starter-logging`（logback），异步 appender 配 disuptor。

## 3. 前端规范

详细代码样例见 [references/frontend.md](references/frontend.md)。

- **配置**：`.umirc.ts` 为唯一配置入口——devServer（host `localhost`，端口自定义）、`base`/`publicPath`（如 `/i5-confirm/`）、`proxy`（将 `/xxx_api` 前缀转发到后端端口并 pathRewrite 重写为 context-path）、`alias`（`$components/$utils/$pages/$config` 等以 `$` 开头）、`routes` 引入集中路由表。
- **路由**：全部集中在 `src/routes/*.js`，按业务域拆文件（manage/project/mobile/external...）后在 `index.js` 合并导出；需要登录的路由用 `wrappers: ['@/routes/privateRoute.js']` 做鉴权包装；路由项为 `{ path, component, wrappers, routes }` 嵌套结构。
- **请求**：统一走 `src/utils/request.js` 封装的 axios 实例——拦截器中加全局 loading（请求计数器）、认证头（UserID 令牌）、统一错误通知（`showNotification`）、blob 下载处理；页面组件不直接 import axios。
- **页面组织**：`src/pages/<业务域>/<功能>/index.js` + 同目录 `index.less`；可复用纯展示组件放 `src/components`，业务组合组件放 `src/businessComponents`；全局模型放 `src/models`（dva）。
- **UI**：Ant Design 4 组件优先，样式用 less，主题变量集中 `src/theme`；生产构建用 `compression-webpack-plugin` 打 gzip，开发环境保留 console、生产经 babel 插件移除。

## 4. 快速核对清单（写代码前后自查）

- [ ] 新接口放在 Controller（web 模块），返回 `ResponseData<T>`，有 `@ApiOperation` 中文说明
- [ ] 业务逻辑在 `XxxServiceImpl`，接口定义在 `IXxxService`；跨层依赖经由接口注入
- [ ] SQL 全部手写在 Dao 层，`?` 占位防注入；字段名大写下划线
- [ ] 异常统一 `BusinessException` + 全局处理器；不允许裸 `catch(Exception)` 后静默返回
- [ ] 新增表 Entity 带审计字段与 `Serializable`；Swagger 注解齐全
- [ ] 前端新页面已注册到 `src/routes` 且加 privateRoute 包装；请求全部走封装的 request
