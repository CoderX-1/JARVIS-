# Source and component attribution

This repository vendors the source of the local JARVIS installation so that
a clone contains the code, rather than unusable Git links to nested repos.
The original `.git` directories were not copied. Existing copyright notices,
component license files, and attributions remain in place.

| Directory | Upstream | Source revision in this snapshot |
| --- | --- | --- |
| `core/` | https://github.com/CoderX-1/Full-stack-Jarvis | `44e7864` |
| `components/backtalk/` | https://github.com/jaredrhod/backtalk | `84b3a6c` plus local JARVIS modifications |
| `components/ai-visualizer/` | https://github.com/jaredrhod/ai-visualizer | `c0d2d92` |
| `components/barehands/` | https://github.com/jaredrhod/barehands | `eb23bed` plus local JARVIS modifications |

The component source retains each upstream `LICENSE`. A copy of the GNU AGPL
license is also at this repository's root. This snapshot excludes the owner's
API keys, memory, downloaded models, device-specific configuration, generated
runtime files, and backups. See `README.md` for the local setup requirement.
