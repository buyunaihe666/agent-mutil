# NEXUS AI — 三层超级智能体架构 + 语音联网搜索 设计文档

**日期**: 2026-06-21
**状态**: Draft — 待审批
**关联**: [[2026-06-21-continue-development]]

---

## 1. 概述

### 1.1 目标

1. **三层 Meta-Agent 架构**：引入 决策层 → 策略层 → 执行层 三个 Meta-Agent，根据任务复杂度自动分层协作
2. **语音联网搜索**：前端集成 Web Speech API 语音转文字输入，配合现有 WebSearchTool 实现语音搜索

### 1.2 核心架构等式

```
Agent 体系 = 3个 Meta-Agent(调度者) + N个 普通Agent(执行者)

Meta-Agent  →  只调用 agent_communication，不直接调用执行工具
普通Agent   →  拥有实际工具(web_search, code_execution, db_query, file_read/write...)
```

### 1.3 PLAN 是 Meta-Agent 之间的通信协议

```
策略Agent(生产者) → PLAN → 执行Agent(消费者) → 结果 → 策略Agent(Reviewer)
```

---

## 2. 三层架构设计

### 2.1 三个 Meta-Agent 定义

| Meta-Agent | 角色 | System Prompt 核心 | Tools | 产出 |
|------------|------|-------------------|-------|------|
| **智能决策Agent** | Decision Maker | 分析用户意图 → 判断任务复杂度(simple/complex) → 决定任务方向 → 选择合适的策略Agent或直接委派普通Agent | `agent_communication` | TriageResult / 委派指令 |
| **策略规划Agent** | Plan Producer & Reviewer | 将决策转化为可执行的 Plan(steps) → 提交用户审批 → 执行完成后 Review 结果质量 → 决定是否需重做 | `agent_communication` | OrchestrationPlan |
| **执行调度Agent** | Plan Consumer & Dispatcher | 接收 Plan → 将每个 step 分配给最合适的普通Agent → 监控执行进度 → 收集结果 → 可指定 Leader Agent 协调子任务 | `agent_communication`, `web_search` | StepResults[] |

### 2.2 工作流

```
用户消息
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ MetaAgentRouter.route(message)                       │
│                                                      │
│  1. 决策Agent.analyze(message)                        │
│     ├─ 判断: simple → 直接委派普通Agent → 返回结果     │
│     └─ 判断: complex → 继续 ▼                         │
│                                                      │
│  2. 策略Agent.generate_plan(direction)                 │
│     ├─ 调用 orchestration_engine.generate_plan()      │
│     ├─ 发出 PLAN_AWAITING_APPROVAL → 用户审批          │
│     └─ 用户批准后 → 继续 ▼                             │
│                                                      │
│  3. 执行Agent.dispatch_plan(plan)                      │
│     ├─ 调用 orchestration_engine.execute_plan()       │
│     ├─ 监控每个 step 的执行                            │
│     ├─ 收集结果 → 返回给策略Agent                       │
│     └─ 继续 ▼                                         │
│                                                      │
│  4. 策略Agent.review(results)                          │
│     ├─ 满意 → 输出最终结果给用户                        │
│     └─ 不满意 → 修正 PLAN → 重新执行 (goto 3)          │
└─────────────────────────────────────────────────────┘
```

### 2.3 消息路由变更

**现有** (`backend/app/api/ws.py:260-271`):
```python
if "agent_communication" in agent_tools:
    await _handle_orchestrated_message(...)
else:
    await _stream_with_tools(...)
```

**新**:
```python
if "agent_communication" in agent_tools:
    if agent.is_meta:  # Meta-Agent → 走 MetaAgentRouter
        await _handle_meta_agent_message(...)
    else:  # 普通有agent_communication的Agent → 现有orchestration
        await _handle_orchestrated_message(...)
else:
    await _stream_with_tools(...)
```

### 2.4 Agent 模型变更

**`AgentDetail` (agent_service.py:70-88) 新增字段**:
```python
is_meta: bool = False  # True = Meta-Agent(调度者), False = 普通Agent(执行者)
```

**`AgentCreate` (agent_service.py:28-39) 新增字段**:
```python
is_meta: bool = False
```

