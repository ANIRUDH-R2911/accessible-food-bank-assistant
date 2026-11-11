import streamlit as st
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from src.conversation.conversation_service import ConversationService
from src.services.session_query_limiter import SessionQueryLimiter
import os

APP_START = time.perf_counter()
print(f"[STARTUP] Imports completed in {time.perf_counter() - APP_START:.2f} seconds")

st.set_page_config(
    page_title="Accessible Food Bank Assistant",
    page_icon="🥫",
    layout="wide"
)

if "gemini_generation_limiter" not in st.session_state:
    st.session_state.gemini_generation_limiter = SessionQueryLimiter(max_generations=3)
    
if "conversation_service" not in st.session_state:
    service_start = time.perf_counter()
    st.session_state.conversation_service = ConversationService(session_generation_limiter=st.session_state.gemini_generation_limiter)
    print(f"[STARTUP] ConversationService initialized in {time.perf_counter() - service_start:.2f} seconds")
    
st.session_state.conversation_service.session_generation_limiter = (st.session_state.gemini_generation_limiter)
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_query" not in st.session_state:
    st.session_state.last_query = None
if "last_search_results" not in st.session_state:
    st.session_state.last_search_results = []

def display_inventory_record(result):
    if not isinstance(result, dict):
        return
    inventory_record = result.get("inventory_data")
    if not isinstance(inventory_record, dict):
        inventory_record = result
    item_id = (inventory_record.get("item_id") or result.get("id"))
    if not item_id:
        return

    with st.expander(f"Inventory Item: {item_id}"):
        st.markdown("**Ingredients**")
        ingredients = inventory_record.get("ingredients")
        if isinstance(ingredients, list) and ingredients:
            st.write(", ".join(str(item) for item in ingredients))
        else:
            st.caption("Not available in this record.")

        st.divider()

        st.markdown("**Allergen Information**")
        contains_allergens = inventory_record.get("contains_allergens")
        may_contain = inventory_record.get("may_contain")
        st.markdown("Contains allergens")
        if isinstance(contains_allergens, list) and contains_allergens:
            st.write(", ".join(str(item) for item in contains_allergens))
        else:
            st.caption("No allergens listed in this record.")

        st.markdown("May contain")
        if isinstance(may_contain, list) and may_contain:
            st.write(", ".join(str(item) for item in may_contain))
        else:
            st.caption("No potential allergens listed in this record.")

        st.divider()
        st.markdown("**Nutritional Information**")
        nutrition = inventory_record.get("nutrition")
        if isinstance(nutrition, dict) and nutrition:
            nutrition_rows = []
            for nutrient, value in nutrition.items():
                display_value = ("Not available" if value is None else str(value))
                nutrition_rows.append({
                    "Nutrient": nutrient.replace("_", " " ).title(),
                    "Value": display_value
                })
            st.table(nutrition_rows)
        else:
            st.caption("Nutritional information is not available.")

st.title("🥫 Accessible Food Bank Assistant")
st.badge("Public Demo", color="blue")
st.write(
    """
    An AI-powered food inventory assistant that helps food bank volunteers discover available foods using natural-language searches for ingredients, allergens, and nutritional requirements.
    """
)
st.caption("This demonstration uses a preloaded sample inventory. It does not support live inventory management.")
st.divider()

left_panel, right_panel = st.columns([0.9, 1.4], gap="large")
with left_panel:
    st.subheader("Search Food Inventory")
    example_queries = [
        "Find foods containing soy",
        "Find foods with more than 10g of protein",
        "Find foods that may contain peanuts",
        "Find dairy and nut free foods",
        "Find foods containing oats"
    ]
    with st.form("food_search_form"):
        selected_example = st.selectbox("Try an example query", options=["Select an example..."] + example_queries)
        user_query = st.text_input("Enter your search query", placeholder="e.g. Find foods containing oats", max_chars=500)
        search_clicked = st.form_submit_button("Search Inventory", use_container_width=True)

    if search_clicked:
        query = user_query.strip()
        if not query and selected_example != "Select an example...":
            query = selected_example
        if not query:
            st.warning("Please enter a search query or select an example.")
        else:
            try:
                search_start = time.perf_counter()
                response = (st.session_state.conversation_service.ask(query))
                search_latency = (time.perf_counter() - search_start)
                print(f"[SEARCH] Query completed in {search_latency:.2f} seconds")
                st.session_state.last_query = query
                st.session_state.last_response = response
                st.session_state.last_search_results = (st.session_state.conversation_service.last_search_results)
            except Exception:
                st.session_state.last_search_results = []
                st.error("Something went wrong while processing your search. Please try again later.")

    st.divider()
    st.subheader("Session Usage")
    limiter = st.session_state.gemini_generation_limiter
    remaining_generations = limiter.remaining_generations
    st.progress(remaining_generations / limiter.max_generations)
    st.caption(f"{remaining_generations} of {limiter.max_generations} Gemini generations remaining")
    st.caption("Inventory searches remain available independently of the Gemini generation limit.")
    if remaining_generations == 0:
        st.info("Your Gemini generation limit has been reached. You can continue searching using retrieval-only responses.")

with right_panel:
    st.subheader("Search Results")
    if st.session_state.last_response is None:
        st.info("Your search results will appear here. Enter a food search query to get started.")
    else:
        st.caption(f"Your search: {st.session_state.last_query}")
        search_results = st.session_state.last_search_results
        st.markdown(st.session_state.last_response)
        st.divider()
        if search_results:
            st.metric(label="Matching Inventory Records", value=len(search_results))
            st.subheader("Detailed Inventory Records")
            st.caption("Expand an inventory record to view its ingredients, allergens, and nutritional information.")
            for result in search_results:
                display_inventory_record(result)
        else:
            st.caption("No matching inventory records were retrieved.")