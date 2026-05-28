你说得对：**不是没考虑到，而是之前把这个模块命名成了 `rosclaw-firewall`，现在的问题是要不要继续叫 firewall，还是改成 sandbox。**

我的判断很明确：

> **对内工程模块建议叫 `rosclaw-sandbox`，对外安全能力叫 `ROSClaw Firewall`。**

也就是：

```text
仓库 / 模块名：rosclaw-sandbox
核心能力之一：firewall / safety gate
产品叙事：ROSClaw Sandbox with Physical Firewall
```

这样最稳。

---

# 一、为什么不建议只叫 rosclaw-firewall

你附件里之前的架构把它叫 `firewall` 是有原因的：它处在 `agent_runtime` 和真实机器人执行之间，负责结合 e-URDF 的物理边界，在 MuJoCo 中推演动作并拦截危险指令。这个定位非常清楚：大模型下发意图后，`firewall` 先仿真、预测碰撞，安全才放行。

但是问题在于，**firewall 这个名字太窄**。

它强调的是：

```text
危险动作拦截
碰撞预测
安全熔断
执行前验证
```

但你现在真正需要开发的模块不只是拦截器，而是一个完整的物理试验场：

```text
机器人模型加载
e-URDF-Zoo 接入
URDF / MJCF 转换
MuJoCo 仿真
任务构造
episode 录制
失败复现
策略评估
provider 验证
dashboard 可视化
practice 数据沉淀
memory 经验归因
darwin benchmark 评测
```

这些远远超过 firewall。

所以如果仓库名叫 `rosclaw-firewall`，后面一定会尴尬：你会不断往 firewall 里塞 sandbox、benchmark、replay、task runtime，最后名字和职责不匹配。

---

# 二、为什么建议叫 rosclaw-sandbox

`sandbox` 更像一个**物理世界的 staging environment**。

软件工程里有：

```text
dev
test
staging
production
```

Physical AI 里应该有：

```text
simulation sandbox
shadow execution
real robot execution
```

`rosclaw-sandbox` 的职责是：

> **在真实物理世界之前，为 agent、skill、provider、memory、practice 提供一个可执行、可回放、可评估、可失败的物理世界副本。**

而 `firewall` 应该是 sandbox 的一个运行模式：

```text
rosclaw-sandbox run --mode eval
rosclaw-sandbox run --mode replay
rosclaw-sandbox run --mode firewall
rosclaw-sandbox run --mode benchmark
```

更准确地说：

```text
rosclaw-sandbox = 物理试验场
rosclaw-firewall = 物理试验场里的安全闸门
```

---

# 三、推荐命名方案

## 最佳方案

```text
Repository:
rosclaw-sandbox

Python package:
rosclaw.sandbox

内部子模块：
rosclaw.sandbox.engines.mujoco
rosclaw.sandbox.firewall
rosclaw.sandbox.tasks
rosclaw.sandbox.replay
rosclaw.sandbox.validators
rosclaw.sandbox.recorders
```

## 对外宣传名

```text
ROSClaw Sandbox
The physical simulation and safety validation layer for ROSClaw.
```

## 安全能力名

```text
ROSClaw Firewall
The action-grounding safety gate powered by ROSClaw Sandbox.
```

## CLI

```bash
rosclaw sandbox run
rosclaw sandbox validate
rosclaw sandbox replay
rosclaw firewall check
rosclaw firewall serve
```

这样你同时保留了 `firewall` 这个很有冲击力的概念，也避免把整个模块命名限制死。

---

# 四、它在 ROSClaw v1.0 中的位置

附件一的判断很关键：ROSClaw 现在的问题不是没有好模块，而是还没有形成一个完整操作系统；真正的核心是 `rosclaw-runtime`，所有模块都应该挂到 Runtime，由 Runtime 统一管理生命周期、配置、插件、日志和事件。

所以 `rosclaw-sandbox` 不应该是孤立模块，而应该挂在 Runtime 下：

```text
rosclaw-runtime
  ├── agent_runtime
  ├── sandbox
  │   ├── firewall
  │   ├── mujoco_engine
  │   ├── task_runtime
  │   ├── replay
  │   └── validator
  ├── practice
  ├── memory
  ├── swarm
  ├── how
  ├── darwin
  └── event_bus
```

你之前的架构强调 Event Bus，要求模块之间不要互相乱调，而是通过 publish / subscribe 解耦。这个原则必须保留。

