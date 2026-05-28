下面给出 **`rosclaw-sandbox` 集成到 ROSClaw v1.0** 的完整方案，目标路径是：

```bash
/home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
```

我建议采取 **“先独立开发、再作为 v1.0 内部一等模块集成”** 的方式。不要把 sandbox 简单复制进去，也不要让它变成孤立脚本，而是要让它挂到 `rosclaw-runtime`、`agent_runtime`、`event_bus`、`practice`、`memory`、`dashboard` 这些主链路里。你的 v1.0 见解里已经明确：ROSClaw 不是一堆模块，而是一个 Physical Intelligence Runtime，所有模块必须挂到 Runtime，由 Runtime 统一管理生命周期、配置、插件、日志和事件。

---

# 一、集成总原则

最终集成形态应该是：

```text
rosclaw-v1.0/
  src/rosclaw/
    sandbox/
      ...
```

而不是：

```text
rosclaw-v1.0/
  rosclaw-sandbox/
    ...
```

也就是说，**开发阶段可以独立仓库 `rosclaw-sandbox`，集成阶段应该进入 v1.0 的 Python namespace：`rosclaw.sandbox`**。

原因很简单：

```text
独立开发阶段：
  方便并行开发、单独测试、快速迭代

v1.0 集成阶段：
  必须由 rosclaw-runtime 统一启动
  必须复用 rosclaw-config
  必须复用 event_bus
  必须复用 e-URDF-Zoo
  必须对 agent_runtime 暴露安全检查能力
```

---

# 二、在 v1.0 中的定位

你之前文档里写过一条核心链路：

```text
LLM
 ↓
ROSClaw Runtime
 ↓
Physical World
```

并且明确提出：大模型不直接接触内部模块，而是通过 `agent_runtime` 进入 Runtime，再由 Runtime 负责物理 grounding。

所以 sandbox 集成后的位置应该是：

```text
Agent Runtime
    ↓
Sandbox / Firewall
    ↓
Practice Capture
    ↓
ROS 2 / Driver / Physical World
```

更完整的 v1.0 链路：

```text
LLM / Claude / Qwen / OpenClaw
        ↓
rosclaw-agent-runtime
        ↓
rosclaw-runtime
        ↓
rosclaw-sandbox
        ├── simulation mode
        ├── task mode
        ├── replay mode
        └── firewall mode
        ↓
rosclaw-practice
        ↓
rosclaw-memory / SeekDB
        ↓
rosclaw-how / recovery
        ↓
rosclaw-dashboard / visualization
```

你的文档里原本把这部分叫 `rosclaw-firewall`，并把它和 `mjlab`、`e-urdf integration` 放在 Physical Alignment Sprint 中，目标是实现碰撞预测和危险动作熔断。
现在建议升级为：

```text
rosclaw-sandbox 是模块名
rosclaw.sandbox.firewall 是安全子模块
```

这样不会丢掉 firewall 的安全语义，也能容纳仿真、任务、回放、评测等更大能力。

---

# 三、推荐 v1.0 目录改造

目标目录：

```bash
/home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
```

建议最终结构：

```text
rosclaw-v1.0/
├── pyproject.toml
├── README.md
├── docker-compose.yaml
├── configs/
│   ├── rosclaw.yaml
│   ├── sandbox.yaml
│   ├── robots.yaml
│   ├── worlds/
│   │   ├── empty.yaml
│   │   ├── flat_ground.yaml
│   │   └── tabletop.yaml
│   └── tasks/
│       ├── ur5e_reach_target.yaml
│       ├── ur5e_pick_cube.yaml
│       ├── go2_stand.yaml
│       └── go2_walk_forward.yaml
│
├── src/
│   └── rosclaw/
│       ├── __init__.py
│       │
│       ├── core/
│       │   ├── runtime.py
│       │   ├── lifecycle.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── dependency.py
│       │
│       ├── event_bus/
│       │   ├── bus.py
│       │   ├── schemas.py
│       │   └── subscribers.py
│       │
│       ├── agent_runtime/
│       │   ├── context.py
│       │   ├── mcp_server.py
│       │   ├── tools.py
│       │   └── interceptors.py
│       │
│       ├── e_urdf/
│       │   ├── loader.py
│       │   ├── profile.py
│       │   └── registry.py
│       │
│       ├── sandbox/
│       │   ├── __init__.py
│       │   ├── core/
│       │   ├── eurdf/
│       │   ├── engines/
│       │   ├── validator/
│       │   ├── worlds/
│       │   ├── tasks/
│       │   ├── firewall/
│       │   ├── traces/
│       │   ├── events/
│       │   ├── server/
│       │   └── cli/
│       │
│       ├── practice/
│       ├── memory/
│       ├── dashboard/
│       ├── swarm/
│       ├── how/
│       ├── know/
│       └── cli/
│           └── main.py
│
├── e-urdf-zoo/
│   ├── ur5e/
│   ├── go2/
│   └── panda/
│
├── runs/
│   └── sandbox/
│
├── tests/
│   ├── sandbox/
│   ├── integration/
│   └── e2e/
│
└── docs/
    ├── sandbox.md
    ├── sandbox_acceptance.md
    └── v1_integration.md
```

