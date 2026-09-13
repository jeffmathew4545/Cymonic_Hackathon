# Demo Script: Sports Lot Optimiser

**Time limit: 10 minutes**

## 1. Introduction (1 min)
- **Hook:** "Sports arenas lose revenue every day when weekday afternoon slots remain vacant. But blindly discounting devalues the brand and destroys margin."
- **Solution:** "We built an Agentic Workforce Optimiser that evaluates vacant slots using deterministic logic to calculate risk (lead time + fill rate) and applies safe interventions within margin constraints."

## 2. The Dashboard (1 min)
- Show the Streamlit Dashboard.
- Briefly point out the total vacant slots vs slots requiring action.
- Mention that some slots are actively "Protected from Discount" because the agent reasoned that they don't need one, or they can't afford one.

## 3. Single Slot Demo: Obviously Fine (2 mins)
- Use the **SELECT SLOT** dropdown to find a slot with a high fill rate (>75%) and long lead time (>15 hours).
- Click **Analyze Slot**.
- Show that the agent decides: `NO ACTION`.
- **Talk track:** "The agent recognized this slot is likely to fill naturally, so it protected our revenue by doing nothing."

## 4. Single Slot Demo: Ambiguous Slot (2 mins)
- Select a slot with medium fill rate (~40%), short/medium lead time, but *very thin margin* (~18%).
- Click **Analyze Slot**.
- Show that the agent decides: `NOTIFY ONLY` (no discount).
- **Talk track:** "Here, the agent detects risk, but it checks the margin constraint. It refuses to offer an unsafe discount, instead opting to just notify the relevant segment at base price."
- Read the generated outreach message dynamically targeting the correct customer segment.
- Click **Apply Action** and show the success message.

## 5. Run All (2 mins)
- Scroll down to the **RUN ALL** section.
- Click **Run All Vacant Slots**.
- **Talk track:** "Instead of manual intervention, the agent evaluates all remaining vacant slots instantly."

## 6. Before/After Visualization (1 min)
- Scroll down to the **DATASET VIEW**.
- Show how the dataframe has updated dynamically.
- Point out different actions for different slots (`monitored`, `notified`) and different discount percentages applied safely across the board.

## 7. Conclusion (1 min)
- **Summary:** "Python decides, AI explains. Our solution is deterministic, safe, margin-aware, and immediately deployable without hallucination risks."
- Ask for questions.
