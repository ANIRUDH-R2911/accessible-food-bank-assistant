import streamlit as st
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from src.conversation.conversation_service import ConversationService
from src.services.session_query_limiter import SessionQueryLimiter
APP_START = time.perf_counter()
print(
    f"[STARTUP] Imports completed in "
    f"{time.perf_counter() - APP_START:.2f} seconds"
)
st.set_page_config(
    page_title="Accessible Food Bank Assistant",
    page_icon="🥫",
    layout="centered"
)

if "conversation_service" not in st.session_state:
    service_start = time.perf_counter()
    st.session_state.conversation_service = ConversationService()
    print(
        f"[STARTUP] ConversationService initialized in "
        f"{time.perf_counter() - service_start:.2f} seconds"
    )
if "query_limiter" not in st.session_state:
    st.session_state.query_limiter = SessionQueryLimiter(max_queries=3)
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_query" not in st.session_state:
    st.session_state.last_query = None
if "last_search_results" not in st.session_state:
    st.session_state.last_search_results = []


st.title("🥫 Accessible Food Bank Assistant")
st.write(
    """
    Search donated food inventory using natural language.
    Find foods by ingredients, allergens, and nutritional requirements without manually browsing inventory records.
    """
)
st.divider()

example_queries = [
    "Find foods containing soy",
    "Find foods with more than 10g of protein",
    "Find foods that may contain peanuts"
]
st.subheader("Try an example")
selected_example = st.selectbox("Choose an example query", options=["Select an example..."] + example_queries)
st.subheader("Search food inventory")
with st.form("food_search_form"):
    user_query = st.text_input("Enter your search query", placeholder="e.g. Find foods containing oats")
    search_clicked = st.form_submit_button("Search Inventory", use_container_width=True)

limiter = st.session_state.query_limiter
remaining_queries = limiter.remaining_queries
st.divider()
st.subheader("Session Usage")
st.progress(remaining_queries / limiter.max_queries)
st.caption(f"{remaining_queries} of {limiter.max_queries} queries remaining")

if search_clicked:
    query = user_query.strip()
    if not query and selected_example != "Select an example...":
        query = selected_example
    if not query:
        st.warning("Please enter a search query or select an example.")
    elif limiter.remaining_queries == 0:
        st.warning("You've reached the limit of 3 queries for this session. Please start a new session to continue.")
    elif limiter.allow_query():
        try:
            search_start = time.perf_counter()
            response = st.session_state.conversation_service.ask(query)
            print(f"[SEARCH] Query completed in " f"{time.perf_counter() - search_start:.2f} seconds")
            st.session_state.last_query = query
            st.session_state.last_response = response
            st.session_state.last_search_results = (st.session_state.conversation_service.last_search_results)
        except Exception:
            st.session_state.last_search_results = []
            st.error("Something went wrong while processing your search. Please try again later.")

def display_inventory_record(result):
    if not isinstance(result, dict):
        return

    inventory_record = result.get("inventory_data")
    if not isinstance(inventory_record, dict):
        inventory_record = result

    item_id = inventory_record.get("item_id") or result.get("id")
    if not item_id:
        return

    with st.expander(f"Inventory Item: {item_id}"):
        st.markdown("#### Ingredients")
        ingredients = inventory_record.get("ingredients")
        if isinstance(ingredients, list) and ingredients:
            st.write(", ".join(str(item) for item in ingredients))
        else:
            st.caption("Not available in this record.")

        st.divider()
        st.markdown("#### Allergen Information")
        contains_allergens = inventory_record.get("contains_allergens")
        may_contain = inventory_record.get("may_contain")
        st.markdown("**Contains allergens**")
        if isinstance(contains_allergens, list) and contains_allergens:
            st.write(", ".join(str(item) for item in contains_allergens))
        else:
            st.caption("No allergens listed in this record.")

        st.markdown("**May contain**")
        if isinstance(may_contain, list) and may_contain:
            st.write(", ".join(str(item) for item in may_contain))
        else:
            st.caption("No potential allergens listed in this record.")

        st.divider()
        st.markdown("#### Nutritional Information")
        nutrition = inventory_record.get("nutrition")
        if isinstance(nutrition, dict) and nutrition:
            nutrition_rows = []
            for nutrient, value in nutrition.items():
                display_value = (
                    "Not available"
                    if value is None
                    else value
                )
                nutrition_rows.append(
                    {
                        "Nutrient": nutrient.replace("_", " ").title(),
                        "Value": display_value
                    }
                )
            st.table(nutrition_rows)
        else:
            st.caption("Nutritional information is not available.")

if st.session_state.last_response is not None:
    st.divider()
    st.subheader("Search Results")
    st.caption(f"Your search: {st.session_state.last_query}")
    st.markdown(st.session_state.last_response)
    search_results = st.session_state.last_search_results
    if search_results:
        st.divider()
        st.subheader("Detailed Inventory Records")
        st.caption(f"{len(search_results)} matching records retrieved")
        for result in search_results:
            display_inventory_record(result)

if limiter.remaining_queries == 0:
    st.info("You have used all 3 searches available in this session.")
