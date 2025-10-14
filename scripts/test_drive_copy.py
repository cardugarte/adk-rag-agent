"""
Script to test DriveToolset and drive_files_copy functionality.
"""
import asyncio
import sys
sys.path.insert(0, '/home/cardugarte/projects/adk-rag-agent')

from asistent.auth.auth_config import drive_tool_set

async def test_drive_tools():
    """Test that DriveToolset is configured correctly and list available tools."""
    print("\n" + "="*60)
    print("TEST: DriveToolset Configuration")
    print("="*60)

    try:
        # Get all available tools
        tools = await drive_tool_set.get_tools()

        print(f"✅ DriveToolset loaded successfully!")
        print(f"📊 Total tools available: {len(tools)}")
        print(f"\n📋 Available tools:")

        for tool in tools:
            print(f"\n  Tool: {tool.name}")
            print(f"  Description: {tool.description[:150]}...")

        # Check if drive_files_copy is available
        copy_tool = None
        for tool in tools:
            if tool.name == "drive_files_copy":
                copy_tool = tool
                break

        if copy_tool:
            print(f"\n✅ drive_files_copy found!")
            print(f"Description: {copy_tool.description}")
        else:
            print(f"\n❌ drive_files_copy NOT found in toolset")

        return tools

    except Exception as e:
        print(f"❌ Error loading DriveToolset: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests."""
    print("\n🧪 Testing DriveToolset\n")

    tools = await test_drive_tools()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ DriveToolset: {'Success' if tools else 'Failed'}")
    print(f"✅ Tools loaded: {len(tools) if tools else 0}")


if __name__ == "__main__":
    asyncio.run(main())