因此，sandbox 应该发布事件：

```text
SandboxEpisodeStarted
SandboxStepExecuted
SandboxCollisionDetected
SandboxActionBlocked
SandboxEpisodeSucceeded
SandboxEpisodeFailed
SandboxReplayCreated
SandboxValidationReportGenerated
```

然后：

```text
practice 订阅 episode / trajectory
memory 订阅 failure / success / reason
dashboard 订阅 state / video / contact / reward
darwin 订阅 benchmark result
how 订阅 failure event 后生成恢复建议
```

---

# 五、rosclaw-sandbox 的正式定义

我建议你在 README 里这样定义：

```markdown
# ROSClaw Sandbox

ROSClaw Sandbox is the embodied simulation, validation, replay, and safety-gating layer of ROSClaw.

It turns e-URDF robot embodiments into executable physical worlds, allowing agents, skills, providers, and policies to be tested before entering the real world.

Its first backend is MuJoCo, with future support for Isaac Sim, Gazebo, and real-robot shadow execution.

ROSClaw Firewall is implemented as a safety mode inside ROSClaw Sandbox.
```

中文定义：

> **ROSClaw Sandbox 是 ROSClaw 的具身物理沙箱，负责把 e-URDF-Zoo 中的机器人本体转化为可执行、可验证、可回放、可评估的物理试验环境。ROSClaw Firewall 是其中的安全闸门模式，用于在真实执行前进行动作预测、碰撞检测和危险动作熔断。**

---

# 六、总体架构

```text
                          ┌──────────────────────────┐
                          │      Agent Runtime        │
                          │ Claude / Qwen / OpenClaw  │
                          └─────────────┬────────────┘
                                        │
                                        │ Goal / Skill / Action Request
                                        ▼
┌────────────────────────────────────────────────────────────────────┐
│                         rosclaw-sandbox                            │
│                                                                    │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────────┐ │
│  │ e-URDF Bridge     │   │ Model Validator  │   │ MuJoCo Engine   │ │
│  │ Physical DNA      │──▶│ safety / limits  │──▶│ simulation      │ │
│  │ robot profile     │   │ collision check  │   │ contact / obs   │ │
│  └──────────────────┘   └──────────────────┘   └────────────────┘ │
│             │                       │                       │       │
│             ▼                       ▼                       ▼       │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────────┐ │
│  │ World Builder     │   │ Task Runtime     │   │ Firewall Mode   │ │
│  │ scene / object    │──▶│ reset / step     │──▶│ simulate first  │ │
│  │ terrain / camera  │   │ reward / done    │   │ allow / block   │ │
│  └──────────────────┘   └──────────────────┘   └────────────────┘ │
│             │                       │                       │       │
│             └───────────────────────┼───────────────────────┘       │
│                                     ▼                               │
│                      ┌────────────────────────┐                    │
│                      │ Trace / Replay / Report │                    │
│                      │ MCAP / JSONL / video    │                    │
│                      │ failure report          │                    │
│                      └────────────────────────┘                    │
└────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
   rosclaw-practice      rosclaw-memory      rosclaw-dashboard
   episode capture       failure memory      visualization
```

---

# 七、和 e-URDF-Zoo 的关系

附件里已经把 e-URDF-Zoo 提升为 **Physical DNA Registry**，而不是普通机器人模型仓库，并建议每个机器人包含 `robot.urdf`、`robot.xml`、`safety.yaml`、`semantic.yaml`、`capabilities.yaml`、`benchmark.yaml` 等文件。

这个判断非常对。

我建议最终结构如下：

```text
e-urdf-zoo/
  unitree_go2/
    robot.urdf
    robot.mjcf.xml
    robot.eurdf.yaml
    safety.yaml
    semantic.yaml
    capabilities.yaml
    benchmark.yaml
    assets/
      meshes/
      textures/
```

其中：

```text
robot.urdf              给 ROS / 传统工具链使用
robot.mjcf.xml          给 MuJoCo 使用
robot.eurdf.yaml        ROSClaw 的本体扩展语义
safety.yaml             sandbox/firewall 使用
semantic.yaml           dashboard/how/memory 使用
capabilities.yaml       swarm/skill/runtime 使用
benchmark.yaml          darwin/sandbox 使用
```

`rosclaw-sandbox` 读取 e-URDF-Zoo 后生成：

```python
RobotEmbodimentProfile
RobotSafetyProfile
RobotCapabilityProfile
RobotSimulationProfile
```

