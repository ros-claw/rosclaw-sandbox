"""
rosclaw-sandbox CLI — main entry point.

Usage:
    rosclaw-sandbox --help
    rosclaw-sandbox doctor
    rosclaw-sandbox robots list
    rosclaw-sandbox robots profile <robot_id>
    rosclaw-sandbox validate <robot_id>
    rosclaw-sandbox run --robot <id> --world <id> [--steps N] [--headless] [--record]
    rosclaw-sandbox run --task <task_id> [--record] [--headless]
    rosclaw-sandbox firewall check --robot <id> --world <id> --action <json>
    rosclaw-sandbox replay <episode_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="rosclaw-sandbox",
    help="ROSClaw Sandbox — embodied physics simulation, validation, and safety-gating.",
    no_args_is_help=True,
)
console = Console()

# Sub-command groups
robots_app = typer.Typer(help="Manage robot embodiments from e-URDF-Zoo.")
app.add_typer(robots_app, name="robots")

firewall_app = typer.Typer(help="Firewall safety-gate commands.")
app.add_typer(firewall_app, name="firewall")

worlds_app = typer.Typer(help="Manage simulation worlds.")
app.add_typer(worlds_app, name="worlds")

@worlds_app.command("list")
def worlds_list():
    from rosclaw.sandbox.worlds.builder import list_worlds, load_world_spec
    worlds = list_worlds()
    if not worlds:
        console.print("[yellow]No world configs found.[/yellow]")
        return
    table = Table(title="Sandbox Worlds")
    table.add_column("World ID", style="cyan")
    table.add_column("Name")
    table.add_column("Objects", justify="right")
    for wid in worlds:
        try:
            spec = load_world_spec(wid)
            table.add_row(wid, spec.name or wid, str(len(spec.objects)))
        except Exception:
            table.add_row(wid, "[red]error[/red]", "-")
    console.print(table)

@worlds_app.command("show")
def worlds_show(world_id: str = typer.Argument(help="World identifier")):
    from rosclaw.sandbox.worlds.builder import load_world_spec
    try:
        spec = load_world_spec(world_id)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    console.print(f"\n[bold]World:[/bold] {spec.name} ({spec.world_id})")
    console.print(f"  Gravity:  {spec.gravity}")
    console.print(f"  Timestep: {spec.timestep}")
    console.print(f"  Objects:  {len(spec.objects)}")



# ---- doctor ----
@app.command()
def doctor() -> None:
    """Check sandbox environment health."""
    console.print("[bold]ROSClaw Sandbox Doctor[/bold]\n")

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"  Python:       {py_ver}")

    try:
        import mujoco
        console.print(f"  MuJoCo:       {mujoco.__version__} [green]OK[/green]")
    except ImportError:
        console.print("  MuJoCo:       [red]NOT INSTALLED[/red]  (pip install mujoco)")

    from rosclaw.sandbox.eurdf.loader import find_eurdf_zoo_path
    zoo_path = find_eurdf_zoo_path()
    if zoo_path:
        robot_count = len([d for d in zoo_path.iterdir() if d.is_dir()]) if zoo_path.is_dir() else 0
        console.print(f"  e-URDF-Zoo:   {zoo_path} ({robot_count} robots) [green]OK[/green]")
    else:
        console.print("  e-URDF-Zoo:   [yellow]NOT FOUND[/yellow]  (set E_URDF_ZOO_PATH)")

    runs_dir = Path("./runs")
    writable = runs_dir.exists() and runs_dir.is_dir()
    console.print(f"  runs dir:     {runs_dir} {'[green]OK[/green]' if writable else '[yellow]MISSING[/yellow]'}")

    from rosclaw.sandbox.core.registry import list_engines
    try:
        import rosclaw.sandbox.engines.mujoco  # noqa: F401
    except ImportError:
        pass
    engines = list_engines()
    console.print(f"  Engines:      {', '.join(engines) if engines else '[yellow]none[/yellow]'}")

    from rosclaw.sandbox import __version__
    console.print(f"\n  rosclaw-sandbox v{__version__}")


# ---- robots list ----
@robots_app.command("list")
def robots_list() -> None:
    """List all available robots in e-URDF-Zoo."""
    from rosclaw.sandbox.eurdf.loader import list_robots, load_robot_profile

    robots = list_robots()
    if not robots:
        console.print("[yellow]No robots found in e-URDF-Zoo.[/yellow]")
        return

    table = Table(title="e-URDF-Zoo Robots")
    table.add_column("Robot ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("DOF", justify="right")

    for rid in robots:
        try:
            profile = load_robot_profile(rid)
            table.add_row(rid, profile.name or "-", profile.semantics.get("robot_type", "-"), str(profile.dof))
        except Exception:
            table.add_row(rid, "[red]error[/red]", "-", "-")

    console.print(table)


# ---- robots profile ----
@robots_app.command("profile")
def robots_profile(
    robot_id: str = typer.Argument(help="Robot identifier"),
    format: str = typer.Option("text", "--format", "-f", help="text|json"),
) -> None:
    """Load and display a robot's embodiment profile."""
    from rosclaw.sandbox.eurdf.loader import load_robot_profile
    try:
        profile = load_robot_profile(robot_id)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if format == "json":
        console.print_json(json.dumps(profile.to_dict(), indent=2, default=str))
    else:
        console.print(f"\n[bold]Robot:[/bold] {profile.name} ({profile.robot_id})")
        console.print(f"  Base type:  {profile.base_type}")
        console.print(f"  DOF:        {profile.dof}")
        console.print(f"  URDF:       {profile.urdf_path or 'N/A'}")
        console.print(f"  MJCF:       {profile.mjcf_path or 'N/A'}")
        console.print(f"  Joints:     {len(profile.joints)}")
        console.print(f"  Links:      {len(profile.links)}")
        console.print(f"  Actuators:  {len(profile.actuators)}")
        if profile.safety:
            console.print(f"  Safety:     {json.dumps(profile.safety, default=str)}")
        if profile.capabilities:
            console.print(f"  Caps:       {json.dumps(profile.capabilities, default=str)}")


