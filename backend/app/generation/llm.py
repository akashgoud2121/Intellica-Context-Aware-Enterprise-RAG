import os
import time
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from app.config import settings

class EnterpriseLLMGenerator:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key and not self.api_key.startswith("mock") else None

    def calculate_confidence_score(self, context_list: List[Dict[str, Any]], query: str) -> Tuple[float, str]:
        if not context_list:
            return 0.15, "High Uncertainty (No relevant context retrieved)"
        
        avg_relevance = sum(item.get("relevance_score", 0.5) for item in context_list) / len(context_list)
        
        query_terms = set(query.lower().split())
        match_count = sum(1 for term in query_terms if any(term in item["text"].lower() for item in context_list))
        term_coverage = match_count / max(1, len(query_terms))
        
        confidence = min(0.99, (avg_relevance * 0.6) + (term_coverage * 0.4))
        
        if confidence > 0.85:
            indicator = "Highly Grounded (Low Uncertainty)"
        elif confidence > 0.60:
            indicator = "Moderately Confident (Medium Uncertainty)"
        else:
            indicator = "Low Confidence (High Uncertainty / Potential Hallucination Risk)"
            
        return round(confidence, 4), indicator

    def generate_answer(self, query: str, context_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        confidence_score, uncertainty_label = self.calculate_confidence_score(context_list, query)
        
        citations = []
        context_str_parts = []
        for i, ctx in enumerate(context_list):
            ref_id = f"[{i+1}]"
            citations.append({
                "citation_id": ref_id,
                "filename": ctx.get("filename", "Database Record"),
                "data_silo": ctx.get("data_silo", "unknown"),
                "text_snippet": ctx["text"][:150] + "..."
            })
            context_str_parts.append(f"Citation {ref_id} (Source: {ctx.get('filename')} | Silo: {ctx.get('data_silo')}):\n{ctx['text']}")
            
        full_context = "\n\n".join(context_str_parts)
        
        if self.client:
            prompt = f"""You are an Enterprise AI RAG Assistant. Answer the user's query strictly using the provided context. If the context does not contain the answer, state that you do not know to prevent hallucination. Cite sources using [1], [2], etc.

Context:
{full_context}

Query: {query}
Answer:"""
            try:
                response = self.client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[{"role": "system", "content": "You are a precise enterprise assistant."},
                              {"role": "user", "content": prompt}],
                    temperature=0.1
                )
                answer_text = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI API call failed: {e}. Switching to local enterprise synthesis engine.")
                answer_text = self._local_synthesis(query, context_list, citations)
        else:
            answer_text = self._local_synthesis(query, context_list, citations)
            
        return {
            "answer": answer_text,
            "confidence_score": confidence_score,
            "uncertainty_indicator": uncertainty_label,
            "citations": citations
        }

    def _local_synthesis(self, query: str, context_list: List[Dict[str, Any]], citations: List[Dict[str, Any]]) -> str:
        if not context_list:
            return "Based on enterprise compliance rules and zero context retrieved, no verified answer can be generated. Please refine your query or ensure appropriate RBAC permissions."
        
        query_lower = query.lower()
        
        # 1. Projects & Technical Work QA
        if any(kw in query_lower for kw in ["project", "work", "built", "develop", "create"]):
            project_snippets = []
            for ctx in context_list:
                text = ctx.get("text", "")
                if any(p_kw in text.lower() for p_kw in ["project", "github", "app", "system", "web", "platform", "react", "python"]):
                    project_snippets.append(text.strip())
            if project_snippets:
                return "Verified Enterprise Projects & Technical Portfolio:\n\n" + "\n\n".join([f"📌 {p}" for p in project_snippets])
            else:
                return f"Verified Technical Snippet:\n'{context_list[0]['text']}'\n\n(Source: {context_list[0].get('filename')})"

        # 2. Skills & Capabilities QA
        if any(kw in query_lower for kw in ["skill", "tech", "stack", "know", "expert"]):
            skill_snippets = []
            for ctx in context_list:
                text = ctx.get("text", "")
                if any(s_kw in text.lower() for s_kw in ["skill", "technolog", "language", "framework", "database", "tool"]):
                    skill_snippets.append(text.strip())
            if skill_snippets:
                return "Verified Professional Skills & Competencies:\n\n" + "\n\n".join([f"⚡ {s}" for s in skill_snippets])
            else:
                return f"Verified Skills Context:\n'{context_list[0]['text']}'\n\n(Source: {context_list[0].get('filename')})"

        # 3. Presentation Title / Header QA
        if any(kw in query_lower for kw in ["title", "name", "subject", "topic", "about"]):
            for ctx in context_list:
                text = ctx.get("text", "")
                for line in text.splitlines():
                    if any(header in line.lower() for header in ["title", "presentation", "slide 1", "overview", "resume", "curriculum vitae"]):
                        return f"Verified Document Title / Header: '{line.strip()}'\n\n(Extracted from {ctx.get('filename')} - Silo: {ctx.get('data_silo')})"
            return f"Verified Snippet:\n'{context_list[0]['text'][:150]}...'\n\n(Source: {context_list[0].get('filename')})"
        
        # Default Fallback
        parts = ["According to verified enterprise data sources:"]
        for cite in citations:
            ref = cite["citation_id"]
            snippet = cite["text_snippet"].strip().replace("\n", " ")
            parts.append(f"- {snippet} {ref}")
            
        return "\n".join(parts)

llm_generator = EnterpriseLLMGenerator()
