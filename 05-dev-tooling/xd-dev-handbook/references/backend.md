# XD 开发手册 — 后端详细样例

与 SKILL.md 配套的可复制代码样例。全部为公共框架写法，可直接在新项目使用。

## 1. Gradle 工程骨架

### settings.gradle

```groovy
rootProject.name = 'xd-app'

include 'xd.web'
include 'xd.core'
include 'xd.service.api'
```

### 根 build.gradle

```groovy
subprojects {
    apply plugin: "java"
    apply plugin: "maven"
    version = "1.0.0"
    sourceCompatibility = "1.8"
    ext {
        springBootVersion = "2.7.18"
        springDependencyManagement = "1.0.10.RELEASE"
    }
    repositories {
        mavenLocal()
        mavenCentral()
    }
    tasks.withType(JavaCompile) {
        options.encoding = "UTF-8"
    }
    compileJava { options.compilerArgs << '-parameters' }
    compileTestJava { options.compilerArgs << '-parameters' }

    // 日志统一：全局排除默认日志实现，改用 log4j2
    configurations {
        all*.exclude group: "org.springframework.boot", module: "spring-boot-starter-logging"
        all*.exclude group: "org.slf4j", module: "slf4j-log4j12"
        all*.exclude group: "org.slf4j", module: "slf4j-simple"
        all*.exclude group: "commons-logging", module: "commons-logging"
    }
    dependencies {
        compileOnly "org.projectlombok:lombok:1.18.2"
        annotationProcessor "org.projectlombok:lombok:1.18.2"
        compile 'com.alibaba:fastjson:1.2.83'
        compile 'org.apache.commons:commons-lang3:3.14.0'
        compile 'io.springfox:springfox-swagger2:2.9.2'
        compile 'io.springfox:springfox-swagger-ui:2.9.2'
    }
}
```

### 启动模块 build.gradle（xd.web）

```groovy
buildscript {
    dependencies {
        classpath("org.springframework.boot:spring-boot-gradle-plugin:${springBootVersion}")
    }
}
plugins {
    id "java"
    id "org.springframework.boot" version "${springBootVersion}"
    id "io.spring.dependency-management" version "${springDependencyManagement}"
}
dependencyManagement {
    imports {
        mavenBom org.springframework.boot.gradle.plugin.SpringBootPlugin.BOM_COORDINATES
    }
}
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web:2.7.18'
    implementation 'org.springframework.boot:spring-boot-starter-log4j2:2.7.18'
    implementation 'com.lmax:disruptor:3.4.4'
    implementation 'org.springframework.boot:spring-boot-starter-data-redis:2.7.18'
    implementation 'org.springframework.session:spring-session-data-redis:2.7.18'
    implementation 'org.springframework.boot:spring-boot-starter-jdbc:2.7.18'
    implementation project(':xd.core')
    implementation project(':xd.service.api')
    testImplementation 'org.springframework.boot:spring-boot-starter-test:2.7.18'
}
```

## 2. 启动类

```java
package cn.xd.app;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class XdApplication {
    public static void main(String[] args) {
        SpringApplication.run(XdApplication.class, args);
    }
}
```

## 3. 统一响应 ResponseData

```java
package cn.xd.common.vo;

import java.io.Serializable;

public class ResponseData<T> implements Serializable {
    private static final long serialVersionUID = 1L;

    /** 200 成功，其余为失败码 */
    private int code;
    /** 提示信息 */
    private String message;
    /** 业务数据 */
    private T data;

    public ResponseData() { this.code = 200; }

    public ResponseData(T data) { this.code = 200; this.data = data; }

    public ResponseData(String message) { this.code = 200; this.message = message; }

    public ResponseData(int code, String message) { this.code = code; this.message = message; }

    public static <T> ResponseData<T> success(T data) { return new ResponseData<>(data); }

    public static <T> ResponseData<T> success(String message, T data) {
        ResponseData<T> r = new ResponseData<>(data);
        r.message = message;
        return r;
    }

    public static <T> ResponseData<T> error(int code, String message) {
        return new ResponseData<>(code, message);
    }

    public static <T> ResponseData<T> error(String message) { return error(500, message); }

    // getter/setter 省略（可用 Lombok @Data 替代）
}
```

