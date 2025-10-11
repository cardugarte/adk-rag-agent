"""
Test script for deployed RAG Agent
"""
import asyncio
from vertexai import agent_engines
import vertexai

# Initialize Vertex AI
vertexai.init(
    project="escribania-mastropasqua",
    location="us-central1"
)

# Get the deployed agent
AGENT_RESOURCE_NAME = "projects/997298514042/locations/us-central1/reasoningEngines/1053512459316363264"
agent = agent_engines.get(AGENT_RESOURCE_NAME)

print("🤖 Testing deployed RAG Legal Agent...")
print(f"   Resource: {agent.resource_name}")
print()

async def test_agent():
    """Test the agent with a simple query"""
    # First, create a session
    print("📝 Creating session...")
    session = await agent.async_create_session(user_id="test-user")
    session_id = session.get('name') or session.get('id') or str(session)
    print(f"   Session created: {session_id}")
    print(f"   Session data: {session}")
    print()

    print("📝 Sending test query: '¿Qué puedes hacer?'")
    print()

    # Use async_stream_query with the session
    response_stream = agent.async_stream_query(
        message="¿Qué puedes hacer?",
        user_id="test-user",
        session_id=session_id
    )

    print("💬 Response:")
    full_response = ""
    event_count = 0
    async for event in response_stream:
        event_count += 1
        print(f"\n[Event #{event_count}]")
        print(f"Type: {type(event)}")
        print(f"Event: {event}")

        # Try different ways to extract text
        if hasattr(event, 'text'):
            full_response += event.text
            print(f"Extracted via .text: {event.text}")
        elif hasattr(event, 'content'):
            full_response += str(event.content)
            print(f"Extracted via .content: {event.content}")
        elif isinstance(event, dict):
            # Try various dict keys
            for key in ['text', 'content', 'message', 'data']:
                if key in event:
                    full_response += str(event[key])
                    print(f"Extracted via dict['{key}']: {event[key]}")
                    break
        elif isinstance(event, str):
            full_response += event
            print(f"Extracted as string: {event}")

    print()
    print(f"\n📊 Total events received: {event_count}")
    print()
    if full_response:
        print(f"✅ Agent is working!")
        print(f"💬 Full response:\n{full_response}")
    else:
        print("⚠️  Agent responded but no text was extracted")

# Run the test
asyncio.run(test_agent())
