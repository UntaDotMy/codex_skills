from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CatalogEntry:
    identifier: str
    display_name: str
    keywords: list[str]
    payload: dict[str, Any]


@dataclass
class EntrySelection:
    entry: CatalogEntry
    total_score: int
    matched_keywords: list[str]
    display_match: bool
    preferred_match: bool


@dataclass
class DesignRecommendation:
    query: str
    platform: str
    stack: str | None
    component_library: str | None
    product_archetype: dict[str, Any]
    style_family: dict[str, Any]
    color_mood: dict[str, Any]
    typography_mood: dict[str, Any]
    stack_profile: dict[str, Any] | None
    design_intelligence_packet: dict[str, Any]
    stack_adaptation_guidance: list[str]
    verification_loop: list[str]
    brownfield_defaults: list[str]
    professional_polish_checks: list[str]
    recovery_checks: list[str]
    anti_patterns: list[str]
    needs_clarification: bool
    clarification_reason: str | None
    selection_signals: dict[str, Any]


GENERIC_PRODUCT_MATCH_TOKENS = {
    "app",
    "product",
    "mobile",
    "web",
    "desktop",
    "site",
    "platform",
    "tool",
    "interface",
}

MOBILE_STACK_IDENTIFIERS = {"flutter-mobile", "react-native-mobile"}