其中最关键的是：

```text
src/rosclaw/sandbox/
```

而不是继续保留：

```text
src/rosclaw/firewall/
```

如果现有 v1.0 已经有 `firewall` 目录，可以改成：

```text
src/rosclaw/sandbox/firewall/
```

并保留兼容层：

```python
# src/rosclaw/firewall/__init__.py

from rosclaw.sandbox.firewall import *
```

这样旧代码不会立刻炸。

---

# 四、pyproject.toml 集成

在 v1.0 的 `pyproject.toml` 中加入 sandbox 依赖组。

建议：

```toml
[project.optional-dependencies]
sandbox = [
    "mujoco>=3.0.0",
    "numpy",
    "pydantic>=2",
    "typer",
    "rich",
    "pyyaml",
]

sandbox-dev = [
    "pytest",
    "pytest-asyncio",
    "ruff",
    "mypy",
]

sandbox-export = [
    "mcap",
    "opencv-python",
]
```

如果 v1.0 使用 `uv`：

```bash
cd /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
uv sync --extra sandbox --extra sandbox-dev
```

如果使用 pip editable：

```bash
pip install -e ".[sandbox,sandbox-dev]"
```

---

# 五、配置文件集成

新增：

```bash
configs/sandbox.yaml
```

内容建议：

```yaml
sandbox:
  enabled: true
  default_engine: mujoco
  mode: simulation

  paths:
    eurdf_zoo: ./e-urdf-zoo
    runs_dir: ./runs/sandbox
    reports_dir: ./runs/sandbox/reports

  mujoco:
    enabled: true
    headless: true
    timestep: 0.002
    control_dt: 0.02
    render_width: 1280
    render_height: 720

  firewall:
    enabled: true
    default_horizon_sec: 2.0
    risk_threshold: 0.75
    block_on_collision: true
    block_on_joint_limit: true
    block_on_workspace_violation: true

  trace:
    record_by_default: true
    export_jsonl: true
    export_mcap: false
    export_video: false

  event_bus:
    publish_events: true
```

然后在主配置：

```bash
configs/rosclaw.yaml
```

里加入：

```yaml
modules:
  core:
    enabled: true
  agent_runtime:
    enabled: true
  e_urdf:
    enabled: true
  sandbox:
    enabled: true
  practice:
    enabled: true
  memory:
    enabled: true
  dashboard:
    enabled: false

sandbox_config: ./configs/sandbox.yaml
```

---

# 六、Runtime 集成方式

v1.0 的核心应该有一个类似：

```python
class Runtime:
    ...
```

你的文档里已经明确 Runtime 要统一管理 memory、practice、firewall、swarm、skill_manager、agent_runtime、event_bus 等组件。

现在要改成：

```python
class Runtime:
    core
    config
    event_bus
    e_urdf
    sandbox
    practice
    memory
    agent_runtime
    dashboard
    swarm
```

建议新增：

```python
# src/rosclaw/sandbox/runtime_adapter.py

class SandboxRuntimeAdapter:
    name = "sandbox"

    def __init__(self, config, event_bus, eurdf_registry):
        self.config = config
        self.event_bus = event_bus
        self.eurdf_registry = eurdf_registry
        self.service = None

    async def start(self):
        self.service = SandboxService(
            config=self.config,
            event_bus=self.event_bus,
            eurdf_registry=self.eurdf_registry,
        )
        await self.service.start()

    async def stop(self):
        if self.service:
            await self.service.stop()

    def health(self):
        return self.service.health()
```