## 4. 业务异常与全局处理器

```java
package cn.xd.common.exception;

public class BusinessException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public BusinessException(String message) { super(message); }

    public BusinessException(String message, Throwable cause) { super(message, cause); }
}
```

```java
package cn.xd.common.exception;

import cn.xd.common.vo.ResponseData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseData<String> handleBusiness(BusinessException e) {
        log.warn("业务异常: {}", e.getMessage());
        return ResponseData.error(e.getMessage());
    }

    @ExceptionHandler(Exception.class)
    public ResponseData<String> handleOther(Exception e) {
        log.error(e.getMessage(), e);
        return ResponseData.error(500, "系统繁忙，请稍后重试！");
    }
}
```

## 5. 分页对象

```java
package cn.xd.common.vo;

import java.io.Serializable;
import java.util.List;

/** 分页参数 */
public class PageSort implements Serializable {
    private static final long serialVersionUID = 1L;
    private int page = 1;        // 页码，从 1 开始
    private int pageSize = 10;   // 每页条数
    private String sortField;    // 排序字段（数据库字段名）
    private String sortOrder;    // asc / desc
    // getter/setter 省略
}

/** 分页结果 */
public class Page<T> implements Serializable {
    private static final long serialVersionUID = 1L;
    private int page;
    private int pageSize;
    private long total;
    private List<T> rows;
    // getter/setter 省略
}
```

## 6. Controller（web 模块）

```java
package cn.xd.web.visit;

import cn.xd.common.vo.Page;
import cn.xd.common.vo.PageSort;
import cn.xd.common.vo.ResponseData;
import cn.xd.service.api.visit.entity.ConfirmVisitEntity;
import cn.xd.service.api.visit.service.IConfirmVisitService;
import com.alibaba.fastjson.JSONObject;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;

@Slf4j
@Api(value = "走访管理接口", tags = {"走访管理接口"})
@RestController
@RequestMapping("/visit")
public class VisitController {

    @Resource
    private IConfirmVisitService confirmVisitService;

    @ApiOperation(value = "分页查询走访记录")
    @RequestMapping(path = "/list", method = RequestMethod.GET)
    public ResponseData<Page<ConfirmVisitEntity>> list(HttpServletRequest req,
                                                       PageSort pageSort,
                                                       @RequestParam Long controlId,
                                                       @RequestParam(required = false) String keyWord) {
        log.info("分页查询走访记录, controlId={}, keyWord={}", controlId, keyWord);
        return ResponseData.success(confirmVisitService.findByPage(pageSort, controlId, keyWord));
    }

    @ApiOperation(value = "新增走访记录")
    @RequestMapping(path = "/add")
    public ResponseData<String> add(HttpServletRequest req, ConfirmVisitEntity visit) {
        confirmVisitService.addVisit(visit);
        return new ResponseData<>("保存成功！");
    }
}
```

要点：
- `@RequestMapping(path = "/动作")`；查询列表用 `method = RequestMethod.GET`
- 参数直接用实体/Vo 接收（Spring 自动绑定 query/form 字段）；上传用 `MultipartFile[]`
- 只做参数接收与调 Service，业务校验放 Service

## 7. Service 接口与实现

```java
package cn.xd.service.api.visit.service;

import cn.xd.common.vo.Page;
import cn.xd.common.vo.PageSort;
import cn.xd.service.api.visit.entity.ConfirmVisitEntity;

public interface IConfirmVisitService {
    Page<ConfirmVisitEntity> findByPage(PageSort pageSort, Long controlId, String keyWord);
    void addVisit(ConfirmVisitEntity visit);
}
```

