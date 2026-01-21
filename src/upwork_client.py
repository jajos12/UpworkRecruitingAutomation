"""Upwork API client with OAuth2 authentication and GraphQL support."""

import httpx
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.utils.logger import get_logger
from src.utils.config_loader import UpworkConfig

logger = get_logger(__name__)


class UpworkAPIError(Exception):
    """Base exception for Upwork API errors."""

    pass


class UpworkRateLimitError(UpworkAPIError):
    """Raised when rate limit is exceeded."""

    pass


class UpworkAuthError(UpworkAPIError):
    """Raised when authentication fails."""

    pass


class UpworkClient:
    """
    Upwork API client using GraphQL endpoint with OAuth2 authentication.

    Handles:
    - OAuth2 Bearer token authentication
    - GraphQL queries and mutations
    - Automatic retry with exponential backoff
    - Rate limiting
    - Token refresh
    """

    BASE_URL = "https://api.upwork.com/graphql"
    TOKEN_REFRESH_URL = "https://www.upwork.com/api/v3/oauth2/token"

    def __init__(self, config: UpworkConfig):
        """
        Initialize Upwork API client.

        Args:
            config: Upwork configuration with credentials
        """
        self.config = config
        self.access_token = config.access_token
        self.refresh_token = config.refresh_token
        self.client = httpx.Client(timeout=30.0)
        logger.info("Upwork API client initialized")

    def _headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "UpworkHireBot/1.0",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Response data dictionary

        Raises:
            UpworkAPIError: If API request fails
            UpworkRateLimitError: If rate limit exceeded
            UpworkAuthError: If authentication fails
        """
        logger.debug(f"Executing GraphQL query: {query[:100]}...")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = self.client.post(
                self.BASE_URL, headers=self._headers(), json=payload
            )

            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting before retry...")
                time.sleep(self.config.rate_limit_delay_seconds)
                raise UpworkRateLimitError("Rate limit exceeded")

            # Handle auth errors
            if response.status_code == 401:
                logger.warning("Authentication failed, attempting token refresh...")
                self._refresh_access_token()
                # Retry with new token
                response = self.client.post(
                    self.BASE_URL, headers=self._headers(), json=payload
                )

            response.raise_for_status()
            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                logger.error(f"GraphQL error: {error_msg}")
                raise UpworkAPIError(f"GraphQL error: {error_msg}")

            logger.debug("Query executed successfully")
            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise UpworkAPIError(f"API request failed: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise UpworkAPIError(f"Request failed: {e}")

    def _refresh_access_token(self) -> None:
        """
        Refresh the access token using refresh token.

        Raises:
            UpworkAuthError: If token refresh fails
        """
        logger.info("Refreshing access token...")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            response = self.client.post(self.TOKEN_REFRESH_URL, data=payload)
            response.raise_for_status()
            data = response.json()

            self.access_token = data["access_token"]
            if "refresh_token" in data:
                self.refresh_token = data["refresh_token"]

            logger.info("Access token refreshed successfully")
            logger.warning(
                "IMPORTANT: Update your .env file with new tokens:\n"
                f"UPWORK_ACCESS_TOKEN={self.access_token}\n"
                f"UPWORK_REFRESH_TOKEN={self.refresh_token}"
            )

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise UpworkAuthError(f"Failed to refresh token: {e}")

    def get_open_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all open job postings for the authenticated user's organization.

        Returns:
            List of job dictionaries with id, title, description
        """
        logger.info("Fetching open jobs...")

        query = """
        query {
          organization {
            jobs(filter: {status: OPEN}) {
              edges {
                node {
                  id
                  title
                  description
                  createdDateTime
                }
              }
            }
          }
        }
        """

        try:
            result = self.execute_query(query)
            jobs = []

            if result.get("data", {}).get("organization", {}).get("jobs"):
                edges = result["data"]["organization"]["jobs"]["edges"]
                jobs = [edge["node"] for edge in edges]

            logger.info(f"Found {len(jobs)} open jobs")
            return jobs

        except Exception as e:
            logger.error(f"Failed to fetch jobs: {e}")
            raise

    def get_job_proposals(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all proposals for a specific job.

        Args:
            job_id: Upwork job ID

        Returns:
            List of proposal dictionaries with applicant and proposal data
        """
        logger.info(f"Fetching proposals for job: {job_id}")

        query = """
        query GetJobProposals($jobId: ID!) {
          marketplaceJobPosting(id: $jobId) {
            id
            title
            description
            proposals {
              edges {
                node {
                  id
                  coverLetter
                  chargedAmount
                  proposedTerms {
                    duration
                  }
                  submittedDateTime
                  freelancer {
                    id
                    name
                    title
                    hourlyRate
                    location {
                      city
                      country
                      timezone
                    }
                    stats {
                      jobSuccessScore
                      totalEarnings
                      totalJobsCount
                    }
                    topRatedStatus
                    skills {
                      name
                    }
                    workHistory {
                      edges {
                        node {
                          title
                          description
                          feedback {
                            score
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        try:
            variables = {"jobId": job_id}
            result = self.execute_query(query, variables)

            proposals = []
            job_data = result.get("data", {}).get("marketplaceJobPosting")

            if job_data and job_data.get("proposals"):
                edges = job_data["proposals"]["edges"]
                proposals = [edge["node"] for edge in edges]

            logger.info(f"Found {len(proposals)} proposals for job {job_id}")
            return proposals

        except Exception as e:
            logger.error(f"Failed to fetch proposals for job {job_id}: {e}")
            raise

    def get_freelancer_profile(self, freelancer_id: str) -> Dict[str, Any]:
        """
        Get detailed freelancer profile information.

        Args:
            freelancer_id: Upwork freelancer ID

        Returns:
            Freelancer profile dictionary
        """
        logger.info(f"Fetching profile for freelancer: {freelancer_id}")

        query = """
        query GetFreelancerProfile($freelancerId: ID!) {
          freelancer(id: $freelancerId) {
            id
            name
            title
            hourlyRate
            location {
              city
              country
              timezone
            }
            stats {
              jobSuccessScore
              totalEarnings
              totalJobsCount
              totalHours
            }
            topRatedStatus
            skills {
              name
              level
            }
            workHistory {
              edges {
                node {
                  title
                  description
                  startDate
                  endDate
                  feedback {
                    score
                    comment
                  }
                }
              }
            }
            portfolio {
              edges {
                node {
                  title
                  description
                  url
                }
              }
            }
          }
        }
        """

        try:
            variables = {"freelancerId": freelancer_id}
            result = self.execute_query(query, variables)

            profile = result.get("data", {}).get("freelancer", {})
            logger.info(f"Retrieved profile for {profile.get('name', 'Unknown')}")
            return profile

        except Exception as e:
            logger.error(f"Failed to fetch freelancer profile {freelancer_id}: {e}")
            raise

    def send_message(self, room_id: str, message: str) -> bool:
        """
        Send a message to an applicant.

        Args:
            room_id: Conversation room ID
            message: Message text to send

        Returns:
            True if message sent successfully
        """
        logger.info(f"Sending message to room: {room_id}")

        mutation = """
        mutation SendMessage($roomId: ID!, $message: String!) {
          sendMessage(input: {
            roomId: $roomId
            message: $message
          }) {
            message {
              id
              createdDateTime
            }
          }
        }
        """

        try:
            variables = {"roomId": room_id, "message": message}
            result = self.execute_query(mutation, variables)

            success = "sendMessage" in result.get("data", {})
            if success:
                logger.info("Message sent successfully")
            else:
                logger.error("Message send failed")

            return success

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def search_freelancers(
        self, query: str, skills: Optional[List[str]] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for freelancers matching criteria.

        Args:
            query: Search query string
            skills: Optional list of required skills
            limit: Maximum number of results

        Returns:
            List of freelancer profile dictionaries
        """
        logger.info(f"Searching for freelancers: {query}")

        # Note: This is a placeholder - actual GraphQL schema may differ
        gql_query = """
        query SearchFreelancers($query: String!, $limit: Int!) {
          freelancerProfileRecords(
            search: $query
            limit: $limit
          ) {
            edges {
              node {
                id
                name
                title
                hourlyRate
                location {
                  country
                  timezone
                }
                stats {
                  jobSuccessScore
                  totalEarnings
                }
                topRatedStatus
                skills {
                  name
                }
              }
            }
          }
        }
        """

        try:
            variables = {"query": query, "limit": limit}
            result = self.execute_query(gql_query, variables)

            freelancers = []
            if result.get("data", {}).get("freelancerProfileRecords"):
                edges = result["data"]["freelancerProfileRecords"]["edges"]
                freelancers = [edge["node"] for edge in edges]

            logger.info(f"Found {len(freelancers)} freelancers")
            return freelancers

        except Exception as e:
            logger.error(f"Freelancer search failed: {e}")
            raise

    def close(self):
        """Close the HTTP client."""
        self.client.close()
        logger.info("Upwork API client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Mock Client Implementation
import random
try:
    from backend.mock_data import JOB_TEMPLATES, FREELANCER_TEMPLATES
except ImportError:
    JOB_TEMPLATES = []
    FREELANCER_TEMPLATES = []

class MockUpworkClient(UpworkClient):
    """Mock client for testing without API access."""
    
    def __init__(self, config: Optional[UpworkConfig] = None):
        # We don't call super().__init__ to avoid httpx client usage
        self.config = config
        logger.info("MOCK Upwork API client initialized - Running in SIMULATION mode")

    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock query execution."""
        return {"data": {}}

    def get_open_jobs(self) -> List[Dict[str, Any]]:
        """Return mock jobs."""
        logger.info("[MOCK] Fetching open jobs...")
        jobs = []
        for i, template in enumerate(JOB_TEMPLATES):
            # Create a deterministic but unique-looking ID
            job_id = f"mock-job-{i}-{abs(hash(template['title'])) % 10000}"
            jobs.append({
                "id": job_id,
                "title": template['title'],
                "description": template['description'],
                "createdDateTime": datetime.now().isoformat()
            })
        
        return jobs

    def get_job_proposals(self, job_id: str) -> List[Dict[str, Any]]:
        """Return mock proposals for a job."""
        logger.info(f"[MOCK] Fetching proposals for job: {job_id}")
        
        proposals = []
        # Generate 3-8 proposals per job, deterministically based on job_id
        seed = 0
        for char in job_id:
            seed = (seed * 31 + ord(char)) & 0xFFFFFFFF
            
        random.seed(seed)
        num_proposals = 3 + (seed % 5)
        
        for i in range(num_proposals):
            # Pick a random freelancer template
            freelancer = FREELANCER_TEMPLATES[i % len(FREELANCER_TEMPLATES)]
            
            proposal_id = f"mock-prop-{job_id}-{i}"
            
            # Format skills for proposal node
            skills_node = [{"name": s} for s in freelancer["skills"]]
            
            proposal_node = {
                "id": proposal_id,
                "coverLetter": freelancer.get("cover_letter_template", "I am interested.").format(
                    skill=freelancer["skills"][0] if freelancer["skills"] else "Python",
                    number=str(random.randint(2,10)),
                    previous_client_type="startups",
                    specific_achievement="built a similar system",
                    reason="it matches my skills",
                    relevant_skill=freelancer["skills"][1] if len(freelancer["skills"]) > 1 else "coding",
                    achievement="great results",
                    project_goal="success"
                ),
                "chargedAmount": {
                    "amount": freelancer["hourly_rate"],
                    "currencyCode": "USD"
                },
                "proposedTerms": {
                    "duration": "1 to 3 months"
                },
                "submittedDateTime": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "freelancer": {
                    "id": f"mock-fl-{abs(hash(freelancer['name']))}",
                    "name": freelancer["name"],
                    "title": freelancer["title"],
                    "hourlyRate": {
                        "amount": freelancer["hourly_rate"],
                        "currencyCode": "USD"
                    },
                    "location": {
                        "city": "Remote City H",
                        "country": "United States",
                        "timezone": "UTC-5"
                    },
                    "stats": {
                        "jobSuccessScore": freelancer["job_success_score"],
                        "totalEarnings": freelancer["total_earnings"],
                        "totalJobsCount": int(freelancer["total_earnings"] / 500) if freelancer["total_earnings"] else 0
                    },
                    "topRatedStatus": freelancer.get("top_rated_status", None),
                    "skills": skills_node,
                    "workHistory": {
                        "edges": [] 
                    }
                }
            }
            proposals.append(proposal_node)
            
        return proposals

    def get_freelancer_profile(self, freelancer_id: str) -> Dict[str, Any]:
        logger.info(f"[MOCK] Fetching profile for: {freelancer_id}")
        # Just return the first template for now as fallback
        f = FREELANCER_TEMPLATES[0]
        return {
            "id": freelancer_id,
            "name": f["name"],
            "title": f["title"],
            "description": f["bio"],
        }

    def send_message(self, room_id: str, message: str) -> bool:
        logger.info(f"[MOCK] Sending message to {room_id}: {message}")
        return True

    def search_freelancers(self, query: str, skills: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        logger.info(f"[MOCK] Searching freelancers: {query}")
        return [] # Implement later if needed
        
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