然后在：

```python
# src/rosclaw/core/runtime.py
```

中注册：

```python
from rosclaw.sandbox.runtime_adapter import SandboxRuntimeAdapter

class Runtime:
    async def start(self):
        self.event_bus = EventBus(...)
        self.e_urdf = EurdfRegistry(...)
        
        if self.config.modules.sandbox.enabled:
            self.sandbox = SandboxRuntimeAdapter(
                config=self.config.sandbox,
                event_bus=self.event_bus,
                eurdf_registry=self.e_urdf,
            )
            await self.sandbox.start()
```

启动日志建议：

```text
[ROSClaw] Loading e-URDF-Zoo...
[ROSClaw] Starting Event Bus...
[ROSClaw] Starting Sandbox...
[ROSClaw] Starting Sandbox Firewall...
[ROSClaw] Starting Agent Runtime...
[ROSClaw] Runtime Online.
```

这和你之前 v1.0 见解中 `rosclaw start` 启动 e-URDF、Firewall、SeekDB、Agent Runtime 的方向一致。

---

# 七、Event Bus 集成

这是最关键的一层。

你文档里明确强调：所有模块禁止互相乱调，要通过 `publish / subscribe` 解耦。
因此 sandbox 集成 v1.0 时，不能让：

```text
sandbox 直接调用 memory
sandbox 直接调用 how
sandbox 直接调用 darwin
```

而应该发布事件。

## 1. Sandbox 发布的事件

```python
SandboxSessionStarted
SandboxSessionStopped
SandboxStepExecuted
SandboxTaskStarted
SandboxTaskSucceeded
SandboxTaskFailed
SandboxCollisionDetected
SandboxValidationReportGenerated
SandboxReplayCreated

FirewallCheckRequested
FirewallActionAllowed
FirewallActionBlocked
FirewallActionModified
```

## 2. Practice 订阅

```python
SandboxTaskStarted
SandboxTaskSucceeded
SandboxTaskFailed
FirewallActionAllowed
FirewallActionBlocked
```

Practice 负责生成：

```text
PraxisEvent
MCAP index
timeline record
```

你的 v1.0 文档也强调：如果 firewall 放行，指令发给 ROS 2，同时 practice 开始录制 MCAP；动作结束后 practice 组装 PraxisEvent，再进入 memory/SeekDB。

## 3. Memory 订阅

```python
SandboxTaskFailed
FirewallActionBlocked
SandboxCollisionDetected
```

生成：

```text
EmbodiedFailureMemory
RiskPatternMemory
RecoveryHintMemory
```

## 4. Dashboard 订阅

```python
SandboxStepExecuted
SandboxCollisionDetected
FirewallActionBlocked
SandboxReplayCreated
```

展示：

```text
仿真画面
关节状态
碰撞点
reward 曲线
失败报告
replay 链接
```

## 5. Darwin 订阅

```python
SandboxTaskSucceeded
SandboxTaskFailed
SandboxValidationReportGenerated
```

用于 benchmark 统计。

---

# 八、Agent Runtime 集成

这是 sandbox/firewall 的第一主入口。

你文档里明确：大模型只和 `agent_runtime` 交互；`agent_runtime` 接收意图后，把指令交给 firewall，firewall 结合 e-URDF 参数在 MuJoCo 中推演。

所以需要新增 `ActionGroundingInterceptor`：

```python
# src/rosclaw/agent_runtime/interceptors.py

class ActionGroundingInterceptor:
    def __init__(self, sandbox_service):
        self.sandbox_service = sandbox_service

    async def before_action(self, action_request):
        decision = await self.sandbox_service.firewall.check(action_request)

        if decision.decision == "ALLOW":
            return action_request

        if decision.decision == "MODIFY_AND_ALLOW":
            return decision.modified_action

        raise ActionBlockedError(
            reason=decision.reason,
            risk_score=decision.risk_score,
            replay_id=decision.replay_id,
        )
```

调用链：

```text
LLM Tool Call
  ↓
Agent Runtime Tool Router
  ↓
ActionGroundingInterceptor
  ↓
Sandbox Firewall Check
  ↓
ALLOW → ROS 2 Driver / MCP Driver
BLOCK → 返回给 LLM
```

