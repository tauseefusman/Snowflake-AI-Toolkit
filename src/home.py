import streamlit as st
from src.utils import *

def display_home(session):
    """
    Displays the home page of the Snowflake AI Toolkit application.
    
    This function creates a visually appealing landing page with information about
    Snowflake Cortex and the application's features. It includes styled sections for:
    - Header with application title
    - Introduction to Snowflake Cortex
    - Overview of the Streamlit UI
    - Available features and functionality
    - Call to action button
    
    Args:
        session: Snowflake session object used for database operations
        
    The function uses custom CSS styling to create a cohesive Snowflake-themed design
    with responsive sections and interactive elements.
    """
    # Apply custom CSS styles for a Snowflake blue-themed layout
    st.markdown("""
        <style>
            .header-section {
                background-color: #56CCF2;
                padding: 30px;
                text-align: center;
                border-radius: 10px;
                color: white;
                font-family: 'Arial', sans-serif;
            }
            .header-title {
                font-size: 3em;
                font-weight: bold;
            }
            .header-subtitle {
                font-size: 1.2em;
                margin-top: 10px;
            }
            .section {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .section-title {
                font-size: 1.8em;
                font-weight: bold;
                color: #56CCF2;
                margin-bottom: 10px;
            }
            .section-content {
                font-size: 1.1em;
                line-height: 1.5;
                color: #333;
            }
            .get-started-btn {
                background-color: #56CCF2;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 1.2em;
                border-radius: 5px;
                margin-top: 20px;
                display: inline-block;
                text-decoration: none;
            }
            .get-started-btn:hover {
                background-color: #2D9CDB;
            }
        </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown("""
        <div class="header-section">
            <div class="header-title">Snowflake AI Toolkit</div>
            <div class="header-subtitle">Unlock the power of AI and data with Snowflake Cortex, now accessible in a no-code environment.</div>
        </div>
    """, unsafe_allow_html=True)

    # Introduction to Snowflake Cortex
    st.markdown("""
        <div class="section">
            <div class="section-title">What is Snowflake Cortex?</div>
            <div class="section-content">
                Snowflake Cortex is a robust suite of AI and machine learning tools integrated directly within the Snowflake platform. It enables users to perform complex tasks such as text completion, summarization, sentiment analysis, information extraction, and more, all while leveraging Snowflake's powerful data storage and processing capabilities.
                <br><br>
                Cortex simplifies the AI workflow by integrating advanced models with your data, helping you create and deploy solutions with ease, speed, and security.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # How the Streamlit UI helps
    st.markdown("""
        <div class="section">
            <div class="section-title">No-Code AI with Streamlit</div>
            <div class="section-content">
                This Streamlit-based UI offers a no-code solution for exploring the full range of Snowflake Cortex functionalities. With an easy-to-use interface, you can experiment with Cortex's powerful AI capabilities without writing a single line of code.
                <br><br>
                Whether you're generating text completions, performing sentiment analysis, or extracting specific data from large datasets, this platform allows you to effortlessly explore these features, test your ideas, and build AI-driven applications within Snowflake's secure environment.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Sections Overview
    st.markdown("""
        <div class="section">
            <div class="section-title">Available Features</div>
            <div class="section-content">
                <strong>Playground:</strong> Experiment with Cortex's AI functionalities like text completion, translation, summarization, and sentiment analysis in an interactive environment. Quickly test various models and see real-time results.
                <br><br>
                <strong>Build:</strong> Create AI-driven workflows for business use cases. Fine-tune models and leverage Retrieval-Augmented Generation (RAG) to enhance the performance of your AI models. This section is designed for building custom solutions with powerful features like model fine-tuning and advanced retrieval mechanisms.
                <br><br>
                <strong>Notification:</strong> Track and manage all operations asynchronously. Get real-time updates on the success or failure of your Cortex operations in one centralized place.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Call to Action Section
    st.markdown("""
        <div style='text-align: center; margin-top: 30px;'>
            <a href='#' class='get-started-btn'>Get Started with Snowflake Cortex</a>
        </div>
    """, unsafe_allow_html=True)
