# M6 — 知识库引擎 (`rag_engine`)

> 模块职责：文档处理流水线（解析→分块→向量化→存储）和 RAG 检索。

---

## 子任务

### 1. 文档分块 (`chunker.py`)

- [ ] 1.1 实现混合分块策略：优先按段落/标题语义分块
- [ ] 1.2 超长段落（>512 token）按固定大小切割
- [ ] 1.3 相邻块之间 10% 内容重叠
- [ ] 1.4 分块结果包含 metadata（来源段落/标题/位置信息）
- [ ] 1.5 返回 Chunk 对象（content + token_count + metadata）

### 2. Embedding 向量化 (`embedding.py`)

- [ ] 2.1 调用 LLM Gateway 的 `get_embedding` 方法
- [ ] 2.2 使用 DeepSeek Embedding API（模型ID从配置读取）
- [ ] 2.3 运行时确认实际向量维度，调整 knowledge_chunks 表的 vector(N) 列定义
- [ ] 2.4 批量 Embedding：一次调用处理多个文本块（如 API 支持）

### 3. 文档索引流水线

- [ ] 3.1 定义 KnowledgeChunk ORM 模型（knowledge_chunks 表，含 pgvector embedding 列）
- [ ] 3.2 实现 `index_document(asset_id)` — 完整流水线：获取文档文本 → 分块 → Embedding → 写入 pgvector
- [ ] 3.3 实现 `reindex_document(asset_id)` — 先删除旧 chunks，再重新索引
- [ ] 3.4 实现 `delete_chunks(asset_id)` — 删除文档所有分块
- [ ] 3.5 配置 pgvector ivfflat 索引（lists=100, vector_cosine_ops）

### 4. 向量检索

- [ ] 4.1 实现向量相似度搜索：将查询文本 Embedding → pgvector Cosine 相似度 → 结果集 R1
- [ ] 4.2 支持 top_k 参数控制返回数量

### 5. 关键词检索（BM25）

- [ ] 5.1 实现 PostgreSQL full-text search：使用 `to_tsvector` + `plainto_tsquery` + `ts_rank`
- [ ] 5.2 对 knowledge_chunks.content 建立 GIN 索引（如需要）
- [ ] 5.3 返回关键词匹配结果集 R2（带 BM25 分数）

### 6. 混合检索与融合排序

- [ ] 6.1 实现加权融合排序：`score = α × cosine_score + (1-α) × bm25_score`
- [ ] 6.2 α 权重从配置读取（默认 0.7）
- [ ] 6.3 融合后返回 Top-K 结果（无 Rerank）

### 7. RAG 检索接口

- [ ] 7.1 实现 `search(query, top_k=5)` — 混合检索主入口
- [ ] 7.2 返回 ChunkResult 列表（content + score + source_asset + source_chunk_index + metadata）
- [ ] 7.3 实现 `get_chunks(asset_id)` — 获取文档的所有分块

### 8. 引用溯源

- [ ] 8.1 ChunkResult 中包含来源文档名称 + 分块位置信息
- [ ] 8.2 Agent 回复时指示前端在引用处添加来源标注（工具调用时注入引用格式指令）

### 9. 测试

- [ ] 9.1 测试混合分块逻辑（各种文档结构）
- [ ] 9.2 Mock Embedding API，测试完整索引流水线
- [ ] 9.3 测试混合检索排序准确性
- [ ] 9.4 集成测试：上传文档 → 索引 → 检索
