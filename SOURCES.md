# Sources, definitions and provenance

The data were retrieved on **21 November 2026**. The analysis covers **2011–2024**. The project uses an intentional historical endpoint so the accompanying text and results refer to a fixed dataset.

## Data

1. **UNHCR Refugee Population Statistics Database.** The frozen response contains 1,547 origin–destination–year records for Syrian origin across 2011–2024, including records for other population categories. `analysis.py` uses the `refugees` and `asylum_seekers` fields, excludes Syria as its own destination, and checks completeness. The refugee category includes people in refugee-like situations and relevant temporary protection under UNHCR's definitions. [API documentation](https://api.unhcr.org/docs/refugee-statistics.html), [statistical definitions](https://www.unhcr.org/refugee-statistics/methodology/definition), [data content](https://www.unhcr.org/refugee-statistics/methodology/data-content), [common stock-and-flow mistakes](https://www.unhcr.org/refugee-statistics/insights/explainers/common-mistakes-forcibly-displaced-data.html).

2. **World Bank, World Development Indicators, `SP.POP.TOTL`.** The preserved response contains 112 population estimates for the eight selected hosts. It reports a source update of 11 November 2026. These are midyear de facto resident-population estimates, rather than citizen counts. [Indicator page](https://data.worldbank.org/indicator/SP.POP.TOTL), [metadata](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SP.POP.TOTL).

3. **UNHCR Lebanon, registration guidance.** New registration of Syrian nationals was suspended on 5 May 2015. This affects the interpretation of recorded counts. [Registration guidance](https://help.unhcr.org/lebanon/en/welcome/registration/).

## Download requests

The exact request URLs, retrieval times, byte counts and SHA-256 digests appear in [data-sources.json](data-sources.json). The two accompanying JSON files retain the provider responses unchanged. No person-level information is included.

```text
https://api.unhcr.org/population/v1/population/?coo=SYR&coa_all=true&yearFrom=2011&yearTo=2024&limit=10000&cf_type=ISO

https://api.worldbank.org/v2/country/LBN;JOR;TUR;IRQ;EGY;DEU;SWE;CAN/indicator/SP.POP.TOTL?date=2011:2024&format=json&per_page=20000
```

## Scope and output dictionary

Country rankings compare Türkiye, Lebanon, Jordan, Iraq, Egypt, Germany, Sweden and Canada. Global totals and concentration include all reported destinations outside Syria. The five regional hosts are Türkiye, Lebanon, Jordan, Iraq and Egypt. Egypt is included as a regional host, although it does not share a land border with Syria.

| File | Contents |
| --- | --- |
| `country-year-panel.csv` | The 112 selected country-year observations, source counts, population, refugee ratio, and combined refugee-plus-asylum-seeker ratio. |
| `hosting-2024.csv` | The eight-country endpoint comparison, including within-group count and ratio ranks. |
| `annual-metrics.csv` | Global and regional counts, regional share, HHI, reciprocal HHI and number of destinations reporting a positive refugee stock. |
| `hosting-comparison.png` | Independently sorted absolute-count and population-ratio comparisons for 2024. |
| `hosting-concentration.png` | Regional share and global HHI for each year. |

`per_1000` equals 1,000 times refugees divided by resident population. `combined_per_1000` adds pending asylum-seekers to the numerator. `hhi` uses shares as fractions between zero and one. `effective_destinations` is the reciprocal of HHI. Rankings are descending, with rank one assigned to the highest value. No absent count is silently converted to zero.

## Attribution and reuse

UNHCR data are credited as **UNHCR Refugee Population Statistics Database**, under its [CC BY 4.0 licence and supplemental dataset terms](https://www.unhcr.org/terms-use-datasets). World Bank population data are credited to **World Bank, World Development Indicators**, under [CC BY 4.0 and its additional terms](https://datacatalog.worldbank.org/public-licenses#cc-by). The organisations retain their respective data rights. The derived tables and figures involve filtering, joining, ratio calculation and aggregation by this project. Neither organisation endorses this analysis or translation.

The English note is an original text for this repository, and the Arabic note translates that text. Preparation, translation and coding used AI assistance. Source links allow readers to inspect the original data and methods.
