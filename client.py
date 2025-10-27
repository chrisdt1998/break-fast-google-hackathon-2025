import asyncio
from fastmcp import Client

# HTTP server
client = Client("http://127.0.0.1:8000/mcp")

async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        # List available operations
        tools = await client.list_tools()
        print(tools)

        # Execute operations
        result = await client.call_tool("get_counter", {})
        print(f"Current counter: {result}")


if __name__ == "__main__":
    asyncio.run(main())
