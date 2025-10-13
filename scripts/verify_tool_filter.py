"""
Script to verify that tool filtering is working correctly for Google API toolsets.
"""
import asyncio
import sys
sys.path.insert(0, '/home/cardugarte/projects/adk-rag-agent')

from asistent.auth.auth_config import gmail_tool_set, docs_tool_set, calendar_tool_set
from asistent.auth.auth_config import GMAIL_TOOLS, DOCS_TOOLS, CALENDAR_TOOLS

async def verify_toolset_filtering(toolset, toolset_name, expected_tools):
    """Verify that a toolset only has the expected filtered tools."""
    print(f"\n{'='*60}")
    print(f"Verificando {toolset_name}")
    print(f"{'='*60}")
    print(f"Herramientas esperadas: {len(expected_tools)}")
    print(f"Lista de herramientas esperadas:")
    for tool in expected_tools:
        print(f"  - {tool}")

    # Get actual tools from the toolset
    tool_list = await toolset.get_tools()
    actual_tool_names = [tool.name for tool in tool_list]

    print(f"\nHerramientas encontradas: {len(actual_tool_names)}")
    print(f"Lista de herramientas encontradas:")
    for tool_name in actual_tool_names:
        print(f"  - {tool_name}")

    # Check if filtering worked
    if set(actual_tool_names) == set(expected_tools):
        print(f"\n✅ ÉXITO: {toolset_name} tiene exactamente las herramientas esperadas")
        return True
    else:
        print(f"\n❌ ERROR: {toolset_name} no tiene las herramientas esperadas")
        extra_tools = set(actual_tool_names) - set(expected_tools)
        missing_tools = set(expected_tools) - set(actual_tool_names)

        if extra_tools:
            print(f"Herramientas extra (no deberían estar): {extra_tools}")
        if missing_tools:
            print(f"Herramientas faltantes: {missing_tools}")
        return False

async def main():
    """Main verification function."""
    print("\n🔍 Verificando filtrado de herramientas en Google API Toolsets...")

    results = []

    # Verify Gmail toolset
    gmail_result = await verify_toolset_filtering(
        gmail_tool_set,
        "GmailToolset",
        GMAIL_TOOLS
    )
    results.append(("GmailToolset", gmail_result))

    # Verify Docs toolset
    docs_result = await verify_toolset_filtering(
        docs_tool_set,
        "DocsToolset",
        DOCS_TOOLS
    )
    results.append(("DocsToolset", docs_result))

    # Verify Calendar toolset
    calendar_result = await verify_toolset_filtering(
        calendar_tool_set,
        "CalendarToolset",
        CALENDAR_TOOLS
    )
    results.append(("CalendarToolset", calendar_result))

    # Summary
    print(f"\n{'='*60}")
    print("RESUMEN DE VERIFICACIÓN")
    print(f"{'='*60}")

    all_passed = True
    for toolset_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{toolset_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 Todas las verificaciones pasaron correctamente!")
        return 0
    else:
        print("\n⚠️  Algunas verificaciones fallaron.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