---

# 八、核心工程目录

建议在 v1.0 中这样组织：

```text
rosclaw-sandbox/
  pyproject.toml
  README.md

  src/rosclaw/sandbox/
    __init__.py

    core/
      env.py
      types.py
      session.py
      registry.py
      errors.py

    eurdf/
      loader.py
      profile.py
      asset_resolver.py
      safety_loader.py
      capability_loader.py
      semantic_loader.py

    engines/
      base.py
      mujoco/
        engine.py
        model_loader.py
        urdf_to_mjcf.py
        renderer.py
        contact.py
        camera.py
        actuator.py

    validator/
      model_validator.py
      safety_validator.py
      collision_validator.py
      actuator_validator.py
      report.py

    worlds/
      schema.py
      builder.py
      primitives.py
      assets.py

    tasks/
      schema.py
      runtime.py
      observation.py
      action.py
      reward.py
      termination.py

    firewall/
      policy.py
      simulator.py
      risk.py
      gate.py
      decision.py

    traces/
      recorder.py
      replay.py
      exporters.py
      mcap.py
      video.py

    events/
      schemas.py
      publisher.py

    server/
      api.py
      websocket.py

    cli/
      main.py

  configs/
    worlds/
      empty.yaml
      flat_ground.yaml
      tabletop.yaml
    tasks/
      go2_stand.yaml
      go2_walk_forward.yaml
      ur5e_reach.yaml
      ur5e_pick_cube.yaml

  examples/
    01_load_robot.py
    02_validate_robot.py
    03_run_mujoco.py
    04_firewall_check.py
    05_record_replay.py
```

---

# 九、核心对象模型

## 1. `SandboxSession`

```python
@dataclass
class SandboxSession:
    session_id: str
    robot_id: str
    engine: str
    world_id: str
    task_id: str | None
    mode: Literal["simulation", "firewall", "benchmark", "replay"]
    status: Literal["created", "running", "paused", "closed", "failed"]
```

## 2. `RobotEmbodimentProfile`

```python
@dataclass
class RobotEmbodimentProfile:
    robot_id: str
    urdf_path: str
    mjcf_path: str | None
    mesh_dir: str
    dof: int
    base_type: Literal["fixed", "floating", "mobile"]
    joints: list[JointProfile]
    links: list[LinkProfile]
    sensors: list[SensorProfile]
    actuators: list[ActuatorProfile]
    capabilities: dict
    safety: dict
    semantics: dict
```

## 3. `FirewallDecision`

```python
@dataclass
class FirewallDecision:
    allowed: bool
    risk_score: float
    reason: str
    predicted_collision: bool
    violated_constraints: list[str]
    simulated_horizon_sec: float
    replay_id: str | None
```

---

# 十、CLI 设计

你要让 Claude Code、开发者、CI 都能直接用。

```bash
# 查看机器人
rosclaw sandbox robots list

# 从 e-URDF-Zoo 安装机器人
rosclaw sandbox robots install unitree_go2

# 验证机器人模型
rosclaw sandbox validate unitree_go2

# 转换 URDF 到 MJCF
rosclaw sandbox convert unitree_go2 --to mjcf

# 跑 MuJoCo 仿真
rosclaw sandbox run \
  --robot unitree_go2 \
  --world flat_ground \
  --task go2_walk_forward

# 运行 firewall 检查
rosclaw firewall check \
  --robot ur5e \
  --world tabletop \
  --action action.json

# 作为 agent runtime 的安全服务启动
rosclaw firewall serve --port 8766

# 回放一次失败
rosclaw sandbox replay runs/2026-05-28/ep_0001

# 导出 MCAP / JSONL / 视频
rosclaw sandbox export runs/ep_0001 --format mcap,jsonl,mp4
```

---

# 十一、API 设计

## HTTP API

```text
POST /v1/sandbox/sessions
POST /v1/sandbox/{session_id}/reset
POST /v1/sandbox/{session_id}/step
GET  /v1/sandbox/{session_id}/state
GET  /v1/sandbox/{session_id}/render
POST /v1/sandbox/{session_id}/close

POST /v1/firewall/check
POST /v1/firewall/simulate_trajectory
POST /v1/firewall/allow_or_block

GET  /v1/robots/{robot_id}/profile
GET  /v1/robots/{robot_id}/validation_report
```

## WebSocket

