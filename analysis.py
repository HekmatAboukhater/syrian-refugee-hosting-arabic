"""Reproduce the Syrian refugee-hosting tables and figures from frozen public data."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd


COUNTRIES = {
    "TUR": "Türkiye",
    "LBN": "Lebanon",
    "JOR": "Jordan",
    "IRQ": "Iraq",
    "EGY": "Egypt",
    "DEU": "Germany",
    "SWE": "Sweden",
    "CAN": "Canada",
}
REGIONAL_HOSTS = {"TUR", "LBN", "JOR", "IRQ", "EGY"}
YEARS = list(range(2011, 2025))
SOURCE_FILES = {"unhcr-snapshot.json", "world-bank-snapshot.json"}


def load_sources(input_dir):
    """Check original bytes before parsing either provider's response."""
    manifest = json.loads((input_dir / "data-sources.json").read_text())
    if {entry["file"] for entry in manifest} != SOURCE_FILES:
        raise ValueError("The manifest must identify both expected source files.")
    sources = {}
    for entry in manifest:
        raw = (input_dir / entry["file"]).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry["sha256"] or len(raw) != entry["bytes"]:
            raise ValueError(f"Source snapshot changed: {entry['file']}")
        sources[entry["file"]] = json.loads(raw)
    return sources


def prepare_data(sources):
    """Retain reported counts and match the selected hosts to WDI population."""
    response = sources["unhcr-snapshot.json"]
    if int(response["maxPages"]) != 1:
        raise ValueError("The frozen UNHCR request does not contain every page.")
    refugees = pd.DataFrame(response["items"])
    if not refugees["coo_iso"].eq("SYR").all():
        raise ValueError("The UNHCR response includes another country of origin.")
    refugees = refugees.loc[refugees["coa_iso"].ne("SYR")].copy()
    refugees = refugees.rename(columns={"coa_iso": "iso3", "coa_name": "host"})
    refugees = refugees[["year", "iso3", "host", "refugees", "asylum_seekers"]]
    for field in ["refugees", "asylum_seekers"]:
        refugees[field] = pd.to_numeric(refugees[field], errors="raise")
        if refugees[field].isna().any() or refugees[field].lt(0).any():
            raise ValueError(f"Missing or negative UNHCR counts in {field}.")
    if refugees.duplicated(["year", "iso3"]).any():
        raise ValueError("Duplicate UNHCR destination-year observations.")
    if sorted(refugees["year"].unique()) != YEARS:
        raise ValueError("Unexpected year coverage.")

    wb_metadata, wb_rows = sources["world-bank-snapshot.json"]
    if int(wb_metadata["pages"]) != 1 or len(wb_rows) != int(wb_metadata["total"]):
        raise ValueError("The frozen World Bank request is incomplete.")
    population = pd.DataFrame(wb_rows).rename(
        columns={"countryiso3code": "iso3", "date": "year", "value": "population"}
    )
    population["year"] = pd.to_numeric(population["year"], errors="raise")
    population = population[["iso3", "year", "population"]]
    selected = refugees.loc[refugees["iso3"].isin(COUNTRIES)].copy()
    panel = selected.merge(population, on=["iso3", "year"], validate="one_to_one")
    if len(panel) != len(COUNTRIES) * len(YEARS):
        raise ValueError("The selected country-year panel is incomplete.")
    if panel["population"].isna().any() or panel["population"].le(0).any():
        raise ValueError("Every selected observation needs a positive population.")
    panel["host"] = panel["iso3"].map(COUNTRIES)
    panel["per_1000"] = 1000 * panel["refugees"] / panel["population"]
    panel["refugees_and_asylum_seekers"] = panel["refugees"] + panel["asylum_seekers"]
    panel["combined_per_1000"] = (
        1000 * panel["refugees_and_asylum_seekers"] / panel["population"]
    )
    return refugees, panel.sort_values(["year", "iso3"]).reset_index(drop=True)