返回给 Agent 的格式：

```json
{
  "status": "blocked",
  "module": "rosclaw-sandbox.firewall",
  "reason": "Predicted collision between wrist_link and table",
  "risk_score": 0.93,
  "replay_id": "firewall_ep_00042",
  "suggestion": "Raise target z by 0.08m and retry."
}
```

这样 agent 能根据原因重新规划。

---

# 九、CLI 集成

开发阶段的独立 CLI：

```bash
rosclaw-sandbox run ...
```

集成到 v1.0 后，主 CLI 应该变成：

```bash
rosclaw sandbox doctor
rosclaw sandbox robots list
rosclaw sandbox validate ur5e
rosclaw sandbox run --task ur5e_reach_target --record
rosclaw sandbox replay runs/sandbox/ep_0001

rosclaw firewall check --robot ur5e --action bad_action.json
rosclaw firewall serve
```

实现方式：

```python
# src/rosclaw/cli/main.py

app.add_typer(sandbox_app, name="sandbox")
app.add_typer(firewall_app, name="firewall")
```

保持兼容：

```bash
rosclaw-sandbox ...
```

可以作为开发者快捷入口，但 v1.0 文档统一推荐：

```bash
rosclaw sandbox ...
```

---

# 十、e-URDF-Zoo 集成

你的文档已经把 e-URDF-Zoo 定位成 **Physical DNA Registry**，包括 `robot.urdf`、`robot.xml`、`safety.yaml`、`semantic.yaml`、`capabilities.yaml`、`benchmark.yaml`，并说明不同模块读取不同文件：Firewall 读取 `safety.yaml`，Swarm 读取 `capabilities.yaml`，Dashboard 读取 `semantic.yaml`，Darwin 读取 `benchmark.yaml`。

集成时建议：

```text
rosclaw-v1.0/e-urdf-zoo/
  ur5e/
    robot.urdf
    robot.mjcf.xml
    safety.yaml
    semantic.yaml
    capabilities.yaml
    benchmark.yaml
    assets/
  go2/
    robot.urdf
    robot.mjcf.xml
    safety.yaml
    semantic.yaml
    capabilities.yaml
    benchmark.yaml
    assets/
```

sandbox 只直接消费：

```text
robot.urdf
robot.mjcf.xml
safety.yaml
capabilities.yaml
semantic.yaml
benchmark.yaml
assets/
```

但必须通过 v1.0 的 `e_urdf.Registry` 读取，而不是自己到处扫目录。

建议接口：

```python
profile = runtime.e_urdf.get_robot_profile("ur5e")
sandbox.load_robot(profile)
```

不要：

```python
sandbox.load_robot("/some/random/path/ur5e")
```

这样以后 e-URDF-Zoo 作为 submodule、远程 registry、clawhub 包管理都能兼容。

---

# 十一、Practice / Memory / SeekDB 集成

这部分不要第一天强耦合，但必须打通事件流。

你的 v1.0 文档里已经明确 SeekDB 不应只是 Memory 的数据库，而应该是 ROSClaw 的 Knowledge Plane，服务 Memory、Practice、How、Know、Auto、Darwin、Skill 等模块。

sandbox 集成策略：

```text
sandbox 不直接写 SeekDB
practice 订阅 sandbox 事件
practice 生成 PraxisEvent
memory 订阅 PraxisEvent
memory 写 SeekDB
```

事件流：

```text
SandboxTaskFailed
  ↓
PracticeTimelineEvent
  ↓
PraxisEvent
  ↓
MemoryExperienceEvent
  ↓
SeekDB experience_graph
```

示例：

```json
{
  "event_type": "SandboxTaskFailed",
  "robot_id": "ur5e",
  "task_id": "ur5e_pick_cube",
  "failure_type": "collision",
  "reason": "wrist_link collided with table",
  "replay_id": "ep_00042",
  "trace_dir": "runs/sandbox/ep_00042"
}
```

Practice 转成：

```json
{
  "event_type": "PraxisEvent",
  "source": "sandbox",
  "robot_id": "ur5e",
  "task_id": "ur5e_pick_cube",
  "status": "failed",
  "mcap_path": "runs/sandbox/ep_00042/episode.mcap",
  "trace_path": "runs/sandbox/ep_00042/trajectory.jsonl",
  "failure_report": "runs/sandbox/ep_00042/failure_report.md"
}
```

