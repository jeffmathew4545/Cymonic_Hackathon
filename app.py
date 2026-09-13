import streamlit as st
import pandas as pd
from src.data_loader import load_slots, load_segments, apply_decision_to_slot, save_slots
from src.engine import decide
from src.messaging import generate_outreach_message

st.set_page_config(page_title="Sports Lot Optimiser", layout="wide")

# Load data into session state
if 'slots' not in st.session_state:
    st.session_state.slots = load_slots()
if 'segments' not in st.session_state:
    st.session_state.segments = load_segments()

slots = st.session_state.slots
segments = st.session_state.segments

st.title("SPORTS LOT OPTIMISER")
st.subheader("AI-powered vacant slot intervention")
st.markdown("---")

# Dashboard
total_vacant = sum(1 for s in slots if s['current_status'] == 'vacant')
action_taken_slots = sum(1 for s in slots if s['action_taken'] in ['notify_only', 'notify_and_discount'])
protected_slots = sum(1 for s in slots if s['action_taken'] == 'no_action' or (s['action_taken'] == 'notify_only' and s.get('reasoning', '').find('margin') != -1))
potential_discounts = sum(1 for s in slots if s['action_taken'] == 'notify_and_discount')

st.header("Dashboard")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Vacant Slots", total_vacant)
col2.metric("Slots Requiring Action", action_taken_slots)
col3.metric("Protected from Discount", protected_slots)
col4.metric("Discounts Offered", potential_discounts)
st.markdown("---")

# SINGLE SLOT DEMO
st.header("SELECT SLOT")
vacant_slots = [s for s in slots if s['current_status'] == 'vacant']
if vacant_slots:
    slot_options = {s['slot_id']: s for s in vacant_slots}
    selected_slot_id = st.selectbox("Choose a slot to analyze:", options=list(slot_options.keys()))
    selected_slot = slot_options[selected_slot_id]
    
    st.write("### Slot Information")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.write(f"**Sport:** {selected_slot['sport_type']}")
    sc1.write(f"**Date:** {selected_slot['date']}")
    sc2.write(f"**Time:** {selected_slot['time_block']}")
    sc2.write(f"**Base Price:** ₹{selected_slot['base_price']}")
    sc3.write(f"**Fill Rate:** {selected_slot['historical_fill_rate']:.0%}")
    sc3.write(f"**Lead Time:** {selected_slot['lead_time_hours']} hours")
    sc4.write(f"**Margin:** {selected_slot['margin_pct']}%")
    
    if st.button("Analyze Slot"):
        st.session_state.current_decision = decide(selected_slot)
        
    if 'current_decision' in st.session_state:
        st.markdown("---")
        st.header("AGENT DECISION")
        decision = st.session_state.current_decision
        
        # Display Decision
        st.write(f"**Action:** {decision['action'].replace('_', ' ').upper()}")
        st.write(f"**Reasoning:** {decision['reasoning']}")
        
        # We need to temporarily assign the segment for the message preview
        from src.data_loader import match_segment
        preview_segment = match_segment(selected_slot['sport_type'], segments)
        temp_decision = decision.copy()
        if decision['action'] != 'no_action':
            temp_decision['segment_notified'] = preview_segment
            st.write(f"**Customer Segment:** {preview_segment}")
            
            outreach = generate_outreach_message(selected_slot, temp_decision)
            if outreach:
                st.write("**Outreach Message:**")
                st.info(outreach)
        
        if st.button("Apply Action"):
            apply_decision_to_slot(selected_slot, decision, segments)
            save_slots(slots)
            st.success("Action applied and dataset updated!")
            del st.session_state.current_decision
            st.rerun()
else:
    st.write("No vacant slots available to analyze.")

st.markdown("---")

# RUN ALL
st.header("RUN ALL")
if st.button("Run All Vacant Slots"):
    updates = 0
    for s in slots:
        if s['current_status'] == 'vacant':
            decision = decide(s)
            apply_decision_to_slot(s, decision, segments)
            updates += 1
    if updates > 0:
        save_slots(slots)
        st.success(f"Processed {updates} slots.")
        st.rerun()
    else:
        st.info("No vacant slots to process.")

st.markdown("---")

# BEFORE / AFTER
st.header("DATASET VIEW (Before / After)")
df = pd.DataFrame(slots)
display_cols = ['slot_id', 'sport_type', 'historical_fill_rate', 'lead_time_hours', 'margin_pct', 'current_status', 'action_taken', 'discount_pct_applied', 'segment_notified', 'reasoning']
st.dataframe(df[display_cols])
