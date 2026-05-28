好，先聚焦 **`rosclaw-sandbox` 模块开发 + 交付验收指南**。
我建议这次不要把它做成“附属工具”，而是作为 ROSClaw v1.0 的 **Physical Alignment / Action Grounding 核心模块** 来开发。你的附件里已经明确：ROSClaw 需要从“一堆优秀模块”走向“完整操作系统”，核心是 Runtime、Event Bus、e-URDF-Zoo 和 SeekDB 这几类公共基础设施。

---

# 一、模块最终定位

## 1. 模块名称

正式模块名：

```text
rosclaw-sandbox
```

内部安全子能力：

```text
rosclaw.sandbox.firewall
```

对外宣传能力：

```text
ROSClaw Firewall
```

也就是：

> **Sandbox 是物理试验场，Firewall 是 Sandbox 内部的安全闸门。**

这能兼容之前文档里的 `rosclaw-firewall / mjlab / e-urdf integration` 思路。附件中 Sprint 3 已经把 `rosclaw-firewall`、`mjlab`、`e-urdf integration` 定义为 Physical Alignment 的核心，目标是碰撞预测和危险动作熔断。

---

## 2. 一句话定义

```text
rosclaw-sandbox 是 ROSClaw 的具身物理沙箱模块，负责把 e-URDF-Zoo 中的机器人本体转化为可执行、可验证、可回放、可评估的 MuJoCo 物理试验环境，并为 Agent Runtime 提供执行前安全验证能力。
```

---

## 3. 它解决的核心问题

```text
1. Agent 动作是否物理可行？
2. 机器人模型是否能在仿真中稳定运行？
3. e-URDF-Zoo 中的物理基因是否能被执行？
4. 危险动作能否在真实执行前被拦截？
5. 失败 episode 能否被记录、回放、分析？
6. 后续能否接入 practice / memory / dashboard / darwin？
```

附件里已经强调大模型不应该直接控制所有内部模块，而应该通过 `agent_runtime` 进入 ROSClaw Runtime，再由内部模块完成 grounding。
所以 sandbox 的核心地位是：

```text
Agent Runtime
    ↓
rosclaw-sandbox / firewall
    ↓
真实机器人 / ROS 2 / driver
```

---

# 二、开发目标分层

## MVP 目标

第一版不要追求大而全，只要做到：

```text
1. 能加载一个 e-URDF-Zoo 机器人
2. 能转换 / 加载 MuJoCo 模型
3. 能运行简单 world / task
4. 能 reset / step / render
5. 能进行动作安全检查
6. 能输出 episode trace
7. 能通过 CLI 使用
8. 能通过 Python API 被其他模块调用
```

---

## v1.0 目标

v1.0 阶段需要达到：

```text
1. 支持 MuJoCo backend
2. 支持 RobotProfile / SafetyProfile / CapabilityProfile
3. 支持模型验证报告
4. 支持任务运行时
5. 支持 firewall mode
6. 支持 episode record / replay
7. 支持事件发布
8. 支持 practice / memory / dashboard 后续接入
```

---

# 三、推荐工程目录

建议单独建立仓库或模块：

