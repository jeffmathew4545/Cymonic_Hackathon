import streamlit as st
import pandas as pd
from src.data_loader import load_slots, load_segments, apply_decision_to_slot, save_slots, match_segment
from src.engine import decide
from src.messaging import generate_outreach_message

st.set_page_config(page_title="Sports Lot Optimiser", layout="wide")

# Refresh dataset from disk button in sidebar
st.sidebar.title("Data Controls")
if st.sidebar.button("Reload CSV Data from Disk"):
    st.session_state.slots = load_slots()
    st.session_state.segments = load_segments()
    st.sidebar.success("Reloaded dataset!")
    st.rerun()

# Load data into session state
if 'slots' not in st.session_state or not st.session_state.slots:
    st.session_state.slots = load_slots()
if 'segments' not in st.session_state or not st.session_state.segments:
    st.session_state.segments = load_segments()

slots = st.session_state.slots
segments = st.session_state.segments

st.title("SPORTS LOT OPTIMISER")
st.subheader("AI-powered vacant slot intervention")
st.markdown("---")

# Dashboard
total_slots = len(slots)
action_taken_slots = sum(1 for s in slots if s.get('action_taken') in ['notify_only', 'notify_and_discount'])
protected_slots = sum(1 for s in slots if s.get('action_taken') == 'no_action' or (s.get('action_taken') == 'notify_only' and 'margin' in str(s.get('reasoning', ''))))
potential_discounts = sum(1 for s in slots if s.get('action_taken') == 'notify_and_discount')

st.header("Dashboard")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Slots in Pipeline", total_slots)
col2.metric("Slots Requiring Action", action_taken_slots)
col3.metric("Protected from Discount", protected_slots)
col4.metric("Discounts Offered", potential_discounts)
st.markdown("---")

# SINGLE SLOT DEMO
st.header("SELECT SLOT")
if slots:
    slot_options = {
        f"{s['slot_id']} | {s['sport_type']} | {s['time_block']} | Status: {s.get('current_status', 'vacant')}": s 
        for s in slots
    }
    selected_label = st.selectbox("Choose a slot to analyze:", options=list(slot_options.keys()))
    selected_slot = slot_options[selected_label]
    
    st.write("### Slot Information")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.write(f"**Sport:** {selected_slot['sport_type']}")
    sc1.write(f"**Date:** {selected_slot['date']}")
    sc2.write(f"**Time:** {selected_slot['time_block']}")
    sc2.write(f"**Base Price:** ₹{selected_slot['base_price']}")
    sc3.write(f"**Fill Rate:** {float(selected_slot['historical_fill_rate']):.0%}")
    sc3.write(f"**Lead Time:** {selected_slot['lead_time_hours']} hours")
    sc4.write(f"**Margin:** {selected_slot['margin_pct']}%")
    
    if st.button("Analyze Slot"):
        st.session_state.current_decision = decide(selected_slot)
        st.session_state.selected_slot_id = selected_slot['slot_id']
        
    if 'current_decision' in st.session_state and st.session_state.get('selected_slot_id') == selected_slot['slot_id']:
        st.markdown("---")
        st.header("AGENT DECISION")
        decision = st.session_state.current_decision
        
        # Display Decision
        st.write(f"**Action:** {decision['action'].replace('_', ' ').upper()}")
        st.write(f"**Risk Score:** {decision['risk_score']}")
        st.write(f"**Reasoning:** {decision['reasoning']}")
        
        # Assign matched segment for preview
        preview_segment = match_segment(selected_slot['sport_type'], segments, selected_slot.get('time_block'))
        temp_decision = decision.copy()
        if decision['action'] != 'no_action':
            temp_decision['segment_notified'] = preview_segment
            st.write(f"**Target Customer Segment:** {preview_segment}")
            
            outreach = generate_outreach_message(selected_slot, temp_decision)
            if outreach:
                st.write("**Outreach Message:**")
                st.info(outreach)
        
        if st.button("Apply Action & Update CSV"):
            apply_decision_to_slot(selected_slot, decision, segments)
            save_slots(slots)
            st.success("Action applied and dataset updated in CSV!")
            del st.session_state.current_decision
            st.rerun()
else:
    st.write("No slots available to analyze.")

st.markdown("---")

# RUN ALL
st.header("RUN ALL SLOTS")
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("Process / Re-evaluate All Slots"):
        updates = 0
        for s in slots:
            decision = decide(s)
            apply_decision_to_slot(s, decision, segments)
            updates += 1
        save_slots(slots)
        st.success(f"Processed and updated {updates} slots in CSV!")
        st.rerun()

st.markdown("---")

# BEFORE / AFTER
st.header("DATASET VIEW (CSV Records)")
df = pd.DataFrame(slots)
display_cols = ['slot_id', 'sport_type', 'date', 'time_block', 'historical_fill_rate', 'lead_time_hours', 'margin_pct', 'current_status', 'action_taken', 'discount_pct_applied', 'segment_notified', 'reasoning']
available_cols = [c for c in display_cols if c in df.columns]
st.dataframe(df[available_cols], use_container_width=True)

