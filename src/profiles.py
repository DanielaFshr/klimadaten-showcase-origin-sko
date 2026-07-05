from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
EXPORTS_DIR = BASE_DIR / "exports"
PROFILES_PATH = EXPORTS_DIR / "place_profiles_all.parquet"


def load_profiles(path: Path = PROFILES_PATH) -> pd.DataFrame:
    df = pd.read_parquet(path)

    # defensive cleanup
    df = df.copy()

    if "month" in df.columns:
        df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")

    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    for col in ["place_id", "place_name", "dataset_type", "scenario", "metric"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df


def get_place_options(df: pd.DataFrame) -> list[dict]:
    places = (
        df[["place_id", "place_name"]]
        .drop_duplicates()
        .sort_values("place_name")
    )

    return [
        {"label": row["place_name"], "value": row["place_id"]}
        for _, row in places.iterrows()
    ]


def get_metric_options(df: pd.DataFrame) -> list[dict]:
    metrics = sorted(df["metric"].dropna().unique())

    metric_labels = {
        "temperature_mean": "Durchschnittstemperatur",
        "hot_days_mean": "Anzahl Hitzetage pro Monat",
        "gdd": "Wärmesumme",
    }

    return [
        {"label": metric_labels.get(metric, metric), "value": metric}
        for metric in metrics
    ]


def get_scenario_options(df: pd.DataFrame, dataset_type: str) -> list[dict]:
    subset = df[df["dataset_type"] == dataset_type].copy()

    scenarios = sorted(subset["scenario"].dropna().unique())

    #Referenz ausblenden
    scenarios = [s for s in scenarios if s != "ref"]

    scenario_labels = {
        "observed": "Beobachtet",
        "ref": "Referenz",
        "gwl1_5": "Erwärmung 1.5 °C",
        "gwl2_0": "Erwärmung 2.0 °C",
        "gwl2_5": "Erwärmung 2.5 °C",
        "gwl3_0": "Erwärmung 3.0 °C",
    }

    return [
        {"label": scenario_labels.get(s, s), "value": s}
        for s in scenarios
    ]


def get_default_scenario(df: pd.DataFrame, dataset_type: str) -> str | None:
    options = get_scenario_options(df, dataset_type)
    if not options:
        return None

    preferred = {
        "historical": "observed",
        "future": "gwl2_0",
    }

    preferred_value = preferred.get(dataset_type)
    available = [opt["value"] for opt in options]

    if preferred_value in available:
        return preferred_value

    return options[0]["value"]


def filter_profile_comparison(
    df: pd.DataFrame,
    place_id: str,
    metric: str,
    future_scenario: str,
    future_scenario_2: str | None = None,
) -> pd.DataFrame:

    subset = df[
        (df["place_id"] == str(place_id))
        & (df["metric"] == metric)
    ].copy()

    if subset.empty:
        return subset

    # Basis: Vergangenheit
    mask = (
        (subset["dataset_type"] == "historical")
        & (subset["scenario"] == "observed")
    )

    # Zukunft 1
    mask |= (
        (subset["dataset_type"] == "future")
        & (subset["scenario"] == future_scenario)
    )

    # Zukunft 2 optional
    if future_scenario_2:
        mask |= (
            (subset["dataset_type"] == "future")
            & (subset["scenario"] == future_scenario_2)
        )

    subset = subset[mask].copy()

    scenario_labels = {
        "observed": "Vergangenheit",
        "ref": "Referenz",
        "gwl1_5": "GWL 1.5",
        "gwl2_0": "GWL 2.0",
        "gwl2_5": "GWL 2.5",
        "gwl3_0": "GWL 3.0",
    }

    def build_label(row):
        if row["dataset_type"] == "historical":
            return "Vergangenheit"
        else:
            label = scenario_labels.get(row["scenario"], row["scenario"])
            return f"Zukunft ({label})"

    subset["comparison_label"] = subset.apply(build_label, axis=1)

    subset = subset.sort_values(["comparison_label", "month"])

    return subset[
        [
            "month",
            "value",
            "place_name",
            "metric",
            "dataset_type",
            "scenario",
            "comparison_label",
        ]
    ]

def month_number_to_label(month: int) -> str:
    month_labels = {
        1: "Januar",
        2: "Februar",
        3: "März",
        4: "April",
        5: "Mai",
        6: "Juni",
        7: "Juli",
        8: "August",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Dezember",
    }
    return month_labels.get(int(month), str(month))


def _get_active_months(values_by_month: dict[float, float], threshold: float = 0.01) -> list[int]:
    active = []
    for month, value in values_by_month.items():
        if value is not None and value > threshold:
            active.append(int(month))
    return sorted(active)


def month_number_to_label(month: int) -> str:
    month_labels = {
        1: "Januar",
        2: "Februar",
        3: "März",
        4: "April",
        5: "Mai",
        6: "Juni",
        7: "Juli",
        8: "August",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Dezember",
    }
    return month_labels.get(int(month), str(month))


def _get_active_months(values_by_month: dict, threshold: float = 0.01) -> list[int]:
    active = []
    for month, value in values_by_month.items():
        if value is not None and value > threshold:
            active.append(int(month))
    return sorted(active)


def _scenario_display_label(scenario: str) -> str:
    scenario_labels = {
        "observed": "Vergangenheit",
        "ref": "Referenz",
        "gwl1_5": "GWL 1.5",
        "gwl2_0": "GWL 2.0",
        "gwl2_5": "GWL 2.5",
        "gwl3_0": "GWL 3.0",
    }
    return scenario_labels.get(scenario, scenario)


def build_profile_interpretation(plot_df: pd.DataFrame, metric: str) -> str:
    if plot_df.empty:
        return "Für diese Auswahl ist keine Interpretation verfügbar."

    hist_df = plot_df[
        (plot_df["dataset_type"] == "historical")
        & (plot_df["scenario"] == "observed")
    ].copy()

    future_df = plot_df[plot_df["dataset_type"] == "future"].copy()

    if hist_df.empty or future_df.empty:
        return "Für diese Auswahl ist kein vollständiger Vergleich zwischen Vergangenheit und Zukunft verfügbar."

    future_scenarios = list(future_df["scenario"].dropna().unique())
    future_scenarios = sorted(future_scenarios)

    hist_values = hist_df.set_index("month")["value"].to_dict()

    scenario_value_dicts = {}
    for scenario in future_scenarios:
        scenario_df = future_df[future_df["scenario"] == scenario].copy()
        scenario_value_dicts[scenario] = scenario_df.set_index("month")["value"].to_dict()

    if not scenario_value_dicts:
        return "Für diese Auswahl sind keine Zukunftsdaten verfügbar."

    primary_scenario = future_scenarios[0]
    primary_values = scenario_value_dicts[primary_scenario]

    common_months = sorted(set(hist_values.keys()) & set(primary_values.keys()))
    if not common_months:
        return "Für diese Auswahl ist keine monatliche Vergleichsbasis vorhanden."

    diffs_primary = {
        int(month): float(primary_values[month]) - float(hist_values[month])
        for month in common_months
    }

    positive_months = [m for m, d in diffs_primary.items() if d > 0.0001]
    negative_months = [m for m, d in diffs_primary.items() if d < -0.0001]

    max_increase_month = max(diffs_primary, key=diffs_primary.get)
    max_increase_value = diffs_primary[max_increase_month]

    hist_total = float(sum(hist_values[m] for m in common_months))
    primary_total = float(sum(primary_values[m] for m in common_months))
    total_diff = primary_total - hist_total

    hist_active = _get_active_months(hist_values, threshold=0.01)
    primary_active = _get_active_months(primary_values, threshold=0.01)

    sentences = []

    # Grundinterpretation für das erste Zukunftsszenario
    if metric == "hot_days_mean":
        if total_diff > 0.01:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} nehmen die Hitzetage gegenüber der Vergangenheit deutlich zu."
            )
        elif total_diff > 0:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} steigen die Hitzetage gegenüber der Vergangenheit leicht an."
            )
        elif total_diff < -0.01:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} gehen die Hitzetage gegenüber der Vergangenheit zurück."
            )
        else:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} bleiben die Hitzetage insgesamt auf ähnlichem Niveau."
            )

        if max_increase_value > 0.01:
            sentences.append(
                f"Die stärkste Zunahme zeigt sich im {month_number_to_label(max_increase_month)}."
            )

        if len(positive_months) >= 1:
            if len(positive_months) <= 3:
                months_text = ", ".join(month_number_to_label(m) for m in positive_months)
                sentences.append(
                    f"Höhere Werte treten vor allem in {months_text} auf."
                )
            else:
                first_month = month_number_to_label(min(positive_months))
                last_month = month_number_to_label(max(positive_months))
                sentences.append(
                    f"Die Phase mit erhöhten Hitzetagen reicht ungefähr von {first_month} bis {last_month}."
                )

        if hist_active and primary_active:
            hist_start = min(hist_active)
            primary_start = min(primary_active)
            hist_end = max(hist_active)
            primary_end = max(primary_active)

            if primary_start < hist_start:
                sentences.append(
                    f"Die Saison beginnt früher, nämlich bereits im {month_number_to_label(primary_start)} statt im {month_number_to_label(hist_start)}."
                )
            if primary_end > hist_end:
                sentences.append(
                    f"Sie reicht zudem länger ins Jahr, nämlich bis {month_number_to_label(primary_end)} statt bis {month_number_to_label(hist_end)}."
                )

    elif metric == "temperature_mean":
        avg_diff = total_diff / len(common_months)

        if avg_diff > 1.0:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} liegen die monatlichen Mitteltemperaturen klar über den beobachteten Werten der Vergangenheit."
            )
        elif avg_diff > 0.2:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} liegen die monatlichen Mitteltemperaturen meist über den beobachteten Werten der Vergangenheit."
            )
        elif avg_diff < -0.2:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} liegen die monatlichen Mitteltemperaturen meist unter den beobachteten Werten der Vergangenheit."
            )
        else:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} bleiben die monatlichen Mitteltemperaturen insgesamt nahe bei den beobachteten Werten der Vergangenheit."
            )

        if max_increase_value > 0.1:
            sentences.append(
                f"Der stärkste Unterschied zeigt sich im {month_number_to_label(max_increase_month)}."
            )

        if len(positive_months) >= 10:
            sentences.append(
                "Die Erwärmung zeigt sich über fast das ganze Jahr hinweg."
            )
        elif len(positive_months) >= 6:
            first_month = month_number_to_label(min(positive_months))
            last_month = month_number_to_label(max(positive_months))
            sentences.append(
                f"Besonders betroffen ist der Zeitraum von {first_month} bis {last_month}."
            )
        elif len(positive_months) > 0:
            months_text = ", ".join(month_number_to_label(m) for m in positive_months)
            sentences.append(
                f"Höhere Temperaturen treten vor allem in {months_text} auf."
            )

        if negative_months and len(positive_months) > len(negative_months):
            sentences.append(
                "Einzelne Monate weichen davon ab, insgesamt überwiegt aber die Erwärmung."
            )

    else:
        if total_diff > 0:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} liegen die Werte insgesamt höher als in der Vergangenheit."
            )
        elif total_diff < 0:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} liegen die Werte insgesamt tiefer als in der Vergangenheit."
            )
        else:
            sentences.append(
                f"Im Szenario {_scenario_display_label(primary_scenario)} bleiben die Werte insgesamt nahe bei der Vergangenheit."
            )

        if max_increase_value > 0:
            sentences.append(
                f"Der grösste Unterschied zeigt sich im {month_number_to_label(max_increase_month)}."
            )

    # Zusätzliche Interpretation bei zwei Zukunftsszenarien
    if len(future_scenarios) >= 2:
        scenario_a = future_scenarios[0]
        scenario_b = future_scenarios[1]

        values_a = scenario_value_dicts[scenario_a]
        values_b = scenario_value_dicts[scenario_b]

        common_future_months = sorted(set(values_a.keys()) & set(values_b.keys()))
        if common_future_months:
            future_diffs = {
                int(month): abs(float(values_b[month]) - float(values_a[month]))
                for month in common_future_months
            }

            avg_future_diff = sum(future_diffs.values()) / len(future_diffs)
            max_future_diff_month = max(future_diffs, key=future_diffs.get)
            max_future_diff_value = future_diffs[max_future_diff_month]

            label_a = _scenario_display_label(scenario_a)
            label_b = _scenario_display_label(scenario_b)

            if metric == "hot_days_mean":
                if avg_future_diff < 0.01:
                    sentences.append(
                        f"Die beiden Zukunftsszenarien {label_a} und {label_b} verlaufen sehr ähnlich."
                    )
                elif avg_future_diff < 0.04:
                    sentences.append(
                        f"Zwischen den Zukunftsszenarien {label_a} und {label_b} zeigen sich moderate Unterschiede."
                    )
                else:
                    sentences.append(
                        f"Zwischen den Zukunftsszenarien {label_a} und {label_b} zeigen sich deutliche Unterschiede."
                    )

                if max_future_diff_value > 0.01:
                    sentences.append(
                        f"Am stärksten gehen die Szenarien im {month_number_to_label(max_future_diff_month)} auseinander."
                    )

            elif metric == "temperature_mean":
                if avg_future_diff < 0.3:
                    sentences.append(
                        f"Die beiden Zukunftsszenarien {label_a} und {label_b} liegen insgesamt nahe beieinander."
                    )
                elif avg_future_diff < 1.0:
                    sentences.append(
                        f"Zwischen den Zukunftsszenarien {label_a} und {label_b} zeigen sich spürbare Unterschiede."
                    )
                else:
                    sentences.append(
                        f"Zwischen den Zukunftsszenarien {label_a} und {label_b} zeigen sich über das Jahr deutliche Unterschiede."
                    )

                if max_future_diff_value > 0.2:
                    sentences.append(
                        f"Am grössten ist der Abstand im {month_number_to_label(max_future_diff_month)}."
                    )

            else:
                if avg_future_diff > 0:
                    sentences.append(
                        f"Die beiden Zukunftsszenarien unterscheiden sich in ihrer Ausprägung."
                    )

    return " ".join(sentences)
