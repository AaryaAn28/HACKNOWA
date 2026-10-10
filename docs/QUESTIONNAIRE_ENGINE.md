# Questionnaire Engine

The Questionnaire Engine is an adaptive, dynamic system designed to gather essential context, goals, and constraints from the user, ensuring simulations are aligned with real-world objectives.

## Dynamic vs. Static Questionnaires

Unlike traditional static forms, Reality Sculptor's questionnaires adapt based on:
1.  **Uploaded Data**: If a user uploads a sewer blueprint, it won't ask if there is a sewer system.
2.  **Previous Answers**: If a user says budget is not a constraint, it won't ask for detailed financial breakdowns.
3.  **Simulation Results**: If a simulation reveals a massive bottleneck, it might prompt a dynamic question: "We found a major blockage here. Is there known construction or damage?"

## Information Value Engine Ranking

Questions are prioritized based on their "Information Value."
*   `Value = (Impact on Simulation Accuracy) * (Probability User Knows Answer) / (Cost of Answering)`
*   High value questions are asked first.
*   Low value questions are deferred or skipped.

## Question Categories

*   **Permission**: "Can we demolish this structure?" "Is this road allowed to be closed?"
*   **Constraint**: "What is the maximum budget?" "What is the maximum acceptable flood depth for primary roads?"
*   **Context**: "Is there historical flooding in this specific area?"
*   **Objective**: "What is the primary goal? (e.g., Stop flooding, improve traffic, reduce heat)."

## Post-Upload Questionnaires

Triggered immediately after a data upload to clarify ambiguities.
*   *Upload*: A CSV of pump capacities.
*   *Question*: "Does this CSV use liters/second or gallons/minute?"
*   *Upload*: A fuzzy PDF blueprint.
*   *Question*: "We couldn't read the diameter of Pipe X. Can you provide it?"

## Objective Translation

The engine translates fuzzy human objectives into measurable simulation targets.
*   *User Input*: "Stop flooding."
*   *Translation*: `Target: Max Flood Depth < 0.1m on all Road nodes; Max Duration < 1 hour`.
*   *User Input*: "Improve traffic."
*   *Translation*: `Target: Average Commute Time < 20 mins; Throughput > 500 cars/hr`.

## Data Gap Analysis

The engine constantly analyzes the World Graph for missing, critical data and generates prompts.
*   "We are missing drainage data for the North Sector. This reduces our flood prediction confidence by 40%. Can you provide it?"

## Example Question Flow

1.  *User uploads project boundary.*
2.  **Q**: What is the primary issue here? (A: Flooding)
3.  **Q**: Which critical infrastructure must be protected first? (A: Hospital)
4.  *System builds initial model, finds missing data.*
5.  **Q**: We lack sewer data for Main St. Do you have blueprints? (A: No)
6.  *System uses procedural generation, marks confidence as ESTIMATED.*
