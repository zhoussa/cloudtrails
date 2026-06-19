# ☁️ 云端轨迹 · Cloud Trails

> 个人知识库网站 — Flask + SQLite，支持 Markdown、分类、标签、搜索、日/夜间主题、密码保护。

---

## 📁 文件结构

```
cloudtrails-package/
├── app.py              # Flask 主应用
├── init_db.py          # 数据库初始化（建表 + 预设分类）
├── requirements.txt    # Python 依赖
├── README.md           # 本文件
├── templates/
│   ├── base.html       # 基础模板（侧栏、顶栏、汉堡菜单）
│   ├── index.html      # 首页（笔记列表 + 标签云）
│   ├── post.html       # 笔记详情页
│   ├── new.html        # 新建/编辑笔记页
│   └── login.html      # 登录页
└── static/
    ├── style.css       # 全局样式（暗/亮主题变量、响应式）
    ├── logo.svg        # 网站 Logo
    └── nginx/
        └── zhou-tcloud  # Nginx 配置示例
```

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | **Python Flask** | 轻量 Web 框架 |
| 数据库 | **SQLite** | 零配置，文件即数据库 |
| Markdown | **Python-Markdown** | 支持代码高亮、表格 |
| 代码高亮 | **highlight.js** | CDN 加载，Monokai 主题 |
| 前端 | **原生 HTML/CSS/JS** | 无框架，CSS 变量主题切换 |
| 反向代理 | **Nginx** | 域名 → Flask 端口转发 |

---

## 🚀 部署步骤

### 1. 环境要求

- Python 3.9+
- pip
- （可选）Nginx — 用于域名绑定

```bash
# 检查 Python 版本
python3 --version   # 需要 ≥ 3.9
```

### 2. 安装依赖

```bash
# 进入项目目录
cd cloudtrails-package

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python3 init_db.py
# 输出: ✅ 数据库初始化完成: /path/to/notes.db
```

这会创建 `notes.db`，包含 **4 张表** 和 **6 个预设分类**。

### 4. 修改密码

编辑 `app.py` 第 14 行：

```python
PASSWORD = '你的密码'   # 改成你自己的密码
```

### 5. 启动服务

```bash
# 方式一：直接启动（开发/测试）
python3 app.py

# 方式二：后台运行（生产）
nohup python3 app.py > /dev/null 2>&1 &

# 方式三：使用 systemd（推荐，见下方）
```

服务默认监听 `0.0.0.0:5050`。

### 6. 验证运行

```bash
curl http://localhost:5050/login
# 应该返回登录页 HTML
```

---

## 🌐 配置 Nginx（域名绑定）

### 创建配置文件

```bash
sudo nano /etc/nginx/sites-available/cloudtrails
```

写入（参考 `static/nginx/zhou-tcloud`）：

```nginx
server {
    listen 80;
    server_name 你的域名.com;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 启用站点

```bash
sudo ln -s /etc/nginx/sites-available/cloudtrails /etc/nginx/sites-enabled/
sudo nginx -t          # 测试配置
sudo systemctl reload nginx
```

### 配置 DNS

在你的域名 DNS 管理后台，添加一条 **A 记录**，指向服务器 IP。

---

## 🔧 Systemd 服务（开机自启）

```bash
sudo nano /etc/systemd/system/cloudtrails.service
```

```ini
[Unit]
Description=云端轨迹 Flask App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cloudtrails-package
ExecStart=/opt/cloudtrails-package/venv/bin/python3 app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudtrails
sudo systemctl start cloudtrails
sudo systemctl status cloudtrails   # 检查状态
```

---

## 🔒 访问控制

- 所有页面（静态文件除外）受密码保护
- 访问 `http://你的域名/login` 输入密码登录
- 登录后 session 维持，关闭浏览器后需重新登录
- 静态资源（CSS/JS/图片）不设限，确保页面正常渲染

---

## 🎨 主题切换

- **暗色模式**：默认，主色 `#17171B`（"深夜观测台"）
- **亮色模式**：点击右上角 🌙/☀️ 按钮切换
- 偏好自动保存到浏览器 `localStorage`

---

## 📱 移动端适配

- 屏幕宽度 ≤ 700px 时侧栏折叠
- 点击左上角 ☰ 汉堡按钮滑出侧栏
- 点击遮罩层或再次 ☰ 关闭

---

## 📂 分类系统

预设 6 个文件夹，可在侧栏新建自定义分类：

| 图标 | 名称 |
|------|------|
| 📚 | 全部笔记 |
| 🐳 | Docker & 容器 |
| ☸️ | Kubernetes |
| ☁️ | HCIE 云计算 |
| 🐧 | Linux & 系统 |
| 📝 | 日常总结 |
| 💻 | 编程开发 |

---

## 🔍 搜索 & 标签

- 顶部搜索栏支持标题 + 内容全文模糊搜索
- 每篇笔记可添加多个标签
- 标签按分类筛选，不跨分类串台

---

## 📝 Markdown 支持

编辑器支持以下格式（工具栏快捷插入）：

- `# 标题` — H1-H3
- `**加粗**` `*斜体*`
- `` `代码` `` 行内代码
- ` ``` ``` ` 代码块（自动高亮）
- `![图片](url)` 图片
- `| 表格 |` GFM 表格
- `> 引用` 引用块

---

## 🖼️ 图片上传

- 编辑页支持拖拽/点击上传
- 自动生成 Markdown 图片语法
- 存储位置：`static/uploads/`
- 支持格式：png, jpg, jpeg, gif, webp, svg, bmp
- 单文件上限 10MB

---

## 🔄 版本历史

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-06-18 | v1.0 | 初版，基础 CRUD + Markdown |
| 2026-06-19 | v2.0 | 标签、搜索、图片上传 |
| 2026-06-20 | v3.0 | 域名绑定 + Nginx + 文件夹侧栏 |
| 2026-06-20 | v4.0 | 暗色主题大改版 + 日/夜切换 |
| 2026-06-21 | v4.1 | 密码保护 + 全站背景修复 |
| 2026-06-22 | v4.2 | 手机汉堡菜单 + 部署打包 |

---

## 📄 许可证

个人项目，随意使用修改。

---

> 全程由 [Hermes Agent](https://hermes-agent.nousresearch.com) 协助开发 🚀
