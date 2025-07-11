from pathlib import Path
from typing import Dict

import polars as pl


def load_llm_data(file_path: str) -> pl.DataFrame:
    """Load LLM usage data from CSV file with proper data types."""
    return pl.read_csv(
        file_path,
        try_parse_dates=True,
        schema_overrides={
            "timestamp": pl.Datetime,
            "input_tokens": pl.Int64,
            "output_tokens": pl.Int64,
            "total_tokens": pl.Int64,
            "latency_ms": pl.Float64,
            "input_cost": pl.Float64,
            "output_cost": pl.Float64,
            "total_cost": pl.Float64,
        },
    )


def get_basic_stats(df: pl.DataFrame) -> Dict[str, any]:
    """Get basic statistics about the dataset."""
    return {
        "total_requests": len(df),
        "date_range": (df["timestamp"].min(), df["timestamp"].max()),
        "total_cost": df["total_cost"].sum(),
        "total_tokens": df["total_tokens"].sum(),
        "unique_models": df["model"].n_unique(),
        "unique_functions": df["function_name"].n_unique(),
    }


def analyze_by_model(df: pl.DataFrame) -> pl.DataFrame:
    """Analyze usage and costs by model."""
    return (
        df.group_by("model")
        .agg(
            [
                pl.len().alias("request_count"),
                pl.col("total_cost").sum().alias("total_cost"),
                pl.col("input_tokens").sum().alias("total_input_tokens"),
                pl.col("output_tokens").sum().alias("total_output_tokens"),
                pl.col("total_tokens").sum().alias("total_tokens"),
                pl.col("latency_ms").mean().alias("avg_latency_ms"),
                pl.col("latency_ms").median().alias("median_latency_ms"),
                pl.col("total_cost").mean().alias("avg_cost_per_request"),
            ]
        )
        .with_columns(
            [
                (pl.col("total_cost") / pl.col("total_tokens") * 1000).alias("cost_per_1k_tokens"),
                (pl.col("total_tokens") / (pl.col("avg_latency_ms") / 1000)).alias("tokens_per_second"),
            ]
        )
        .sort("total_cost", descending=True)
    )


def analyze_by_function(df: pl.DataFrame) -> pl.DataFrame:
    """Analyze usage by function name."""
    return (
        df.group_by("function_name")
        .agg(
            [
                pl.len().alias("request_count"),
                pl.col("total_cost").sum().alias("total_cost"),
                pl.col("total_tokens").sum().alias("total_tokens"),
                pl.col("latency_ms").mean().alias("avg_latency_ms"),
            ]
        )
        .sort("request_count", descending=True)
    )


def analyze_time_patterns(df: pl.DataFrame) -> pl.DataFrame:
    """Analyze usage patterns over time."""
    return (
        df.with_columns(
            [
                pl.col("timestamp").dt.date().alias("date"),
                pl.col("timestamp").dt.hour().alias("hour"),
            ]
        )
        .group_by("date")
        .agg(
            [
                pl.len().alias("requests_per_day"),
                pl.col("total_cost").sum().alias("cost_per_day"),
                pl.col("total_tokens").sum().alias("tokens_per_day"),
            ]
        )
        .sort("date")
    )


def find_expensive_requests(df: pl.DataFrame, top_n: int = 10) -> pl.DataFrame:
    """Find the most expensive requests."""
    return (
        df.select(
            ["timestamp", "model", "function_name", "total_cost", "total_tokens", "latency_ms", "input_content_preview"]
        )
        .sort("total_cost", descending=True)
        .head(top_n)
    )


def analyze_efficiency_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """Calculate efficiency metrics for each model."""
    return (
        df.group_by("model")
        .agg(
            [
                pl.col("total_tokens").sum().alias("total_tokens"),
                pl.col("total_cost").sum().alias("total_cost"),
                pl.col("latency_ms").mean().alias("avg_latency"),
                pl.len().alias("request_count"),
            ]
        )
        .with_columns(
            [
                (pl.col("total_cost") / pl.col("total_tokens") * 1000).alias("cost_per_1k_tokens"),
                (pl.col("total_tokens") / pl.col("avg_latency") * 1000).alias("tokens_per_second"),
                (pl.col("total_cost") / pl.col("avg_latency") * 1000).alias("cost_per_second"),
            ]
        )
        .sort("cost_per_1k_tokens")
    )


