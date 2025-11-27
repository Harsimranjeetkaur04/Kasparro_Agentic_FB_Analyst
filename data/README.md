# Data Documentation

This directory contains the dataset used by the Kasparro Agentic Facebook Performance Analyst.

## Dataset Overview

[cite_start]The file `sample_fb_ads.csv` is a **synthetic dataset** representing Facebook Ads performance for an eCommerce brand. It combines quantitative performance metrics (Spend, ROAS, CTR) with qualitative creative data (Creative Message, Type).

## Schema

The dataset includes the following columns used by the **Data Agent** and **Insight Agent**:

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `date` | Date | Daily aggregation date (YYYY-MM-DD). |
| `campaign_name` | String | Name of the high-level campaign. |
| `adset_name` | String | Name of the specific ad set. |
| `creative_type` | String | Format of the ad (e.g., Image, Video, Carousel). |
| `creative_message` | String | **Key Input**: The actual ad copy/headline used. Used for generating new creatives. |
| `audience_type` | String | Target audience (e.g., Broad, Interest-based, Lookalike). |
| `platform` | String | Placement platform (e.g., Facebook, Instagram). |
| `country` | String | Target country code (e.g., US, UK). |
| `spend` | Float | Total amount spent in USD. |
| `impressions` | Integer | Total number of times the ad was shown. |
| `clicks` | Integer | Total number of clicks. |
| `ctr` | Float | Click-Through Rate (Clicks / Impressions). |
| `purchases` | Integer | Total conversion events. |
| `revenue` | Float | Total value generated in USD. |
| `roas` | Float | Return on Ad Spend (Revenue / Spend). |

## Usage in System

1.  **Ingestion**: The `Data Agent` loads this CSV to perform aggregations (e.g., "Sum spend by campaign").
2.  **Analysis**: The `Insight Agent` looks for correlations between `creative_message` and low `roas`.
3.  [cite_start]**Creative Generation**: The `Creative Improvement Generator` uses the `creative_message` column as few-shot examples to generate new, better copy for underperforming ads[cite: 8].

## Configuration

To switch between the sample data and a full dataset, modify `config/config.yaml`:

```yaml
use_sample_data: true
# Set to false to load from a different path specified in config