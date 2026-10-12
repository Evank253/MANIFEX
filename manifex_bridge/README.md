# MANIFEX \u2194 Integration Layer Bridge

Gives MANIFEX the same Integration Layer used by the Super Cognitive Ecosystem.

```python
from manifex_bridge import ManifexBridge

bridge = ManifexBridge()
bridge.bootstrap()

bridge.record_action(
    subject_id="build-42",
    subject_type="artifact",
    action="built",
    actor_id="manifex-build",
    content={"target": "release", "hash": "abc123"},
)

package = bridge.export_evidence("build-42")
assert package["verified"]
```
