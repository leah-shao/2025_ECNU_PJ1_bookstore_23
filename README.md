
# Bookstore 后端（Flask + SQLite/MongoDB）

一个支持图书电商核心流程的后端服务，涵盖用户注册与鉴权、卖家店铺与上架、库存管理、买家充值/下单/支付，以及订单生命周期（取消/发货/收货/查询）与图书搜索（Mongo 全文优先，SQLite 回退）。

## 功能概览
- 用户与鉴权
  - 注册、登录、登出、注销、修改密码
  - 多终端 token 登录（`terminal`）
- 卖家
  - 创建店铺
  - 添加书籍信息（含标签、简介、内容、图片等）
  - 增加库存
  - 发货
- 买家
  - 充值
  - 下单、付款
  - 取消订单（主动取消或超时未支付自动取消）
  - 收货、查询历史订单
- 图书搜索
  - 关键字搜索，支持字段覆盖标题/tags/简介/内容等
  - 支持按店铺范围过滤
  - 分页
  - MongoDB 全文索引优先，SQLite LIKE 回退
- 测试与覆盖率
  - 覆盖基础 60% 与附加 40% 功能的自动化测试
  - 可生成 HTML 覆盖率报告


## 贡献者与分工
- 李晨语：鉴权/卖家端/SQLite 结构与迁移
- 邵乐怡：买家端/订单生命周期/搜索（Mongo 优先与回退）

## 技术栈
- 后端：Flask
- 数据库：SQLite（事务/关系数据、存量 demo 数据）、MongoDB（全文检索与扩展数据）
- 测试：pytest
- 依赖：见 `requirements.txt`

## 目录结构
```
bookstore
  |-- be/                    后端源代码
  |   |-- app.py             启动入口
  |   |-- serve.py           Flask 应用装配与启动
  |   |-- model/             业务逻辑与数据访问
  |   |-- view/              REST API 蓝图（auth/seller/buyer/search）
  |
  |-- fe/                    前端访问层 & 测试（无需 UI）
  |   |-- access/            访问封装
  |   |-- test/              pytest 用例（功能/流程/搜索/覆盖率）
  |   |-- bench/             性能基准/会话模拟
  |   |-- conf.py            测试配置（默认 BASE URL 等）
  |   |-- data/              数据与脚本（含 `import_books_mongo.py`）
  |
  |-- doc/                   接口与索引说明
  |   |-- auth.md
  |   |-- buyer.md
  |   |-- seller.md
  |   |-- indexing.md
  |
  |-- script/
  |   |-- import_sqlite_to_mongo.py  SQLite→Mongo 导入脚本
  |
  |-- requirements.txt
  |-- setup.py
```

## 环境准备
- Python 3.8+
- MongoDB（本地或远程均可；搜索功能推荐启用）
- Windows 用户若遇到 Werkzeug 兼容提示，可降级：
  ```powershell
  pip install flask==2.0.0
  pip install Werkzeug==2.0.0
  ```

## 安装与运行
1) 安装依赖
```powershell
pip install -r requirements.txt
```

2) 导入图书数据到 MongoDB（推荐，用于启用全文检索）
- 方案 A（带索引创建，推荐）：
```powershell
python fe/data/import_books_mongo.py --mongo-url mongodb://localhost:27017/ --db bookstore --sqlite-file fe/data/book.db
```
- 方案 B（最小导入）：
```powershell
python script/import_sqlite_to_mongo.py
```

3) 启动后端
```powershell
python be/app.py
```
默认地址：`http://127.0.0.1:5000/`（可在 `fe/conf.py` 调整）

## API 文档
- 鉴权与用户：`bookstore/doc/auth.md`
- 卖家：`bookstore/doc/seller.md`
- 买家：`bookstore/doc/buyer.md`
- 检索：GET `/search/`，参数：
  - `q`: 关键词
  - `fields`: 结果字段（可选，Mongo 模式用于 projection）
  - `store_id`: 店铺过滤（可选）
  - `page`/`page_size`: 分页
- 示例：
  ```
  GET /search/?q=python&page=1&page_size=10
  GET /search/?q=data&store_id=store_123
  ```

## 索引与性能
- MongoDB：为 `books` 设置 text 索引与 `store_id`、`isbn` 等精确索引，详见 `doc/indexing.md`
- SQLite 回退：使用 LIKE/FTS5（若启用）进行匹配，尽量创建必要索引
- 应用层：分页优先、条件尽量下推数据库、避免热路径全表扫描

## 测试与覆盖率
- 运行全部测试（Windows 可直接执行）
```powershell
pytest -q
```
- 生成覆盖率（示例）
```powershell
pytest --cov=be --cov-report=html
```
生成的 HTML 报告位于 `htmlcov/`。

常用用例（部分）：
- 鉴权：`fe/test/test_register.py`、`test_login.py`、`test_password.py`
- 卖家：`fe/test/test_create_store.py`、`test_add_book.py`、`test_add_stock_level.py`
- 买家：`fe/test/test_add_funds.py`、`test_new_order.py`、`test_payment.py`
- 订单流程：`fe/test/test_order_lifecycle.py`（取消/发货/收货/查询）
- 搜索：`fe/test/test_search_api.py`、`test_search_fallback.py`、`test_search_view_branches.py`

## 关键实现说明
- 服务入口：`be/serve.py` 注册 `auth/seller/buyer/search` 蓝图，初始化数据库并启动 Flask
- 搜索：`be/model/search.py`
  - 优先使用 Mongo `$text`，按 `textScore` 排序
  - 不可用时回退到 SQLite 的 LIKE 方案（按店铺过滤与分页）
- 订单生命周期：提供取消（含自动取消）、发货、收货、查询接口，测试覆盖端到端流程

## 常见问题
- 提示 “Not running with the Werkzeug Server”：请按上文降级 Flask/Werkzeug
- 搜索无结果或报错：
  - 确认已将 `fe/data/book.db` 导入 Mongo
  - 确认 `books` 集合已创建 text 索引（使用 `fe/data/import_books_mongo.py` 脚本可自动创建）
- 覆盖率无报告：确认使用了 `--cov` 与 `--cov-report=html` 参数