你的文档里也写到，Practice 整合后要把包含时间戳、MCAP 路径、大模型意图的 `PraxisEvent` 推给 memory，再写入 SeekDB。

---

# 十二、docker-compose 集成

你原来的 v1.0 见解里已经提出根目录提供 `docker-compose.yaml`，拉起 SeekDB 和 `rosclaw-kernel`，并使用 host 网络打通 ROS 2 DDS。

现在需要加 sandbox 环境变量和 volume。

```yaml
version: "3.8"

services:
  seekdb:
    image: oceanbase/seekdb:latest
    ports:
      - "2881:2881"
    volumes:
      - ~/.rosclaw/data/seekdb:/var/lib/seekdb

  rosclaw-kernel:
    build: .
    network_mode: "host"
    environment:
      - SEEKDB_URI=http://localhost:2881
      - ROS_DOMAIN_ID=42
      - ROSCLAW_CONFIG=/app/configs/rosclaw.yaml
      - ROSCLAW_EURDF_ZOO=/app/e-urdf-zoo
      - ROSCLAW_SANDBOX_RUNS=/app/runs/sandbox
      - ROSCLAW_SANDBOX_ENGINE=mujoco
      - ROSCLAW_SANDBOX_FIREWALL=1
    volumes:
      - ./configs:/app/configs
      - ./e-urdf-zoo:/app/e-urdf-zoo
      - ./runs:/app/runs
      - ~/.rosclaw/mcap_records:/data/mcap
    command:
      - rosclaw
      - start
      - --enable-sandbox
      - --enable-firewall
```

注意：MuJoCo headless 在服务器上跑时，可能需要处理 EGL / OSMesa。建议 v1.0 第一阶段默认：

```yaml
sandbox:
  mujoco:
    headless: true
    render_backend: none
```

视频导出放到 P1。

---

# 十三、集成阶段分步路线

## Phase I：代码并入，但不启用

目标：让代码进入 v1.0，不影响现有启动。

操作：

```bash
cd /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0

mkdir -p src/rosclaw/sandbox
cp -r /path/to/rosclaw-sandbox/src/rosclaw/sandbox/* src/rosclaw/sandbox/
cp -r /path/to/rosclaw-sandbox/configs/worlds configs/
cp -r /path/to/rosclaw-sandbox/configs/tasks configs/
```

配置：

```yaml
modules:
  sandbox:
    enabled: false
```

验收：

```bash
cd /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
python -c "import rosclaw.sandbox; print('sandbox import ok')"
pytest tests/sandbox
```

通过标准：

```text
不影响 rosclaw start
不影响 agent_runtime
不影响 practice / memory
sandbox 单元测试通过
```

---

## Phase II：CLI 集成

目标：主 CLI 能调用 sandbox。

新增：

```bash
rosclaw sandbox doctor
rosclaw sandbox validate ur5e
rosclaw firewall check ...
```

验收：

```bash
rosclaw --help
rosclaw sandbox --help
rosclaw firewall --help
rosclaw sandbox doctor
```

通过标准：

```text
主 CLI 能看到 sandbox 子命令
主 CLI 能看到 firewall 子命令
doctor 能检查 MuJoCo / e-URDF-Zoo / runs_dir
```

---

## Phase III：e-URDF-Zoo 接入

目标：sandbox 不再自己找机器人，而是通过 v1.0 的 e_urdf registry。

验收：

```bash
rosclaw sandbox robots list
rosclaw sandbox robots profile ur5e
rosclaw sandbox validate ur5e
```

通过标准：

```text
能从 /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0/e-urdf-zoo 读取机器人
能读取 safety.yaml
能读取 capabilities.yaml
能读取 semantic.yaml
能输出 validation report
```

---

## Phase IV：Runtime 启动集成

目标：`rosclaw start --enable-sandbox` 能启动 sandbox service。

验收：

```bash
cd /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
rosclaw start --enable-sandbox
```

预期日志：

```text
[ROSClaw] Loading config...
[ROSClaw] Starting Event Bus...
[ROSClaw] Loading e-URDF-Zoo...
[ROSClaw] Starting Sandbox Service...
[ROSClaw] Sandbox engine: mujoco
[ROSClaw] Sandbox runs dir: ./runs/sandbox
[ROSClaw] Runtime Online.
```