**`Agent` DB模型 (`models/agent.py`) 新增列**:
```python
is_meta: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 2.5 三个新预设 Meta-Agent

在 `agent_service.py` 现有3个预设之外**新增**3个 Meta-Agent 预设（共存，不替换）:

```python
# 预设: 智能决策Agent (is_meta=True, is_preset=True)
{
    "name": "智能决策",
    "description": "Meta-Agent: 分析用户意图，判断任务复杂度，决定执行方向",
    "system_prompt": "你是NEXUS AI的决策层Meta-Agent。你的职责是：\n"
                     "1. 分析用户消息的意图和复杂度\n"
                     "2. 判断任务属于 simple(直接委派普通Agent) 还是 complex(需策略Agent制定Plan)\n"
                     "3. 简单任务：选择合适的普通Agent直接处理\n"
                     "4. 复杂任务：将任务描述传递给策略Agent进行Plan制定\n"
                     "判断规则：需要多步骤协调、多Agent协作、或多工具配合的任务为complex；单步可完成的简单查询为simple。",
    "tools": ["agent_communication"],
    "permission_level": 4,
    "temperature": 0.3,
    "is_meta": True,
    "auto_execute": True,
},
{
    "name": "策略规划",
    "description": "Meta-Agent: 制定执行计划，审查执行结果",
    "system_prompt": "你是NEXUS AI的策略层Meta-Agent。你的职责是：\n"
                     "1. 根据决策Agent确定的方向，将任务分解为可执行的Plan(steps)\n"
                     "2. 为每个step指定最合适的普通Agent\n"
                     "3. 提交Plan给用户审批\n"
                     "4. 执行完成后Review结果质量\n"
                     "5. 如结果不满意，修正Plan并重新执行",
    "tools": ["agent_communication"],
    "permission_level": 4,
    "temperature": 0.3,
    "is_meta": True,
},
{
    "name": "执行调度",
    "description": "Meta-Agent: 分配Plan步骤，监控执行，协调Agent",
    "system_prompt": "你是NEXUS AI的执行层Meta-Agent。你的职责是：\n"
                     "1. 接收策略Agent制定的Plan\n"
                     "2. 将每个step分配给最合适的普通Agent\n"
                     "3. 监控每个step的执行进度\n"
                     "4. 收集各Agent的执行结果\n"
                     "5. 可在子任务中指定Leader Agent协调多人协作\n"
                     "6. 将汇总结果返回给策略Agent",
    "tools": ["agent_communication", "web_search"],
    "permission_level": 3,
    "temperature": 0.4,
    "is_meta": True,
},
```

### 2.6 WebSocket 消息类型新增

在 `ws.py` MessageType enum 新增:

```python
# Meta-Agent 分层消息
META_AGENT_STARTED = "meta_agent_started"       # Meta-Agent 开始工作
META_AGENT_COMPLETED = "meta_agent_completed"   # Meta-Agent 完成工作
META_AGENT_DISPATCH = "meta_agent_dispatch"     # 执行Agent派发step给普通Agent
TRIAGE_RESULT = "triage_result"                 # 决策Agent的复杂度判断结果
LAYER_TRANSITION = "layer_transition"           # 层级切换 (decision→strategy→execution)
```

---

## 3. 新增模块设计

### 3.1 `MetaAgentRouter` (`backend/app/core/meta_agent_router.py`)

核心调度器，替代当前 `_handle_orchestrated_message` 的扁平编排逻辑。

```python
class MetaAgentRouter:
    """三层Meta-Agent调度路由器"""

    def __init__(self, agent_store, orchestration_engine, llm_gateway):
        self.agent_store = agent_store
        self.orchestration_engine = orchestration_engine
        self.llm_gateway = llm_gateway

    async def route(
        self,
        message: str,
        conversation_id: str,
        orchestrator_agent_id: str,
        orchestrator_model: str,
        ws_event_callback: Callable,
    ) -> str:
        """
        主入口：根据orchestrator是否是Meta-Agent来决定路径
        - is_meta=True → 走三层流水线
        - is_meta=False → 走现有扁平编排 (向后兼容)
        """
        agent = self.agent_store.get_agent(orchestrator_agent_id)
        if agent.get("is_meta"):
            return await self._run_meta_pipeline(
                message, conversation_id, agent, orchestrator_model, ws_event_callback
            )
        else:
            # 向后兼容：现有扁平编排
            return await self._run_flat_orchestration(
                message, conversation_id, agent, orchestrator_model, ws_event_callback
            )

    async def _run_meta_pipeline(self, message, conversation_id, decision_agent, model, callback) -> str:
        """
        三层流水线:
        Layer 1: 决策Agent → 分析意图
        Layer 2: 策略Agent → 生成/修正 Plan
        Layer 3: 执行Agent → 派发/监控 Plan
        Review:  策略Agent → 审查结果
        """
        # Layer 1: Decision
        await callback("meta_agent_started", {"layer": "decision", "agent_name": decision_agent["name"]})
        triage = await self._run_decision_layer(message, decision_agent, model)
        await callback("meta_agent_completed", {"layer": "decision", "result": triage})
        await callback("layer_transition", {"from": "decision", "to": "strategy" if triage["complexity"] == "complex" else "execution"})

        if triage["complexity"] == "simple":
            return await self._delegate_simple(message, triage, callback)

        # Layer 2: Strategy
        strategy_agent = self._get_meta_agent("strategy")
        await callback("meta_agent_started", {"layer": "strategy", "agent_name": strategy_agent["name"]})
        plan = await self._run_strategy_layer(triage, strategy_agent, model)
        await callback("plan_created", {"plan_id": plan.plan_id, "title": plan.title, ...})

        # Wait for approval (handled by existing approve flow)
        await self._wait_for_approval(plan.plan_id)
        await callback("meta_agent_completed", {"layer": "strategy", "plan_id": plan.plan_id})

        # Layer 3: Execution
        execution_agent = self._get_meta_agent("execution")
        await callback("meta_agent_started", {"layer": "execution", "agent_name": execution_agent["name"]})
        await callback("layer_transition", {"from": "strategy", "to": "execution"})
        results = await self._run_execution_layer(plan, execution_agent, callback)
        await callback("meta_agent_completed", {"layer": "execution", "step_count": len(results)})

        # Review: Strategy reviews results
        await callback("meta_agent_started", {"layer": "strategy_review"})
        synthesis = await self._run_review_layer(plan, results, strategy_agent, model)
        await callback("meta_agent_completed", {"layer": "strategy_review"})

        return synthesis
