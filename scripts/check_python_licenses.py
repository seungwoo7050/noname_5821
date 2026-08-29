from importlib import metadata


def license_text(distribution):
    values = [
        distribution.metadata.get("License-Expression", ""),
        distribution.metadata.get("License", ""),
    ]
    values.extend(
        item.removeprefix("License :: ")
        for item in distribution.metadata.get_all("Classifier", [])
        if item.startswith("License :: ")
    )
    return " ".join(value for value in values if value).strip()


distributions = list(metadata.distributions())
missing = sorted(
    distribution.metadata.get("Name", "unknown")
    for distribution in distributions
    if not license_text(distribution)
)
forbidden = sorted(
    distribution.metadata.get("Name", "unknown")
    for distribution in distributions
    if "AGPL" in license_text(distribution).upper()
)
if missing:
    raise SystemExit(f"missing Python license metadata: {', '.join(missing)}")
if forbidden:
    raise SystemExit(f"forbidden Python licenses: {', '.join(forbidden)}")
print(f"Python license metadata passed: {len(distributions)} installed distributions")