```java
package cn.xd.core.visit.service.impl;

import cn.xd.common.exception.BusinessException;
import cn.xd.common.vo.Page;
import cn.xd.common.vo.PageSort;
import cn.xd.core.visit.dao.ConfirmVisitDao;
import cn.xd.service.api.visit.entity.ConfirmVisitEntity;
import cn.xd.service.api.visit.service.IConfirmVisitService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;

@Slf4j
@Service
public class ConfirmVisitServiceImpl implements IConfirmVisitService {

    @Resource
    private ConfirmVisitDao confirmVisitDao;

    @Override
    public Page<ConfirmVisitEntity> findByPage(PageSort pageSort, Long controlId, String keyWord) {
        return confirmVisitDao.findByPage(pageSort, controlId, keyWord);
    }

    @Override
    public void addVisit(ConfirmVisitEntity visit) {
        if (visit.getControlId() == null) {
            throw new BusinessException("未设置控制表信息，请设置后再进行新增！");
        }
        confirmVisitDao.addVisit(visit);
    }
}
```

## 8. Dao（JdbcTemplate 手写 SQL）

```java
package cn.xd.core.visit.dao;

import cn.xd.common.vo.Page;
import cn.xd.common.vo.PageSort;
import cn.xd.service.api.visit.entity.ConfirmVisitEntity;
import com.alibaba.fastjson.JSONArray;
import org.springframework.jdbc.core.BeanPropertyRowMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.apache.commons.lang3.StringUtils;

import java.util.List;

@Repository
public class ConfirmVisitDao {

    private final JdbcTemplate jdbcTemplate;

    public ConfirmVisitDao(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    /** 分页查询：动态条件 + 预编译参数 */
    public Page<ConfirmVisitEntity> findByPage(PageSort ps, Long controlId, String keyWord) {
        JSONArray params = new JSONArray();
        StringBuilder sql = new StringBuilder();
        sql.append("select ");
        sql.append("    t.*, ");
        sql.append("    tu.name as createUserName ");
        sql.append("from IB_CONFIRM_VISIT t ");
        sql.append("    left join TUSER tu on tu.id = t.CREATE_USER ");
        sql.append("where t.CONTROL_ID = ? ");
        params.add(controlId);
        if (StringUtils.isNotEmpty(keyWord)) {
            sql.append("  and (t.BE_NAME like ? or t.CONTACT_PERSON like ?) ");
            params.add("%" + keyWord + "%");
            params.add("%" + keyWord + "%");
        }
        // 排序（PageSort.sortField 已限定为合法列）
        if (StringUtils.isNotBlank(ps.getSortField())) {
            sql.append(" order by t.").append(ps.getSortField())
               .append(" ").append("desc".equalsIgnoreCase(ps.getSortOrder()) ? "desc" : "asc");
        } else {
            sql.append(" order by t.CREATE_TIME desc ");
        }

        String dataSql = buildPageSql(sql.toString(), ps);
        List<ConfirmVisitEntity> rows = jdbcTemplate.query(
                dataSql, params.toArray(), new BeanPropertyRowMapper<>(ConfirmVisitEntity.class));
        Long total = jdbcTemplate.queryForObject(
                buildCountSql(sql.toString()), Long.class, params.toArray());

        Page<ConfirmVisitEntity> page = new Page<>();
        page.setPage(ps.getPage());
        page.setPageSize(ps.getPageSize());
        page.setTotal(total == null ? 0 : total);
        page.setRows(rows);
        return page;
    }

    /** 达梦/Oracle 风格分页 */
    private String buildPageSql(String sql, PageSort ps) {
        int end = ps.getPage() * ps.getPageSize();
        int start = (ps.getPage() - 1) * ps.getPageSize();
        return "select * from ( select tmp_page.*, rownum rn from ( " + sql
                + " ) tmp_page where rownum <= " + end + " ) where rn > " + start;
    }

    private String buildCountSql(String sql) {
        return "select count(*) from ( " + sql + " ) cnt";
    }

    /** 新增 */
    public void addVisit(ConfirmVisitEntity visit) {
        String sql = "insert into IB_CONFIRM_VISIT (ID, CONTROL_ID, BE_NAME, CONTACT_PERSON, CREATE_USER, CREATE_TIME) "
                   + "values (?, ?, ?, ?, ?, sysdate) ";
        jdbcTemplate.update(sql, visit.getId(), visit.getControlId(),
                visit.getBeName(), visit.getContactPerson(), visit.getCreateUser());
    }

    /** 更新 */
    public void updateVisit(ConfirmVisitEntity visit) {
        String sql = "update IB_CONFIRM_VISIT set BE_NAME = ?, CONTACT_PERSON = ?, UPDATE_TIME = sysdate where ID = ? ";
        jdbcTemplate.update(sql, visit.getBeName(), visit.getContactPerson(), visit.getId());
    }

    /** 删除 */
    public void deleteVisit(Long id) {
        jdbcTemplate.update("delete from IB_CONFIRM_VISIT where ID = ? ", id);
    }
}
```