```text
rosclaw-sandbox/
├── pyproject.toml
├── README.md
├── docs/
│   ├── architecture.md
│   ├── quickstart.md
│   ├── acceptance.md
│   └── integration_notes.md
├── src/
│   └── rosclaw/
│       └── sandbox/
│           ├── __init__.py
│           │
│           ├── core/
│           │   ├── env.py
│           │   ├── session.py
│           │   ├── types.py
│           │   ├── registry.py
│           │   └── errors.py
│           │
│           ├── eurdf/
│           │   ├── loader.py
│           │   ├── profile.py
│           │   ├── safety.py
│           │   ├── capabilities.py
│           │   ├── semantic.py
│           │   └── asset_resolver.py
│           │
│           ├── engines/
│           │   ├── base.py
│           │   └── mujoco/
│           │       ├── engine.py
│           │       ├── model_loader.py
│           │       ├── renderer.py
│           │       ├── contact.py
│           │       ├── camera.py
│           │       ├── actuator.py
│           │       └── urdf_to_mjcf.py
│           │
│           ├── validator/
│           │   ├── model_validator.py
│           │   ├── safety_validator.py
│           │   ├── collision_validator.py
│           │   ├── actuator_validator.py
│           │   └── report.py
│           │
│           ├── worlds/
│           │   ├── schema.py
│           │   ├── builder.py
│           │   ├── primitives.py
│           │   └── assets.py
│           │
│           ├── tasks/
│           │   ├── schema.py
│           │   ├── runtime.py
│           │   ├── observation.py
│           │   ├── action.py
│           │   ├── reward.py
│           │   └── termination.py
│           │
│           ├── firewall/
│           │   ├── policy.py
│           │   ├── simulator.py
│           │   ├── risk.py
│           │   ├── gate.py
│           │   └── decision.py
│           │
│           ├── traces/
│           │   ├── recorder.py
│           │   ├── replay.py
│           │   ├── exporters.py
│           │   ├── jsonl.py
│           │   ├── mcap.py
│           │   └── video.py
│           │
│           ├── events/
│           │   ├── schemas.py
│           │   └── publisher.py
│           │
│           ├── server/
│           │   ├── api.py
│           │   └── websocket.py
│           │
│           └── cli/
│               └── main.py
│
├── configs/
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
├── examples/
│   ├── 01_load_robot.py
│   ├── 02_validate_robot.py
│   ├── 03_run_task.py
│   ├── 04_firewall_check.py
│   └── 05_record_replay.py
│
└── tests/
    ├── test_eurdf_loader.py
    ├── test_mujoco_engine.py
    ├── test_validator.py
    ├── test_task_runtime.py
    ├── test_firewall.py
    └── test_replay.py
```

---

# 四、核心对象设计

## 1. `RobotEmbodimentProfile`

对应 e-URDF-Zoo 的机器人本体描述。

附件里已经把 e-URDF-Zoo 重新定位为 **Physical DNA Registry**，不是普通模型仓库；其中 `safety.yaml` 给 Firewall 使用，`capabilities.yaml` 给 Swarm 使用，`semantic.yaml` 给 Dashboard 使用，`benchmark.yaml` 给 Darwin 使用。

```python
@dataclass
class RobotEmbodimentProfile:
    robot_id: str
    name: str
    urdf_path: str | None
    mjcf_path: str | None
    mesh_dir: str | None

    base_type: Literal["fixed", "floating", "mobile"]
    dof: int

    joints: list[dict]
    links: list[dict]
    sensors: list[dict]
    actuators: list[dict]

    safety: dict
    capabilities: dict
    semantics: dict
    benchmark: dict | None = None
```

---

## 2. `SandboxSession`

```python
@dataclass
class SandboxSession:
    session_id: str
    robot_id: str
    engine: Literal["mujoco"]
    world_id: str
    task_id: str | None
    mode: Literal["simulation", "firewall", "benchmark", "replay"]
    status: Literal["created", "running", "paused", "closed", "failed"]
```

---

## 3. `SandboxEnv`

```python
class SandboxEnv(Protocol):
    def reset(self, seed: int | None = None) -> dict:
        ...

    def step(self, action: dict) -> "StepResult":
        ...

    def render(self, mode: str = "rgb_array"):
        ...

    def get_state(self) -> dict:
        ...

    def set_state(self, state: dict) -> None:
        ...

    def close(self) -> None:
        ...
```

---

## 4. `StepResult`

```python
@dataclass
class StepResult:
    observation: dict
    reward: float
    terminated: bool
    truncated: bool
    info: dict
```

---

## 5. `FirewallDecision`