```text
/ws/sandbox/{session_id}
  state
  joint_state
  contact
  image
  reward
  event
  failure
```

---

# 十二、MuJoCo MVP 开发路线

## Phase 1：MuJoCo Engine

目标：先跑起来，不追求复杂任务。

产出：

```text
MujocoEngine
load_mjcf()
load_urdf()
reset()
step()
render()
get_joint_state()
get_contact_state()
```

验收：

```bash
rosclaw sandbox run --robot ur5e --world empty
```

可以加载模型、渲染、step。

---

## Phase 2：e-URDF Bridge

目标：和 e-URDF-Zoo 真正连接。

产出：

```text
RobotEmbodimentProfile
RobotSafetyProfile
RobotCapabilityProfile
AssetResolver
ManifestLoader
```

验收：

```bash
rosclaw sandbox validate unitree_go2
```

输出：

```text
PASS mesh path resolved
PASS joint tree valid
WARN missing actuator profile
WARN collision mesh too complex
PASS safety limits loaded
```

---

## Phase 3：Task Runtime

目标：从“能仿真”变成“能测试任务”。

产出：

```text
TaskSpec
WorldSpec
ObservationSpec
ActionSpec
RewardSpec
TerminationSpec
```

示例任务：

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

---

## Phase 4：Firewall Mode

目标：从任务仿真升级为动作安全闸门。

调用链：

```text
Agent Runtime
  ↓
ActionRequest
  ↓
Sandbox Firewall
  ↓
simulate horizon
  ↓
risk analysis
  ↓
allow / block / modify / require_human_confirm
```

决策类型：

```text
ALLOW
BLOCK
MODIFY_AND_ALLOW
REQUIRE_HUMAN_CONFIRMATION
DEFER_TO_LOWER_LEVEL_CONTROLLER
```

示例返回：

```json
{
  "decision": "BLOCK",
  "risk_score": 0.92,
  "reason": "Predicted collision between wrist_link and table",
  "violated_constraints": ["self_collision", "workspace_boundary"],
  "simulated_horizon_sec": 2.0,
  "replay_id": "ep_firewall_00042"
}
```

这就和你附件里提到的 `[FIREWALL BLOCKED] Collision predicted` 验收标准一致。

---

## Phase 5：Trace / Replay / Practice

目标：所有仿真和拦截都能沉淀为经验。

每次运行生成：

```text
runs/
  ep_00042/
    metadata.json
    task.yaml
    robot_profile.yaml
    trajectory.jsonl
    contacts.jsonl
    events.jsonl
    video.mp4
    episode.mcap
    failure_report.md
```

发布事件：

```python
publish(SandboxEpisodeFinished(...))
publish(SandboxFailureDetected(...))
publish(FirewallActionBlocked(...))
```

Practice 订阅后生成 `PraxisEvent`。附件二里已经明确了 Practice 负责 MCAP 黑匣子截流，Memory 负责将事件写入 SeekDB。

---

# 十三、和 ROSClaw 各模块的连接

## 1. Agent Runtime

Agent Runtime 不直接控制真实机器人，而是先请求 sandbox/firewall：

```text
AgentRuntime.submit_action()
  ↓
SandboxFirewall.check()
  ↓
ALLOW → driver / ROS 2
BLOCK → return reason to agent
```

附件二中也强调，大模型只和 `agent_runtime` 交互，内部由 `agent_runtime` 把意图交给 firewall 推演。

---

## 2. Practice

Practice 不应该主动调用 sandbox 内部细节，只订阅事件：

```text
SandboxEpisodeFinished
FirewallActionBlocked
SandboxTaskFailed
```

然后生成：

```text
PraxisEvent
PracticeTimeline
MCAP index
```

---

## 3. Memory

Memory 存的不是普通日志，而是“可复现的物理经验”：

```yaml
memory_type: embodied_failure
robot_id: ur5e
task_id: pick_cube
failure_type: collision
sandbox_replay_id: ep_00042
cause:
  - wrist_link collided with table
  - target pose too low
recommendation:
  - raise approach z by 8 cm
  - use side approach
```

---

## 4. Dashboard

Dashboard 显示：

```text
机器人模型
世界场景
仿真画面
轨迹
关节状态
接触点
reward 曲线
失败报告
firewall allow/block 决策
```

---

## 5. Darwin

Darwin 用 sandbox 做 benchmark：

```text
same robot
same world
same task
different agent / skill / provider
```

输出：