def detect_outliers(df: pl.DataFrame) -> Dict[str, pl.DataFrame]:
    """Detect outliers in key metrics."""
    outliers = {}

    # High latency requests (> 95th percentile)
    latency_threshold = df["latency_ms"].quantile(0.95)
    outliers["high_latency"] = df.filter(pl.col("latency_ms") > latency_threshold)

    # High cost requests (> 95th percentile)
    cost_threshold = df["total_cost"].quantile(0.95)
    outliers["high_cost"] = df.filter(pl.col("total_cost") > cost_threshold)

    # High token usage (> 95th percentile)
    token_threshold = df["total_tokens"].quantile(0.95)
    outliers["high_tokens"] = df.filter(pl.col("total_tokens") > token_threshold)

    return outliers


def generate_summary_report(df: pl.DataFrame) -> str:
    """Generate a comprehensive summary report."""
    stats = get_basic_stats(df)
    model_analysis = analyze_by_model(df)

    report = f"""
LLM Usage Analysis Report
========================

Basic Statistics:
- Total Requests: {stats["total_requests"]:,}
- Date Range: {stats["date_range"][0]} to {stats["date_range"][1]}
- Total Cost: ${stats["total_cost"]:.4f}
- Total Tokens: {stats["total_tokens"]:,}
- Unique Models: {stats["unique_models"]}
- Unique Functions: {stats["unique_functions"]}

Top Models by Cost:
{model_analysis.head(5)}

Most Efficient Models (Cost per 1K tokens):
{model_analysis.sort("cost_per_1k_tokens").head(3).select(["model", "cost_per_1k_tokens", "avg_latency_ms"])}

Fastest Models (Tokens per second):
{model_analysis.sort("tokens_per_second", descending=True).head(3).select(["model", "tokens_per_second", "avg_latency_ms"])}
"""
    return report


def main():
    """Main analysis function."""
    file_path = "llm_usage_log.csv"

    if not Path(file_path).exists():
        print(f"Error: File {file_path} not found")
        return

    try:
        # Load data
        print("Loading LLM usage data...")
        df = load_llm_data(file_path)
        print(f"Loaded {len(df)} records")

        # Check for any null values in critical columns
        null_counts = df.null_count()
        if null_counts.sum_horizontal().item() > 0:
            print("Warning: Found null values in data:")
            print(null_counts)

        # Generate analyses
        print("\nGenerating analysis...")

        print("\n" + "=" * 50)
        print(generate_summary_report(df))

        print("\n" + "=" * 50)
        print("DETAILED ANALYSIS BY MODEL:")
        print(analyze_by_model(df))

        print("\n" + "=" * 50)
        print("ANALYSIS BY FUNCTION:")
        print(analyze_by_function(df))

        print("\n" + "=" * 50)
        print("TIME PATTERNS (Recent 10 days):")
        print(analyze_time_patterns(df).tail(10))

        print("\n" + "=" * 50)
        print("TOP 5 MOST EXPENSIVE REQUESTS:")
        expensive = find_expensive_requests(df, 5)
        print(expensive)

        print("\n" + "=" * 50)
        print("EFFICIENCY METRICS:")
        print(analyze_efficiency_metrics(df))

        # Detect outliers
        outliers = detect_outliers(df)
        print("\n" + "=" * 50)
        print("OUTLIER DETECTION:")
        print(f"High latency requests: {len(outliers['high_latency'])}")
        print(f"High cost requests: {len(outliers['high_cost'])}")
        print(f"High token requests: {len(outliers['high_tokens'])}")

        if len(outliers["high_cost"]) > 0:
            print("\nTop 3 highest cost outliers:")
            print(
                outliers["high_cost"].head(3).select(["timestamp", "model", "total_cost", "total_tokens", "latency_ms"])
            )

    except Exception as e:
        print(f"Error analyzing data: {e}")
        return


if __name__ == "__main__":
    main()
