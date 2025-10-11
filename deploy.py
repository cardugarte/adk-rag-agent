"""
Deployment script for RAG Legal Agent to Vertex AI Agent Engine
"""
import os
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "escribania-mastropasqua")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = "gs://cloud-ai-platform-23597a65-584b-4f31-af48-fc810cfe7cd0"

print("🚀 Starting deployment to Agent Engine...")
print(f"   Project: {PROJECT_ID}")
print(f"   Location: {LOCATION}")
print(f"   Staging Bucket: {STAGING_BUCKET}")
print()

# Initialize Vertex AI
print("⚙️  Initializing Vertex AI...")
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Import agent after Vertex AI initialization
print("📦 Loading agent...")
from asistent.agent import root_agent

# Wrap agent in AdkApp
print("🔧 Wrapping agent in AdkApp...")
app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True
)

# Deploy to Agent Engine
print("☁️  Deploying to Agent Engine...")
print("   (This may take several minutes, please wait...)")
print()

try:
    remote_app = agent_engines.create(
        agent_engine=app,
        requirements=[
            "google-cloud-aiplatform[adk,agent_engines]",
            "google-generativeai",
            "python-dotenv",
            "google-cloud-storage",
            "google-genai"
        ],
        extra_packages=["./asistent"],
        display_name="RAG Legal Agent",
        description="Vertex AI RAG Agent specialized in legal contract analysis for Argentina"
    )

    print()
    print("✅ Agent deployed successfully!")
    print()
    print(f"📍 Resource name: {remote_app.resource_name}")
    print()
    print("🧪 Testing deployment...")

    # Simple test query
    response = remote_app.query("Hola, ¿estás funcionando?")
    print(f"   Response: {response}")
    print()
    print("🎉 Deployment completed successfully!")
    print()
    print("📝 To interact with your agent:")
    print("   from vertexai import agent_engines")
    print(f"   agent = agent_engines.get('{remote_app.resource_name}')")
    print("   response = agent.query('tu pregunta aquí')")

except Exception as e:
    print()
    print(f"❌ Deployment failed: {str(e)}")
    print()
    print("💡 Common issues:")
    print("   - Check that Vertex AI API is enabled")
    print("   - Verify your authentication is valid")
    print("   - Ensure your project has billing enabled")
    raise
