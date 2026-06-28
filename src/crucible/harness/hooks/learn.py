"""learn hook — async, fires after post_run to update the Adaptive Brain."""

from __future__ import annotations

from ..runner import RunContext


async def forge_write(ctx: RunContext) -> None:
    """Write all attacks from this run into the Knowledge Forge."""
    if ctx.result is None:
        return

    from ...memory.forge import KnowledgeForge

    forge = KnowledgeForge()
    if not forge.is_available():
        return

    fp = ctx.metadata.get("codebase_fingerprint", "")
    for attack in ctx.result.all_attacks:
        forge.store_attack(
            attack_id=attack.id,
            description=attack.description,
            cwe=attack.cwe,
            severity=attack.severity,
            run_id=ctx.run_id,
            effectiveness=attack.score,
            codebase_fingerprint=fp,
        )


async def effectiveness_update(ctx: RunContext) -> None:
    """Update the Adaptive Brain's effectiveness scores for this run's attacks."""
    if ctx.result is None:
        return

    from ...brain.effectiveness import AttackEffectivenessTracker

    tracker = AttackEffectivenessTracker()
    fp = ctx.metadata.get("codebase_fingerprint", "")
    for attack in ctx.result.all_attacks:
        tracker.update(attack.cwe, attack.score, fp)
