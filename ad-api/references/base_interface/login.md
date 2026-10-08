## 登录

调用任何数据接口之前，必须先调用登录接口。

SDK的账号、密码、ip和端口号需联系您的开户营业部申请开通权限之后获取。

**接口**: login

**描述**: api 登陆

### 输入参数

| 参数 | 数据类型 | 必选 | 解释 |
| --- | --- | --- | --- |
| username | str | 是 | 账号 |
| password | str | 是 | 密码 |
| ip | str | 是 | 服务器ip |
| host | int | 是 | 服务器端口号 |

### 示例代码

```python
# 第一步 登录api
import AmazingData as ad
ad.login(username='username', password='password',host='***.***.***.***',port=****)
```