# ---- validate ----
@app.command()
def validate(
    robot_id: str = typer.Argument(help="Robot identifier"),
    report: Optional[str] = typer.Option(None, "--report", "-r", help="Save report to path"),
) -> None:
    """Validate a robot model and generate a validation report."""
    from rosclaw.sandbox.eurdf.loader import load_robot_profile
    from rosclaw.sandbox.validator.model_validator import ModelValidator

    try:
        profile = load_robot_profile(robot_id)
    except Exception as e:
        console.print(f"[red]Error loading profile:[/red] {e}")
        raise typer.Exit(1)

    validator = ModelValidator(profile)
    result = validator.validate()

    console.print(f"\n[bold]Validation Report: {robot_id}[/bold]")
    console.print(f"  Status: {result.status_label()}\n")

    for check in result.checks:
        icon = {"PASS": "[green]PASS[/green]", "WARN": "[yellow]WARN[/yellow]", "FAIL": "[red]FAIL[/red]"}
        console.print(f"  {icon.get(check.status, check.status)} {check.message}")

    if report:
        result.save_markdown(report)
        console.print(f"\n  Report saved to: {report}")


# ---- run ----
@app.command()
def run(
    robot: Optional[str] = typer.Option(None, "--robot", help="Robot ID"),
    world: str = typer.Option("empty", "--world", help="World ID"),
    task: Optional[str] = typer.Option(None, "--task", help="Task ID"),
    steps: int = typer.Option(100, "--steps", help="Max simulation steps"),
    headless: bool = typer.Option(False, "--headless", help="No rendering"),
    record: bool = typer.Option(False, "--record", help="Record episode"),
    engine: str = typer.Option("mujoco", "--engine", help="Physics engine"),
) -> None:
    """Run a simulation or task in the sandbox."""
    if task:
        _run_task(task, headless=headless, record=record, engine=engine)
    elif robot:
        _run_robot(robot, world, steps, headless=headless, record=record, engine=engine)
    else:
        console.print("[red]Error:[/red] Specify --robot or --task")
        raise typer.Exit(1)


