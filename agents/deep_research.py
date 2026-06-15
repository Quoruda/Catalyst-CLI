import json
import concurrent.futures
from typing import Dict, Any, List, Optional, Callable
from agent import BaseAgent

class DeepResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="deep_research",
            description="Programmatic agent that performs deep internet research using iterative BFS and concurrent scraping.",
            tools=["web_search", "read_webpage"],
            delegation_instruction="State the research objective clearly."
        )
        # Configuration for research limits
        self.max_depth = 3  # 0 = initial search, 1-3 = follow-ups
        self.max_urls_per_query = 3
        self.max_concurrent_workers = 5

    def fetch_pages_in_parallel(self, urls: List[str]) -> Dict[str, str]:
        import contextvars
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_workers) as executor:
            future_to_url = {
                executor.submit(contextvars.copy_context().run, self.call_tool, "read_webpage", url=url): url 
                for url in urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content = future.result()
                    if content and not str(content).startswith("Error"):
                        results[url] = content
                except Exception as e:
                    self.log_error(f"Error fetching {url}: {e}")
        return results

    def extract_facts_in_parallel(self, pages: Dict[str, str], original_query: str) -> List[str]:
        import contextvars
        extracted_notes = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_workers) as executor:
            future_to_url = {}
            for url, content in pages.items():
                prompt = (
                    "Extract all key facts, findings, and figures from the following text "
                    "that are highly relevant to answering the user's research topic: '{query}'.\n"
                    "Do not omit any important details, statistics, or conflicting viewpoints.\n"
                    "Ignore navigation menus, ads, and irrelevant information.\n"
                    "Source URL: {url}\n\n"
                    "Text content:\n{content}"
                ).format(query=original_query, url=url, content=content[:6000])
                
                future = executor.submit(contextvars.copy_context().run, self.generate, [{"role": "user", "content": prompt}])
                future_to_url[future] = url
                
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    response = future.result()
                    if response.content:
                        extracted_notes.append(f"Source: {url}\nKey Findings:\n{response.content.strip()}")
                except Exception as e:
                    self.log_error(f"Error extracting facts from {url}: {e}")
                    
        return extracted_notes

    def generate_initial_queries(self, original_query: str) -> List[str]:
        self.log_thought("Planning initial research strategy...")
        prompt = (
            "You are a deep research planner. The user wants to research: '{query}'\n"
            "Generate up to 3 distinct, highly optimized search queries to begin the research.\n"
            "Queries should be simple, natural, and keyword-focused. Avoid complex boolean operators (like OR, AND, -, filetype:) as they do not work well on the search engine.\n"
            "Respond ONLY with a JSON array of strings. Example: [\"query 1\", \"query 2\"]\n"
        ).format(query=original_query)
        
        try:
            res = self.generate([{"role": "user", "content": prompt}])
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            queries = json.loads(content.strip())
            if isinstance(queries, list) and queries:
                return queries[:3]
        except Exception:
            pass
        return [original_query]

    def generate_follow_up_queries(self, current_facts: List[str], original_query: str) -> List[str]:
        if not current_facts:
            return []
            
        facts_text = "\n\n".join(current_facts)
        prompt = (
            "You are a deep research planner. The user wants to thoroughly research: '{query}'\n"
            "Based on the facts gathered so far (below), identify critical missing information or "
            "interesting new leads that need to be explored to provide a complete answer.\n"
            "If the current facts completely and thoroughly answer the user's research topic, and no further information is needed, return an empty array [].\n"
            "Otherwise, generate up to 2 specific follow-up search queries.\n"
            "Queries should be simple, natural, and keyword-focused. Avoid complex boolean operators (like OR, AND, -, filetype:) as they do not work well on the search engine.\n"
            "Respond ONLY with a JSON array of strings. Example: [\"new query 1\", \"new query 2\"]\n\n"
            "Current Facts:\n{facts}"
        ).format(query=original_query, facts=facts_text)
        
        try:
            res = self.generate([{"role": "user", "content": prompt}])
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            queries = json.loads(content.strip())
            if isinstance(queries, list):
                return queries[:2]
        except Exception:
            pass
        return []

    def synthesize_report(self, facts: List[str], original_query: str) -> str:
        self.log_thought("Synthesizing final research report")
        if not facts:
            return "No relevant facts could be found to answer the query."
            
        synthesize_prompt = (
            "You are a Senior Researcher. Write a comprehensive, detailed, and well-structured "
            "research report answering the user's query: '{query}'\n"
            "Use the following research notes gathered from multiple sources.\n"
            "Synthesize the information logically. Resolve contradictions if possible, or highlight them.\n"
            "Cite the source URLs inline where appropriate. Write in Markdown format.\n\n"
            "Research Notes:\n{notes}"
        ).format(query=original_query, notes="\n\n---\n\n".join(facts))
        
        try:
            final_report = self.generate([{"role": "user", "content": synthesize_prompt}])
            return final_report.content or "No findings generated."
        except Exception as e:
            return f"Error synthesizing research report: {str(e)}"

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        self._step_callback = step_callback
        from discovery import active_agent_name
        token_agent = active_agent_name.set(self.name)
        
        try:
            if step_callback:
                step_callback("agent_start", self.name, query)
                
            initial_queries = self.generate_initial_queries(query)
            queue = [{"query": q, "depth": 0} for q in initial_queries]
            visited_queries = set()
            visited_urls = set()
            all_facts = []
            
            while queue:
                item = queue.pop(0)
                current_query = item["query"]
                depth = item["depth"]
                
                if current_query in visited_queries:
                    continue
                visited_queries.add(current_query)
                
                if depth > self.max_depth:
                    continue
                    
                self.log_thought(f"[Level {depth}] Searching web for: {current_query}")
                search_results_raw = self.call_tool("web_search", query=current_query)
                
                try:
                    results = json.loads(search_results_raw) if isinstance(search_results_raw, str) else search_results_raw
                    new_urls = []
                    if isinstance(results, list):
                        for r in results:
                            if isinstance(r, dict) and ("link" in r or "url" in r):
                                url = r.get("link") or r.get("url")
                                if url and url not in visited_urls:
                                    new_urls.append(url)
                except Exception:
                    # Fallback string parsing for text-formatted search results
                    new_urls = []
                    if isinstance(search_results_raw, str):
                        for line in search_results_raw.split('\n'):
                            if line.startswith("URL: ") or line.startswith("link: "):
                                url = line.split(":", 1)[1].strip()
                                if url and url not in visited_urls:
                                    new_urls.append(url)
                                
                new_urls = new_urls[:self.max_urls_per_query]
                
                if not new_urls:
                    self.log_thought(f"[Level {depth}] No new URLs found for query: {current_query}")
                    continue
                    
                self.log_thought(f"[Level {depth}] Found {len(new_urls)} URLs. Fetching them concurrently...")
                pages_content = self.fetch_pages_in_parallel(new_urls)
                
                # Marquer les URLs comme visitées même si elles ont échoué
                visited_urls.update(new_urls)
                
                if not pages_content:
                    self.log_thought(f"[Level {depth}] All fetched pages were empty or returned errors.")
                    continue
                    
                self.log_thought(f"[Level {depth}] Successfully fetched {len(pages_content)} pages. Extracting facts concurrently...")
                new_facts = self.extract_facts_in_parallel(pages_content, query)
                
                if new_facts:
                    all_facts.extend(new_facts)
                    self.log_thought(f"[Level {depth}] Extracted {len(new_facts)} facts.")
                    
                    if depth < self.max_depth:
                        self.log_thought(f"[Level {depth}] Generating follow-up queries based on new facts...")
                        follow_ups = self.generate_follow_up_queries(new_facts, query)
                        for fq in follow_ups:
                            if fq not in visited_queries:
                                queue.append({"query": fq, "depth": depth + 1})
                                
            final_report = self.synthesize_report(all_facts, query)
            
            if step_callback:
                step_callback("agent_done", self.name, "")
                
            return final_report
            
        except Exception as e:
            self.log_error(f"Deep Research failed: {e}")
            error_res = f"Deep Research failed due to an error: {e}"
            if step_callback:
                step_callback("agent_done", self.name, "")
            return error_res
        finally:
            active_agent_name.reset(token_agent)
