# Emission factors and calculation notes

This file lists the factors EcoMeter uses and explains where they come from. Some values are taken from published studies or guidance; others are assumptions used to make the app's estimates possible when a directly applicable value is not available. I label those assumptions rather than presenting them as measured facts.

EcoMeter calculates each activity as:

> **Emissions (kg CO₂e) = activity quantity × emission factor**

All results in the app are reported in kg CO₂e. Factors are not universally applicable: geography, year, product, and calculation boundary can all affect the result.

## Electricity

| Item | Value |
|---|---|
| Activity | Indian grid electricity (2026) |
| Factor | 0.70 kg CO₂e/kWh |
| Status | Illustrative project assumption |
| Reference | Central Electricity Authority (CEA), *CO₂ Baseline Database for the Indian Power Sector*, Version 22.0, August 2026 |
| Link | [CEA baseline database](https://cea.nic.in/cdm-co2-baseline-view/) |

The 0.70 value is an assumption for this project. It is not a verified CEA-published CO₂e factor. Electricity emissions are calculated as:

> **Electricity emissions = consumption in kWh × 0.70**

The app uses the 2026 electricity entry only.

## Transportation

EcoMeter uses passenger-kilometres: the distance travelled by the passenger is multiplied by the factor for the selected mode.

| Mode | Factor |
|---|---:|
| Private car | 0.170 kg CO₂e/passenger-km |
| Two-wheeler | 0.040 kg CO₂e/passenger-km |
| Bus | 0.030 kg CO₂e/passenger-km |
| Delhi Metro | 0.035 kg CO₂e/passenger-km |
| Walking | 0 kg CO₂e/km direct operational emissions |
| Cycling | 0 kg CO₂e/km direct operational emissions |

The motorized-mode values are illustrative project assumptions for comparing personal travel. They are not verified measurements for a particular vehicle or operator. Delhi Metro uses one passenger-kilometre method.

> **Transport emissions = passenger distance in km × mode factor**

For example, a 20 km Delhi Metro trip is estimated at `20 × 0.035 = 0.70 kg CO₂e`.

Walking and cycling have zero **direct operational** emissions in this calculation. Vehicle manufacturing, infrastructure, maintenance, and other indirect emissions are outside that boundary.

References:

- TERI, [*Emission Saving Made by a Passenger by Choosing to Travel by Delhi Metro*](https://teriin.org/sites/default/transport/Per_passenger_emission_in_Delhi_Different_Modes.pdf)
- International Transport Forum (2023), [*Life-cycle Assessment of Passenger Transport: An Indian Case Study*](https://doi.org/10.1787/2d11e416-en)

## Food

Food estimates are daily diet averages, not estimates for individual meals or ingredients.

### Indian vegetarian estimate

Pathak, H., Jain, N., Bhatia, A., Patel, J., and Aggarwal, P. K. (2010), *Carbon Footprints of Indian Food Items*, *Agriculture, Ecosystems & Environment*, Volume 139, pages 66–73.

| Diet | Factor |
|---|---:|
| Balanced Indian vegetarian diet | 0.7237 kg CO₂e/person/day |

The study also reports that the mutton meal in its comparison had approximately 1.8 times the emissions of the vegetarian meal.

Reference: [https://doi.org/10.1016/j.agee.2010.07.002](https://doi.org/10.1016/j.agee.2010.07.002)

### Vegan, vegetarian, and non-vegetarian estimates

Rosi, A. et al. (2017), *Environmental Impact of Omnivorous, Ovo-Lacto-Vegetarian, and Vegan Diet*, *Scientific Reports*, Volume 7, Article 6105. The study is based on seven-day dietary records from 153 Italian adults.

| Diet | Factor |
|---|---:|
| Vegan | 2.3361 kg CO₂e/person/day |
| Vegetarian (ovo-lacto) | 2.5983 kg CO₂e/person/day |
| Non-vegetarian (omnivorous) | 3.9593 kg CO₂e/person/day |

> **Food emissions = daily diet factor × number of days**

For example, the Italian vegetarian estimate for 30 days is `2.5983 × 30 = 77.949 kg CO₂e`.

Reference: [https://doi.org/10.1038/s41598-017-06466-8](https://doi.org/10.1038/s41598-017-06466-8)

The Indian and Italian figures describe different populations and dietary patterns, so they should not be treated as interchangeable.

## Waste

Waste emissions depend on both the material and how it is handled. Quantities are entered in kilograms.

### Organic waste

Source: Ministry of Environment, Forest and Climate Change (MoEFCC), Government of India, *Low Carbon Lifestyles: Right Choices for Our Planet* (November 2016).

| Treatment | Factor |
|---|---:|
| Composting | 0.32 kg CO₂e/kg |
| Landfilling | 1.29 kg CO₂e/kg |

Reference: [MoEFCC publication](https://moef.gov.in/uploads/2019/10/LOW-CARBON-LIFESTYLES.pdf)

### Inorganic waste

For these materials, EcoMeter uses simplified assumptions rather than a single verified factor applicable to all inorganic waste.

| Material | Treatment | Assumed factor |
|---|---|---:|
| Plastic | Landfilling | 0.02 kg CO₂e/kg |
| Glass | Landfilling | 0.01 kg CO₂e/kg |
| Metals | Landfilling | 0.01 kg CO₂e/kg |
| Other inorganic waste | Landfilling | 0.02 kg CO₂e/kg |

### Electronic waste

The mixed e-waste/IT factor comes from a range supplied for this project. EcoMeter uses the midpoint as one factor:

| Material | Treatment | Factor used |
|---|---|---:|
| Mixed e-waste / IT | Specialised recycling | 0.125 kg CO₂e/kg |

The supplied range is 0.05–0.20 kg CO₂e/kg. It describes dismantling, sorting, and toxic-material extraction. The midpoint is a project assumption, not an independently verified or universal recycling factor.

> **Waste emissions = waste quantity in kg × factor for the material and treatment**

Actual results can differ with waste composition, treatment conditions, landfill operations, and disposal practices.

## Shopping

Shopping estimates represent approximate emissions associated with making the purchased products. They are not universal values for every product.

### Electronics

Source: European Commission Joint Research Centre (JRC).

| Product | Estimate |
|---|---:|
| Smartphone | 55 ± 12 kg CO₂e/item |
| Tablet | 113 kg CO₂e/item |
| Laptop | 200 kg CO₂e/item |

Reference: [JRC report](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC129957/JRC129957_01.pdf)

### Other products

| Product | Assumed estimate |
|---|---:|
| Clothing item | 20 kg CO₂e/item |
| Other consumer product | 5 kg CO₂e/item |

These are simplified defaults, not life-cycle assessments of specific products. Where available, product-specific data is preferable.

> **Shopping emissions = sum of (number of items × factor for each product)**

## Overall calculation

EcoMeter adds the category estimates to produce a total:

> **Total = electricity + transportation + food + waste + shopping**

The app's factors and results use kg CO₂e. The categories do not all use the same system boundary: for example, walking and cycling include direct operational emissions only, while product estimates are embodied-emission estimates. The total is an educational estimate, not an audited greenhouse-gas inventory.

## Limitations and data status

- The electricity and motorized transport factors are illustrative assumptions.
- The Indian and Italian diet estimates are population-level daily averages and may not describe an individual's actual diet.
- Inorganic waste values and clothing/other-product values are simplified assumptions.
- The e-waste value is the midpoint of the range supplied for the project.
- Published product and waste estimates may depend on their original study's boundary and context.
- Actual emissions vary with location, consumption, manufacturing, transport, product lifetime, and waste treatment.
- Factors should be reviewed and updated when better, geographically relevant data is available.

In the app, factors should retain their category, activity type, value, unit, source, geography, reference year, methodology, and whether the value is published or assumed. This makes the estimates easier to inspect and update.
