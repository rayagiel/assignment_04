"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.

import streamlit as st
import pandas as pd
import numpy as np
from payroll.compute import build_payroll, payroll_export
from payroll.extract import load_timesheet, load_employees


st.title("Salt City Coffee - Weekly Payroll")
st.text("Upload the weekly timesheet (export. The roster is loaded automatically.Check the totals, fix anything flagged, the download the file for the payroll provider.")

roster = load_employees()
timesheet = st.file_uploader("Upload Weekly timesheet (CSV)", key="timesheet")

if timesheet is not None:
    timesheet = load_timesheet(timesheet)
    payroll = build_payroll(timesheet, roster)
    export = payroll_export(payroll)
    st.subheader(f"Pay Period Ending: {payroll['payroll_date'][1]}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Employees paid", len(export["employeeid"]))
    with col2:
        st.metric("Total hours", payroll["hours_worked"].sum())
    with col3:
        st.metric("Total gross pay", f"${payroll['gross_pay'].sum():,.2f}")
    with col4:
        st.metric("Overtime weeks", len(payroll[payroll["hours_worked"] > 40]))
    export = payroll_export(payroll)
    missing_id = payroll[payroll["pay_type"] == "unmatched"]
    if len(missing_id) == 0:
        st.success("All employee IDs are matched.")
    else:
        st.warning(f"{len(missing_id)} timesheet row(s) have an employee_id that is not on the roster: {list(missing_id['employee_id'])}")

    st.dataframe(payroll)
    st.subheader("Payroll table")
    st.text("Raw values on the left, computed columns on the right - nothing is overwritten.")
    export_final = export.to_csv(index=False)
    st.download_button(key="download", label="Download payroll CSV for the provider", data=export_final, file_name = "payroll_export.csv", mime="text/csv")