```

### 3.2 关键方法

| 方法 | 职责 | 复用现有 |
|------|------|---------|
| `_run_decision_layer()` | 调用决策Agent LLM → 返回 TriageResult | 使用 `llm_gateway.chat_completion()` |
| `_run_strategy_layer()` | 调用策略Agent → 返回 Plan | 内部调用 `orchestration_engine.generate_plan(user_content, available_agents, orchestrator_model=strategy_model)` |
| `_run_execution_layer()` | 派发Plan steps → 监控执行 | 内部调用 `orchestration_engine.execute_plan()` |
| `_run_review_layer()` | 策略Agent审查执行结果 | 使用 `llm_gateway.chat_completion_stream()` |
| `_delegate_simple()` | 简单任务直接委派普通Agent | 使用现有 `_stream_with_tools()` 逻辑 |
| `_get_meta_agent(type)` | 从 agent_store 查找 Meta-Agent | 过滤 `is_meta=True`，按 name 匹配类型（决策/策略/执行） |

### 3.3 审批等待机制（`_wait_for_approval`）

复用现有 WebSocket 审批流程（`backend/app/api/ws.py` 中已有 `plan_approved`/`plan_rejected` 消息处理）:

```python
async def _wait_for_approval(self, plan_id: str) -> bool:
    """等待用户审批 Plan。超时默认拒绝。"""
    event = asyncio.Event()
    approved = False

    def on_approval(data):
        nonlocal approved
        approved = data.get("plan_id") == plan_id
        event.set()

    self._approval_callbacks[plan_id] = on_approval
    try:
        await asyncio.wait_for(event.wait(), timeout=300)  # 5分钟超时
    except asyncio.TimeoutError:
        pass
    finally:
        self._approval_callbacks.pop(plan_id, None)
    return approved
```

### 3.4 TriageResult Schema

```python
class TriageResult(BaseModel):
    complexity: Literal["simple", "complex"]
    reasoning: str                          # 判断理由
    suggested_direction: Optional[str]      # 建议的处理方向
    suggested_agent_id: Optional[str]       # simple时：建议委派的Agent ID
    needs_plan: bool                        # complex时：是否需要Plan