def measure_distribution(refugees):
    """Calculate global totals, concentration and the five-host regional share."""
    rows = []
    for year, group in refugees.groupby("year", sort=True):
        total = int(group["refugees"].sum())
        if total <= 0:
            raise ValueError("A yearly global refugee total is zero.")
        shares = group["refugees"] / total
        regional_total = int(
            group.loc[group["iso3"].isin(REGIONAL_HOSTS), "refugees"].sum()
        )
        hhi = float((shares**2).sum())
        rows.append(
            {
                "year": int(year),
                "global_refugees": total,
                "regional_refugees": regional_total,
                "regional_share": regional_total / total,
                "hhi": hhi,
                "effective_destinations": 1 / hhi,
                "positive_destinations": int(group["refugees"].gt(0).sum()),
            }
        )
    return pd.DataFrame(rows)


def draw_figures(panel, annual, output_dir):
    """Create static figures using the same values exported in the CSV tables."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "#faf8f3",
            "axes.facecolor": "#faf8f3",
            "savefig.facecolor": "#faf8f3",
        }
    )
    last = panel.loc[panel["year"].eq(2024)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.7))
    for ax, field, title in zip(
        axes,
        ["refugees", "per_1000"],
        ["Syrian refugees, year-end 2024", "Refugees per 1,000 residents"],
    ):
        ordered = last.sort_values(field)
        divisor = 1_000_000 if field == "refugees" else 1
        bars = ax.barh(ordered["host"], ordered[field] / divisor, color="#206864")
        if field == "refugees":
            labels = [f"{value:,.0f}" for value in ordered[field]]
        else:
            labels = [f"{value:.2f}" if value < 1 else f"{value:.1f}" for value in ordered[field]]
        ax.bar_label(bars, labels=labels, padding=5, fontsize=9)
        ax.set_title(title, loc="left", fontweight="bold", pad=18)
        ax.set_xlabel("Millions of people" if field == "refugees" else "Per 1,000 residents")
        ax.set_xlim(0, (ordered[field] / divisor).max() * 1.4)
        ax.grid(axis="x", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle("The denominator changes the comparison", x=0.03, ha="left", fontsize=18)
    fig.text(0.03, 0.025, "Eight selected hosts. Sources: UNHCR and World Bank WDI. Frozen source files accompany the code.", fontsize=9)
    fig.tight_layout(rect=[0, 0.07, 1, 0.91])
    fig.savefig(output_dir / "hosting-comparison.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].plot(annual["year"], annual["regional_share"], color="#206864", linewidth=2.5)
    axes[0].set_title("Share in five regional host countries", loc="left", fontweight="bold")
    axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].set_ylim(0, 1)
    axes[1].plot(annual["year"], annual["hhi"], color="#a35035", linewidth=2.5)
    axes[1].set_title("Concentration across all reported destinations", loc="left", fontweight="bold")
    axes[1].set_ylabel("Herfindahl–Hirschman index")
    axes[1].set_ylim(0, 1)
    for ax in axes:
        ax.set_xticks([2011, 2015, 2019, 2024])
        ax.grid(alpha=0.15)
    fig.text(0.03, 0.02, "Regional hosts: Türkiye, Lebanon, Jordan, Iraq and Egypt. Year-end stocks; UNHCR snapshot.", fontsize=9)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    fig.savefig(output_dir / "hosting-concentration.png", dpi=180)
    plt.close(fig)


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=root)
    parser.add_argument("--output-dir", type=Path, default=root)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sources = load_sources(args.input_dir)
    refugees, panel = prepare_data(sources)
    annual = measure_distribution(refugees)
    last = panel.loc[panel["year"].eq(2024)].copy()
    for field, rank in [("refugees", "count_rank"), ("per_1000", "per_capita_rank"),
                        ("combined_per_1000", "combined_rank")]:
        last[rank] = last[field].rank(ascending=False, method="min").astype(int)
    panel.to_csv(args.output_dir / "country-year-panel.csv", index=False, float_format="%.8f")
    annual.to_csv(args.output_dir / "annual-metrics.csv", index=False, float_format="%.8f")
    last = last.sort_values("count_rank")
    last.to_csv(args.output_dir / "hosting-2024.csv", index=False, float_format="%.8f")
    draw_figures(panel, annual, args.output_dir)
    print(last[["host", "refugees", "population", "per_1000", "count_rank", "per_capita_rank", "combined_rank"]].to_string(index=False))
    print(annual.loc[annual["year"].isin([2011, 2015, 2024])].to_string(index=False))


if __name__ == "__main__":
    main()
