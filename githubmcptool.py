from typing import List,Dict,Optional
import os
import requests
import logging
from prometheus_client import Counter,Histogram,Gauge,start_http_server
from fastapi import FastAPI,Depends,HTTPException,Query
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel,Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MCP_BASE_URL= os.environ.get("MCP_BASE_URL", "http://localhost:8000")

GITHUB_SEARCHES = Counter('github_searches_total', 'Total GitHub searches', ['status'])

# --- Pydantic Models for FastAPI/MCP ---
# Define the response schema clearly for the AI agent (Tool Definition)
class RepositoryRecommendation(BaseModel):
    """A highly scored GitHub repository recommendation with hands-on content."""
    name: str = Field(..., description="The full name of the repository (e.g., 'user/repo-name').")
    url: str = Field(..., description="The public URL to the repository.")
    description: Optional[str] = Field(None, description="A brief description of the repository.")
    stars: int = Field(..., description="The number of star-gazers the repository has.")
    score: float = Field(..., description="The hands-on content score assigned by the analysis tool.")
    language: Optional[str] = Field(None, description="The primary language of the repository.")

class GitHubMcpTool:
    """MCP Tool for Researching Github Repository"""

    def __init__(self,github_token: Optional[str] = None):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }

        if self.github_token:
            self.headers['Authorization'] =f'token {self.github_token}'
            logger.info("GitHUbMcpTool initialized with token")
        else:
            logger.warning("Github_Token not found.")


    def search_repositories(self, query:str, keywords: List[str]) -> List[dict]:
        """Search Github Repositories based on query and keyword"""

        try:
            
            # hands_on_terms = "hands-on tutorial practical example"

            search_query = f"{query}"

            search_query += " in:name,description"

            logger.info(f"Github Search Query: {search_query}")

            params = {
                'q': search_query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 10
            }

            response = requests.get(
                f'{self.base_url}/search/repositories',
                headers=self.headers,
                params=params
            )

            if response.status_code == 200:
                GITHUB_SEARCHES.labels(status='success').inc()
                repos = response.json().get('items',[])
                return repos
            else:
                GITHUB_SEARCHES.labels(status='error').inc()
                logger.error(f"Github API Error: {response.status_code}")
                return []
        except Exception as e:
            GITHUB_SEARCHES.labels(status='error').inc()
            logger.error(f"Github searchh failed: {str(e)}",e)
            return []
        

    def analyze_repository(self,repo:Dict) -> Dict:

        """Analyze repository for hands-on content"""

        score = 0

        score += min(repo.get('stargazers_count',0) / 100 , 50)

        score += min(repo.get('forks_count',0) / 100 , 20)

        description = (repo.get('description','') or '').lower()
            
        hands_on_keywords = ['tutorial', 'example', 'hands-on', 'practical', 'guide', 'workshop', 'project']

        for keyword in hands_on_keywords:
            if keyword in description:
                score += 5


        if repo.get('has_wiki'):
            score += 5
        if 'README'in description.upper():
            score += 5

        return {
            'name': repo.get('full_name'),
            'url': repo.get('html_url'),
            'description': repo.get('description'),
            'stars': repo.get('stargazers_count', 0),
            'forks': repo.get('forks_count', 0),
            'language': repo.get('language'),
            'score': score,
            'updated_at': repo.get('updated_at')
        }
        
    def get_top_recommendations(self,event_title:str , max_results: int = 3) -> List[Dict]:
        """Get top GitHub repository recommendations for an event"""

        keywords = self._extract_keywords(event_title)
        
        repos = self.search_repositories(event_title,keywords)

        analyzed_repos = [self.analyze_repository(repo) for repo in repos]

        sorted_repos = sorted(analyzed_repos,key=lambda x: x['score'],reverse=True)

        return sorted_repos[:max_results]
    
    def _extract_keywords(self,text: str) -> List[str]:
        """Extract relevant keywords from event title"""
        tech_keywords = [
            'python', 'javascript', 'java', 'react', 'node', 'ai', 'ml', 
            'agent', 'llm', 'langchain', 'api', 'web', 'cloud', 'docker',
            'kubernetes', 'tensorflow', 'pytorch', 'django', 'flask'
        ]

        text_lower = text.lower()
        found_keywords = [kw for kw in tech_keywords if kw in text_lower]
        return found_keywords
    
app = FastAPI(
    title="GitHUb Learning Tool MCP Server",
    description="A Model Context Protocol server exposing a tool to find the best hands-on GitHub repositories for learning events.",
    version="1.0.0",
    servers=[
        {"url": MCP_BASE_URL}
    ]
)

github_tool = GitHubMcpTool()

@app.get(
    "/recommendation",
    response_model=List[RepositoryRecommendation],
    operation_id="get_top_github_recommendations",
    tags=["github_tool"]
)
async def get_top_recommendation_endpoint(
    event_title: str = Query(
        ...,
        description="The title of the learning event (e.g., 'Advanced Python with Asyncio')."
    ),
    max_results: int = Query(3, gt=0, le=10, description="The maximum number of repositories to return.")
):
    """
    Get top GitHub repository recommendations for a learning event.
    
    This function searches GitHub using the event title and keywords, then applies a custom
    hands-on score to rank the results, returning the best resources for a learner.
    """

    try:
        #Call the core logic of the tool instance
        results = github_tool.get_top_recommendations(event_title,max_results)
        return results
    except requests.exceptions.HTTPError as e:
        # Catch API errors (e.g., GitHub rate limit, 404)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.reason}. Check server logs for details."
        )
    
mcp = FastApiMCP(
    app,
    name="GitHub_HandsOn_Searcher",
    description="Tool for finding the best hands-on learning repositories on GitHub for any event."
)

mcp.mount()

if __name__ == "__main__":
    import uvicorn
    start_http_server(8001)
    logger.info("Starting FastAPI/MCP server on port 8000...")
    uvicorn.run(app,host="127.0.0.1",port=8000)