```text
success rate
collision rate
completion time
energy cost
recovery rate
generalization score
```

---

# 十四、Sprint 实施方案

## Sprint 0：架构冻结

产出：

```text
RFC-000X ROSClaw Sandbox Architecture
RFC-000X e-URDF-Zoo Integration
RFC-000X Firewall Decision Protocol
RFC-000X Sandbox Event Schema
```

冻结以下接口：

```text
RobotEmbodimentProfile
SandboxSession
TaskSpec
WorldSpec
FirewallDecision
SandboxEvent
```

验收：

```text
Runtime / Agent Runtime / Practice / Memory / Dashboard 都知道如何接 sandbox
```

---

## Sprint 1：MuJoCo 最小后端

开发：

```text
MujocoEngine
MJCF loader
URDF loader
reset / step / render
joint state
contact state
```

验收：

```bash
rosclaw sandbox run --robot ur5e --world empty
```

---

## Sprint 2：e-URDF-Zoo Bridge

开发：

```text
e-URDF loader
RobotEmbodimentProfile
safety.yaml loader
capabilities.yaml loader
semantic.yaml loader
asset resolver
validation report
```

验收：

```bash
rosclaw sandbox validate unitree_go2
rosclaw sandbox profile unitree_go2
```

---

## Sprint 3：Task Runtime

开发：

```text
WorldSpec
TaskSpec
Observation manager
Action adapter
Reward manager
Termination manager
```

首批任务：

```text
ur5e_reach_target
ur5e_pick_cube
go2_stand
go2_walk_forward
```

验收：

```bash
rosclaw sandbox run --task ur5e_reach_target --record
```

---

## Sprint 4：Firewall Mode

开发：

```text
simulate_trajectory()
risk_score()
constraint_checker()
allow_or_block()
firewall server
```

验收：

```bash
rosclaw firewall check --robot ur5e --action bad_action.json
```

输出：

```text
[FIREWALL BLOCKED] Collision predicted
```

---

## Sprint 5：Trace / Replay / Event Bus

开发：

```text
trajectory recorder
event recorder
video recorder
MCAP exporter
replay engine
event bus publisher
```

验收：

```bash
rosclaw sandbox replay runs/ep_0001
```

Practice 能收到：

```text
SandboxEpisodeFinished
FirewallActionBlocked
```

---

## Sprint 6：Runtime 集成

开发：

```text
rosclaw start --enable-sandbox
rosclaw start --enable-firewall
dependency injection
config management
health check
```

验收：

```bash
rosclaw start
```

输出：

```text
Loading e-URDF-Zoo...
Starting Agent Runtime...
Starting Sandbox...
Starting Firewall...
Connecting Event Bus...
Connecting SeekDB...
ROSClaw Runtime Online.
```

这和附件里 `rosclaw start` 拉起核心组件、连接 e-URDF、Firewall、SeekDB、Agent Runtime 的方向一致。

---

# 十五、P0 / P1 / P2 优先级

## P0：必须做

```text
rosclaw-sandbox 仓库/包结构
MuJoCo backend
e-URDF-Zoo loader
RobotEmbodimentProfile
Model validation
Task runtime
FirewallDecision
CLI
```

## P1：v1.0 应该做

```text
episode record/replay
event bus integration
practice integration
memory failure event
dashboard websocket stream
MCAP export
```

## P2：v1.1 再做

```text
Isaac Sim backend
Gazebo backend
multi-agent sandbox
natural language scene generation
large-scale benchmark runner
sim-to-real calibration
domain randomization
```

---

# 十六、最终建议

你现在不要把它作为一个“新模块随便补上”，而应该把它提升为 ROSClaw v1.0 的核心执行层之一。

我建议最终命名与定位如下：

```text
rosclaw-sandbox
  ROSClaw 的具身物理沙箱层

rosclaw.sandbox.firewall
  sandbox 内部的安全闸门子模块

ROSClaw Firewall
  对外宣传的安全能力名

rosclaw-runtime
  负责启动、配置、依赖注入和事件总线

e-URDF-Zoo
  Physical DNA Registry

SeekDB
  Knowledge Plane
```

一句话定案：

> **模块叫 `rosclaw-sandbox`，能力叫 `firewall`。Sandbox 是物理试验场，Firewall 是安全闸门。**

这样既继承了你之前架构里的 `firewall` 思想，又不会把未来的任务仿真、回放、benchmark、practice、memory 闭环都塞进一个过窄的名字里。
