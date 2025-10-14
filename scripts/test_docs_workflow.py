"""
Script to test Google Docs workflow:
1. Get a document and inspect its JSON structure
2. Test what parameters docs_documents_create accepts
"""
import asyncio
import json
import sys
sys.path.insert(0, '/home/cardugarte/projects/adk-rag-agent')

from asistent.auth.auth_config import docs_tool_set

async def test_get_document():
    """Test getting a document and inspect the JSON structure."""
    print("\n" + "="*60)
    print("TEST 1: Getting document structure")
    print("="*60)

    # Document ID from the error you showed me
    document_id = "1LNNuCNSORhw4yH2k9-jBqHxSycToDIUeCBANrvMVug0"

    # Get all available tools
    tools = await docs_tool_set.get_tools()

    # Find the get tool
    get_tool = None
    for tool in tools:
        if tool.name == "docs_documents_get":
            get_tool = tool
            break

    if not get_tool:
        print("❌ docs_documents_get not found!")
        return None

    print(f"✅ Found tool: {get_tool.name}")
    print(f"Description: {get_tool.description[:100]}...")

    # Try to get the document
    print(f"\n📄 Getting document: {document_id}")
    try:
        # Execute the tool
        result = await get_tool.execute(document_id=document_id)
        print(f"\n✅ Document retrieved successfully!")
        print(f"Type of result: {type(result)}")

        # Save to file for inspection
        with open('/tmp/document_structure.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full JSON saved to: /tmp/document_structure.json")

        # Print summary
        if isinstance(result, dict):
            print(f"\n📊 JSON Structure:")
            print(f"  - Keys: {list(result.keys())}")
            if 'title' in result:
                print(f"  - Title: {result['title']}")
            if 'documentId' in result:
                print(f"  - Document ID: {result['documentId']}")
            if 'body' in result:
                print(f"  - Has body: Yes")
                if 'content' in result['body']:
                    print(f"  - Body content items: {len(result['body']['content'])}")
            if 'documentStyle' in result:
                print(f"  - Has documentStyle: Yes")
                print(f"  - Style keys: {list(result['documentStyle'].keys())}")

        return result

    except Exception as e:
        print(f"❌ Error getting document: {e}")
        return None


async def test_create_document_params():
    """Test what parameters docs_documents_create accepts."""
    print("\n" + "="*60)
    print("TEST 2: Checking docs_documents_create parameters")
    print("="*60)

    # Get all available tools
    tools = await docs_tool_set.get_tools()

    # Find the create tool
    create_tool = None
    for tool in tools:
        if tool.name == "docs_documents_create":
            create_tool = tool
            break

    if not create_tool:
        print("❌ docs_documents_create not found!")
        return

    print(f"✅ Found tool: {create_tool.name}")
    print(f"Description: {create_tool.description}")

    # Inspect the tool's input schema
    if hasattr(create_tool, 'input_schema'):
        print(f"\n📋 Input Schema:")
        print(json.dumps(create_tool.input_schema, indent=2))

    # Try to access the underlying API method
    if hasattr(create_tool, '_openapi_tool'):
        print(f"\n🔧 Underlying OpenAPI tool info available")


async def test_create_simple_document():
    """Test creating a simple document with just title."""
    print("\n" + "="*60)
    print("TEST 3: Creating simple document (title only)")
    print("="*60)

    tools = await docs_tool_set.get_tools()
    create_tool = None
    for tool in tools:
        if tool.name == "docs_documents_create":
            create_tool = tool
            break

    if not create_tool:
        print("❌ docs_documents_create not found!")
        return None

    try:
        result = await create_tool.execute(title="Test Document - Simple")
        print(f"✅ Document created!")
        print(f"Document ID: {result.get('documentId')}")
        return result
    except Exception as e:
        print(f"❌ Error creating document: {e}")
        return None


async def test_create_with_body():
    """Test creating a document with body content."""
    print("\n" + "="*60)
    print("TEST 4: Creating document with body content")
    print("="*60)

    tools = await docs_tool_set.get_tools()
    create_tool = None
    for tool in tools:
        if tool.name == "docs_documents_create":
            create_tool = tool
            break

    if not create_tool:
        print("❌ docs_documents_create not found!")
        return None

    # Try with body parameter
    try:
        body_content = {
            'title': 'Test Document - With Body',
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'This is test content\n'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        print(f"Attempting to create with body parameter...")
        result = await create_tool.execute(**body_content)
        print(f"✅ Document created with body!")
        print(f"Document ID: {result.get('documentId')}")
        return result
    except Exception as e:
        print(f"❌ Error creating with body: {e}")
        print(f"Error type: {type(e)}")
        return None


async def main():
    """Run all tests."""
    print("\n🧪 Testing Google Docs Workflow\n")

    # Test 1: Get document structure
    doc_structure = await test_get_document()

    # Test 2: Check create parameters
    await test_create_document_params()

    # Test 3: Create simple document
    simple_doc = await test_create_simple_document()

    # Test 4: Try creating with body
    body_doc = await test_create_with_body()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Get document: {'Success' if doc_structure else 'Failed'}")
    print(f"✅ Create simple: {'Success' if simple_doc else 'Failed'}")
    print(f"✅ Create with body: {'Success' if body_doc else 'Failed'}")
    print("\n📄 Check /tmp/document_structure.json for full document JSON")


if __name__ == "__main__":
    asyncio.run(main())
