# M5 — 资产管理 (`asset_service`)

> 模块职责：文件的上传、存储、预览、管理。通过存储抽象层支持本地文件系统和未来 S3 切换。

---

## 子任务

### 1. 存储抽象层

- [ ] 1.1 定义 StorageBackend ABC：save / read / delete / exists 四个方法
- [ ] 1.2 实现 LocalStorageBackend（基于本地文件系统，存储路径从配置读取）
- [ ] 1.3 预留 S3StorageBackend 接口（boto3 客户端，interface 已定义，实现后续补充）
- [ ] 1.4 存储路径按隔离规则组织：`/{assets_dir}/{user_id or 'default'}/{asset_id}/{filename}`

### 2. 文件上传

- [ ] 2.1 定义 Asset ORM 模型（assets 表）
- [ ] 2.2 实现 `upload(file: UploadFile, tags)` — 接收文件上传
- [ ] 2.3 验证文件类型：CSV, XLSX, XLS, JSON, TXT, PNG, JPG, PDF, DOCX
- [ ] 2.4 验证文件大小：单文件 ≤ 50MB
- [ ] 2.5 文件上传后写入 StorageBackend + 创建 Asset 数据库记录（status='uploading'→'processing'→'ready'）
- [ ] 2.6 对于知识库文档（PDF/Word/MD/TXT）：上传完成后自动触发 RAG 文档处理流水线
- [ ] 2.7 上传进度（可选）：通过 WebSocket 推送进度

### 3. 文件管理

- [ ] 3.1 实现 `list_assets(filters)` — 支持分页 + 按类型筛选 + 搜索名称/标签
- [ ] 3.2 实现 `get_asset(asset_id)` — 获取资产元数据
- [ ] 3.3 实现 `download(asset_id)` — 返回文件流（bytes + content_type + filename）
- [ ] 3.4 实现 `delete_asset(asset_id)` — 删除 DB 记录 + StorageBackend.delete

### 4. 文件预览

- [ ] 4.1 实现 `get_preview(asset_id)` — 根据 file_type 返回不同格式的预览数据
- [ ] 4.2 图片（PNG/JPG）：返回缩略图 URL 或 base64
- [ ] 4.3 PDF：返回文件流供前端 PDF.js 渲染
- [ ] 4.4 文本/代码/JSON：返回文本内容（content_text 字段或读取文件）
- [ ] 4.5 CSV/Excel：解析前 N 行返回表格数据（列名 + 行数据）
- [ ] 4.6 其他类型：返回 PreviewData 仅含元数据（name/size/type/日期）

### 5. 文件提取（用于知识库）

- [ ] 5.1 实现 PDF 文本提取（PyPDF2 或 pdfplumber）
- [ ] 5.2 实现 Word (.docx) 文本提取（python-docx）
- [ ] 5.3 实现 Markdown/TXT 文本直读
- [ ] 5.4 提取的文本存储到 assets.content_text 字段

### 6. 重新处理

- [ ] 6.1 实现 `reprocess(asset_id)` — 对知识库文档重新执行分块 + Embedding + 存储
- [ ] 6.2 重新处理时先清理旧的 knowledge_chunks 记录

### 7. API 端点

- [ ] 7.1 `GET /api/assets` — 资产列表（分页+筛选+搜索）
- [ ] 7.2 `POST /api/assets/upload` — 上传文件
- [ ] 7.3 `GET /api/assets/{id}` — 资产详情/元数据
- [ ] 7.4 `GET /api/assets/{id}/download` — 下载原始文件
- [ ] 7.5 `GET /api/assets/{id}/preview` — 获取预览数据
- [ ] 7.6 `DELETE /api/assets/{id}` — 删除资产
- [ ] 7.7 `POST /api/assets/{id}/reprocess` — 重新处理知识库文档

### 8. Pydantic Schema

- [ ] 8.1 AssetCreate / AssetInfo / AssetDetail / AssetFilter Schema
- [ ] 8.2 PreviewData Schema（按 file_type 区分结构）
- [ ] 8.3 UploadResponse Schema

### 9. 测试

- [ ] 9.1 测试 StorageBackend 抽象层 + LocalStorage
- [ ] 9.2 测试文件上传 + 下载完整链路
- [ ] 9.3 测试文件类型/大小验证
- [ ] 9.4 测试文件预览（各类型）
- [ ] 9.5 测试文本提取（PDF/Word）
