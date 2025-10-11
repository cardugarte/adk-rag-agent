"""
Simple script to interact with the deployed RAG Legal Agent
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

print("🤖 RAG Legal Agent - Interactive Session")
print(f"📍 Resource: {agent.resource_name}")
print()

async def chat():
    """Interactive chat with the agent"""
    # Create a session
    print("📝 Creating session...")
    session = await agent.async_create_session(user_id="interactive-user")
    session_id = session.get('id')
    print(f"✅ Session created: {session_id}")
    print()
    print("💬 You can now chat with the agent. Type 'exit' to quit.")
    print("-" * 60)
    print()

    while True:
        # Get user input
        user_message = input("You: ")
        if user_message.lower() in ['exit', 'quit', 'salir']:
            print("\n👋 Goodbye!")
            break

        # Send message to agent
        print("Agent: ", end='', flush=True)
        response_stream = agent.async_stream_query(
            message=user_message,
            user_id="interactive-user",
            session_id=session_id
        )

        # Process response
        async for event in response_stream:
            if isinstance(event, dict) and 'content' in event:
                # Extract text from the response
                parts = event['content'].get('parts', [])
                for part in parts:
                    if 'text' in part:
                        print(part['text'], end='', flush=True)

        print("\n")

# Run the chat
asyncio.run(chat())
