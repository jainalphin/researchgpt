import os
import streamlit as st
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.schema import SystemMessage

# Page configuration
st.set_page_config(
    page_title="ResearchGPT - LangChain Search Agent",
    page_icon="🔎",
    layout="wide"
)

# Application title and description
st.title("🔎 ResearchGPT - Chat with Search")
st.markdown("""
This application combines LangChain's powerful agent capabilities with multiple research tools:
- **Wikipedia** for general knowledge
- **arXiv** for scientific papers
- **DuckDuckGo** for web search

The agent decides which tool to use based on your question, providing comprehensive answers with citations.
""")

# Sidebar configuration
st.sidebar.title("⚙️ Configuration")
st.sidebar.markdown("---")

# API key input with validation
groq_api_key = st.sidebar.text_input("Enter your Groq API key:", type="password", help="Get your API key from https://console.groq.com/keys")

# Model selection
model_options = {
    "Llama3-8b-8192": "Llama 3 8B (Fast)",
    "llama3-70b-8192": "Llama 3 70B (Powerful)",
    "mixtral-8x7b-32768": "Mixtral 8x7B (Balanced)"
}
selected_model = st.sidebar.selectbox("Select model:", list(model_options.keys()), format_func=lambda x: model_options[x])

# Tool configuration
st.sidebar.markdown("---")
st.sidebar.subheader("Tool Settings")

wiki_results = st.sidebar.slider("Wikipedia results:", min_value=1, max_value=5, value=1)
arxiv_results = st.sidebar.slider("arXiv papers:", min_value=1, max_value=5, value=1)
max_content_length = st.sidebar.slider("Max content length:", min_value=250, max_value=2000, value=500)

# About section
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("This application uses LangChain with Streamlit to create an interactive research assistant. View more examples at [github.com/langchain-ai/streamlit-agent](https://github.com/langchain-ai/streamlit-agent).")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I'm ResearchGPT! Ask me any research question, and I'll search across Wikipedia, arXiv papers, and the web to find answers for you."}
    ]

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Initialize tools with user settings
def initialize_search_tools():
    # Wikipedia tool
    wiki_wrapper = WikipediaAPIWrapper(
        top_k_results=wiki_results,
        doc_content_chars_max=max_content_length
    )
    wiki_tool = WikipediaQueryRun(name="wikipedia", api_wrapper=wiki_wrapper)
    
    # arXiv tool
    arxiv_wrapper = ArxivAPIWrapper(
        top_k_results=arxiv_results,
        doc_content_chars_max=max_content_length
    )
    arxiv_tool = ArxivQueryRun(name="arxiv", api_wrapper=arxiv_wrapper)
    
    # DuckDuckGo search tool
    search_tool = DuckDuckGoSearchRun(name="web_search")
    
    return [wiki_tool, arxiv_tool, search_tool]

# Process chat input
if groq_api_key:
    if prompt := st.chat_input(placeholder="Ask me a research question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        try:
            # Initialize LLM
            llm = ChatGroq(
                groq_api_key=groq_api_key,
                model_name=selected_model,
                streaming=True,
                temperature=0.5
            )
            
            # Initialize tools and agent
            tools = initialize_search_tools()
            
            # System message for agent
            system_message = SystemMessage(content="""
            You are ResearchGPT, a helpful research assistant that provides accurate information.
            When answering questions:
            1. Use the most appropriate tool based on the question.
            2. For scientific or academic topics, prefer arXiv.
            3. For general knowledge, use Wikipedia.
            4. For recent information or specific queries, use web search.
            5. Always cite your sources.
            6. Be concise but comprehensive.
            """)
            
            # Initialize agent
            agent = initialize_agent(
                llm=llm,
                tools=tools,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                handle_parsing_errors=True,
                verbose=True,
                early_stopping_method="generate",
                system_message=system_message
            )
            
            # Process with streaming callback
            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
                response = agent.run(prompt, callbacks=[st_cb])
                st.write(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"I'm sorry, I encountered an error: {str(e)}"})
else:
    st.warning("⚠️ Please enter your Groq API key in the sidebar to start chatting.")
    # Display demo image if available