要点：
- SQL 关键字小写、表/字段大写下划线（与达梦 DM8 兼容 Oracle 风格一致）
- 所有用户输入走 `?` 占位；动态条件用 `StringBuilder` + `JSONArray` 按序追加
- 分页在 Dao 层实现并返回 `Page<T>`，Service/Controller 不关心分页 SQL

## 9. Entity

```java
package cn.xd.service.api.visit.entity;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;
import java.util.Date;

/**
 * 走访记录
 */
@Getter
@Setter
public class ConfirmVisitEntity implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "主键ID")
    private Long id;

    @ApiModelProperty(value = "控制表ID")
    private Long controlId;

    @ApiModelProperty(value = "被函证方姓名")
    private String beName;

    @ApiModelProperty(value = "联系人")
    private String contactPerson;

    @ApiModelProperty(value = "联系人电话")
    private String contactPhone;

    @ApiModelProperty(value = "创建人ID")
    private Long createUser;
    /** 关联查询出的展示字段（非表字段，命名为 xxxName 风格） */
    private String createUserName;

    @ApiModelProperty(value = "创建时间")
    private Date createTime;

    @ApiModelProperty(value = "更新人ID")
    private Long updateUser;

    @ApiModelProperty(value = "更新时间")
    private Date updateTime;
}
```

要点：
- `@Getter @Setter`（不用 @Data，避免 equals/hashCode 副作用）、`implements Serializable` + `serialVersionUID`
- 字段驼峰，数据库列大写下划线（如 `BE_NAME` ↔ `beName`，依赖 BeanPropertyRowMapper/查询别名自动映射）
- join 出来的展示字段也放 Entity（或 Vo），SQL 中用别名映射

## 10. application.yml 模板

```yaml
application:
  name: xd

server:
  port: 5704
  servlet:
    context-path: /xd_api

spring:
  application:
    name: xd
  session:
    store-type: redis
  jackson:
    time-zone: GMT+8
    date-format: yyyy-MM-dd HH:mm:ss
  servlet:
    multipart:
      max-file-size: 5120MB
      max-request-size: 100MB
  redis:
    host: 127.0.0.1
    port: 6379
    timeout: 10000
  datasource:
    driver-class-name: dm.jdbc.driver.DmDriver
    url: jdbc:dm://127.0.0.1:5236?schema=XD
    username: xd
    password: xd
```

多环境：`application-{env}.yml`（hztest/hzpre 等），启动时 `--spring.profiles.active=hzpre` 指定。

## 11. log4j2 配置要点

- 依赖 `spring-boot-starter-log4j2` + `com.lmax:disruptor`，全局排除默认 logback（见根 build.gradle）
- `src/main/resources/log4j2.xml`：Console + RollingFile（按天滚动、保留 N 天），异步日志加 `<AsyncLogger>` 或 `-Dlog4j2.contextSelector=...Async`
- 代码中只用 `@Slf4j`（Lombok）取 logger，不直接引用 log4j API