```

---

## 4. 语音输入设计

### 4.1 技术方案

使用浏览器 **Web Speech API** (`SpeechRecognition`)，纯客户端实现，无后端依赖。

### 4.2 `VoiceInput` 组件 (`frontend/src/components/conversation/VoiceInput.tsx`)

```
┌──────────────────────────────────────────┐
│  [🎤]  点击开始录音                        │
│                                          │
│  录音中:  ▁▃▅▇▅▃▁ (波形动画)  00:12      │
│  [⏹ 停止]                                │
│                                          │
│  转写结果: "今天天气怎么样"  [✏编辑] [📤发送]│
└──────────────────────────────────────────┘
```

### 4.3 关键实现

```typescript
function VoiceInput({ onTranscription }: { onTranscription: (text: string) => void }) {
  const [isRecording, setIsRecording] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [isSupported, setIsSupported] = useState(true);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
    }
  }, []);

  if (!isSupported) return null;  // 浏览器不支持时静默隐藏

  const startRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript).join('');
      setInterimText(transcript);
      if (event.results[0].isFinal) {
        onTranscription(transcript);
      }
    };

    recognition.onerror = (event) => {
      // 处理错误: no-speech, audio-capture, not-allowed
      setIsRecording(false);
    };

    recognition.start();
    setIsRecording(true);
  };

  // ... stopRecording, render
}
```

### 4.4 集成方式

在 `ConversationUI.tsx` 的 `ChatInput` 组件中（现有 disabled Mic 按钮位置，约 line 590）:
- 将 disabled 的 Mic 按钮替换为 `<VoiceInput onTranscription={handleVoiceTranscription} />`
- `handleVoiceTranscription` 将转写文字填入 input 的 value，用户可编辑后发送

### 4.5 降级策略

| 场景 | 行为 |
|------|------|
| 浏览器不支持 SpeechRecognition | 隐藏麦克风按钮（`isSupported=false` → return null） |
| 用户拒绝麦克风权限 | 显示 tooltip 提示需要权限 |
| 无语音输入 (no-speech) | 超时后自动停止，不产生文字 |
| 浏览器兼容性 | Chrome/Edge 完全支持；Firefox 部分支持（隐藏按钮） |

---

## 5. WebSearchTool 增强

### 5.1 现有状态

`WebSearchTool` (`tool_registry.py`) 使用 DuckDuckGo Instant Answer API:
- URL: `https://api.duckduckgo.com/`
- 参数: `q`, `format=json`, `no_html=1`, `skip_disambig=1`
- 返回: `AbstractText` + `RelatedTopics`
- 问题: 结果单一，无法控制数量，无法过滤

### 5.2 增强内容

```python
class WebSearchToolInput(BaseModel):
    query: str = Field(..., description="搜索关键词")
    num_results: int = Field(default=5, ge=1, le=20, description="返回结果数")
    search_type: Literal["web", "news"] = Field(default="web", description="搜索类型")
    language: str = Field(default="zh-CN", description="语言偏好")

class WebSearchToolOutput(BaseModel):
    results: list[SearchResult]  # SearchResult: {title, url, snippet, published_date?}
    total_found: int
    search_engine: str
```

### 5.3 实现变更

- 保留 DuckDuckGo 作为默认引擎（免费、无需 API Key）
- 扩展参数支持 `num_results`, `search_type`, `language`
- 结构化返回结果（title, url, snippet, published_date）
- 在 `yaml_config.py` 的 `DEFAULT_CONFIG` 中新增 `web_search` 配置段，预留给未来多引擎切换

---

## 6. 前端变更

### 6.1 `conversationSlice.ts` — 新增 Meta-Agent 状态

```typescript
// 新增接口
export interface MetaAgentState {
  current_layer: "decision" | "strategy" | "execution" | "review" | null;
  layer_history: { layer: string; agent_name: string; timestamp: string }[];
  triage_result: { complexity: "simple" | "complex"; reasoning: string } | null;
}

// OrchestrationPlan 扩展
export interface OrchestrationPlan {
  // ... 现有字段
  meta_agent_layers?: string[];  // ["decision", "strategy", "execution"]
}
```

### 6.2 `PlanViewer.tsx` — 显示层级进度

在 Plan 视图中新增层级进度指示器:
```
决策 ▸ 策略 ▸ 执行 ▸ 审查
 ✓      ◑      ○      ○
```

### 6.3 `AgentManagerUI.tsx` — is_meta 字段编辑

- Agent 编辑表单新增 `is_meta` 复选框
- Agent 列表卡片显示 Meta/普通 标签

---

## 7. 测试策略

### 7.1 新增测试文件

| 文件 | 测试内容 | 预估用例数 |
|------|---------|-----------|
| `backend/tests/test_meta_agent_router.py` | MetaAgentRouter 单元测试 (triage分流、三层流水线、降级路径) | ~15 |
| `backend/tests/test_meta_agent_integration.py` | Meta-Agent 端到端集成测试 | ~8 |
| `frontend/src/__tests__/components/conversation/VoiceInput.test.tsx` | VoiceInput 组件测试 | ~8 |
| `frontend/src/__tests__/components/conversation/PlanViewer.test.tsx` | 层级进度显示测试 | ~5 |