PRODUCT_BRIEF_HINTS: dict[str, dict[str, Any]] = {
    "saas-dashboard": {
        "target_user": "operator or team member monitoring work",
        "trigger": "opening the product to inspect status, triage issues, or complete an operational task",
        "primary_surface_model": "overview plus focused task panels",
        "critical_failure_modes": [
            "core status is buried under decoration",
            "important actions compete with each other",
            "dense data loses scanability under narrow widths",
        ],
    },
    "marketing-landing": {
        "target_user": "prospective customer evaluating the offer",
        "trigger": "arriving from a campaign, search result, or referral",
        "primary_surface_model": "hero plus proof and conversion rhythm",
        "critical_failure_modes": [
            "the first screen does not explain the offer quickly",
            "proof and reassurance appear too late",
            "competing calls to action slow commitment",
        ],
    },
    "fintech-product": {
        "target_user": "account holder making a high-trust financial decision",
        "trigger": "checking status, moving money, or approving a sensitive action",
        "primary_surface_model": "status summary plus guarded action flow",
        "critical_failure_modes": [
            "security or fee implications are unclear",
            "high-risk actions are not visually distinct",
            "error recovery weakens trust at commitment moments",
        ],
    },
    "healthcare-service": {
        "target_user": "person seeking care or managing a healthcare task",
        "trigger": "starting or resuming a care-related action that benefits from reassurance",
        "primary_surface_model": "guided service flow with clear next step and support cues",
        "critical_failure_modes": [
            "language increases anxiety instead of reducing it",
            "forms ask for information without enough context",
            "recovery paths after interruption are unclear",
        ],
    },
    "ecommerce-storefront": {
        "target_user": "shopper evaluating or purchasing an item",
        "trigger": "arriving to compare, choose, or complete a purchase",
        "primary_surface_model": "catalog or product detail plus purchase path",
        "critical_failure_modes": [
            "pricing and trust signals are fragmented",
            "primary purchase actions lose visual dominance",
            "checkout interruptions cause lost momentum",
        ],
    },
    "portfolio-showcase": {
        "target_user": "visitor evaluating the creator or firm",
        "trigger": "arriving to assess quality, fit, and credibility",
        "primary_surface_model": "proof-led narrative with one contact or booking path",
        "critical_failure_modes": [
            "visual effects overpower the work itself",
            "proof lacks structure or pacing",
            "the contact path is unclear",
        ],
    },
    "education-platform": {
        "target_user": "learner advancing to the next study step",
        "trigger": "returning to continue progress or complete a learning task",
        "primary_surface_model": "guided content flow with visible progress",
        "critical_failure_modes": [
            "the next step is unclear",
            "content becomes a wall of text without pacing",
            "progress or recovery cues disappear after interruption",
        ],
    },
    "productivity-tool": {
        "target_user": "person organizing or completing work",
        "trigger": "opening the product to resume a task with minimal friction",
        "primary_surface_model": "current task plus lightweight context and quick actions",
        "critical_failure_modes": [
            "too many quick actions compete for attention",
            "status context is hidden until after navigation",
            "empty states do not point toward a useful next step",
        ],
    },
    "ai-workspace": {
        "target_user": "person supervising or refining assisted output",
        "trigger": "reviewing generated work and deciding what to approve, edit, or retry",
        "primary_surface_model": "assistant output plus trust and control cues",
        "critical_failure_modes": [
            "outputs appear without enough control or source context",
            "novelty styling outruns trust-building cues",
            "the next safe action is unclear after an error or partial result",
        ],
    },
    "developer-tool": {
        "target_user": "developer or operator resolving a technical task",
        "trigger": "opening the product to inspect state, logs, or diffs under time pressure",
        "primary_surface_model": "high-signal task pane with explicit system state",
        "critical_failure_modes": [
            "status hierarchy is weak in dense views",
            "destructive actions blend into ordinary controls",
            "navigation adds friction before the user reaches the active problem",
        ],
    },
    "marketplace-platform": {
        "target_user": "buyer or seller comparing offers",
        "trigger": "searching, filtering, or choosing between offers with trade-offs",
        "primary_surface_model": "discovery list plus comparison and transaction cues",
        "critical_failure_modes": [
            "important price or availability signals are buried",
            "comparison criteria are hard to retain across screens",
            "trust proof is absent at transaction moments",
        ],
    },
    "mobile-companion": {
        "target_user": "person resuming a lightweight recurring task",
        "trigger": "opening the product quickly on a small screen and expecting continuity",
        "primary_surface_model": "single-thumb primary action plus clear history or progress",
        "critical_failure_modes": [
            "desktop-style density appears on a small screen",
            "the keyboard or system chrome obscures the main action",
            "the flow loses context after an interruption",
        ],
    },
    "messaging-product": {
        "target_user": "person resuming or sending a conversation",
        "trigger": "opening the product to scan conversations, read updates, or send a reply",
        "primary_surface_model": "conversation list plus active thread plus persistent composer",
        "critical_failure_modes": [
            "the user cannot tell which thread needs attention first",
            "send, retry, or delivery state is unclear",
            "drafts, attachments, or scroll position are lost across interruption",
        ],
    },
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Codex-native design-intelligence recommendation packet."
    )
    parser.add_argument("query", help="Design request, product description, or UI brief.")
    parser.add_argument("--platform", default="web", help="Platform surface, for example web, mobile, desktop.")
    parser.add_argument("--stack", default=None, help="Optional implementation stack, such as nextjs or flutter.")
    parser.add_argument(
        "--component-library",
        default=None,
        help="Optional component library, such as shadcn, material, or custom.",
    )
    parser.add_argument("--product-archetype", default=None, help="Force a product archetype id.")
    parser.add_argument("--style-family", default=None, help="Force a style family id.")
    parser.add_argument("--color-mood", default=None, help="Force a color mood id.")
    parser.add_argument("--typography-mood", default=None, help="Force a typography mood id.")
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "compact"],
        default="markdown",
        help="Output format.",
    )
    parser.add_argument("--persist", action="store_true", help="Persist the recommendation into docs/design-system.")
    parser.add_argument("--project-name", default=None, help="Optional project name for persistence.")
    parser.add_argument("--page", default=None, help="Optional page or flow override name for persistence.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory where docs/design-system should be written when --persist is used.",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "design_intelligence_catalog.json",
        help="Catalog file path.",
    )
    return parser.parse_args()


def load_catalog(catalog_path: Path) -> dict[str, list[CatalogEntry]]:
    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Design-intelligence catalog not found at {catalog_path}. Ensure the skill sync copied the data directory or pass --catalog explicitly."
        )
    catalog_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog: dict[str, list[CatalogEntry]] = {}
    for section_name, items in catalog_payload.items():
        catalog[section_name] = [
            CatalogEntry(
                identifier=item["id"],
                display_name=item["display_name"],
                keywords=list(item.get("keywords", [])),
                payload=item,
            )
            for item in items
        ]
    return catalog