```python
@dataclass
class FirewallDecision:
    decision: Literal[
        "ALLOW",
        "BLOCK",
        "MODIFY_AND_ALLOW",
        "REQUIRE_HUMAN_CONFIRMATION",
        "DEFER_TO_CONTROLLER",
    ]
    risk_score: float
    reason: str
    predicted_collision: bool
    violated_constraints: list[str]
    simulated_horizon_sec: float
    replay_id: str | None = None
```

---

# 五、CLI 设计

第一版必须有 CLI。没有 CLI，Claude Code 和人类开发者都不好验收。

```bash
# 查看 sandbox 状态
rosclaw-sandbox doctor

# 列出机器人
rosclaw-sandbox robots list

# 加载机器人 profile
rosclaw-sandbox robots profile ur5e

# 验证机器人模型
rosclaw-sandbox validate ur5e

# 转换 URDF 到 MJCF
rosclaw-sandbox convert ur5e --to mjcf

# 运行空场景
rosclaw-sandbox run --robot ur5e --world empty

# 运行任务
rosclaw-sandbox run --task ur5e_reach_target --record

# 执行 firewall 检查
rosclaw-sandbox firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/bad_action.json

# 回放 episode
rosclaw-sandbox replay runs/ep_0001

# 导出记录
rosclaw-sandbox export runs/ep_0001 --format jsonl,mcap,mp4
```

后续集成到主 CLI 时可以再映射为：

```bash
rosclaw sandbox run
rosclaw sandbox validate
rosclaw firewall check
```

---

# 六、开发 Sprint 计划

## Sprint S0：架构冻结与骨架搭建

目标：先把边界、接口、目录、配置固定下来。

开发项：

```text
1. 建立 rosclaw-sandbox 项目结构
2. 创建 pyproject.toml
3. 定义 RobotEmbodimentProfile
4. 定义 SandboxSession
5. 定义 SandboxEnv interface
6. 定义 FirewallDecision
7. 定义 WorldSpec / TaskSpec schema
8. 写 README 和 architecture.md
```

验收：

```bash
python -m rosclaw.sandbox.cli.main --help
pytest tests/test_types.py
```

交付物：

```text
README.md
docs/architecture.md
src/rosclaw/sandbox/core/types.py
src/rosclaw/sandbox/core/session.py
```

---

## Sprint S1：MuJoCo Engine MVP

目标：能跑最小 MuJoCo 仿真。

开发项：

```text
1. MujocoEngine
2. load_mjcf()
3. reset()
4. step()
5. render()
6. get_joint_state()
7. get_contact_state()
8. empty world
```

验收命令：

```bash
rosclaw-sandbox run --robot ur5e --world empty
```

最低验收：

```text
1. 能加载 MJCF
2. 能 reset
3. 能 step 100 次
4. 不崩溃
5. 能输出 joint state
6. 能输出基础 render 图像或 headless 状态
```

---

## Sprint S2：e-URDF-Zoo Bridge

目标：把 e-URDF-Zoo 接进来。

开发项：

```text
1. e-URDF-Zoo path resolver
2. robot manifest loader
3. safety.yaml loader
4. capabilities.yaml loader
5. semantic.yaml loader
6. benchmark.yaml loader
7. asset resolver
8. RobotEmbodimentProfile 生成器
```

建议 e-URDF-Zoo 单机器人结构：

```text
e-urdf-zoo/
└── ur5e/
    ├── robot.urdf
    ├── robot.mjcf.xml
    ├── safety.yaml
    ├── semantic.yaml
    ├── capabilities.yaml
    ├── benchmark.yaml
    └── assets/
        └── meshes/
```

验收命令：

```bash
rosclaw-sandbox robots profile ur5e
rosclaw-sandbox validate ur5e
```

最低验收：

```text
1. 能找到 robot.urdf / robot.mjcf.xml
2. 能解析 safety.yaml
3. 能解析 capabilities.yaml
4. mesh 路径能被解析
5. 输出 RobotEmbodimentProfile JSON
```

---

## Sprint S3：Model Validator

目标：模型不是能加载就行，还要知道是否可靠。

开发项：

