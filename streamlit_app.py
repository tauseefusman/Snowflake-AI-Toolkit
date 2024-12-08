import streamlit as st
from src.utils import *
from src import home, playground, build, notification, setup
from snowflake.snowpark.context import get_active_session
from pathlib import Path
import json
from snowflake.snowpark.exceptions import SnowparkSQLException
from src.notification import *

# Load the config file
config_path = Path("src/settings_config.json")
with open(config_path, "r") as f:
    config = json.load(f)

# Set the page title and layout
st.set_page_config(page_title="Snowflake AI Toolkit", layout="wide")

# Ensure session state variables are initialized
if 'page' not in st.session_state:
    st.session_state.page = "Home"  # Default page

if 'snowflake_session' not in st.session_state:
    st.session_state.snowflake_session = None

# Establish the session if not already initialized
if st.session_state.snowflake_session is None:
    if config["mode"] == "native":
        try:
            st.session_state.snowflake_session = get_active_session()
        except Exception as e:
            st.error(f"Failed to get active session in native mode: {e}")
    elif config["mode"] == "debug":
        try:
            connection_parameters = {
                "account": config["snowflake"]["account"],"user": config["snowflake"]["user"],"password": config["snowflake"]["password"],
                "role": config["snowflake"]["role"],"warehouse": config["snowflake"]["warehouse"],"database": config["snowflake"]["database"],
                "schema": config["snowflake"]["schema"]
            }
            st.session_state.snowflake_session = Session.builder.configs(connection_parameters).create()
        except Exception as e:
            st.error(f"Failed to create session in debug mode: {e}")

# Check if session is successfully created
if st.session_state.snowflake_session is None:
    st.error("Failed to connect to Snowflake.")
else:
    try:
        create_database_and_stage_if_not_exists(st.session_state.snowflake_session)
    except Exception as e:
        st.error(f"Error while creating database and stage: {e}")



# Set up UDF at app start
setup_pdf_text_chunker(st.session_state.snowflake_session)


# Load custom CSS for sidebar styling
st.markdown("""
    <style>
    /* Custom CSS for Sidebar */
    .css-18e3c8v {
        background-color: #333;
        padding: 20px;
        color: white;
    }

    .sidebar-title {
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 10px;
        color: white;
    }

    .sidebar-section {
        background-color: #444;
        border-radius: 8px;
        margin-bottom: 10px;
        padding: 15px;
        color: white;
        border: 1px solid #555;
    }

    .sidebar-section h2 {
        font-size: 1.3em;
        margin-bottom: 10px;
        font-weight: bold;
        color: #56CCF2;
    }

    .sidebar-section-item {
        font-size: 1em;
        padding: 5px 0;
        margin-left: 10px;
        color: white;
        cursor: pointer;
    }

    .sidebar-section-item:hover {
        color: #56CCF2;
        cursor: pointer;
    }

    .sidebar-image {
        text-align: center;
        margin-bottom: 20px;
    }

    .sidebar-image img {
        width: 150px;
        height: auto;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation with logo
render_image(config["default_settings"]["logo_path"])

# Sidebar content with expanders and buttons under each category
with st.sidebar:
    st.title("📋 Select Menu")

    # Overview Section
    with st.expander("🔍 **Overview**", expanded=False):
        if st.button("📄 About"):
            st.session_state.page = "Home"
        if st.button("⚙️ Setup"):
            st.session_state.page = "Setup"

    # Components Section
    with st.expander("✨ **Components**", expanded=False):
        if st.button("🎮 Playground"):
            st.session_state.page = "Playground"
        if st.button("🔧 Build"):
            st.session_state.page = "Build"
        if st.button("🔔 Notification"):
            st.session_state.page = "Notification"

# Pages dictionary with corresponding display functions
pages = {
    "Home": home.display_home,
    "Playground": playground.display_playground,
    "Build": build.display_build,
    "Notification": notification.display_notification,
    "Setup": setup.display_setup
}

# Render the selected page from the pages dictionary
if st.session_state.page in pages:
    try:
        pages[st.session_state.page](st.session_state.snowflake_session)
    except Exception as e:
        st.error(f"Error loading {st.session_state.page} page: {e}")
