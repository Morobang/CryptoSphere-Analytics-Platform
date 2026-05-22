# Data Dictionary

All fields returned by the CoinMarketCap `/v1/cryptocurrency/listings/latest` endpoint, as they land in the Bronze layer and CSV files.

---

## Table: `bronze.cryptocurrency_data` / `cryptocurrency_data.csv`

One row = one coin at one collection timestamp.

| Column | Type | Description | Example |
|---|---|---|---|
| `id` | int | CoinMarketCap internal coin ID | `1` (BTC), `1027` (ETH) |
| `name` | str | Full coin name | `Bitcoin` |
| `symbol` | str | Ticker symbol | `BTC` |
| `slug` | str | URL-safe name | `bitcoin` |
| `num_market_pairs` | int | Number of active trading pairs | `12415` |
| `date_added` | timestamp | Date the coin was listed on CMC | `2010-07-13T00:00:00.000Z` |
| `tags` | list[str] | Classification tags | `['mineable', 'pow', 'sha-256']` |
| `max_supply` | float | Hard cap on total coins (null if infinite) | `21000000.0` for BTC |
| `circulating_supply` | float | Coins currently in public circulation | `19932790.0` |
| `total_supply` | float | Total coins minus burned/locked | `19932790.0` |
| `infinite_supply` | bool | True if there is no supply cap | `False` for BTC, `True` for ETH |
| `platform` | object | Chain info for tokens (null for native coins) | `{'id': 1027, 'name': 'Ethereum', ...}` |
| `platform_id` | float | Chain's CMC ID | `1027.0` |
| `platform_name` | str | Chain name | `Ethereum` |
| `platform_symbol` | str | Chain ticker | `ETH` |
| `platform_slug` | str | Chain slug | `ethereum` |
| `platform_token_address` | str | Contract address for ERC-20 etc. | `0xdac17f958d2...` |
| `cmc_rank` | int | Current market cap rank | `1` |
| `self_reported_circulating_supply` | float | Supply reported by team (may differ from CMC) | null for BTC |
| `self_reported_market_cap` | float | Market cap using self-reported supply | null for BTC |
| `tvl_ratio` | float | Total value locked / market cap ratio (DeFi) | null for most |
| `last_updated` | timestamp | When CMC last updated this coin's data | `2025-10-12T08:03:00.000Z` |
| `collection_timestamp` | timestamp | When we fetched this record | `2025-10-12T10:23:18` |

### Price and market data (all in USD)

| Column | Type | Description | Example |
|---|---|---|---|
| `quote_USD_price` | float | Current price | `111651.945` |
| `quote_USD_volume_24h` | float | 24-hour trading volume | `8.055841e+10` |
| `quote_USD_volume_change_24h` | float | % change in 24h volume vs previous 24h | `-56.85` |
| `quote_USD_percent_change_1h` | float | Price % change over last 1 hour | `-0.127` |
| `quote_USD_percent_change_24h` | float | Price % change over last 24 hours | `1.067` |
| `quote_USD_percent_change_7d` | float | Price % change over last 7 days | `-10.455` |
| `quote_USD_percent_change_30d` | float | Price % change over last 30 days | `-3.003` |
| `quote_USD_percent_change_60d` | float | Price % change over last 60 days | `-6.626` |
| `quote_USD_percent_change_90d` | float | Price % change over last 90 days | `-8.929` |
| `quote_USD_market_cap` | float | Price × circulating supply | `2.225535e+12` |
| `quote_USD_market_cap_dominance` | float | This coin's % of total crypto market cap | `59.6446` (BTC dominance) |
| `quote_USD_fully_diluted_market_cap` | float | Price × max supply (worst case dilution) | `2.344691e+12` |
| `quote_USD_tvl` | float | USD value of TVL (DeFi only) | null for most |
| `quote_USD_last_updated` | timestamp | Timestamp of price data | `2025-10-12T08:03:00.000Z` |

---

## Table: `bronze.api_response_status` / `api_status.csv`

One row = one API call.

| Column | Type | Description | Example |
|---|---|---|---|
| `timestamp` | timestamp | Server-side time of the API response | `2025-10-12T07:03:01.000Z` |
| `error_code` | int | 0 = success, non-zero = error | `0` |
| `error_message` | str | Null on success, error text otherwise | `null` |
| `elapsed` | int | API server processing time in milliseconds | `247` |
| `credit_count` | int | API credits consumed by this call | `1` |
| `notice` | str | Optional API message | `null` |
| `total_count` | int | Total number of coins tracked by CMC | `9517` |
| `collection_timestamp` | timestamp | When we made this call | `2025-10-12T10:23:18` |

---

## Silver layer additions

The Silver ETL adds these computed columns on top of Bronze:

| Column | Derived from | Description |
|---|---|---|
| `log_return_1h` | `quote_USD_percent_change_1h` | Log return: `ln(1 + pct/100)` |
| `log_return_24h` | `quote_USD_percent_change_24h` | Log return over 24h |
| `is_stablecoin` | `tags` | True if 'stablecoin' in tags |
| `supply_utilization` | `circulating_supply / max_supply` | How much of max supply is circulating |
| `volume_to_mcap_ratio` | `quote_USD_volume_24h / quote_USD_market_cap` | Liquidity proxy |

---

## Gold layer additions

The Gold ETL aggregates across time windows and adds technical context:

| Column | Window | Description |
|---|---|---|
| `price_sma_7` | 7 snapshots | Simple moving average of price |
| `price_sma_30` | 30 snapshots | Simple moving average over ~5 days |
| `realized_volatility_7` | 7 snapshots | Rolling std dev of log returns |
| `realized_volatility_30` | 30 snapshots | Rolling std dev of log returns |
| `rsi_14` | 14 snapshots | Relative Strength Index |
| `btc_correlation_30` | 30 snapshots | Rolling Pearson correlation with BTC price |

---

## Notes on data quality

- **Stablecoins**: USDT and USDC will have near-zero price change. Filter them out for most analyses unless you're looking at supply dynamics.
- **`platform` field**: Stored as a stringified dict in CSV. Parse with `ast.literal_eval()` if needed.
- **`tags` field**: Same — stored as a stringified list.
- **`self_reported_*` fields**: Often null. Don't depend on them for analysis.
- **Timestamps**: API timestamps are UTC. `collection_timestamp` is local machine time. Align them before joining.