```text
1. mesh path validation
2. joint limit validation
3. inertial validation
4. actuator validation
5. collision geometry validation
6. safety profile validation
7. validation report generator
```

验收命令：

```bash
rosclaw-sandbox validate ur5e --report reports/ur5e_validation.md
```

报告示例：

```text
Robot: ur5e
Status: PASS_WITH_WARNINGS

[PASS] robot model found
[PASS] mesh paths resolved
[PASS] joint tree valid
[PASS] safety limits loaded
[WARN] missing actuator profile for wrist_3_joint
[WARN] collision mesh is high-poly
[PASS] MuJoCo compile success
```

最低验收：

```text
1. 缺文件能报明确错误
2. mesh path 错误能定位
3. joint limit 缺失能 warning
4. MuJoCo 编译失败能给出原因
5. 报告可保存为 markdown/json
```

---

## Sprint S4：World / Task Runtime

目标：从“仿真引擎”升级为“任务运行时”。

开发项：

```text
1. WorldSpec schema
2. TaskSpec schema
3. WorldBuilder
4. ObservationManager
5. ActionAdapter
6. RewardManager
7. TerminationManager
8. TaskRuntime
```

第一批 world：

```text
empty
flat_ground
tabletop
```

第一批 task：

```text
ur5e_reach_target
ur5e_pick_cube
go2_stand
go2_walk_forward
```

任务配置示例：

```yaml
task_id: ur5e_reach_target
robot_id: ur5e
world_id: tabletop

action:
  type: joint_position
  hz: 20

observation:
  - joint_position
  - joint_velocity
  - end_effector_pose
  - contact

goal:
  type: reach_pose
  target_link: tool0
  target_pose: [0.4, 0.2, 0.3, 0, 3.14, 0]

termination:
  max_steps: 500
  success_distance: 0.03
  collision_fail: true
```

验收命令：

```bash
rosclaw-sandbox run --task ur5e_reach_target --record
```

最低验收：

```text
1. 能加载 task yaml
2. 能创建 world
3. 能 reset task
4. 能 step action
5. 能判断 success / failure / timeout
6. 能输出 reward 和 info
```

---

## Sprint S5：Firewall Mode

目标：支持执行前动作验证。

附件二明确提出：`agent_runtime` 接收到移动指令后，应插入 `await firewall.simulate_trajectory()`，错误动作要输出 `[FIREWALL BLOCKED] Collision predicted` 并返回给大模型。

开发项：

```text
1. ActionRequest schema
2. simulate_trajectory()
3. constraint_checker()
4. collision_checker()
5. workspace_checker()
6. joint_limit_checker()
7. risk_score()
8. allow_or_block()
```

动作请求示例：

```json
{
  "robot_id": "ur5e",
  "world_id": "tabletop",
  "action_type": "target_pose",
  "target_link": "tool0",
  "target_pose": [0.5, 0.0, 0.05, 0, 3.14, 0],
  "horizon_sec": 2.0
}
```

Firewall 返回示例：

```json
{
  "decision": "BLOCK",
  "risk_score": 0.93,
  "reason": "Predicted collision between wrist_link and table",
  "predicted_collision": true,
  "violated_constraints": ["workspace_boundary", "collision"],
  "simulated_horizon_sec": 2.0,
  "replay_id": "firewall_ep_00042"
}
```

验收命令：

```bash
rosclaw-sandbox firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/bad_table_collision.json
```

最低验收：

```text
1. 安全动作返回 ALLOW
2. 明显碰撞动作返回 BLOCK
3. 超出关节限制返回 BLOCK
4. 超出工作空间返回 BLOCK
5. 输出 risk_score
6. 生成 replay_id
7. 日志中出现清晰 block reason
```

---

## Sprint S6：Trace / Replay / Export

目标：每次仿真都能成为可复现物理经验。

开发项：

```text
1. EpisodeRecorder
2. JSONL trajectory exporter
3. event exporter
4. contact exporter
5. metadata exporter
6. ReplayEngine
7. MCAP exporter placeholder
8. video exporter placeholder
```

