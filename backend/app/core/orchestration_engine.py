"""Orchestration Engine - supervisor-worker pattern, task breakdown, scheduling."""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog
from pydantic import BaseModel, Field

from app.core.yaml_config import get_yaml_config

logger = structlog.get_logger(__name__)

yaml_config = get_yaml_config()
ORCH_CONFIG = yaml_config.get("orchestration", {})


# --- Enums ---

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CONFIRM = "waiting_confirm"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DependencyType(str, Enum):
    NONE = "none"       # Can run in parallel
    SEQUENTIAL = "sequential"  # Must run after previous step
    DATA_DEPENDENCY = "data_dependency"  # Needs output from another step


# --- Schemas ---

class SubTask(BaseModel):
    """A single subtask in the orchestration plan."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)  # step_ids this depends on
    dependency_type: DependencyType = DependencyType.NONE
    input_variables: list[str] = Field(default_factory=list)
    expected_output: Optional[str] = None


class OrchestrationPlan(BaseModel):
    """The complete execution plan."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    subtasks: list[SubTask]
    parallel_groups: list[list[str]] = Field(default_factory=list)  # Groups of step_ids that can run in parallel
    total_estimated_steps: int = 0
    variable_table_keys: list[str] = Field(default_factory=list)


class StepResult(BaseModel):
    """Result from a completed step."""
    step_id: str
    status: StepStatus
    output: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class VariableEntry(BaseModel):
    """A single entry in the variable table."""
    key: str
    value: Optional[dict] = None
    data_type: str = "string"
    written_by_step: Optional[str] = None


# --- Orchestration Engine ---

