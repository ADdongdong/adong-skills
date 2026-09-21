# XD 开发手册 — 前端详细样例

与 SKILL.md 配套的可复制样例。技术栈：UmiJS 3.5 + React 17 + Ant Design 4 + dva。

## 1. .umirc.ts 模板

```ts
import { defineConfig } from 'umi';
import { resolve } from 'path';
import Routes from './src/routes/index';

export default defineConfig({
  devServer: {
    host: 'localhost',   // Windows + Node 高版本必须用 localhost，不能 0.0.0.0/127.0.0.1
    port: 5002,
    hot: true,
    compress: true,
    client: { overlay: false },
  },
  base: '/i5-confirm/',
  publicPath: '/i5-confirm/',
  title: 'XD 系统',
  webpack5: {},
  dynamicImport: { loading: '@/Loading' },
  fastRefresh: {},
  routes: [...Routes],
  // 接口代理：前端请求 /xxx_api 前缀 → 后端端口 + context-path
  proxy: {
    '/i5_xd_api': {
      target: 'http://localhost:5704',
      changeOrigin: true,
      pathRewrite: { '^/i5_xd_api': '/xd_api' },
    },
  },
  alias: {
    $components: resolve(__dirname, './src/components'),
    $businessComponents: resolve(__dirname, './src/businessComponents'),
    $models: resolve(__dirname, './src/models'),
    $routes: resolve(__dirname, './src/routes'),
    $utils: resolve(__dirname, './src/utils'),
    $pages: resolve(__dirname, './src/pages'),
    $config: resolve(__dirname, './src/config'),
    $assets: resolve(__dirname, './src/assets'),
  },
  locale: {
    default: 'zh-CN',
    antd: false,
    baseNavigator: true,
    baseSeparator: '-',
  },
  dva: { immer: { enableES5: true }, hmr: true },
});
```

## 2. 目录结构

```
src/
  app.js                 # umi 入口（dva 配置、运行时逻辑）
  global.less            # 全局样式
  Loading.js             # dynamicImport 加载态
  assets/                # 图片、图标
  components/            # 通用纯展示组件
  businessComponents/    # 业务组合组件
  config/                # 全局常量、路径（BASE_PATH、LBS_PATH 等）
  layouts/               # 布局（menu、header）
  locales/               # 国际化资源 zh-CN / en-US
  models/                # dva 全局 model
  pages/                 # 页面：pages/<业务域>/<功能>/index.js + index.less
  routes/                # 路由集中定义 + 鉴权包装器
  theme/                 # less 主题变量
  utils/                 # request 封装、工具函数
```

## 3. 路由集中管理

`src/routes/index.js` 合并各业务域路由：

```js
import exceptionRoutes from './exception';
import projectRoutes from './project';

export default [...exceptionRoutes, ...projectRoutes];
```

`src/routes/project.js`（按业务域拆分，嵌套结构 + 鉴权包装）：

```js
const projectRouter = [
  {
    path: '/',
    component: '@/layouts/pageLayout',
    wrappers: ['@/routes/privateRoute.js'],   // 登录鉴权包装器
    routes: [
      { path: '/visit/list', component: '@/pages/visit/list' },
      { path: '/visit/detail/:id', component: '@/pages/visit/detail' },
      { component: '@/pages/404' },
    ],
  },
];
export default projectRouter;
```

`src/routes/privateRoute.js`（包装器示例）：

```js
import RenderAuthorized from '$utils/authorized';
import { getAuthority } from '$utils/authority';

export default (props) => {
  const { children } = props;
  const currentAuthority = getAuthority();
  const Authorized = RenderAuthorized(currentAuthority);
  return (
    <Authorized authority={[...]} noMatch={<Redirect to="/exception/403" />}>
      {children}
    </Authorized>
  );
};
```

## 4. request 封装模式（src/utils/request.js）

页面不直接使用 axios，统一经封装实例。核心能力：

1. **全局 loading**：请求计数器，首个请求挂载 Spin、全部结束卸载
2. **认证头**：拦截器统一附加 `UserID`（登录令牌 / 开发环境 DEV_USER_TOKEN）
3. **统一错误通知**：响应拦截器中按 code 调 `showNotification('error', message)`
4. **blob 下载**：识别 `content-disposition`，触发浏览器另存
5. **取消重复请求**：相同 url+params 的在途请求自动取消（pathToRegexp 匹配）

```js
// 页面内使用示例
import C5axios from '$utils/request.js';

export async function fetchVisitList(params) {
  return C5axios({
    url: '/i5_xd_api/visit/list',
    method: 'GET',
    params,                      // GET 用 params；POST 表单用 qs.stringify 或 FormData
  });
}

// 下载类接口：responseType: 'blob'，封装层自动处理另存
export async function downloadFile(params) {
  return C5axios({ url: '/i5_xd_api/visit/export', method: 'GET', params, responseType: 'blob' });
}
```

URL 约定：前端请求写代理前缀（如 `/i5_xd_api/...`），由 umi proxy 重写到后端 context-path。

## 5. 页面组件规范

`src/pages/visit/list/index.js`：

```jsx
import React, { useEffect, useState } from 'react';
import { Card, Table, Input, Button, Space } from 'antd';
import { fetchVisitList } from '$utils/apis/visit.js';
import './index.less';

const VisitList = () => {
  const [dataSource, setDataSource] = useState([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState({ page: 1, pageSize: 10, keyWord: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetchVisitList(query);
        setDataSource(res?.data?.rows || []);
        setTotal(res?.data?.total || 0);
      } finally {
        setLoading(false);
      }
    })();
  }, [query]);

  const columns = [
    { title: '被函证方', dataIndex: 'beName' },
    { title: '联系人', dataIndex: 'contactPerson' },
    { title: '创建时间', dataIndex: 'createTime' },
  ];

  return (
    <Card className="visit-list">
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="关键字"
          onSearch={(v) => setQuery((q) => ({ ...q, page: 1, keyWord: v }))}
        />
        <Button type="primary">新增</Button>
      </Space>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={dataSource}
        pagination={{ current: query.page, pageSize: query.pageSize, total }}
        onChange={(p) => setQuery((q) => ({ ...q, page: p.current, pageSize: p.pageSize }))}
      />
    </Card>
  );
};

export default VisitList;
```

约定：
- 数据结构对齐后端 `ResponseData<T>`：`res.data` 即 `Page<T>`，取 `rows/total`
- 响应数据通过 `res?.data?.xx` 安全取值
- 时间字段展示用 `moment`，格式 `YYYY-MM-DD HH:mm:ss`
- 组件内状态用 hooks；跨页面共享状态用 dva model（`src/models`，`connect` 注入）

## 6. 构建与依赖

- 安装：`npm install --legacy-peer-deps --ignore-scripts --prefer-offline`
- `--ignore-scripts` 后必须执行 `node_modules\.bin\umi generate tmp` 再 `umi dev`
- Node 高版本（v17+）需 `NODE_OPTIONS=--openssl-legacy-provider`
- 私有 GitHub 依赖不可达时用 `package.json` `overrides` + `vendor-stubs/` 本地空壳包替代
- 生产构建自动 gzip（compression-webpack-plugin，threshold 10240）