每次运行输出：

```text
runs/
└── ep_0001/
    ├── metadata.json
    ├── task.yaml
    ├── robot_profile.json
    ├── trajectory.jsonl
    ├── contacts.jsonl
    ├── events.jsonl
    ├── summary.json
    └── failure_report.md
```

验收命令：

```bash
rosclaw-sandbox run --task ur5e_reach_target --record
rosclaw-sandbox replay runs/ep_0001
```

最低验收：

```text
1. episode 目录完整生成
2. trajectory.jsonl 不为空
3. summary.json 包含 success/failure/reward/steps
4. replay 能复现状态序列
5. failure_report.md 能说明失败原因
```

---

## Sprint S7：事件接口预留

目标：不强行集成 v1.0，但要为 v1.0 集成预留标准事件。

附件一强调，ROSClaw 未来应该通过 Event Bus 解耦，模块之间不应互相硬调用，而应该 publish / subscribe。

开发项：

```text
1. SandboxEvent base schema
2. SandboxSessionStarted
3. SandboxStepExecuted
4. SandboxCollisionDetected
5. SandboxTaskSucceeded
6. SandboxTaskFailed
7. FirewallActionAllowed
8. FirewallActionBlocked
9. SandboxReplayCreated
10. EventPublisher interface
```

事件示例：

```json
{
  "event_type": "FirewallActionBlocked",
  "timestamp": "2026-05-28T10:00:00Z",
  "session_id": "sandbox_abc",
  "robot_id": "ur5e",
  "task_id": "ur5e_pick_cube",
  "risk_score": 0.93,
  "reason": "Predicted collision between wrist_link and table",
  "replay_id": "firewall_ep_00042"
}
```

最低验收：

```text
1. 每个事件可序列化为 JSON
2. 每个事件有 timestamp / session_id / robot_id
3. EventPublisher 可替换为 NullPublisher / RuntimePublisher
4. 不依赖 ROSClaw v1.0 主工程也能单独运行
```

---

# 七、交付验收指南

下面是建议交给开发者 / Claude Code 的正式验收标准。

---

## 1. 交付物清单

必须交付：

```text
1. rosclaw-sandbox 源码
2. README.md
3. docs/architecture.md
4. docs/quickstart.md
5. docs/acceptance.md
6. pyproject.toml
7. CLI 工具
8. Python API
9. 单元测试
10. 集成测试
11. 示例机器人配置
12. 示例 world 配置
13. 示例 task 配置
14. 示例 action JSON
15. validation report 示例
16. episode replay 示例
```

---

## 2. 基础安装验收

命令：

```bash
cd rosclaw-sandbox
pip install -e ".[dev,mujoco]"
pytest
```

通过标准：

```text
1. 安装无错误
2. pytest 通过
3. CLI 可用
4. import rosclaw.sandbox 成功
```

命令：

```bash
python -c "import rosclaw.sandbox; print(rosclaw.sandbox.__version__)"
```

必须输出版本号。

---

## 3. CLI 验收

命令：

```bash
rosclaw-sandbox --help
rosclaw-sandbox doctor
```

通过标准：

```text
1. help 信息完整
2. doctor 输出 Python 版本
3. doctor 输出 MuJoCo 是否可用
4. doctor 输出 e-URDF-Zoo 路径是否存在
5. doctor 输出 runs 目录是否可写
```

---

## 4. e-URDF-Zoo 解析验收

命令：

```bash
rosclaw-sandbox robots list
rosclaw-sandbox robots profile ur5e --format json
```

通过标准：

```text
1. 能列出至少 1 个机器人
2. profile 中包含 robot_id
3. profile 中包含 dof
4. profile 中包含 joints
5. profile 中包含 safety
6. profile 中包含 capabilities
7. profile 可以导出 JSON
```

---

## 5. 模型验证验收

命令：

```bash
rosclaw-sandbox validate ur5e --report reports/ur5e_validation.md
```