class OrchestrationEngine:
    """Manages task orchestration lifecycle."""

    def __init__(self):
        self._plans: dict[str, OrchestrationPlan] = {}
        self._step_results: dict[str, dict[str, StepResult]] = {}  # plan_id -> {step_id -> result}
        self._variable_tables: dict[str, dict[str, VariableEntry]] = {}  # plan_id -> {key -> entry}
        self._statuses: dict[str, TaskStatus] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def create_plan(
        self,
        title: str,
        subtask_descriptions: list[str],
        available_agents: list[dict],
        conversation_id: Optional[str] = None,
    ) -> OrchestrationPlan:
        """Create an execution plan from task description.

        This is the supervisor's main task: analyze and break down.
        """
        plan_id = str(uuid.uuid4())

        # Build subtasks with dependency analysis
        subtasks = []
        for i, desc in enumerate(subtask_descriptions):
            # Simple heuristic: if a subtask mentions "after", "then", "based on",
            # it likely depends on previous steps
            dependencies = []
            dep_type = DependencyType.NONE

            if i > 0 and any(kw in desc.lower() for kw in ["after", "then", "based on", "using the result"]):
                dependencies = [subtasks[i-1].step_id if subtasks else str(uuid.uuid4())]
                dep_type = DependencyType.SEQUENTIAL

            # Assign agent
            agent = available_agents[i % len(available_agents)] if available_agents else None
            subtask = SubTask(
                description=desc,
                assigned_agent_id=agent.get("id") if agent else None,
                assigned_agent_name=agent.get("name") if agent else None,
                dependencies=dependencies,
                dependency_type=dep_type,
            )
            subtasks.append(subtask)

        # Group into parallel execution groups
        parallel_groups = self._compute_parallel_groups(subtasks)

        plan = OrchestrationPlan(
            plan_id=plan_id,
            title=title,
            subtasks=subtasks,
            parallel_groups=parallel_groups,
            total_estimated_steps=len(subtasks),
        )

        self._plans[plan_id] = plan
        self._step_results[plan_id] = {}
        self._variable_tables[plan_id] = {}
        self._statuses[plan_id] = TaskStatus.PENDING
        self._locks[plan_id] = asyncio.Lock()

        logger.info("Execution plan created", plan_id=plan_id, subtask_count=len(subtasks))
        return plan

    async def execute_plan(self, plan_id: str) -> list[StepResult]:
        """Execute all subtasks in the plan, respecting dependencies."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        self._statuses[plan_id] = TaskStatus.RUNNING
        results: list[StepResult] = []

        # Execute in order of parallel groups
        for group in plan.parallel_groups:
            if self._statuses[plan_id] == TaskStatus.CANCELLED:
                break

            # Run parallel subtasks
            tasks = []
            for step_id in group:
                task = asyncio.create_task(self._execute_step(plan_id, step_id))
                tasks.append(task)

            group_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(group_results):
                step_id = group[i]
                if isinstance(result, Exception):
                    step_result = StepResult(
                        step_id=step_id,
                        status=StepStatus.FAILED,
                        error=str(result),
                    )
                else:
                    step_result = result
                self._step_results[plan_id][step_id] = step_result
                results.append(step_result)

        # Finalize
        all_completed = all(r.status == StepStatus.COMPLETED for r in results)
        if self._statuses[plan_id] != TaskStatus.CANCELLED:
            self._statuses[plan_id] = TaskStatus.COMPLETED if all_completed else TaskStatus.FAILED

        return results

    async def _execute_step(self, plan_id: str, step_id: str) -> StepResult:
        """Execute a single step (mock implementation)."""
        plan = self._plans[plan_id]
        subtask = next((s for s in plan.subtasks if s.step_id == step_id), None)
        if not subtask:
            return StepResult(step_id=step_id, status=StepStatus.FAILED, error="Subtask not found")

        now = datetime.now(timezone.utc).isoformat()
        logger.info("Executing step", step_id=step_id, description=subtask.description[:50])

        # Simulate work
        await asyncio.sleep(0.01)

        return StepResult(
            step_id=step_id,
            status=StepStatus.COMPLETED,
            output=f"Completed: {subtask.description}",
            agent_id=subtask.assigned_agent_id,
            started_at=now,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    async def pause(self, plan_id: str) -> bool:
        if plan_id in self._statuses and self._statuses[plan_id] == TaskStatus.RUNNING:
            self._statuses[plan_id] = TaskStatus.PAUSED
            return True
        return False

    async def resume(self, plan_id: str) -> bool:
        if plan_id in self._statuses and self._statuses[plan_id] == TaskStatus.PAUSED:
            self._statuses[plan_id] = TaskStatus.RUNNING
            return True
        return False

    async def cancel(self, plan_id: str) -> bool:
        if plan_id in self._statuses:
            self._statuses[plan_id] = TaskStatus.CANCELLED
            return True
        return False

    async def set_variable(self, plan_id: str, key: str, value: dict, step_id: Optional[str] = None) -> VariableEntry:
        entry = VariableEntry(key=key, value=value, written_by_step=step_id)
        self._variable_tables.setdefault(plan_id, {})[key] = entry
        return entry

    async def get_variable(self, plan_id: str, key: str) -> Optional[VariableEntry]:
        return self._variable_tables.get(plan_id, {}).get(key)

    async def get_all_variables(self, plan_id: str) -> dict[str, VariableEntry]:
        return self._variable_tables.get(plan_id, {})

    def get_status(self, plan_id: str) -> Optional[TaskStatus]:
        return self._statuses.get(plan_id)

    def get_plan(self, plan_id: str) -> Optional[OrchestrationPlan]:
        return self._plans.get(plan_id)

    def get_step_results(self, plan_id: str) -> dict[str, StepResult]:
        return self._step_results.get(plan_id, {})

    def _compute_parallel_groups(self, subtasks: list[SubTask]) -> list[list[str]]:
        """Group subtasks by dependency: independent tasks can run in parallel."""
        if not subtasks:
            return []

        # Simple: all tasks without dependencies run in one group,
        # then each dependent task runs in its own group
        independent = [s for s in subtasks if not s.dependencies]
        dependent = [s for s in subtasks if s.dependencies]

        groups = []
        if independent:
            groups.append([s.step_id for s in independent])

        for s in dependent:
            groups.append([s.step_id])

        return groups


# Global engine
orchestration_engine = OrchestrationEngine()
