import atexit
import asyncio
import logging

import gradio as gr
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

from agent import create_mcp_server, create_agent, MCP_SERVER_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_mcp_server = None
_agent = None


async def get_agent():
    global _mcp_server, _agent
    if _agent is None:
        logger.info("Connecting to MCP server at %s", MCP_SERVER_URL)
        _mcp_server = create_mcp_server()
        await _mcp_server.__aenter__()
        _agent = create_agent(_mcp_server)
    return _agent


def _shutdown():
    if _mcp_server is None:
        return
    try:
        asyncio.get_event_loop().run_until_complete(_mcp_server.__aexit__(None, None, None))
    except RuntimeError:
        pass


atexit.register(_shutdown)


def unwrap_content(content) -> str:
    
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(item.text)
        return "\n".join(parts) if parts else str(content)
    if hasattr(content, "text"):
        return content.text
    return str(content)


async def respond(message: str, history: list[dict], agent_state: list):

    try:
        current_agent = await get_agent()
    except ConnectionError:
        logger.exception("MCP connection failed")
        yield "I'm having trouble connecting to our systems right now. Please try again in a moment.", agent_state
        return

    agent_input = agent_state + [{"role": "user", "content": message}]

    try:
        streamed_run = Runner.run_streamed(current_agent, input=agent_input)

        accumulated_text = ""
        async for event in streamed_run.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                if event.data.delta:
                    accumulated_text += event.data.delta
                    yield accumulated_text, gr.skip()

        completed_text = unwrap_content(streamed_run.final_output) if streamed_run.final_output else ""

        # Carry forward the full conversation state including tool call results
        updated_state = streamed_run.to_input_list()

        if not completed_text and not accumulated_text:
            yield "I'm sorry, I wasn't able to process that. Could you try rephrasing?", updated_state
        elif completed_text and completed_text != accumulated_text:
            yield completed_text, updated_state
        else:
            yield accumulated_text, updated_state

    except Exception:
        logger.exception("Agent run failed for message: %s", message[:100])
        yield "Something went wrong while handling your request. Please try again.", agent_state


css = """
.header { text-align: center; padding: 1.2rem 0 0.4rem 0; }
.header h1 { margin: 0; font-size: 1.6rem; color: #1e3a5f; }
.header p { margin: 0.3rem 0 0 0; color: #666; font-size: 0.95rem; }
footer { display: none !important; }
"""

with gr.Blocks() as app:
    gr.HTML("""
        <div class="header">
            <h1>🖥️ Meridian Electronics</h1>
            <p>Customer Support — Browse products, check orders, or place a new order</p>
        </div>
    """)

    agent_state = gr.State([])

    gr.ChatInterface(
        fn=respond,
        chatbot=gr.Chatbot(
            height=520,
            placeholder="Welcome to Meridian Electronics! How can I help you today?",
        ),
        textbox=gr.Textbox(
            placeholder="Type your message here...",
            container=False,
            scale=7,
        ),
        additional_inputs=[agent_state],
        additional_outputs=[agent_state],
        examples=[
            ["What products do you have?"],
            ["Show me your monitors"],
            ["I'd like to check my order history"],
            ["Help me find a keyboard"],
            ["I want to place an order"],
        ],
        cache_examples=False,
    )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        css=css,
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"),
    )
