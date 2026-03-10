# Codex Design-Intelligence Generator

Use this reference when you want a structured UI recommendation packet generated from local data rather than relying on freeform invention alone.

## Script

`scripts/design_intelligence.py`

## Backing Catalog

`data/design_intelligence_catalog.json`

## Recommended Use

1. Start with the raw product or feature query.
2. Generate a first-pass design-intelligence packet.
3. Add `--stack` and `--component-library` when implementation constraints should shape the recommendation.
4. Compare the result with the actual repository, brand constraints, and brownfield realities.
5. Persist the system only if team alignment benefits from a shared artifact.
6. Validate the resulting components and states in isolated tooling when available.
7. Review the emitted professional polish checks and recovery checks before shipping.

## Example Commands

```bash
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "saas dashboard for incident response"
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "portfolio redesign for a creative agency" --format json
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "AI workspace for research copilots" --stack nextjs --component-library shadcn --format json
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "direct messaging mobile app with unread states and voice notes" --stack flutter --format json
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "checkout recovery improvements" --persist --project-name "Storefront Revamp" --page "Checkout Flow"
```

## Output Shape Highlights

The generator now emits more than style picks:

- stack-aware adaptation guidance when `--stack` is provided
- professional polish checks for affordance, CTA clarity, contrast, and layout stability
- recovery checks for validation, interruption, and high-trust flow handling
- product-family-aware recommendations for familiar surfaces such as direct messaging
- selection signals and an explicit clarification flag when the prompt is too vague to classify safely

## Persistence Safety

The script is designed to avoid the type of crash seen in external tools that assume optional names are always present:

- project and page names are normalized to safe slugs
- missing names fall back to the query or `design-system`
- parent directories are created automatically before writing
- `MASTER.md` is the source of truth and page files are overrides
