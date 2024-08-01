import requests
from bs4 import BeautifulSoup

def python_math_execution(math_string):
    try:
        answer = eval(math_string)
        if answer:
            return str(answer)
    except:
        return 'invalid code generated' 

def analyze_sentiment(game_name: str) -> dict:
    """
    Fetches the Metacritic score for a given game.
    Returns a dictionary with the game name and its Metacritic score.
    """
    try:
        # Format the game name for the URL
        formatted_name = game_name.lower().replace(':', '').replace(' ', '-')
        url = f"https://www.metacritic.com/game/{formatted_name}"

        # Send a GET request to the URL
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the Metascore element
        metascore_elem = soup.find('div', title=lambda value: value and 'Metascore' in value)
        
        if metascore_elem:
            score = metascore_elem['title'].split()[1]
            return {"game": game_name, "metascore": score}
        else:
            return {"game": game_name, "metascore": "Not found"}

    except requests.RequestException as e:
        return {"game": game_name, "error": str(e)}

    except Exception as e:
        return {"game": game_name, "error": f"An unexpected error occurred: {str(e)}"}


functions = [ 
    {
        "type": "function",
        "function": {
            "name": "python_math_execution",
            "description": "Solve a math problem using python code",
            "parameters": {
                "type": "object",
                "properties": {
                    "math_string": {
                        "type": "string",
                        "description": "A string that solves a math problem that conforms with python syntax that could be passed directly to an eval() function",
                    },
                },
                "required": ["math_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sentiment",
            "description": "Returns the metacritic score of a video game",
            "parameters": {
                "type": "object",
                "properties": {
                    "game_name": {
                        "type": "string",
                        "description":"The name of the video game that will be looked up",
                    },
                },
                "required": ["game_name"],
            },
        },
    },
    
]

def run_function(name: str, args: dict): 
    if name == "python_math_execution":
        return python_math_execution(args["math_string"])
    elif name == "analyze_sentiment":
        return analyze_sentiment(args["game_name"])
    else:
        return None