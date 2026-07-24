from mcp.server.fastmcp import FastMCP
import random

mcp = FastMCP("its-lab")   # il nome del server

@mcp.tool()
def roll_dice(sides: int = 6, n: int = 1) -> list[int]:
    """Tira n dadi da 'sides' facce."""
    return [random.randint(1, sides) for _ in range(n)]

@mcp.tool()
def count_words(text: str) -> int:
    """Conta le parole in un testo."""
    t = text.strip()
    return len(t.split()) if t else 0

@mcp.tool()
def check_build_log(log: str) -> dict:
    """Analizza un log di build: conta gli errori
    e dice se e' passata."""
    errori = log.lower().count("error")
    return {"errori": errori, "passata": errori == 0}

@mcp.resource("config://motd")
def motd() -> str:
    """Messaggio del giorno."""
    return "Benvenuti al lab MCP di ITS ICT Piemonte!"

if __name__ == "__main__":
    mcp.run(transport="stdio")




    # "C:","Users","riccardo.gouthier","Desktop","GITHUB","Laboratorio-Boglia-1","CORSO_AUTOMATION_PIPELINE","MCPServer",
    # prova a inserirle come modifica nel file di configurazione del server .json