def tokenize_text(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def choose_entry(
    entries: list[CatalogEntry],
    query_tokens: set[str],
    explicit_identifier: str | None = None,
    preferred_identifiers: list[str] | None = None,
    demoted_keywords: set[str] | None = None,
) -> EntrySelection:
    if explicit_identifier is not None:
        for entry in entries:
            if entry.identifier == explicit_identifier:
                matched_keywords = sorted(query_tokens & set(entry.keywords))
                return EntrySelection(
                    entry=entry,
                    total_score=len(matched_keywords) + 5,
                    matched_keywords=matched_keywords,
                    display_match=bool(tokenize_text(entry.display_name) & query_tokens),
                    preferred_match=False,
                )
        raise ValueError(f"Unknown identifier: {explicit_identifier}")

    best_selection = EntrySelection(
        entry=entries[0],
        total_score=-1,
        matched_keywords=[],
        display_match=False,
        preferred_match=False,
    )
    best_score = -1
    preferred_set = set(preferred_identifiers or [])
    demoted_keyword_set = demoted_keywords or set()
    for entry in entries:
        matched_keywords = sorted(query_tokens & set(entry.keywords))
        meaningful_matches = [
            keyword for keyword in matched_keywords if keyword not in demoted_keyword_set
        ]
        display_match = bool(tokenize_text(entry.display_name) & query_tokens)
        preferred_match = entry.identifier in preferred_set
        keyword_score = len(meaningful_matches) * 2
        preferred_bonus = 2 if preferred_match else 0
        display_bonus = 1 if display_match else 0
        total_score = keyword_score + preferred_bonus + display_bonus
        if total_score > best_score:
            best_selection = EntrySelection(
                entry=entry,
                total_score=total_score,
                matched_keywords=matched_keywords,
                display_match=display_match,
                preferred_match=preferred_match,
            )
            best_score = total_score
    return best_selection


def normalize_identifier(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def merge_preferred_identifiers(*identifier_groups: list[str]) -> list[str]:
    merged_identifiers: list[str] = []
    seen_identifiers: set[str] = set()
    for identifier_group in identifier_groups:
        for identifier in identifier_group:
            if identifier not in seen_identifiers:
                merged_identifiers.append(identifier)
                seen_identifiers.add(identifier)
    return merged_identifiers


def choose_stack_profile(
    entries: list[CatalogEntry],
    query_tokens: set[str],
    stack_name: str | None,
) -> CatalogEntry | None:
    if not entries:
        return None

    normalized_stack_name = normalize_identifier(stack_name)
    if normalized_stack_name:
        for entry in entries:
            candidate_identifiers = {
                normalize_identifier(entry.identifier),
                *(normalize_identifier(alias) for alias in entry.payload.get("aliases", [])),
            }
            if normalized_stack_name in candidate_identifiers:
                return entry

    best_entry: CatalogEntry | None = None
    best_score = 0
    for entry in entries:
        aliases = [entry.identifier, *entry.payload.get("aliases", [])]
        entry_best_score = 0
        for alias in aliases:
            alias_tokens = tokenize_text(alias)
            if not alias_tokens:
                continue
            if alias_tokens.issubset(query_tokens):
                entry_best_score = max(entry_best_score, len(alias_tokens) + 1)
            elif len(alias_tokens) == 1 and alias_tokens & query_tokens:
                entry_best_score = max(entry_best_score, 1)
        if entry_best_score > best_score:
            best_entry = entry
            best_score = entry_best_score

    return best_entry if best_score > 0 else None


def build_stack_adaptation_guidance(
    platform: str,
    component_library: str | None,
    stack_profile: CatalogEntry | None,
) -> list[str]:
    stack_adaptation_guidance: list[str] = []
    if stack_profile is not None:
        stack_adaptation_guidance.extend(stack_profile.payload.get("guidance", []))
        for preview_tool in stack_profile.payload.get("component_preview_tools", []):
            stack_adaptation_guidance.append(
                f"Validate critical states in {preview_tool} before approving the integrated screen."
            )
    else:
        stack_adaptation_guidance.append(
            f"Adapt the recommendation to the existing {platform} implementation constraints instead of inventing a parallel UI system."
        )

    if component_library:
        stack_adaptation_guidance.append(
            f"Map the design direction onto {component_library} primitives instead of forking a second component language."
        )

    return list(dict.fromkeys(stack_adaptation_guidance))


def infer_platform_surface(
    requested_platform: str,
    query_tokens: set[str],
    stack_profile: CatalogEntry | None,
) -> str:
    normalized_requested_platform = normalize_identifier(requested_platform)
    if normalized_requested_platform and normalized_requested_platform != "web":
        return requested_platform

    if stack_profile is not None and stack_profile.identifier in MOBILE_STACK_IDENTIFIERS:
        return "mobile"

    if query_tokens & {"mobile", "ios", "android", "iphone", "ipad"}:
        return "mobile"

    if query_tokens & {"desktop", "macos", "windows", "linux"}:
        return "desktop"

    return requested_platform


def build_brief_hints(product_archetype: CatalogEntry) -> dict[str, Any]:
    return PRODUCT_BRIEF_HINTS.get(
        product_archetype.identifier,
        {
            "target_user": "person completing the product's primary task",
            "trigger": "arriving to complete a task with minimal friction",
            "primary_surface_model": "one strong primary workflow with supporting context",
            "critical_failure_modes": [
                "the primary task is hard to find",
                "the next safe action is unclear",
                "the interface loses progress after interruption",
            ],
        },
    )


def build_benchmark_strategy(product_archetype: CatalogEntry) -> list[str]:
    return [
        f"Benchmark mature {product_archetype.display_name.lower()} references that users in this category already understand.",
        "Pair those product-family references with one mature design-system source to keep components and states reusable.",
        "Use one accessibility-forward reference to verify hierarchy, focus, contrast, and recovery behavior.",
    ]


def build_selection_signals(
    product_selection: EntrySelection,
    style_selection: EntrySelection,
    color_selection: EntrySelection,
    typography_selection: EntrySelection,
    stack_profile: CatalogEntry | None,
) -> dict[str, Any]:
    meaningful_product_matches = [
        token for token in product_selection.matched_keywords if token not in GENERIC_PRODUCT_MATCH_TOKENS
    ]
    return {
        "product_archetype": {
            "identifier": product_selection.entry.identifier,
            "score": product_selection.total_score,
            "matched_keywords": product_selection.matched_keywords,
            "meaningful_matched_keywords": meaningful_product_matches,
            "display_match": product_selection.display_match,
        },
        "style_family": {
            "identifier": style_selection.entry.identifier,
            "score": style_selection.total_score,
            "matched_keywords": style_selection.matched_keywords,
            "preferred_match": style_selection.preferred_match,
        },
        "color_mood": {
            "identifier": color_selection.entry.identifier,
            "score": color_selection.total_score,
            "matched_keywords": color_selection.matched_keywords,
            "preferred_match": color_selection.preferred_match,
        },
        "typography_mood": {
            "identifier": typography_selection.entry.identifier,
            "score": typography_selection.total_score,
            "matched_keywords": typography_selection.matched_keywords,
            "preferred_match": typography_selection.preferred_match,
        },
        "stack_profile": stack_profile.identifier if stack_profile is not None else None,
    }


def build_professional_polish_checks(
    platform: str,
    stack_profile: CatalogEntry | None,
    product_archetype: CatalogEntry,
) -> list[str]:
    professional_polish_checks = [
        "Use one product-grade icon family; avoid emoji or novelty icons in core product UI.",
        "Use outcome-specific CTA labels instead of generic verbs such as Submit, Continue, or Learn More.",
        "Keep interaction affordances obvious: clickable elements should look clickable, expandable areas should signal disclosure, and destructive actions should feel meaningfully distinct.",
        "Protect readability on tinted, glass, or deep-contrast surfaces by checking real text contrast and layer separation.",
    ]

    mobile_tokens = {"flutter-mobile", "react-native-mobile"}
    if platform.lower() == "mobile" or (
        stack_profile is not None and stack_profile.identifier in mobile_tokens
    ):
        professional_polish_checks.append(
            "Protect thumb reach, safe areas, keyboard overlap, and sticky primary actions on small screens."
        )
    else:
        professional_polish_checks.append(
            "Protect fixed headers, sticky actions, and dense table or card layouts from overlap, clipping, or unreadable compression."
        )

    professional_polish_checks.extend(product_archetype.payload.get("professional_polish_checks", []))

    return professional_polish_checks


def build_recovery_checks(
    platform: str,
    product_archetype: CatalogEntry,
) -> list[str]:
    recovery_checks = [
        "Preserve entered data and user progress after validation, network, or permission failures.",
        "Explain what failed, what remains saved, and the next safe action in plain language.",
        "Keep retry, back, and alternate-path actions visible when a step cannot complete.",
    ]

    high_trust_archetypes = {"fintech-product", "healthcare-service", "ecommerce-storefront", "marketplace-platform"}
    if product_archetype.identifier in high_trust_archetypes:
        recovery_checks.append(
            "For high-trust flows, reassure users about unchanged data, payment state, or account status before asking them to retry."
        )

    if platform.lower() == "mobile":
        recovery_checks.append(
            "Recover gracefully from interrupted sessions, keyboard dismissal, and connectivity changes without dumping the user back to the start."
        )

    recovery_checks.extend(product_archetype.payload.get("recovery_checks", []))

    return recovery_checks


def build_verification_loop(
    platform: str,
    product_archetype: CatalogEntry,
    stack_profile: CatalogEntry | None,
) -> list[str]:
    verification_loop = [
        "Verify primary CTA clarity, hierarchy, and outcome specificity.",
        "Check default, hover, focus, active, disabled, loading, empty, error, and success states in isolation.",
        "Run responsive and theme checks on the dominant surface before approving the full page.",
        "Confirm brownfield changes preserve trusted navigation, language, and proven component behavior.",
    ]
    verification_loop.extend(product_archetype.payload.get("verification_checks", []))
    if stack_profile is not None:
        verification_loop.extend(stack_profile.payload.get("validation_checks", []))
    return verification_loop


def build_design_intelligence_packet(
    query: str,
    platform: str,
    stack: str | None,
    component_library: str | None,
    product_archetype: CatalogEntry,
    style_family: CatalogEntry,
    color_mood: CatalogEntry,
    typography_mood: CatalogEntry,
    stack_profile: CatalogEntry | None,
    selection_signals: dict[str, Any],
) -> dict[str, Any]:
    brief_hints = build_brief_hints(product_archetype)
    benchmark_strategy = build_benchmark_strategy(product_archetype)
    benchmark_direction = [
        benchmark_strategy[0],
        f"Use {style_family.display_name} as the dominant design-system family.",
        f"Ground palette decisions in {color_mood.display_name}.",
        f"Use {typography_mood.display_name} to drive hierarchy and readability.",
    ]
    if stack_profile is not None:
        benchmark_direction.append(
            f"Adapt implementation details to {stack_profile.display_name} constraints and preview tooling."
        )

    return {
        "product_type": product_archetype.display_name,
        "platform_surface": platform,
        "primary_user_story": query,
        "target_user": brief_hints["target_user"],
        "trigger": brief_hints["trigger"],
        "primary_goal": query,
        "primary_surface_model": brief_hints["primary_surface_model"],
        "critical_failure_modes": brief_hints["critical_failure_modes"],
        "trust_posture": product_archetype.payload["trust_posture"],
        "content_priorities": product_archetype.payload["content_priorities"],
        "style_family": style_family.display_name,
        "color_mood": color_mood.display_name,
        "typography_mood": typography_mood.display_name,
        "motion_posture": product_archetype.payload["recommended_motion_posture"],
        "density": product_archetype.payload["recommended_density"],
        "component_library": component_library or "existing system or custom",
        "stack": stack or "unspecified",
        "stack_profile": stack_profile.display_name if stack_profile is not None else "generic delivery constraints",
        "benchmark_strategy": benchmark_strategy,
        "benchmark_direction": benchmark_direction,
        "selection_signals": selection_signals,
    }


def build_recommendation(arguments: argparse.Namespace) -> DesignRecommendation:
    catalog = load_catalog(arguments.catalog)
    query_tokens = tokenize_text(
        " ".join(
            part
            for part in [arguments.query, arguments.platform, arguments.stack or "", arguments.component_library or ""]
            if part
        )
    )
    stack_profile = choose_stack_profile(
        catalog.get("stack_profiles", []),
        query_tokens,
        arguments.stack,
    )

    product_selection = choose_entry(
        catalog["product_archetypes"],
        query_tokens,
        explicit_identifier=arguments.product_archetype,
        demoted_keywords=GENERIC_PRODUCT_MATCH_TOKENS,
    )
    resolved_platform = infer_platform_surface(
        requested_platform=arguments.platform,
        query_tokens=query_tokens,
        stack_profile=stack_profile,
    )
    style_selection = choose_entry(
        catalog["style_families"],
        query_tokens,
        explicit_identifier=arguments.style_family,
        preferred_identifiers=merge_preferred_identifiers(
            product_selection.entry.payload.get("recommended_style_families", []),
            stack_profile.payload.get("preferred_style_families", []) if stack_profile is not None else [],
        ),
    )
    color_selection = choose_entry(
        catalog["color_moods"],
        query_tokens,
        explicit_identifier=arguments.color_mood,
        preferred_identifiers=merge_preferred_identifiers(
            product_selection.entry.payload.get("recommended_color_moods", []),
            stack_profile.payload.get("preferred_color_moods", []) if stack_profile is not None else [],
        ),
    )
    typography_selection = choose_entry(
        catalog["typography_moods"],
        query_tokens,
        explicit_identifier=arguments.typography_mood,
        preferred_identifiers=merge_preferred_identifiers(
            product_selection.entry.payload.get("recommended_typography_moods", []),
            stack_profile.payload.get("preferred_typography_moods", []) if stack_profile is not None else [],
        ),
    )

    selection_signals = build_selection_signals(
        product_selection=product_selection,
        style_selection=style_selection,
        color_selection=color_selection,
        typography_selection=typography_selection,
        stack_profile=stack_profile,
    )
    needs_clarification = not selection_signals["product_archetype"]["meaningful_matched_keywords"]
    clarification_reason = None
    if needs_clarification:
        clarification_reason = (
            "The request does not yet contain enough surface-specific detail to safely infer the product family. Clarify the core workflow, dominant surface, or user task before trusting the recommendation."
        )

    anti_patterns = list(dict.fromkeys(
        product_selection.entry.payload.get("anti_patterns", []) + style_selection.entry.payload.get("anti_patterns", [])
    ))
    stack_adaptation_guidance = build_stack_adaptation_guidance(
        platform=resolved_platform,
        component_library=arguments.component_library,
        stack_profile=stack_profile,
    )
    verification_loop = build_verification_loop(
        platform=resolved_platform,
        product_archetype=product_selection.entry,
        stack_profile=stack_profile,
    )
    brownfield_defaults = [
        "Audit what already works before redesigning.",
        "Keep proven brand signals and domain language unless research says they are the problem.",
        "Document what remains stable versus what is changing.",
        "Persist the system as MASTER plus optional page overrides when team alignment needs it.",
    ]
    professional_polish_checks = build_professional_polish_checks(
        platform=resolved_platform,
        stack_profile=stack_profile,
        product_archetype=product_selection.entry,
    )
    recovery_checks = build_recovery_checks(
        platform=resolved_platform,
        product_archetype=product_selection.entry,
    )

    packet = build_design_intelligence_packet(
        query=arguments.query,
        platform=resolved_platform,
        stack=arguments.stack,
        component_library=arguments.component_library,
        product_archetype=product_selection.entry,
        style_family=style_selection.entry,
        color_mood=color_selection.entry,
        typography_mood=typography_selection.entry,
        stack_profile=stack_profile,
        selection_signals=selection_signals,
    )

    return DesignRecommendation(
        query=arguments.query,
        platform=resolved_platform,
        stack=arguments.stack,
        component_library=arguments.component_library,
        product_archetype=product_selection.entry.payload,
        style_family=style_selection.entry.payload,
        color_mood=color_selection.entry.payload,
        typography_mood=typography_selection.entry.payload,
        stack_profile=stack_profile.payload if stack_profile is not None else None,
        design_intelligence_packet=packet,
        stack_adaptation_guidance=stack_adaptation_guidance,
        verification_loop=verification_loop,
        brownfield_defaults=brownfield_defaults,
        professional_polish_checks=professional_polish_checks,
        recovery_checks=recovery_checks,
        anti_patterns=anti_patterns,
        needs_clarification=needs_clarification,
        clarification_reason=clarification_reason,
        selection_signals=selection_signals,
    )


def slugify(value: str | None) -> str:
    if value is None:
        return ""
    normalized_value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized_value


def resolve_project_slug(project_name: str | None, query: str) -> str:
    for candidate in [project_name, query, "design-system"]:
        slug = slugify(candidate)
        if slug:
            return slug
    return "design-system"


def render_markdown(recommendation: DesignRecommendation) -> str:
    packet = recommendation.design_intelligence_packet
    lines = [
        f"# {packet['product_type']} Design Recommendation",
        "",
        "## Design Intelligence Packet",
        f"- Primary user story: {packet['primary_user_story']}",
        f"- Platform surface: {packet['platform_surface']}",
        f"- Trust posture: {packet['trust_posture']}",
        f"- Style family: {packet['style_family']}",
        f"- Color mood: {packet['color_mood']}",
        f"- Typography mood: {packet['typography_mood']}",
        f"- Motion posture: {packet['motion_posture']}",
        f"- Density: {packet['density']}",
        f"- Stack: {packet['stack']}",
        f"- Component library: {packet['component_library']}",
        "",
        "## Brief Hardening",
        f"- Target user: {packet['target_user']}",
        f"- Trigger: {packet['trigger']}",
        f"- Primary goal: {packet['primary_goal']}",
        f"- Primary surface model: {packet['primary_surface_model']}",
        "",
        "## Content Priorities",
    ]
    lines.extend(f"- {priority}" for priority in packet["content_priorities"])
    lines.extend(["", "## Critical Failure Modes"])
    lines.extend(f"- {item}" for item in packet["critical_failure_modes"])
    lines.extend(["", "## Benchmark Strategy"])
    lines.extend(f"- {item}" for item in packet["benchmark_strategy"])
    if recommendation.needs_clarification and recommendation.clarification_reason:
        lines.extend(["", "## Clarification Needed", f"- {recommendation.clarification_reason}"])
    lines.extend([
        "",
        "## Recommended System",
        f"- Product archetype: {recommendation.product_archetype['display_name']}",
        f"- Style family: {recommendation.style_family['display_name']} — {recommendation.style_family['visual_direction']}",
        f"- Color mood: {recommendation.color_mood['display_name']} — {recommendation.color_mood['palette_direction']}",
        f"- Typography mood: {recommendation.typography_mood['display_name']} — {recommendation.typography_mood['direction']}",
        f"- Stack profile: {packet['stack_profile']}",
        f"- CTA guidance: {recommendation.product_archetype['cta_guidance']}",
        "",
        "## Selection Signals",
        f"- Product archetype score: {recommendation.selection_signals['product_archetype']['score']}",
        f"- Product archetype matches: {', '.join(recommendation.selection_signals['product_archetype']['matched_keywords']) or 'none'}",
        f"- Style family matches: {', '.join(recommendation.selection_signals['style_family']['matched_keywords']) or 'none'}",
        "",
        "## Stack Adaptation",
    ])
    lines.extend(f"- {item}" for item in recommendation.stack_adaptation_guidance)
    lines.extend([
        "",
        "## Brownfield Defaults",
    ])
    lines.extend(f"- {item}" for item in recommendation.brownfield_defaults)
    lines.extend(["", "## Verification Loop"])
    lines.extend(f"- {item}" for item in recommendation.verification_loop)
    lines.extend(["", "## Professional Polish Checks"])
    lines.extend(f"- {item}" for item in recommendation.professional_polish_checks)
    lines.extend(["", "## Recovery Checks"])
    lines.extend(f"- {item}" for item in recommendation.recovery_checks)
    lines.extend(["", "## Anti-Patterns"])
    lines.extend(f"- {item}" for item in recommendation.anti_patterns)
    return "\n".join(lines)


def build_clarification_payload(recommendation: DesignRecommendation) -> dict[str, Any]:
    return {
        "query": recommendation.query,
        "platform": recommendation.platform,
        "stack": recommendation.stack,
        "component_library": recommendation.component_library,
        "needs_clarification": recommendation.needs_clarification,
        "clarification_reason": recommendation.clarification_reason,
        "requested_brief_fields": [
            "target user",
            "dominant workflow",
            "primary surface",
            "success state",
            "failure and recovery expectations",
        ],
        "selection_signals": recommendation.selection_signals,
    }


def render_clarification_markdown(recommendation: DesignRecommendation) -> str:
    clarification_payload = build_clarification_payload(recommendation)
    lines = [
        "# Clarification Needed",
        "",
        f"- Query: {clarification_payload['query']}",
        f"- Platform surface: {clarification_payload['platform']}",
        f"- Reason: {clarification_payload['clarification_reason']}",
        f"- Tentative product-family match: {clarification_payload['selection_signals']['product_archetype']['identifier']}",
        f"- Tentative match keywords: {', '.join(clarification_payload['selection_signals']['product_archetype']['matched_keywords']) or 'none'}",
        "",
        "## Add Before Re-running",
    ]
    lines.extend(f"- {item}" for item in clarification_payload["requested_brief_fields"])
    return "\n".join(lines)


def render_compact(recommendation: DesignRecommendation) -> str:
    packet = recommendation.design_intelligence_packet
    return (
        f"{recommendation.product_archetype['display_name']} | "
        f"style={recommendation.style_family['display_name']} | "
        f"color={recommendation.color_mood['display_name']} | "
        f"type={recommendation.typography_mood['display_name']} | "
        f"trust={packet['trust_posture']} | density={packet['density']} | "
        f"stack={packet['stack_profile']} | clarify={'yes' if recommendation.needs_clarification else 'no'}"
    )


def persist_recommendation(
    recommendation: DesignRecommendation,
    output_directory: Path,
    project_name: str | None,
    page_name: str | None,
) -> dict[str, str]:
    project_slug = resolve_project_slug(project_name, recommendation.query)
    design_system_directory = output_directory / "docs" / "design-system"
    pages_directory = design_system_directory / "pages"
    design_system_directory.mkdir(parents=True, exist_ok=True)
    pages_directory.mkdir(parents=True, exist_ok=True)

    master_file_path = design_system_directory / "MASTER.md"
    master_content = render_markdown(recommendation)
    master_header = f"<!-- project-slug: {project_slug} -->\n"
    master_file_path.write_text(master_header + master_content + "\n", encoding="utf-8")

    persisted_paths = {"master": str(master_file_path)}
    if page_name:
        page_slug = resolve_project_slug(page_name, recommendation.query)
        page_file_path = pages_directory / f"{page_slug}.md"
        page_lines = [
            f"# {page_name} Override",
            "",
            f"Use `docs/design-system/MASTER.md` as the base system for `{project_slug}`.",
            "",
            "## Override Guidance",
            "- Keep the same trust posture and typography baseline unless this page has a validated reason to diverge.",
            "- Document only page-specific layout, CTA, or state differences here.",
            "- Re-run component-state and responsive checks for this flow before shipping.",
        ]
        page_file_path.write_text("\n".join(page_lines) + "\n", encoding="utf-8")
        persisted_paths["page"] = str(page_file_path)

    return persisted_paths


def emit_output(recommendation: DesignRecommendation, output_format: str) -> str:
    if recommendation.needs_clarification:
        clarification_payload = build_clarification_payload(recommendation)
        if output_format == "json":
            return json.dumps(clarification_payload, indent=2)
        if output_format == "compact":
            return (
                f"Clarification Needed | top={clarification_payload['selection_signals']['product_archetype']['identifier']} | "
                f"platform={clarification_payload['platform']}"
            )
        return render_clarification_markdown(recommendation)
    if output_format == "json":
        return json.dumps(asdict(recommendation), indent=2)
    if output_format == "compact":
        return render_compact(recommendation)
    return render_markdown(recommendation)


def main() -> int:
    arguments = parse_arguments()
    recommendation = build_recommendation(arguments)
    rendered_output = emit_output(recommendation, arguments.format)
    print(rendered_output)

    if arguments.persist:
        if recommendation.needs_clarification:
            print(
                "Cannot persist a low-confidence design recommendation. Clarify the core workflow, dominant surface, and user task first.",
                file=sys.stderr,
            )
            return 1
        persisted_paths = persist_recommendation(
            recommendation=recommendation,
            output_directory=arguments.output_dir,
            project_name=arguments.project_name,
            page_name=arguments.page,
        )
        print(json.dumps({"persisted": persisted_paths}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