def _run_robot(robot_id: str, world_id: str, steps: int, headless: bool, record: bool, engine: str) -> None:
    from rosclaw.sandbox.sandbox_api import Sandbox

    sandbox = Sandbox.create(robot_id=robot_id, world_id=world_id, engine=engine)
    obs = sandbox.reset()
    console.print(f"[green]Session started:[/green] {sandbox.session.session_id}")

    recorder = None
    if record:
        from rosclaw.sandbox.traces.recorder import EpisodeRecorder
        recorder = EpisodeRecorder(sandbox.session, output_dir=Path("./runs"))
        recorder.start()

    result = None
    for i in range(steps):
        action = {"type": "noop"}
        result = sandbox.step(action)
        if recorder:
            recorder.record_step(action, result)
        if result.terminated or result.truncated:
            break

    sandbox.close()
    console.print(f"  Steps: {i + 1}  Reward: {result.reward:.4f}  Terminated: {result.terminated}")

    if recorder:
        ep_dir = recorder.finish()
        console.print(f"  Episode saved: {ep_dir}")


def _run_task(task_id: str, headless: bool, record: bool, engine: str) -> None:
    from rosclaw.sandbox.tasks.runtime import TaskRuntime

    runtime = TaskRuntime(task_id=task_id, engine=engine, headless=headless, record=record)
    summary = runtime.run_episode()

    console.print(f"\n[bold]Task:[/bold] {task_id}")
    console.print(f"  Success:      {summary.get('success', False)}")
    console.print(f"  Total steps:  {summary.get('total_steps', 0)}")
    console.print(f"  Total reward: {summary.get('total_reward', 0.0):.4f}")
    if summary.get("episode_dir"):
        console.print(f"  Episode dir:  {summary['episode_dir']}")


# ---- firewall check ----
@firewall_app.command("check")
def firewall_check(
    robot: str = typer.Option(..., "--robot", help="Robot ID"),
    world: str = typer.Option("tabletop", "--world", help="World ID"),
    action: str = typer.Option(..., "--action", help="Action JSON file path"),
    engine: str = typer.Option("mujoco", "--engine", help="Physics engine"),
) -> None:
    """Run a firewall safety check on an action."""
    from rosclaw.sandbox.firewall.gate import FirewallGate

    action_path = Path(action)
    if not action_path.exists():
        console.print(f"[red]Error:[/red] Action file not found: {action}")
        raise typer.Exit(1)

    with open(action_path) as f:
        action_data = json.load(f)

    gate = FirewallGate(robot_id=robot, world_id=world, engine=engine)
    decision = gate.check(action_data)

    if decision.is_allowed:
        console.print(f"[green][FIREWALL ALLOWED][/green] risk_score={decision.risk_score:.2f}")
    else:
        console.print(f"[red][FIREWALL BLOCKED][/red] {decision.reason} (risk={decision.risk_score:.2f})")
        if decision.violated_constraints:
            console.print(f"  Violated: {', '.join(decision.violated_constraints)}")
        if decision.replay_id:
            console.print(f"  Replay:   {decision.replay_id}")


# ---- replay ----
@app.command()
def replay(episode_dir: str = typer.Argument(help="Episode directory path")) -> None:
    """Replay a recorded episode."""
    from rosclaw.sandbox.traces.replay import ReplayEngine

    ep_path = Path(episode_dir)
    if not ep_path.exists():
        console.print(f"[red]Error:[/red] Not found: {episode_dir}")
        raise typer.Exit(1)

    replayer = ReplayEngine(ep_path)
    summary = replayer.replay()
    console.print(f"\n[bold]Replay:[/bold] {summary.get('steps', 0)} steps, {summary.get('duration_sec', 0.0):.2f}s")


# ---- convert (placeholder) ----
@app.command()
def convert(
    robot_id: str = typer.Argument(help="Robot ID"),
    to: str = typer.Option("mjcf", "--to", help="Target format"),
) -> None:
    """Convert robot model between formats."""
    console.print(f"Converting {robot_id} to {to}... [yellow]placeholder[/yellow]")


# ---- export (placeholder) ----
@app.command()
def export(
    episode_dir: str = typer.Argument(help="Episode directory"),
    format: str = typer.Option("jsonl", "--format", help="Formats: jsonl,mcap,mp4"),
) -> None:
    """Export a recorded episode."""
    console.print(f"Exporting {episode_dir} to {format}... [yellow]placeholder[/yellow]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