通过标准：

```text
1. 生成 markdown 报告
2. 生成 json 报告
3. 报告包含 PASS / WARN / FAIL
4. mesh 缺失时能 FAIL
5. safety.yaml 缺失时能 WARN 或 FAIL，按配置决定
6. MuJoCo compile 失败时给出明确错误
```

---

## 6. MuJoCo Engine 验收

命令：

```bash
rosclaw-sandbox run --robot ur5e --world empty --steps 100 --headless
```

通过标准：

```text
1. 成功创建 MuJoCo model
2. 成功创建 MuJoCo data
3. reset 成功
4. step 100 次成功
5. joint state 可读取
6. contact state 可读取
7. 程序正常退出
```

---

## 7. Task Runtime 验收

命令：

```bash
rosclaw-sandbox run --task ur5e_reach_target --headless --record
```

通过标准：

```text
1. 成功加载 task yaml
2. 成功加载 world yaml
3. 成功加载 robot profile
4. 运行至少 1 个 episode
5. 输出 reward
6. 输出 terminated / truncated
7. 输出 summary.json
```

---

## 8. Firewall 验收

准备两个动作：

```text
examples/actions/safe_reach.json
examples/actions/bad_table_collision.json
```

命令：

```bash
rosclaw-sandbox firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/safe_reach.json
```

必须返回：

```text
ALLOW
```

命令：

```bash
rosclaw-sandbox firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/bad_table_collision.json
```

必须返回：

```text
BLOCK
```

并且输出类似：

```text
[FIREWALL BLOCKED] Collision predicted
```

这与现有 v1.0 见解中的 Action Grounding 验收标准保持一致。

---

## 9. Replay 验收

命令：

```bash
rosclaw-sandbox replay runs/ep_0001
```

通过标准：

```text
1. 能读取 metadata.json
2. 能读取 trajectory.jsonl
3. 能逐步恢复状态
4. replay 不依赖原始实时执行
5. replay 完成后输出 replay summary
```

---

## 10. Trace 文件验收

每次 `--record` 后必须生成：

```text
metadata.json
task.yaml
robot_profile.json
trajectory.jsonl
events.jsonl
summary.json
```

如果失败，额外生成：

```text
failure_report.md
```

通过标准：

```text
1. trajectory.jsonl 每一行是合法 JSON
2. events.jsonl 每一行是合法 JSON
3. summary.json 包含 success 字段
4. summary.json 包含 total_steps 字段
5. summary.json 包含 total_reward 字段
6. failure_report.md 包含 failure_type / reason / replay_id
```

---

## 11. Python API 验收

示例代码必须能运行：

```python
from rosclaw.sandbox import Sandbox

sandbox = Sandbox.create(
    robot_id="ur5e",
    world_id="empty",
    engine="mujoco",
)

obs = sandbox.reset()

for _ in range(100):
    action = {"type": "noop"}
    result = sandbox.step(action)

sandbox.close()
```

通过标准：

```text
1. import 成功
2. create 成功
3. reset 返回 dict
4. step 返回 StepResult
5. close 成功
```

---

## 12. 事件接口验收

命令：

```bash
rosclaw-sandbox run --task ur5e_reach_target --record --events-json runs/events.jsonl
```

通过标准：

```text
1. events.jsonl 存在
2. 至少包含 SandboxSessionStarted
3. 至少包含 SandboxStepExecuted
4. episode 结束时包含 SandboxTaskSucceeded 或 SandboxTaskFailed
5. firewall block 时包含 FirewallActionBlocked
```

---

# 八、质量门禁

## P0 必须通过

```text
1. 安装成功
2. CLI 成功
3. MuJoCo engine 成功
4. e-URDF profile 成功
5. validate 成功
6. task run 成功
7. firewall allow/block 成功
8. record/replay 成功
9. pytest 通过
```

---

## P1 建议通过

```text
1. MCAP exporter 初版
2. video exporter 初版
3. websocket stream 初版
4. HTTP API 初版
5. dashboard mock 接入
6. practice event mock 接入
```

