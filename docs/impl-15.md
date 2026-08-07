# E2E: Edit teleop to hot-reload to sim moves

> Issue: [#15](https://github.com/mergeos-bounties/Lappa/issues/15) - 200 MRG
> CI: [ci-15.yml](../.github/workflows/ci-15.yml)

## Overview

This implementation captures the end-to-end workflow: **edit a teleop file** in the Lappa IDE, trigger **hot-reload**, and observe the **simulation update** live. The workflow is verified through CI tests that validate the teleop module integrity and native sim session lifecycle with hot-reload enabled.

## Architecture

```
IDE edits teleop.py on disk
  -> SimSession detects mtime change
    -> hot reload triggers
      -> engine restarts
        -> sim state updates (pose, twist, lidar)
```

## Supported Demos

| Demo | Teleop | Drive Kind | Hot-Reload |
|------|--------|------------|------------|
| diff_drive_2w | teleop.py | differential | yes |
| omni_3w | teleop.py | omnidirectional | yes |
| ackermann_4w | teleop.py | ackermann | yes |
| tricycle_1fw2rw | kinematics-only | tricycle | yes |
| simple_arm | kinematics-only | planar arm | yes |

## Steps to Reproduce (Windows)

### 1. Setup

```
git clone https://github.com/mergeos-bounties/Lappa.git
cd Lappa
cd packages/server
pip install -e ".[dev]"
```

### 2. Launch the IDE

```
lappa-gui
```

### 3. Open a Demo Package

1. In the workspace explorer, navigate to `packages/demos/diff_drive_2w/`
2. Open `diff_drive_2w/teleop.py` in the editor

### 4. Start Native Simulation

```
lappa sim start --demo diff_drive_2w
```

The native sim engine starts immediately. Hot-reload is enabled by default.

### 5. Edit Teleop and Hot-Reload

Edit `teleop.py` parameter and save (`Ctrl+S`). The `SimSession` detects the mtime change on the package directory and triggers a hot reload: the engine is restarted with the updated package state, preserving trajectory history.

### 6. Observe Sim Moves

- The 3D view updates with new pose/twist based on the edited teleop parameters
- Trajectory points continue recording
- Lidar scans regenerate with the new obstacle map

### 7. Verify

```
lappa sim status
lappa sim stop
```

## CI Verification

The `ci-15.yml` workflow validates:

1. **Teleop integrity** - all demo packages with teleop modules have proper entry points
2. **Native sim engines** - all 5 required engines are registered
3. **Hot-reload lifecycle** - sim starts, time advances, trajectory records, sim stops cleanly
4. **Edit to hot-reload flow** - file system change triggers SimSession reload detection

## Key Files

| File | Role |
|------|------|
| packages/server/src/lappa/sim/session.py | SimSession with hot_reload, start_watch_unlocked, mtime polling |
| packages/server/src/lappa/sim/engines.py | ENGINES registry, create_engine, native kinematics |
| packages/demos/*/teleop.py | ROS2 teleop nodes with /cmd_vel to /odom and /scan |
| .github/workflows/ci-15.yml | CI workflow for this implementation |

## Notes

- Hot-reload uses a background thread polling package mtimes every 1 second
- reload_count counter tracks engine restart count after file changes
- When Docker is available, edits mount live into the container for real ROS2 launch
- Without ROS2 host install, native sim provides offline kinematics fallback