### 7.2 向后兼容测试

现有 299 个测试全部保持通过。新增测试 mock 所有外部依赖（LLM API, Docker, PostgreSQL, Redis）。

---

## 8. 文件变更清单

### 后端新增
| 文件 | 说明 |
|------|------|
| `backend/app/core/meta_agent_router.py` | Meta-Agent 三层调度路由器 |
| `backend/app/schemas/meta_agent.py` | MetaAgent 相关 Pydantic models |

### 后端修改
| 文件 | 变更 |
|------|------|
| `agent_service.py` | AgentDetail/AgentCreate 新增 `is_meta` 字段；新增3个 Meta-Agent 预设 |
| `ws.py` | MessageType 新增 5 个 Meta-Agent 消息类型 |
| `api/ws.py` | `_handle_user_message` 路由接入 MetaAgentRouter |
| `orchestration_engine.py` | `generate_plan()` 可选接收 strategy_agent 参数 |
| `yaml_config.py` | DEFAULT_CONFIG 新增 `meta_agents` 和 `web_search` 配置段 |
| `models/agent.py` | Agents 表新增 `is_meta` 列 |
| `tool_registry.py` | WebSearchTool 参数扩展 |

### 前端新增
| 文件 | 说明 |
|------|------|
| `frontend/src/components/conversation/VoiceInput.tsx` | 语音录制组件 |

### 前端修改
| 文件 | 变更 |
|------|------|
| `ConversationUI.tsx` | ChatInput 集成 VoiceInput 替换 disabled Mic 按钮 |
| `conversationSlice.ts` | 新增 MetaAgentState + OrchestrationPlan 扩展 |
| `PlanViewer.tsx` | 新增层级进度指示器 |
| `AgentManagerUI.tsx` | is_meta 字段编辑/显示 |
| `i18n.ts` | 新增 voice.* 和 meta_agent.* i18n keys |

### 基础设施
| 文件 | 变更 |
|------|------|
| `docker-compose.yml` | 无变更（无需新服务） |
| `Makefile` | 无变更（测试命令不变） |

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Meta-Agent 调用链增加延迟 | 每次三层调用增加 3-8s 延迟 | 简单查询不走三层（决策Agent直接委派）；流式显示减少体感 |
| 决策Agent 误判复杂度 | 简单任务走冗长流程 / 复杂任务被简单处理 | Triage prompt 持续优化；用户可在前端手动切换模式 |
| Meta-Agent 之间通信断裂 | Plan 传递失败导致流程中断 | 每层有独立超时+retry；关键状态写入 variable table |
| Web Speech API 兼容性 | Firefox 部分不支持 | 功能检测 → 不支持时隐藏按钮；Chrome/Edge 主要支持即可 |
| 向后兼容性 | 现有 Agent 和编排逻辑受影响 | `is_meta=False` 默认值确保现有Agent行为不变；路由层检查 `is_meta` 分流 |

---

## 10. 与现有系统的共存关系

```
                    _handle_user_message()
                            │
                    agent_communication in tools?
                           ╱ ╲
                         No   Yes
                         │      │
               单Agent路径    is_meta?
                (不变)        ╱ ╲
                          Yes   No
                           │      │
                   MetaAgentRouter  现有扁平编排
                   (新增)          (不变)
```

- **单Agent路径（无 agent_communication）**: 完全不变
- **扁平编排路径（有 agent_communication 但 is_meta=False）**: 完全不变（数字主管、现有自定义编排Agent）
- **三层Meta-Agent路径（is_meta=True）**: 新路径，不影响上述两条路径

---

## 11. 实现依赖关系

```
Phase 1: Agent 模型扩展 (is_meta 字段 + 3个新预设)
    ↓
Phase 2: MetaAgentRouter 核心模块
    ↓
Phase 3: WS 消息类型 + api/ws.py 路由接入
    ↓
Phase 4: 前端 VoiceInput 组件
    ↓
Phase 5: 前端 PlanViewer + conversationSlice 更新
    ↓
Phase 6: WebSearchTool 增强
    ↓
Phase 7: 测试 + 向后兼容验证
```

Phase 1-3 必须顺序执行。Phase 4 和 Phase 6 可以并行。Phase 5 依赖 Phase 3。