健康检查：

```bash
rosclaw status
```

输出应包含：

```text
sandbox: healthy
sandbox.engine: mujoco
sandbox.firewall: disabled/enabled
```

---

## Phase V：Firewall 拦截 Agent Runtime

目标：agent 发动作前必须经过 sandbox firewall。

验收动作：

```bash
rosclaw start --enable-sandbox --enable-firewall
```

然后通过 agent_runtime 发一个危险动作。

预期：

```text
[FIREWALL BLOCKED] Collision predicted
```

并返回给 agent：

```json
{
  "status": "blocked",
  "reason": "Predicted collision",
  "risk_score": 0.9,
  "replay_id": "firewall_ep_xxx"
}
```

这正好对应你文档里 Action Grounding 的验收标准。

---

## Phase VI：Practice 事件接入

目标：sandbox 事件能被 practice 订阅。

验收：

```bash
rosclaw start --enable-sandbox --enable-practice
rosclaw sandbox run --task ur5e_reach_target --record
```

检查：

```bash
ls runs/sandbox/
ls ~/.rosclaw/mcap_records/
```

预期：

```text
episode trace 生成
practice timeline 生成
如果启用 MCAP，MCAP 路径被记录
```

---

## Phase VII：Memory / SeekDB 接入

目标：sandbox failure 能沉淀为 memory。

验收：

```bash
rosclaw start --enable-sandbox --enable-practice --enable-memory
rosclaw sandbox run --task ur5e_pick_cube_bad --record
```

然后查询 memory / SeekDB：

```bash
rosclaw memory search "ur5e collision"
```

预期结果：

```text
找到刚刚的 sandbox failure
包含 task_id
包含 failure_type
包含 replay_id
包含 failure_report 路径
```

---

## Phase VIII：Dashboard 接入

目标：dashboard 能展示 sandbox session。

最低接入：

```text
当前 session
robot_id
task_id
status
reward
collision
replay link
failure report
```

后续增强：

```text
MuJoCo 画面
contact 点
joint state 曲线
trajectory
```

---

# 十四、v1.0 集成验收清单

最终在：

```bash
/home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
```

下面执行。

## 1. 安装验收

```bash
cd /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
pip install -e ".[sandbox]"
python -c "import rosclaw.sandbox; print('ok')"
```

必须通过。

---

## 2. CLI 验收

```bash
rosclaw sandbox doctor
rosclaw sandbox robots list
rosclaw sandbox validate ur5e
```

必须通过。

---

## 3. Runtime 验收

```bash
rosclaw start --enable-sandbox
```

必须出现：

```text
Starting Sandbox Service...
Sandbox engine: mujoco
Runtime Online.
```

---

## 4. Firewall 验收

```bash
rosclaw start --enable-sandbox --enable-firewall
rosclaw firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/bad_table_collision.json
```

必须返回：

```text
BLOCK
[FIREWALL BLOCKED] Collision predicted
```

---

## 5. Task 验收

```bash
rosclaw sandbox run --task ur5e_reach_target --record --headless
```

必须生成：

```text
runs/sandbox/<episode_id>/metadata.json
runs/sandbox/<episode_id>/trajectory.jsonl
runs/sandbox/<episode_id>/events.jsonl
runs/sandbox/<episode_id>/summary.json
```

---

## 6. Replay 验收

```bash
rosclaw sandbox replay runs/sandbox/<episode_id>
```

必须成功。

---

## 7. Event Bus 验收

```bash
rosclaw events tail --filter Sandbox
```

运行 task 时应该看到：

```text
SandboxSessionStarted
SandboxTaskStarted
SandboxStepExecuted
SandboxTaskSucceeded 或 SandboxTaskFailed
```

---

## 8. Practice 验收

```bash
rosclaw start --enable-sandbox --enable-practice
rosclaw sandbox run --task ur5e_reach_target --record
rosclaw practice list
```

必须能看到来自 sandbox 的 practice event。

---

## 9. Memory 验收

```bash
rosclaw start --enable-sandbox --enable-practice --enable-memory
rosclaw sandbox run --task ur5e_pick_cube_bad --record
rosclaw memory search "collision"
```

