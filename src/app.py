import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
import os
from dotenv import load_dotenv

# Settings.llm = OpenAI(model="gpt-4o-mini")

# Load environment variables from .env file
load_dotenv()

# Access your environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Initialize Dash app
app = dash.Dash(__name__, assets_folder='assets')

# Load and index your data
documents = SimpleDirectoryReader("egov").load_data()
index = VectorStoreIndex.from_documents(documents)



query_engine = index.as_query_engine()

# Define the PDF URL
pdf_url = "https://egovsg.ch/wp-content/uploads/2023/01/E-Government-Strategie-des-Kantons-St.Gallen-und-der-St.Galler-Gemeinden-2023-2026.pdf"

# Define the layout
app.layout = html.Div([
    # PDF viewer (2/3 width on the right)
    html.Div([
        html.H1("PDF Viewer", style={'textAlign': 'center', 'marginBottom': '10px'}),
        html.Embed(
            src=pdf_url,
            style={'width': '100%', 'height': 'calc(100vh - 100px)'}
        )
    ], style={'width': '60%', 'float': 'right', 'padding': '20px', 'boxSizing': 'border-box', 'height': '100vh'}),
    
    # Chat window (1/3 width on the left)
    html.Div([
        html.H1("eGov: St. Gallen digital", style={'textAlign': 'center', 'marginBottom': '10px'}),
        html.Div([
            dcc.Textarea(
                id='user-input',
                placeholder='Stelle eine Frage zum Dokument...?',
                style={'width': 'calc(100% - 110px)', 'height': 40, 'marginRight': '20px', 'verticalAlign': 'middle', 'fontFamily': 'Helvetica, Arial, sans-serif', 'fontSize': '14px'},
            ),
            html.Button('Frage senden', id='submit-button', n_clicks=0, 
                        style={'width': '150px', 'height': '40px', 'borderRadius': '25px', 'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 'verticalAlign': 'middle'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
        html.Div(id='chat-output', style={'overflowY': 'auto', 'height': 'calc(100vh - 250px)', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'flex-start', 'paddingRight': '20px'}),
        html.Div(id='scroll-to-bottom'),  # Add this line
        dcc.Store(id='conversation-history', data=[]) 
    ], style={'width': '38%', 'float': 'left', 'padding': '20px', 'boxSizing': 'border-box', 'height': '100vh'}),
], style={'backgroundColor': '#f0f0f0', 'height': '100vh', 'overflow': 'hidden'})

# Define styles for chat bubbles
user_bubble_style = {
    'backgroundColor': '#9fbff5',
    'color': 'black',
    'padding': '10px',
    'borderRadius': '20px',
    'maxWidth': '70%',
    'marginLeft': 'auto',
    'marginBottom': '10px',
    'alignSelf': 'flex-end',
    'fontFamily': 'Helvetica, Arial, sans-serif',
    'fontSize': '14px',
}

ai_bubble_style = {
    'backgroundColor': '#c0ebde',
    'color': 'black',
    'padding': '10px',
    'borderRadius': '20px',
    'maxWidth': '80%',
    'marginRight': 'auto',
    'marginBottom': '10px',
    'alignSelf': 'flex-start',
    'fontFamily': 'Helvetica, Arial, sans-serif',
    'fontSize': '14px',
}

# Define the callback
@app.callback(
    Output('chat-output', 'children'),
    Output('scroll-to-bottom', 'children'),
    Input('submit-button', 'n_clicks'),
    [State('user-input', 'value'),
     State('chat-output', 'children'),
     State('conversation-history', 'data')],
    prevent_initial_call=True
)
def update_output(n_clicks, value, chat_history, conversation_history):
    if value:
        # Initialize conversation history if it doesn't exist
        if conversation_history is None:
            conversation_history = []

        # Prepare the conversation context
        context = "\n".join([f"Human: {msg['content']}" if msg['role'] == 'user' else f"AI: {msg['content']}" for msg in conversation_history[-5:]])
        
        # Query the index with context
        response = query_engine.query(f"Context: {context}\n\nNew question: {value}\nAlways respond in german")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": value})
        conversation_history.append({"role": "assistant", "content": str(response)})
        
        # Create new chat bubbles
        user_bubble = html.Div(value, style=user_bubble_style)
        ai_bubble = html.Div(str(response), style=ai_bubble_style)
        
        # Add new bubbles to chat history
        new_chat_history = chat_history or []
        new_chat_history.extend([user_bubble, ai_bubble])
        
        # Return the updated chat history and a dummy div to trigger scrolling
        return new_chat_history, html.Div()
    return "Bitte stelle eine Frage.", html.Div()

# Add this clientside callback to handle scrolling
app.clientside_callback(
    """
    function(children) {
        if (children) {
            var chatOutput = document.getElementById('chat-output');
            chatOutput.scrollTop = chatOutput.scrollHeight;
        }
        return {};
    }
    """,
    Output('scroll-to-bottom', 'style'),
    Input('scroll-to-bottom', 'children')
)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

