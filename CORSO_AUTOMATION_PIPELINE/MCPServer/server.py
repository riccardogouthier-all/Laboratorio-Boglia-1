from mcp.server.fastmcp import FastMCP
import random

mcp = FastMCP("its-lab")   # il nome del server

@mcp.tool()
def roll_dice(sides: int = 6, n: int = 1) -> list[int]:
    """Tira n dadi da 'sides' facce."""
    return [random.randint(1, sides) for _ in range(n)]

if __name__ == "__main__":
    mcp.run(transport="stdio")