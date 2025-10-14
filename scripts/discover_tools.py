# Script final para descubrir herramientas de Google API en el ADK.
import asyncio

from google.adk.tools.google_api_tool import (
    CalendarToolset,
    DocsToolset,
    GmailToolset
)

async def discover_tools(toolset, name):
    """Imprime las herramientas y sus descripciones para un toolset dado."""
    print(f"--- Herramientas en {name} ---")
    # get_tools() es una corutina, por lo que necesita ser llamada con 'await'
    tool_list = await toolset.get_tools()
    if not tool_list:
        print("No se encontraron herramientas en este Toolset.")
        return
    
    for tool in tool_list:
        description = ' '.join(tool.description.split())
        print(f"  - {tool.name}: {description[:120]}...")
    print("\n")

async def main():
    """Función principal asíncrona para ejecutar el descubrimiento."""
    print("Descubriendo herramientas disponibles en los Toolsets de Google API...\n")
    
    # Crear instancias de los Toolsets
    gmail_toolset = GmailToolset()
    docs_toolset = DocsToolset()
    calendar_toolset = CalendarToolset()

    await discover_tools(gmail_toolset, "GmailToolset")
    await discover_tools(docs_toolset, "DocsToolset")
    await discover_tools(calendar_toolset, "CalendarToolset")

if __name__ == "__main__":
    # Ejecutar la función principal asíncrona
    asyncio.run(main())
