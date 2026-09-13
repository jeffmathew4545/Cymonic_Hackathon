import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sports Lot Optimiser", layout="wide")

# ==========================================
# DUMMY FUNCTIONS (Replace later in Phase 3)
# ==========================================

def load_dummy_slots():
    """Dummy version of Member 1's data loader"""
    return [
        {"slot_id": "S1001", "sport_type": "Box Cricket", "date": "2026-09-14", "time_block": "14:00 - 15:00", "base_price": 800, "historical_fill_rate": 0.25, "lead_time_hours": 2.5, "margin_pct": 45, "current_status": "vacant", "action_taken": "", "discount_pct_applied": 0, "segment_notified": "", "reasoning": ""},
        {"slot_id": "S1002", "sport_type": "Badminton", "date": "2026-09-14", "time_block": "16:00 - 17:00", "base_price": 400, "historical_fill_rate": 0.85, "lead_time_hours": 24.0, "margin_pct": 50, "current_status": "vacant", "action_taken": "", "discount_pct_applied": 0, "segment_notified": "", "reasoning": ""},
    ]

def dummy_decide(slot):
    """Dummy version of Member 2's engine"""
    if slot['historical_fill_rate'] < 0.5:
        return {"action": "notify_and_discount", "discount_pct": 15.0, "reasoning": "High risk detected. Margin supports a 15% discount."}
    return {"action": "no_action", "discount_pct": 0.0, "reasoning": "Slot will likely fill naturally. No intervention needed."}

def dummy_get_message_payload(slot, decision):
    """Dummy version of Member 3's messaging engine (Handles segment matching!)"""
    if decision['action'] == 'no_action':
        return None, None
        
    segment = "Corporate Football League" # Mocking Member 3's segment match
    message = f"🔥 Notify + {decision['discount_pct']}% Discount\n\nTargeting: {segment}\n\nAct fast to book {slot['sport_type']}!"
    return segment, message

def dummy_update_slot_state(slot, decision, segment):
    """Dummy version of Member 1's update function"""
    slot['action_taken'] = decision['action']
    slot['discount_pct_applied'] = decision['discount_pct']
    slot['reasoning'] = decision['reasoning']
    slot['segment_notified'] = segment if segment else ""
    slot['current_status'] = "handled"
    return slot

# ==========================================
# UI IMPLEMENTATION
# ==========================================

# 1. Load Data into Session State
if 'slots' not in st.session_state:
    st.session_state.slots = load_dummy_slots()
slots = st.session_state.slots

# Hide Streamlit Deploy button and Menu
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("SPORTS LOT OPTIMISER")
st.markdown("---")

# 3. Per-Slot Inspector View
st.header("Single Slot Inspector")
vacant_slots = [s for s in slots if s['current_status'] == 'vacant']

if vacant_slots:
    slot_options = {s['slot_id']: s for s in vacant_slots}
    selected_id = st.selectbox("Select a vacant slot:", options=list(slot_options.keys()))
    selected_slot = slot_options[selected_id]
    
    st.write(f"**Analyzing:** {selected_slot['sport_type']} at {selected_slot['time_block']} | Fill Rate: {selected_slot['historical_fill_rate']:.0%} | Margin: {selected_slot['margin_pct']}%")
    
    if st.button("Run Optimizer"):
        # The 3-step pipeline integration!
        # Step A: Member 2 calculates the decision
        decision = dummy_decide(selected_slot)
        
        # Step B: Member 3 matches the segment and builds the message
        segment, outreach_msg = dummy_get_message_payload(selected_slot, decision)
        
        # UI Rendering
        st.write("### Agent Decision")
        st.write(f"**Action:** {decision['action'].upper()}")
        st.write(f"**Reasoning:** {decision['reasoning']}")
        
        if outreach_msg:
            st.info(f"**Outreach Payload (Sent to {segment}):**\n\n{outreach_msg}")
            
        # Step C: Member 1 updates the database
        if st.button("Apply Action & Update Database"):
            dummy_update_slot_state(selected_slot, decision, segment)
            st.success("Database updated successfully!")
            st.rerun()
else:
    st.success("All slots have been handled!")

st.markdown("---")

# 4. Run All Batch View
st.header("Batch Process All")
if st.button("Run All Vacant Slots"):
    updates = 0
    for s in slots:
        if s['current_status'] == 'vacant':
            dec = dummy_decide(s)
            seg, msg = dummy_get_message_payload(s, dec)
            dummy_update_slot_state(s, dec, seg)
            updates += 1
    st.success(f"Processed {updates} slots.")
    st.rerun()

st.markdown("---")

# 5. Before/After State View
st.header("Live Database View")
df = pd.DataFrame(slots)
# Use st.table() instead of st.dataframe() to bypass the PyArrow security block
st.table(df[['slot_id', 'sport_type', 'current_status', 'action_taken', 'discount_pct_applied', 'segment_notified', 'reasoning']])