必须能搜索到失败经验。

---

# 十五、集成后的 v1.0 模块关系

最终应该形成：

```text
rosclaw-runtime
  ├── loads config
  ├── starts event_bus
  ├── starts e_urdf registry
  ├── starts sandbox
  │     ├── mujoco engine
  │     ├── task runtime
  │     ├── firewall
  │     └── replay/trace
  ├── starts agent_runtime
  │     └── action grounding interceptor → sandbox.firewall
  ├── starts practice
  │     └── subscribes sandbox events
  ├── starts memory
  │     └── subscribes praxis events
  └── starts dashboard
        └── subscribes sandbox state/events
```

---

# 十六、向开发者下发的集成任务书

可以直接把下面这段发给 Claude Code / 开发者：

```text
任务：将 rosclaw-sandbox 集成到 ROSClaw v1.0。

目标项目路径：
/home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0

集成要求：
1. 将 sandbox 作为 rosclaw.sandbox Python 子包集成到 src/rosclaw/sandbox。
2. 保留 rosclaw.sandbox.firewall 作为原 rosclaw-firewall 的兼容安全子模块。
3. 在 pyproject.toml 中添加 sandbox 依赖组，包括 mujoco、pydantic、pyyaml、typer、rich。
4. 新增 configs/sandbox.yaml，并在 configs/rosclaw.yaml 中加入 sandbox 配置。
5. 在 rosclaw core Runtime 中注册 SandboxRuntimeAdapter。
6. rosclaw start --enable-sandbox 可以启动 sandbox service。
7. rosclaw start --enable-sandbox --enable-firewall 可以启动 firewall mode。
8. 在 rosclaw CLI 中加入 rosclaw sandbox 和 rosclaw firewall 子命令。
9. sandbox 必须通过 v1.0 的 e_urdf registry 读取 e-URDF-Zoo，而不是自己私有扫描路径。
10. sandbox 必须向 event_bus 发布 SandboxSessionStarted、SandboxTaskSucceeded、SandboxTaskFailed、FirewallActionBlocked 等事件。
11. agent_runtime 必须增加 ActionGroundingInterceptor，在真实动作执行前调用 sandbox.firewall.check。
12. practice 订阅 sandbox 事件，生成 PraxisEvent。
13. memory 后续通过 Practice/Mem pipeline 写入 SeekDB，sandbox 不直接写 SeekDB。
14. dashboard 后续通过事件和 websocket 读取 sandbox 状态。
15. 所有集成必须不破坏现有 rosclaw start、agent_runtime、practice、memory 功能。

最终验收命令：
cd /home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0
pip install -e ".[sandbox]"
python -c "import rosclaw.sandbox; print('ok')"
rosclaw sandbox doctor
rosclaw sandbox validate ur5e
rosclaw sandbox run --task ur5e_reach_target --record --headless
rosclaw sandbox replay runs/sandbox/<episode_id>
rosclaw start --enable-sandbox
rosclaw start --enable-sandbox --enable-firewall
rosclaw firewall check --robot ur5e --world tabletop --action examples/actions/bad_table_collision.json

验收标准：
1. import 成功；
2. CLI 成功；
3. Runtime 能启动 sandbox；
4. firewall 能 block 危险动作；
5. sandbox 能发布事件；
6. practice 能接收 sandbox episode；
7. memory 能通过 practice 管道获得失败经验；
8. 不破坏 v1.0 现有模块。
```

---

# 十七、最终建议

集成时不要把它当成“仿真插件”，而要把它当成 **ROSClaw v1.0 的 Physical Alignment Layer**。

最终命名和职责建议保持：

```text
rosclaw.sandbox
  物理沙箱、任务仿真、回放、评估

rosclaw.sandbox.firewall
  动作安全闸门、碰撞预测、危险熔断

rosclaw-runtime
  生命周期、配置、依赖注入、事件总线

e-URDF-Zoo
  Physical DNA Registry

Practice
  黑匣子记录与 PraxisEvent

Memory / SeekDB
  经验沉淀与查询
```

一句话：

> **`rosclaw-sandbox` 集成进 v1.0 后，不应该只是 MuJoCo wrapper，而应该成为 Agent Runtime 进入物理世界之前的标准安全验证层、任务试验层和失败回放层。**