---

## P2 后续再做

```text
1. Isaac Sim backend
2. Gazebo backend
3. 多机器人 sandbox
4. 大规模 benchmark runner
5. domain randomization
6. sim-to-real calibration
7. 自然语言生成 world
```

---

# 九、开发者任务分配建议

可以给 Claude Code 拆成 5 个并行任务。

## Developer A：core + CLI

```text
负责：
core/types.py
core/session.py
cli/main.py
README.md
doctor command
```

验收：

```bash
rosclaw-sandbox --help
rosclaw-sandbox doctor
```

---

## Developer B：e-URDF Bridge + Validator

```text
负责：
eurdf/*
validator/*
robots profile
validate command
```

验收：

```bash
rosclaw-sandbox robots profile ur5e
rosclaw-sandbox validate ur5e
```

---

## Developer C：MuJoCo Engine

```text
负责：
engines/base.py
engines/mujoco/*
empty world
basic render
```

验收：

```bash
rosclaw-sandbox run --robot ur5e --world empty --steps 100
```

---

## Developer D：Task Runtime

```text
负责：
worlds/*
tasks/*
configs/worlds/*
configs/tasks/*
```

验收：

```bash
rosclaw-sandbox run --task ur5e_reach_target --record
```

---

## Developer E：Firewall + Trace

```text
负责：
firewall/*
traces/*
events/*
```

验收：

```bash
rosclaw-sandbox firewall check --robot ur5e --action bad_action.json
rosclaw-sandbox replay runs/ep_0001
```

---

# 十、最终交付标准

`rosclaw-sandbox` 可以宣布完成 Alpha 交付，当且仅当以下命令全部通过：

```bash
# 1. 环境检查
rosclaw-sandbox doctor

# 2. 机器人 profile
rosclaw-sandbox robots profile ur5e --format json

# 3. 模型验证
rosclaw-sandbox validate ur5e --report reports/ur5e_validation.md

# 4. MuJoCo 空场景运行
rosclaw-sandbox run --robot ur5e --world empty --steps 100 --headless

# 5. 任务运行
rosclaw-sandbox run --task ur5e_reach_target --record --headless

# 6. Firewall 安全动作
rosclaw-sandbox firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/safe_reach.json

# 7. Firewall 危险动作
rosclaw-sandbox firewall check \
  --robot ur5e \
  --world tabletop \
  --action examples/actions/bad_table_collision.json

# 8. 回放
rosclaw-sandbox replay runs/ep_0001

# 9. 测试
pytest
```

---

# 十一、我建议写进任务书的最终版本

可以直接发给开发者：

```text
目标：开发 rosclaw-sandbox Alpha。

rosclaw-sandbox 是 ROSClaw 的具身物理沙箱模块，用于将 e-URDF-Zoo 中的机器人本体加载到 MuJoCo 中，提供模型验证、任务运行、动作安全检查、episode 记录和 replay 能力。

模块必须支持：
1. e-URDF-Zoo robot profile 加载；
2. MuJoCo backend；
3. robot validation report；
4. world/task runtime；
5. firewall allow/block；
6. episode record/replay；
7. CLI；
8. Python API；
9. 标准事件 schema。

第一阶段不要求真实机器人控制，不要求 Isaac Sim，不要求完整 dashboard，不要求 SeekDB 写入，但必须为 ROSClaw Runtime / Practice / Memory / Dashboard 后续集成保留事件接口。

最终验收以 docs/acceptance.md 中的命令全部通过为准。
```

---

核心结论：

> **先把 `rosclaw-sandbox` 做成一个独立可运行、可验证、可回放、可拦截危险动作的 MuJoCo 沙箱。不要一开始就和 v1.0 主工程强耦合，但所有接口必须按 Runtime + Event Bus + e-URDF-Zoo 的方向预留。**

这样开发风险最低，后续并入 ROSClaw v1.0 也最顺。
