# 吉安大平台登录程序使用说明

## 概述

`jian_platform_login.py` 是一个根据 Java 代码编写的 Python 版本的吉安大平台登录程序，用于获取 access token。

## 功能特性

- ✅ 从环境变量读取登录配置
- ✅ RSA 公钥加密密码
- ✅ HTTP POST 请求登录
- ✅ 解析响应获取 access token
- ✅ 完整的错误处理和日志记录
- ✅ 类型注解和文档字符串

## 环境变量配置

在运行程序前，需要设置以下环境变量：

### 必需的环境变量

```bash
DAC_LOGIN_URL=https://your-jian-platform-domain.com/api/login  # 登录URL
DAC_USERNAME=your_username                                      # 用户名
DAC_PASSWORD=your_password                                      # 密码
```

### 可选的环境变量

```bash
DAC_PUBLIC_KEY=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAKoR8mX0rGKLqzcWmOzbfj64K8ZIgOdHnzkXSOVOZbFu/TJhZ7rFAN+eaGkl3C4buccQd/EjEsj9ir7ijT7h96MCAwEAAQ==
```

> 注意：如果不设置 `DAC_PUBLIC_KEY`，程序会使用默认的公钥

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 🌟 推荐方法: 使用.env 文件

1. 复制配置模板文件为 `.env`：

```bash
# Windows
copy env_template.txt .env

# Linux/macOS
cp env_template.txt .env
```

2. 编辑 `.env` 文件，填入实际配置：

```ini
# 吉安大平台登录配置
DAC_LOGIN_URL=https://your-actual-domain.com/api/login
DAC_USERNAME=your_actual_username
DAC_PASSWORD=your_actual_password
# DAC_PUBLIC_KEY=your_public_key_if_different
```

3. 直接运行程序（程序已内置.env 支持）：

```bash
python jian_platform_login.py
```

**优势**:

- ✅ 配置集中管理，方便维护
- ✅ 避免在命令行历史中暴露敏感信息
- ✅ 支持版本控制（.env 文件通常被 git 忽略）
- ✅ 程序已内置支持，无需额外配置

### 方法 2: 在命令行中设置环境变量

#### Windows (cmd)

```cmd
set DAC_LOGIN_URL=https://your-domain.com/api/login
set DAC_USERNAME=your_username
set DAC_PASSWORD=your_password
python jian_platform_login.py
```

#### Windows (PowerShell)

```powershell
$env:DAC_LOGIN_URL="https://your-domain.com/api/login"
$env:DAC_USERNAME="your_username"
$env:DAC_PASSWORD="your_password"
python jian_platform_login.py
```

#### Linux/macOS

```bash
export DAC_LOGIN_URL="https://your-domain.com/api/login"
export DAC_USERNAME="your_username"
export DAC_PASSWORD="your_password"
python jian_platform_login.py
```

### 方法 3: 在代码中使用

```python
from jian_platform_login import JianPlatformLoginClient
import os

# 方式1: 使用.env文件（推荐）
# 确保项目根目录有.env文件，程序会自动加载

# 方式2: 动态设置环境变量
os.environ['DAC_LOGIN_URL'] = 'https://your-domain.com/api/login'
os.environ['DAC_USERNAME'] = 'your_username'
os.environ['DAC_PASSWORD'] = 'your_password'

# 创建客户端并登录
client = JianPlatformLoginClient()
if client.login():
    access_token = client.get_access_token()
    print(f"Access Token: {access_token}")

    # 使用access_token进行后续API调用
    # headers = {'Authorization': f'Bearer {access_token}'}
    # response = requests.get('https://api.example.com/data', headers=headers)
else:
    print("登录失败")
```

## 输出示例

### 成功登录

```
=== 吉安大平台登录程序 ===
2024-01-01 10:00:00,000 - INFO - Attempting to login to JiAn platform...
2024-01-01 10:00:00,100 - INFO - Sending login request to https://your-domain.com/api/login
2024-01-01 10:00:00,500 - INFO - Successfully logged in and obtained access token

✅ 登录成功!
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 登录失败

```
=== 吉安大平台登录程序 ===
错误: 缺少以下环境变量: DAC_LOGIN_URL, DAC_USERNAME

请设置以下环境变量:
DAC_LOGIN_URL=<登录URL>
DAC_USERNAME=<用户名>
DAC_PASSWORD=<密码>
DAC_PUBLIC_KEY=<RSA公钥> (可选)
```

## API 说明

### JianPlatformLoginClient 类

#### 主要方法

- `__init__()`: 初始化客户端，从环境变量读取配置
- `login() -> bool`: 执行登录，返回是否成功
- `get_access_token() -> Optional[str]`: 获取 access token
- `is_logged_in() -> bool`: 检查是否已登录

#### 私有方法

- `_validate_config() -> bool`: 验证配置参数
- `_encrypt_password_with_rsa(password: str, public_key_str: str) -> str`: RSA 加密密码

## 错误处理

程序包含完整的错误处理：

- 环境变量缺失检查
- RSA 加密异常处理
- HTTP 请求异常处理
- JSON 解析异常处理
- 业务状态码检查

## 技术实现

- **RSA 加密**: 使用 `cryptography` 库实现 RSA 公钥加密
- **HTTP 请求**: 使用 `requests` 库发送 POST 请求
- **JSON 处理**: 使用标准库 `json` 模块
- **日志记录**: 使用标准库 `logging` 模块
- **类型注解**: 完整的类型提示支持

## 注意事项

1. 确保网络连接正常，可以访问登录 URL
2. 用户名和密码必须正确
3. 如果使用自定义公钥，确保公钥格式正确
4. 程序会自动处理密码的 RSA 加密
5. access token 获取后可用于后续 API 调用

## 故障排除

### 常见问题

1. **环境变量未设置**: 检查是否正确设置了所有必需的环境变量
2. **网络连接失败**: 检查登录 URL 是否正确，网络是否通畅
3. **RSA 加密失败**: 检查公钥格式是否正确
4. **认证失败**: 检查用户名和密码是否正确

### 调试方法

程序包含详细的日志输出，可以通过日志信息来定位问题。如需更详细的调试信息，可以修改日志级别：

```python
logging.basicConfig(level=logging.DEBUG)
```
