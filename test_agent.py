import asyncio
import pytest
from agents import Runner
from agent import create_mcp_server, create_agent


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def support_agent():
    mcp = create_mcp_server()
    async with mcp:
        yield create_agent(mcp)


@pytest.mark.asyncio
async def test_product_browsing(support_agent):
    run = await Runner.run(support_agent, input="What monitors do you have?")
    reply = run.final_output.lower()
    assert "monitor" in reply
    assert "sku" in reply or "price" in reply or "$" in reply


@pytest.mark.asyncio
async def test_auth_required_for_orders(support_agent):
    run = await Runner.run(support_agent, input="Show me my order history")
    reply = run.final_output.lower()
    assert "email" in reply or "pin" in reply or "verify" in reply or "authenticate" in reply


@pytest.mark.asyncio
async def test_successful_auth(support_agent):
    run = await Runner.run(support_agent, input=[
        {"role": "user", "content": "I want to see my orders"},
        {"role": "assistant", "content": "I'd be happy to help! Could you please provide your email address and 4-digit PIN?"},
        {"role": "user", "content": "donaldgarcia@example.net 7912"},
    ])
    reply = run.final_output.lower()
    assert "donald" in reply or "order" in reply


@pytest.mark.asyncio
async def test_failed_auth(support_agent):
    run = await Runner.run(support_agent, input=[
        {"role": "user", "content": "Check my orders please"},
        {"role": "assistant", "content": "Sure! Please provide your email and 4-digit PIN."},
        {"role": "user", "content": "donaldgarcia@example.net 0000"},
    ])
    reply = run.final_output.lower()
    assert "try again" in reply or "incorrect" in reply or "not" in reply or "invalid" in reply
